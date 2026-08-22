#!/usr/bin/env python3
"""
Your context window is a budget you re-pay every turn.

An agent transcript is an append-only log that is re-read on EVERY turn, so a
token's real cost is its size times the number of turns that come after it.
Prompt caching discounts that re-read 10x -- but only for the prefix bytes you
never touch, and it charges a 1.25x premium on everything you do touch.

Priced with published claude-opus-5 rates ($5 / 1M input tokens) and the
documented cache multipliers: read 0.1x, 5-minute write 1.25x. Input only --
output is billed once at $25/1M and barely differs between these strategies.

Pure stdlib.  Run:  python3 code_example.py
"""

PRICE_IN = 5.00 / 1_000_000  # claude-opus-5 input, $/token
READ = 0.10                  # cache read multiplier
WRITE = 1.25                 # cache write multiplier, 5-minute TTL

SYSTEM = 3_000       # system prompt + CLAUDE.md
TOOLS = 9_000        # tool schemas, incl. a couple of chatty MCP servers
USER = 120           # a typical user turn
REPLY = 400          # a typical assistant turn
BIG = 6_000          # one file read / grep dump
SUMMARY = 300        # what a subagent hands back instead
EVERY = 3            # a big read every third turn
SUB_TOOLS, TASK = 2_000, 200


def simulate(mode, turns=60):
    """Return (main_tokens, subagent_tokens, final_prefix) in *effective* tokens."""
    prefix, cached, billed, sub = SYSTEM + TOOLS, 0, 0.0, 0.0
    for turn in range(1, turns + 1):
        prefix += USER
        if mode == "thrash":
            cached = 0  # a timestamp at position 0 killed the whole prefix
        if mode == "nocache":
            billed += prefix
        else:
            billed += cached * READ + (prefix - cached) * WRITE
            cached = prefix
        prefix += REPLY
        if turn % EVERY == 0:
            if mode == "offload":
                prefix += SUMMARY
                sub += subagent()
            else:
                prefix += BIG
    return billed, sub, prefix


def subagent():
    """One fork: small prefix, reads the big file, hands back a summary."""
    prefix, cached, billed = SYSTEM + SUB_TOOLS + TASK, 0, 0.0
    for step in range(2):
        billed += cached * READ + (prefix - cached) * WRITE
        cached = prefix
        prefix += BIG if step == 0 else REPLY
    return billed


MODES = [
    ("no cache at all", "nocache"),
    ("cached, append-only", "cached"),
    ("cached, but prefix edited every turn", "thrash"),
    ("cached + subagent offload", "offload"),
]

print("=" * 74)
print("1. SAME 60-TURN SESSION, FOUR STRATEGIES")
print("=" * 74)
print(f"{'strategy':<38}{'ctx':>9}{'eff.tok':>11}{'cost':>9}")
for label, mode in MODES:
    main, sub, ctx = simulate(mode)
    print(f"{label:<38}{ctx:>8,}{main + sub:>11,.0f}{(main + sub) * PRICE_IN:>9.2f}")
print("\nThrashing the cache costs MORE than never caching: you pay the 1.25x")
print("write premium on the entire prefix, every single turn, forever.")

print()
print("=" * 74)
print("2. WHEN A TOKEN ARRIVES DECIDES WHAT IT COSTS")
print("=" * 74)
print("A 6,000-token file read, dropped into a 60-turn cached session:\n")
print(f"{'arrives at turn':>16}{'re-reads left':>15}{'multiplier':>13}{'eff.tok':>11}{'cost':>9}")
for k in (1, 5, 20, 40, 55, 60):
    mult = WRITE + READ * (60 - k)
    print(f"{k:>16}{60 - k:>15}{mult:>12.2f}x{BIG * mult:>11,.0f}{BIG * mult * PRICE_IN:>9.3f}")
early, late = WRITE + READ * 59, WRITE + READ * 0
print(f"\nIdentical read, {early / late:.1f}x the cost. Nothing about the file changed --")
print("only how many turns were left to re-read it.")

print()
print("=" * 74)
print("3. THE BENEFIT OF OFFLOADING GROWS WITH SESSION LENGTH")
print("=" * 74)
print(f"{'turns':>7}{'inline $':>11}{'offload $':>12}{'  of which subagents':>22}{'saved':>8}")
for t in (20, 30, 40, 60, 120, 200):
    inline = sum(simulate("cached", t)[:2]) * PRICE_IN
    m, s, _ = simulate("offload", t)
    off = (m + s) * PRICE_IN
    print(f"{t:>7}{inline:>11.2f}{off:>12.2f}{s * PRICE_IN:>22.2f}{1 - off / inline:>7.0%}")
print("\nSubagents are not free -- they re-establish their own prefix, so on short")
print("sessions offloading LOSES money. It pays off only once enough turns remain")
print("to re-read what you kept out. Note where the sign flips.")

print()
print("=" * 74)
print("4. THE COMPACTION CLIFF")
print("=" * 74)
main, _, ctx = simulate("cached", 60)
compacted = 40_000  # summariser rewrites 163K of history down to ~40K
print(f"Context at turn 60            {ctx:>10,} tokens  (cache is warm)")
print(f"Compaction rewrites it to     {compacted:>10,} tokens")
print(f"But the prefix changed, so the next turn is a full cache WRITE:")
print(f"  next turn, warm cache       {ctx * READ * PRICE_IN:>10.2f}")
print(f"  next turn, post-compaction  {compacted * WRITE * PRICE_IN:>10.2f}"
      f"   ({compacted * WRITE / (ctx * READ):.1f}x)")
print("\nCompaction shrinks the window and spikes the bill on the same turn.")
print("It is a cliff you fall off, not a slope you ease down.")
