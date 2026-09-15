"""Telemetry -> issues.

An agent cannot act on a telemetry dump. It acts on a small number of named problems, each
with a severity and a place to start reading. This is the step that makes the aggregate
useful: it turns a table of functions into a short list of things that are wrong.
"""

SLOW_MEAN_MS = 25.0      # a function this slow on average is worth an agent's attention
SLOW_MIN_CALLS = 20      # ...but only if it runs often enough to matter
ERROR_RATE_WARN = 0.01


def detect(snap):
    issues = []

    # 1. Exception clusters. One issue per fingerprint, not per crash.
    for exc in snap.get("exceptions", []):
        issues.append({
            "id": "EXC-" + exc["fingerprint"],
            "type": "exception",
            "severity": _severity_for_count(exc["count"]),
            "title": "%s in %s" % (
                exc["type"],
                exc["frames"][-1]["function"] if exc["frames"] else "unknown",
            ),
            "count": exc["count"],
            "function": exc["frames"][-1]["function"] if exc["frames"] else None,
            "message": exc["message"],
            "fingerprint": exc["fingerprint"],
        })

    # 2. Latency outliers. Only meaningful because durations were sampled continuously,
    #    including on calls that never threw — which is the data shape an error tracker
    #    does not have.
    for fn in snap.get("functions", []):
        mean = fn.get("mean_ms")
        if mean and mean >= SLOW_MEAN_MS and fn["calls"] >= SLOW_MIN_CALLS:
            issues.append({
                "id": "PERF-" + fn["key"].replace(":", "-"),
                "type": "performance",
                "severity": "high" if mean >= SLOW_MEAN_MS * 4 else "medium",
                "title": "%s averages %.1fms over %d calls" % (fn["key"], mean, fn["calls"]),
                "count": fn["calls"],
                "function": fn["key"],
                "mean_ms": mean,
                "max_ms": fn.get("max_ms"),
            })

    # 3. Functions that fail often enough to be structurally wrong rather than unlucky.
    for fn in snap.get("functions", []):
        if fn.get("error_rate", 0) > ERROR_RATE_WARN and fn["errors"] > 1:
            issues.append({
                "id": "RATE-" + fn["key"].replace(":", "-"),
                "type": "error_rate",
                "severity": "high" if fn["error_rate"] > 0.05 else "medium",
                "title": "%s fails %.1f%% of the time (%d/%d)" % (
                    fn["key"], fn["error_rate"] * 100, fn["errors"], fn["calls"]),
                "count": fn["errors"],
                "function": fn["key"],
                "error_rate": fn["error_rate"],
            })

    # Rank by severity, then by KIND, and only then by count.
    #
    # The kind tiebreak matters and is easy to get wrong. `count` means a different thing for
    # each issue type -- failures for an exception, total invocations for a latency outlier --
    # so comparing the two numbers directly is meaningless and lets a merely-slow function
    # outrank a crash simply because it runs more often. An on-call engineer triages
    # correctness before latency; so does this.
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    kind_rank = {"exception": 0, "error_rate": 1, "performance": 2}
    issues.sort(key=lambda i: (
        severity_rank.get(i["severity"], 9),
        kind_rank.get(i["type"], 9),
        -i["count"],
    ))
    return issues


def _severity_for_count(count):
    if count >= 50:
        return "critical"
    if count >= 10:
        return "high"
    if count >= 3:
        return "medium"
    return "low"


def find(snap, issue_id):
    for issue in detect(snap):
        if issue["id"] == issue_id:
            return issue
    return None


def forensics_for(snap, fingerprint):
    for exc in snap.get("exceptions", []):
        if exc["fingerprint"] == fingerprint:
            return exc
    return None


def function_stats(snap, key):
    for fn in snap.get("functions", []):
        if fn["key"] == key:
            return fn
    return None


def call_graph(snap, key):
    """Callers and callees of one function — the blast radius an agent needs before it
    changes a signature or a return type."""
    callers, callees = [], []
    for edge, count in snap.get("edges", {}).items():
        src, _, dst = edge.partition(" -> ")
        if dst == key:
            callers.append({"function": src, "calls": count})
        if src == key:
            callees.append({"function": dst, "calls": count})
    callers.sort(key=lambda e: -e["calls"])
    callees.sort(key=lambda e: -e["calls"])
    return {"function": key, "called_by": callers, "calls_into": callees}
