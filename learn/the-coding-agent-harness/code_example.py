#!/usr/bin/env python3
"""
A coding agent is a host loop: model → permission → tool → append →
(compact if full) → repeat. Sub-agents keep bulky reads out of the parent.

Pure stdlib.  Run:  python3 code_example.py
"""

SYSTEM, TOOL_SCHEMAS = 2500, 200 + 180 + 220 + 400  # read, edit, bash, mcp
BIG_READ, SUMMARY, EDIT, BASH, USER, REPLY = 6000, 200, 80, 60, 40, 90
COMPACT_AT, COMPACT_TO = 8000, 2200
POLICY = {"read": "allow", "edit": "ask", "bash": "ask", "rm": "deny"}


def decide(tool, approved):
    rule = POLICY[tool]
    if rule == "deny":
        return "deny"
    if rule == "allow":
        return "allow"
    return "allow" if approved else "ask-blocked"


def compact(tokens):
    return COMPACT_TO if tokens >= COMPACT_AT else tokens


def run(use_subagent, approve_ask=True):
    parent = SYSTEM + TOOL_SCHEMAS
    child = 0
    peak = parent
    log = []

    def bill(delta, where="parent"):
        nonlocal parent, child, peak
        if where == "child":
            child += delta
        else:
            parent += delta
            peak = max(peak, parent)
            before = parent
            parent = compact(parent)
            if parent != before:
                log.append(f"autocompact {before} → {parent}")

    bill(USER + REPLY)
    for i in range(3):
        d = decide("read", True)
        log.append(f"read[{i}] {d}")
        if use_subagent:
            child += SYSTEM + 200 + BIG_READ + SUMMARY
            bill(SUMMARY)
        else:
            bill(BIG_READ)
    for tool, delta in (("edit", EDIT), ("bash", BASH), ("rm", 0)):
        d = decide(tool, approve_ask)
        log.append(f"{tool} {d}")
        if d == "allow":
            bill(delta + REPLY)
        else:
            bill(40)
    return parent, child, peak, log


def main():
    print("Policy:", POLICY)
    print(f"Compact when parent ≥ {COMPACT_AT}; keep ~{COMPACT_TO}\n")
    for name, sub, ask in (
        ("inline reads, asks approved", False, True),
        ("inline reads, asks refused", False, False),
        ("sub-agent reads, asks approved", True, True),
    ):
        parent, child, peak, log = run(sub, ask)
        print(f"== {name} ==")
        print("  " + " · ".join(log))
        print(f"  parent now {parent:,}   peak {peak:,}   child {child:,}")
        print()
    p_inline, _, peak_inline, _ = run(False, True)
    p_sub, c_sub, peak_sub, _ = run(True, True)
    print("Same three 6,000-token reads:")
    print(f"  inlined: parent now {p_inline:,} (peak {peak_inline:,} — compact thrashed)")
    print(f"  child:   parent now {p_sub:,} (peak {peak_sub:,}) + child {c_sub:,}")
    print("The model only emitted tool calls. The harness decided the rest.")


if __name__ == "__main__":
    main()
