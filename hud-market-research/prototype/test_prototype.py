"""Self-checks for the prototype. Stdlib unittest, no dependencies.

    python3 -m unittest test_prototype -v
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hud_lite import issues, prompts, store
from hud_lite.hook import Sensor, _should_time

HERE = os.path.dirname(os.path.abspath(__file__))


class TestRedaction(unittest.TestCase):
    def test_secret_names_are_never_recorded(self):
        for name in ["password", "API_KEY", "db_secret", "auth_token", "session_cookie"]:
            self.assertEqual(store.redact(name, "hunter2"), "<redacted>", name)

    def test_ordinary_values_survive(self):
        self.assertEqual(store.redact("price_cents", 53452), "53452")

    def test_long_values_are_bounded(self):
        out = store.redact("blob", "x" * 5000)
        self.assertLess(len(out), 300)
        self.assertIn("chars)", out)

    def test_a_throwing_repr_does_not_take_the_sensor_down(self):
        class Hostile:
            def __repr__(self):
                raise ValueError("nope")

        self.assertIn("unreprable", store.redact("thing", Hostile()))


class TestSampling(unittest.TestCase):
    def test_early_calls_are_always_timed(self):
        self.assertTrue(all(_should_time(n) for n in range(20)))

    def test_hot_calls_are_timed_rarely(self):
        sampled = sum(1 for n in range(2000, 5000) if _should_time(n))
        self.assertLessEqual(sampled, 5)


class TestFingerprint(unittest.TestCase):
    def test_same_crash_site_collapses_to_one_issue(self):
        frames = [{"function": "a.py:f", "file": "a.py"}]
        self.assertEqual(
            store.fingerprint("TypeError", frames),
            store.fingerprint("TypeError", frames),
        )

    def test_different_crash_sites_stay_separate(self):
        self.assertNotEqual(
            store.fingerprint("TypeError", [{"function": "a.py:f", "file": "a.py"}]),
            store.fingerprint("TypeError", [{"function": "b.py:g", "file": "b.py"}]),
        )


class TestSensor(unittest.TestCase):
    def test_it_records_calls_edges_and_unsampled_exceptions(self):
        sensor = Sensor(app_root=HERE).install()
        try:
            for _ in range(5):
                with sensor.watching():
                    _outer()
        except Exception:
            pass
        finally:
            sensor.uninstall()

        snap = sensor.store.snapshot()
        keys = {f["key"] for f in snap["functions"]}
        self.assertIn("test_prototype.py:_outer", keys)
        self.assertIn("test_prototype.py:_inner", keys)
        self.assertTrue(any("_outer -> " in e for e in snap["edges"]))
        self.assertEqual(len(snap["exceptions"]), 1)

    def test_it_never_instruments_itself(self):
        sensor = Sensor(app_root=os.path.dirname(HERE)).install()
        try:
            _outer_safe()
        finally:
            sensor.uninstall()
        keys = {f["key"] for f in sensor.store.snapshot()["functions"]}
        self.assertFalse([k for k in keys if k.startswith(("hook.py", "store.py"))], keys)

    def test_forensics_capture_locals_at_the_moment_of_failure(self):
        sensor = Sensor(app_root=HERE)
        try:
            _boom(discount_bps="150")
        except TypeError as exc:
            sensor.capture(exc)
        frame = sensor.store.snapshot()["exceptions"][0]["frames"][-1]
        self.assertEqual(frame["locals"]["discount_bps"], "'150'")
        self.assertEqual(frame["file"], "test_prototype.py")  # relative, never absolute


class TestIssuesAndPrompts(unittest.TestCase):
    def setUp(self):
        self.snap = {
            "functions": [{
                "key": "svc.py:charge", "file": "svc.py", "line": 1, "calls": 500,
                "timed": 40, "errors": 30, "error_rate": 0.06, "mean_ms": 120.0, "max_ms": 400.0,
            }],
            "edges": {"svc.py:handler -> svc.py:charge": 500},
            "exceptions": [{
                "fingerprint": "deadbeef", "type": "TypeError", "message": "bad operand",
                "count": 30, "first_seen": 0, "last_seen": 1,
                "frames": [{"function": "svc.py:charge", "file": "svc.py", "line": 9,
                            "source": "x // y", "locals": {"y": "'150'"}}],
            }],
        }

    def test_all_three_issue_kinds_are_detected(self):
        kinds = {i["type"] for i in issues.detect(self.snap)}
        self.assertEqual(kinds, {"exception", "performance", "error_rate"})

    def test_high_volume_exceptions_rank_first(self):
        self.assertEqual(issues.detect(self.snap)[0]["type"], "exception")

    def test_call_graph_reports_real_callers(self):
        graph = issues.call_graph(self.snap, "svc.py:charge")
        self.assertEqual(graph["called_by"][0]["function"], "svc.py:handler")

    def test_the_prompt_names_tools_instead_of_inlining_context(self):
        prompt = prompts.fix_prompt(issues.detect(self.snap)[0])
        for tool in ["get_issue", "get_function_stats", "get_call_graph"]:
            self.assertIn(tool, prompt)
        # MCP-not-inline: the prompt must not carry the forensics payload itself.
        self.assertNotIn("bad operand", prompt)

    def test_the_prompt_hands_the_pr_to_github_mcp(self):
        prompt = prompts.fix_prompt(issues.detect(self.snap)[0])
        for step in ["GitHub MCP", "create_branch", "create_pull_request"]:
            self.assertIn(step, prompt)

    def test_every_issue_kind_produces_a_prompt(self):
        for issue in issues.detect(self.snap):
            self.assertIn("## Investigate", prompts.fix_prompt(issue))


class TestMcpProtocol(unittest.TestCase):
    def test_a_full_handshake_over_stdio(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump({"functions": [], "edges": {}, "exceptions": []}, fh)
            path = fh.name
        try:
            requests = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                 "params": {"name": "list_issues", "arguments": {}}},
            ]
            proc = subprocess.run(
                [sys.executable, "-m", "hud_lite.mcp_server", "--data", path],
                input="\n".join(json.dumps(r) for r in requests),
                capture_output=True, text=True, cwd=HERE, timeout=30,
            )
            replies = [json.loads(l) for l in proc.stdout.strip().splitlines()]
        finally:
            os.unlink(path)

        # The notification must not get a reply; the three requests must.
        self.assertEqual([r["id"] for r in replies], [1, 2, 3])
        self.assertEqual(replies[0]["result"]["serverInfo"]["name"], "hud-lite")
        self.assertEqual(len(replies[1]["result"]["tools"]), 5)
        self.assertIn("content", replies[2]["result"])


# -- fixtures used by the sensor tests ------------------------------------------------

def _inner():
    raise ValueError("boom")


def _outer():
    return _inner()


def _outer_safe():
    return sum(range(10))


def _boom(discount_bps):
    return 100 * discount_bps // 10000


if __name__ == "__main__":
    unittest.main()
