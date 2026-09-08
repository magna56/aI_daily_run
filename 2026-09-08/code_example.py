"""A PreToolUse hook, from scratch, and what it saves.

Implements the Claude Code hook contract with nothing but the standard library:
read the pending tool call as JSON on stdin, decide, print a decision. Then
prices the decision, because the reason a blocked read matters is not the one
turn you skipped -- it is every turn afterwards that no longer carries the file.

Run:  python3 code_example.py
As a real hook:  echo '<event json>' | python3 code_example.py --hook

Raise MIN_LINES past a file's length and watch the same call go from deny to
allow, which is the only knob this whole technique has.
"""

import json
import sys

MIN_LINES = 350           # the threshold, and the entire policy
BYTES_PER_TOKEN = 4       # rough, and only used to compare against itself
TURNS_AFTER = 8           # how many more turns the session runs


def decide(event, min_lines=MIN_LINES, line_count=None):
    """The hook itself. Returns the JSON to print, or None to stay quiet.

    Staying quiet matters: an absent permissionDecision falls through to the
    normal permission flow. A hook that answers every call has to be right
    about every call.
    """
    ti = event.get("tool_input", {})
    path = ti.get("file_path", "")

    # A bounded read is already the behavior we want. Never punish it.
    if ti.get("offset") is not None or ti.get("limit") is not None:
        return None

    n = line_count if line_count is not None else _count(path)
    if n is None or n <= min_lines:
        return None

    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason":
            "%s is %d lines. Summarize it with /bulk-reader, or re-read with "
            "offset and limit if you need one region." % (path, n),
    }}


def _count(path):
    try:
        with open(path, "rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return None            # not our business; let normal flow handle it


def tokens(text):
    return max(1, round(len(text) / BYTES_PER_TOKEN))


def cost(event, decision, file_bytes):
    """What lands in the context this turn, and what it still costs later."""
    if decision is None:
        first = round(file_bytes / BYTES_PER_TOKEN)
        what = "the whole file"
    else:
        first = tokens(decision["hookSpecificOutput"]["permissionDecisionReason"])
        what = "one sentence"
    return first, first * (TURNS_AFTER + 1), what


def main():
    if "--hook" in sys.argv:                      # real hook mode
        out = decide(json.load(sys.stdin))
        if out:
            print(json.dumps(out))
        return 0

    call = {"hook_event_name": "PreToolUse", "tool_name": "Read",
            "tool_input": {"file_path": "src/main/java/PaymentRouter.java"}}

    print("One Read call, three ways\n")
    print("  %-28s %-9s %11s %14s" % ("scenario", "decision", "this turn", "after %d turns" % TURNS_AFTER))

    rows = [
        ("4,012-line file, no hook", 4012, 168_000, dict(call), 10 ** 9),
        ("4,012-line file, hook on", 4012, 168_000, dict(call), MIN_LINES),
        ("40-line file", 40, 1_700, dict(call), MIN_LINES),
    ]
    for label, lines, nbytes, ev, thresh in rows:
        d = decide(ev, min_lines=thresh, line_count=lines)
        first, total, what = cost(ev, d, nbytes)
        print("  %-28s %-9s %10s %13s   (%s)"
              % (label, "deny" if d else "allow",
                 "{:,}".format(first), "{:,}".format(total), what))

    # The bounded read is the escape hatch, and it has to keep working.
    bounded = dict(call)
    bounded["tool_input"] = dict(call["tool_input"], offset=120, limit=60)
    print("  %-28s %-9s %10s %13s   (%s)"
          % ("same file, offset+limit", "allow" if decide(bounded, line_count=4012) is None
             else "deny", "2,520", "22,680", "60 lines"))

    print("\nWhat the model is told when the read is denied\n")
    d = decide(dict(call), line_count=4012)
    print("  " + d["hookSpecificOutput"]["permissionDecisionReason"])
    print("\n  That sentence is the whole cost of not reading the file. It is also the")
    print("  part people leave out: a deny with no alternative makes the agent worse,")
    print("  because the model has been stopped without being redirected.")

    print("\n  Note the third row. The hook returns nothing for a small file, so the call")
    print("  goes through the normal permission flow — a hook that answers every call")
    print("  has to be right about every call.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
