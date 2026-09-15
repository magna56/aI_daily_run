"""Aggregated runtime store.

This is the piece that makes the whole approach cheap. Hud's stated design is to skip
distributed tracing entirely and instead keep a rolling *aggregate* of how each function
behaves, plus an unsampled record of every exception. Aggregates are O(number of functions),
not O(number of requests), so the memory footprint stops growing while traffic keeps rising.
"""

import hashlib
import json
import os
import re
import time

# Locals whose names look like credentials are never recorded. The sensor runs in production
# and its output is read by an agent and pasted into a PR, so this filter is load-bearing.
_SECRET_RE = re.compile(
    r"(pass|pwd|secret|token|api[_-]?key|auth|credential|cookie|session|private)", re.I
)
_MAX_REPR = 200
_MAX_EXCEPTIONS = 500


def redact(name, value):
    """Return a bounded, secret-safe repr of one local variable."""
    if _SECRET_RE.search(name):
        return "<redacted>"
    try:
        text = repr(value)
    except Exception as exc:  # a __repr__ that throws must not take the sensor down
        return "<unreprable: %s>" % type(exc).__name__
    if len(text) > _MAX_REPR:
        text = text[:_MAX_REPR] + "... (%d chars)" % len(text)
    return text


def fingerprint(exc_type, frames):
    """Collapse many crashes into one issue.

    The fingerprint is the exception type plus the innermost *application* frame. That is what
    turns 4,812 stack traces into one issue an agent can reason about, and it is why the prompt
    handed to the agent stays small enough to fit in context.
    """
    top = frames[-1] if frames else {"function": "?", "file": "?"}
    raw = "%s|%s|%s" % (exc_type, top.get("file"), top.get("function"))
    return hashlib.sha1(raw.encode()).hexdigest()[:8]


class RuntimeStore:
    def __init__(self):
        self.functions = {}
        self.edges = {}
        self.exceptions = []
        self.started_at = time.time()

    # -- function-level aggregates ---------------------------------------------------

    def _fn(self, key, file, line):
        fn = self.functions.get(key)
        if fn is None:
            fn = {
                "key": key,
                "file": file,
                "line": line,
                "calls": 0,
                "timed": 0,      # how many calls we actually measured
                "total_ns": 0,
                "max_ns": 0,
                "errors": 0,
                "first_seen": time.time(),
            }
            self.functions[key] = fn
        return fn

    def record_call(self, key, file, line):
        self._fn(key, file, line)["calls"] += 1

    def record_duration(self, key, ns):
        fn = self.functions.get(key)
        if fn is None:
            return
        fn["timed"] += 1
        fn["total_ns"] += ns
        if ns > fn["max_ns"]:
            fn["max_ns"] = ns

    def record_edge(self, caller, callee):
        k = caller + " -> " + callee
        self.edges[k] = self.edges.get(k, 0) + 1

    # -- exceptions: never sampled ---------------------------------------------------

    def record_exception(self, exc_type, message, frames):
        fp = fingerprint(exc_type, frames)
        if frames:
            fn = self.functions.get(frames[-1]["function"])
            if fn is not None:
                fn["errors"] += 1
        # Keep full forensics for the first sighting of each fingerprint and count the rest.
        # An agent needs one good crash, not a thousand identical ones.
        for rec in self.exceptions:
            if rec["fingerprint"] == fp:
                rec["count"] += 1
                rec["last_seen"] = time.time()
                return fp
        if len(self.exceptions) < _MAX_EXCEPTIONS:
            self.exceptions.append({
                "fingerprint": fp,
                "type": exc_type,
                "message": message,
                "count": 1,
                "first_seen": time.time(),
                "last_seen": time.time(),
                "frames": frames,
            })
        return fp

    # -- persistence -----------------------------------------------------------------

    def snapshot(self):
        out = []
        for fn in self.functions.values():
            rec = dict(fn)
            rec["mean_ms"] = round(fn["total_ns"] / fn["timed"] / 1e6, 3) if fn["timed"] else None
            rec["max_ms"] = round(fn["max_ns"] / 1e6, 3) if fn["max_ns"] else None
            rec["error_rate"] = round(fn["errors"] / fn["calls"], 4) if fn["calls"] else 0.0
            out.append(rec)
        out.sort(key=lambda r: -r["calls"])
        return {
            "collected_for_seconds": round(time.time() - self.started_at, 1),
            "functions": out,
            "edges": self.edges,
            "exceptions": self.exceptions,
        }

    def save(self, path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as fh:
            json.dump(self.snapshot(), fh, indent=2)
        return path


def load(path):
    with open(path) as fh:
        return json.load(fh)
