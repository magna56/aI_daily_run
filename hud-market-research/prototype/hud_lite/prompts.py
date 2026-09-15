"""Prompt to Fix.

The centerpiece of the whole design, and the part worth studying rather than skimming.

The naive version of this feature inlines the forensics into a prompt blob and hands it over.
Hud explicitly does not do that: the prompt is *MCP-based rather than context-inlined*, meaning
it tells the agent WHICH TOOLS TO CALL instead of pasting the answer in.

Three reasons that is the better design, all of which this module is built to demonstrate:

  1. Investigation beats export. An inlined blob caps the agent at whatever the issue page
     decided to include. A tool list lets the agent form a hypothesis, fetch more, and revise.
  2. Context economy. The prompt stays a few hundred tokens no matter how much runtime data
     exists behind it. The agent pulls only the slice it needs.
  3. It is the defensible business choice. An export is a one-shot file any competitor can
     reproduce. A tool surface the agent calls repeatedly, every investigation, becomes the
     thing the workflow is built around.

Note what the last line of every prompt does: it hands off to GitHub MCP. This module never
writes a patch and never opens a PR. That division of labor is the product strategy, not an
implementation shortcut — see research/02-architecture.md, "Hop 4 — who opens the PR".
"""

_HEADER = """You are fixing a real production issue detected by a runtime code sensor.

The sensor observed this in the live system. Do not assume you can reproduce it locally:
it is load-, data- or environment-dependent, which is why it reached production at all.

## Issue
  id:       {id}
  type:     {type}
  severity: {severity}
  summary:  {title}
  observed: {count} time(s)
"""

_FOOTER = """
## Rules
- Fix the root cause the runtime data points at, not the symptom in the stack trace.
- Before you change any signature or return type, call `get_call_graph` and account for
  every caller. The sensor knows the real callers; the repo's grep does not know which of
  them actually execute.
- Do not add a broad try/except to make the error disappear. The sensor will keep seeing it.
- If the runtime data contradicts what the code looks like it should do, trust the runtime data.

## When you have the fix
Use the **GitHub MCP server** to ship it:
  1. `create_branch`     -> fix/{id_slug}
  2. `create_or_update_file` (or `push_files`) with the patch
  3. `create_pull_request` titled "{title}"
     In the body, state: what the sensor observed, the root cause, the fix, and how the
     sensor will confirm it worked ({verify}).
Leave the PR for human review. Do not merge it.
"""

_EXCEPTION_BODY = """
## Investigate — call these tools in this order
1. `get_issue("{id}")`
   Returns the full forensics captured at the moment of failure: every application frame,
   and the LOCAL VARIABLE VALUES in each one. Read the locals first. They usually contain
   the answer, and they are the one thing a stack trace in a log file can never give you.
2. `get_function_stats("{function}")`
   How often this function runs and what fraction of those runs fail. A 0.4% failure rate
   and a 40% failure rate need completely different fixes.
3. `get_call_graph("{function}")`
   Who actually calls this in production. Fix it for all of them.
"""

_PERF_BODY = """
## Investigate — call these tools in this order
1. `get_function_stats("{function}")`
   Mean and max duration, call volume, and how many calls were actually measured. The sensor
   samples durations incrementally, so `timed` will be far lower than `calls` — that is
   expected and the mean is still representative.
2. `get_call_graph("{function}")`
   Look at `calls_into` with high counts. A function that is slow because it calls something
   else N times has a different fix from one that is slow on its own.
3. `list_issues()`
   Check whether anything downstream is also flagged before you optimize the wrong hop.
"""

_RATE_BODY = """
## Investigate — call these tools in this order
1. `get_function_stats("{function}")` — confirm the failure rate and the call volume.
2. `list_issues()` — find the EXC-* issue for this function; that one carries the forensics.
3. `get_issue("<that EXC id>")` — read the locals at the moment of failure.
4. `get_call_graph("{function}")` — decide whether the bad input originates here or upstream.
   A high failure rate concentrated in one caller means the bug is in the caller.
"""

_BODIES = {"exception": _EXCEPTION_BODY, "performance": _PERF_BODY, "error_rate": _RATE_BODY}

_VERIFY = {
    "exception": "the exception fingerprint stops appearing in new sensor data",
    "performance": "mean duration for this function drops below the threshold",
    "error_rate": "the failure rate for this function returns to zero",
}


def fix_prompt(issue):
    """Build the ready-to-send prompt for one issue. This is the 'one click'."""
    body = _BODIES.get(issue["type"], _EXCEPTION_BODY)
    fields = {
        "id": issue["id"],
        "id_slug": issue["id"].lower(),
        "type": issue["type"],
        "severity": issue["severity"],
        "title": issue["title"],
        "count": issue["count"],
        "function": issue.get("function") or "unknown",
        "verify": _VERIFY.get(issue["type"], "the issue stops being reported"),
    }
    return (_HEADER + body + _FOOTER).format(**fields)
