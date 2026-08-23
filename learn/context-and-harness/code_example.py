#!/usr/bin/env python3
"""
The model is stateless. The harness rebuilds the prefix every turn.

Toy harness: tools | system | messages, a prefix-hash cache (0.1x hit, 1.25x
write), and compaction when the notebook exceeds a ceiling. Three runs —
stable prefix, a timestamp in the system prompt, then a compact rewrite —
print who did what (harness vs model) and the effective token bill.

Run:  python3 code_example.py
"""

TOOLS, SYSTEM, USER, REPLY = 90, 40, 12, 20
READ, WRITE, LIMIT = 0.10, 1.25, 220


def run(name, turns=8, volatile=False, compact=False):
    tools, system, messages = TOOLS, SYSTEM, 0
    cached, bill, events = None, 0.0, []
    for t in range(1, turns + 1):
        sys = system + t if volatile else system
        if compact and tools + sys + messages + USER > LIMIT:
            messages = 50
            cached = None
            extra = " + compacted"
        else:
            extra = ""
        front = (tools, sys, messages)
        sent = tools + sys + messages + USER
        if front == cached:
            bill += (tools + sys + messages) * READ + USER
            who = f"harness: built prefix{extra} / cache hit 0.1x on front"
        else:
            bill += sent * WRITE
            who = f"harness: built prefix{extra} / cache write 1.25x"
        messages += USER + REPLY
        cached = (tools, sys, messages)
        events.append((t, sent, who, "model: emitted reply"))
    print(f"\n== {name} ==")
    for t, n, h, m in events:
        print(f"  turn {t}: {n:3d} tokens sent")
        print(f"           {h}")
        print(f"           {m}")
    print(f"  effective tokens billed: {bill:.1f}")
    return bill


def main():
    print("Prefix order every turn: tools | system | messages")
    print("Model generates. Harness assembles, caches, and cuts.")
    a = run("stable prefix")
    b = run("timestamp in system prompt", volatile=True)
    c = run("compact when over ceiling", compact=True)
    print("\nSAME 8 TURNS")
    print(f"  stable:    {a:.1f}")
    print(f"  volatile:  {b:.1f}   (thrash pays write every turn)")
    print(f"  compact:   {c:.1f}   (smaller notebook, new prefix, cache write)")
    print("\nDaily lab 2026-08-22 prices this on a 60-turn session.")


if __name__ == "__main__":
    main()
