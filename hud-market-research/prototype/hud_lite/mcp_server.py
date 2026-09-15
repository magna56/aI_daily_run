"""MCP server — the surface a coding agent actually talks to.

Speaks JSON-RPC 2.0 over stdio with newline-delimited messages, which is MCP's stdio
transport. No dependencies: the protocol is small enough to implement directly, and doing so
makes it obvious how little sits between a runtime sensor and a coding agent.

Run it:
    python3 -m hud_lite.mcp_server --data .hud-demo/runtime.json          # serve over stdio
    python3 -m hud_lite.mcp_server --data .hud-demo/runtime.json --demo   # print every tool

Wire it into Claude Code:
    claude mcp add hud-lite -- python3 -m hud_lite.mcp_server --data /abs/path/runtime.json
"""

import argparse
import json
import os
import sys

from . import issues as _issues
from . import prompts as _prompts
from . import store as _store

PROTOCOL_VERSION = "2025-06-18"

TOOLS = [
    {
        "name": "list_issues",
        "description": (
            "List production issues the runtime sensor has detected, most severe first. "
            "Start here. Each issue has an id you can pass to get_issue or get_fix_prompt."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "description": "Optional filter: critical, high, medium or low.",
                }
            },
        },
    },
    {
        "name": "get_issue",
        "description": (
            "Full forensics for one issue, captured at the moment of failure in production: "
            "every application stack frame with its source line and its LOCAL VARIABLE VALUES. "
            "The locals are the part you cannot get from a log file or by reading the repo."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"issue_id": {"type": "string"}},
            "required": ["issue_id"],
        },
    },
    {
        "name": "get_function_stats",
        "description": (
            "Aggregated runtime behavior of one function: invocation count, mean and max "
            "duration, and error rate. Covers the calls that succeeded as well as the ones "
            "that threw, so you can tell a always-broken function from a rarely-broken one."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"function": {"type": "string"}},
            "required": ["function"],
        },
    },
    {
        "name": "get_call_graph",
        "description": (
            "Who calls this function and what it calls, with real production call counts. "
            "Use this for blast radius before changing a signature: it reflects the callers "
            "that actually execute, which is a smaller and different set than grep finds."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"function": {"type": "string"}},
            "required": ["function"],
        },
    },
    {
        "name": "get_fix_prompt",
        "description": (
            "The 'Prompt to Fix' for one issue: a ready-to-run instruction telling a coding "
            "agent which of these tools to call, in what order, and how to ship the result as "
            "a pull request through the GitHub MCP server."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"issue_id": {"type": "string"}},
            "required": ["issue_id"],
        },
    },
]


class HudLiteServer:
    def __init__(self, data_path):
        self.data_path = data_path

    def snapshot(self):
        # Re-read on every call: production data is live, and an agent mid-investigation
        # should see what the sensor sees now, not what it saw when the server booted.
        if not os.path.exists(self.data_path):
            raise RuntimeError(
                "No runtime data at %s. Run demo_app.py first." % self.data_path
            )
        return _store.load(self.data_path)

    # -- tools ---------------------------------------------------------------------

    def list_issues(self, severity=None):
        found = _issues.detect(self.snapshot())
        if severity:
            found = [i for i in found if i["severity"] == severity]
        return {"count": len(found), "issues": found}

    def get_issue(self, issue_id):
        snap = self.snapshot()
        issue = _issues.find(snap, issue_id)
        if issue is None:
            return {"error": "no such issue: %s" % issue_id}
        out = dict(issue)
        if issue.get("fingerprint"):
            forensics = _issues.forensics_for(snap, issue["fingerprint"])
            if forensics:
                out["forensics"] = {
                    "exception": "%s: %s" % (forensics["type"], forensics["message"]),
                    "occurrences": forensics["count"],
                    "frames": forensics["frames"],
                }
        if issue.get("function"):
            out["function_stats"] = _issues.function_stats(snap, issue["function"])
        return out

    def get_function_stats(self, function):
        fn = _issues.function_stats(self.snapshot(), function)
        if fn is None:
            return {"error": "function not observed at runtime: %s" % function}
        return fn

    def get_call_graph(self, function):
        return _issues.call_graph(self.snapshot(), function)

    def get_fix_prompt(self, issue_id):
        issue = _issues.find(self.snapshot(), issue_id)
        if issue is None:
            return {"error": "no such issue: %s" % issue_id}
        return {"issue_id": issue_id, "prompt": _prompts.fix_prompt(issue)}

    def call(self, name, args):
        fn = getattr(self, name, None)
        if fn is None or name not in {t["name"] for t in TOOLS}:
            return {"error": "unknown tool: %s" % name}
        return fn(**args)

    # -- JSON-RPC ------------------------------------------------------------------

    def handle(self, msg):
        method = msg.get("method")
        msg_id = msg.get("id")

        if method == "initialize":
            result = {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "hud-lite", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = msg.get("params", {})
            try:
                payload = self.call(params.get("name"), params.get("arguments") or {})
                result = {
                    "content": [
                        {"type": "text", "text": json.dumps(payload, indent=2, default=str)}
                    ]
                }
            except Exception as exc:
                result = {
                    "content": [{"type": "text", "text": "tool failed: %s" % exc}],
                    "isError": True,
                }
        elif method is not None and method.startswith("notifications/"):
            return None  # notifications get no response
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": "method not found: %s" % method},
            }

        if msg_id is None:
            return None
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def serve_stdio(self):
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            response = self.handle(msg)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()


def _demo(server):
    """Print what an agent would see, without needing an MCP client attached."""
    rule = "=" * 78
    print(rule + "\n1. list_issues()  -- the agent's entry point\n" + rule)
    listing = server.list_issues()
    for issue in listing["issues"]:
        print("  [%-8s] %-34s %s" % (issue["severity"], issue["id"], issue["title"]))

    if not listing["issues"]:
        print("  (no issues detected)")
        return

    top = next((i for i in listing["issues"] if i["type"] == "exception"), listing["issues"][0])

    print("\n" + rule + "\n2. get_issue(%r)  -- forensics from the moment of failure\n" % top["id"] + rule)
    detail = server.get_issue(top["id"])
    forensics = detail.get("forensics")
    if forensics:
        print("  %s  (seen %d times)" % (forensics["exception"], forensics["occurrences"]))
        for frame in forensics["frames"]:
            print("    %s:%s  in %s" % (frame["file"], frame["line"], frame["function"]))
            print("      %s" % frame["source"])
            for name, value in frame["locals"].items():
                print("        %-14s = %s" % (name, value))
    else:
        print(json.dumps(detail, indent=2, default=str))

    if top.get("function"):
        print("\n" + rule + "\n3. get_call_graph(%r)  -- blast radius\n" % top["function"] + rule)
        print(json.dumps(server.get_call_graph(top["function"]), indent=2))

    print("\n" + rule + "\n4. get_fix_prompt(%r)  -- the one click\n" % top["id"] + rule)
    print(server.get_fix_prompt(top["id"])["prompt"])


def main(argv=None):
    parser = argparse.ArgumentParser(description="hud-lite MCP server")
    parser.add_argument("--data", default=".hud-demo/runtime.json",
                        help="path to the runtime snapshot written by the sensor")
    parser.add_argument("--demo", action="store_true",
                        help="print each tool's output instead of serving stdio")
    args = parser.parse_args(argv)

    server = HudLiteServer(args.data)
    if args.demo:
        _demo(server)
    else:
        server.serve_stdio()


if __name__ == "__main__":
    main()
