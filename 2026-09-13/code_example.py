"""What a prompt cache actually costs, including the misses.

A cache write is dearer than not caching at all; a read is nearly free. So the
hit rate is not a performance number here, it is the sign of the bill.

Simulates a day of traffic against a prefix that occasionally gets invalidated
-- by a tool reorder, an effort bump, a compaction -- and prices four policies
against never caching. No network, no SDK.

Run: python3 code_example.py

Set INVALIDATE_EVERY low to see a cache that costs more than no cache at all.
"""

import random

SEED = 5
CALLS = 400
PREFIX_TOKENS = 5_629          # the diagnostics example's reusable prefix
TTL_MINUTES = 30
GAP_MINUTES = 4.0              # mean gap between calls that share a prefix

WRITE_RATE = 1.25              # GPT-5.6+: a cache write costs 1.25x uncached
READ_RATE = 0.10               # ... and a read costs 0.1x
MIN_PREFIX = 1_024             # below this nothing is cached at all

# How often something invalidates the prefix, in calls. Every one of these is a
# config change, not an edit to the prompt text.
INVALIDATE_EVERY = {
    "no hygiene":        9,    # tool order varies, effort tuned per request
    "pinned tool order": 24,
    "pinned everything": 90,   # only deliberate deploys change the prefix
    "no cache":          0,    # baseline: never cache
}


def simulate(invalidate_every, rng, gap=None):
    """Return (cost, writes, reads) in units of one uncached prefix."""
    gap_mean = gap
    if PREFIX_TOKENS < MIN_PREFIX:
        return CALLS * 1.0, 0, 0            # nothing is cacheable
    cost = writes = reads = 0
    warm = False
    since_write = 0.0
    for i in range(CALLS):
        gap = rng.expovariate(1.0 / (gap_mean or GAP_MINUTES))
        since_write += gap
        expired = since_write > TTL_MINUTES
        broken = invalidate_every and (i % invalidate_every == 0) and i > 0
        if not warm or expired or broken:
            cost += WRITE_RATE                # pay the premium to store it
            writes += 1
            warm = True
            since_write = 0.0
        else:
            cost += READ_RATE
            reads += 1
            since_write = 0.0                 # a read refreshes the TTL
    return cost, writes, reads


def main():
    print("%d calls, %s-token prefix, %d-minute TTL, %.0f-minute mean gap\n"
          % (CALLS, "{:,}".format(PREFIX_TOKENS), TTL_MINUTES, GAP_MINUTES))
    print("  %-20s %8s %8s %12s %12s"
          % ("policy", "writes", "reads", "cost", "vs no cache"))

    base = float(CALLS)                        # never caching: 1.0x per call
    rows = []
    for name, every in INVALIDATE_EVERY.items():
        if name == "no cache":
            rows.append((name, 0, 0, base))
            continue
        rng = random.Random(SEED)
        cost, w, r = simulate(every, rng)
        rows.append((name, w, r, cost))

    for name, w, r, cost in rows:
        delta = (cost / base - 1) * 100
        print("  %-20s %8d %8d %11.1fx %11s"
              % (name, w, r, cost / CALLS, ("%+.0f%%" % delta) if delta else "—"))

    print("\n  Read the writes column against the reads column. A policy with many")
    print("  writes and few reads is paying %.2fx to store prefixes nobody reuses."
          % WRITE_RATE)

    print("\n  Break-even, for one prefix\n")
    print("    %-26s %10s" % ("reuses before it expires", "cost vs uncached"))
    for n in (0, 1, 2, 5, 20):
        cached = WRITE_RATE + READ_RATE * n
        plain = 1.0 * (n + 1)
        print("    %-26d %9.2fx" % (n, cached / plain))
    print("\n  Zero reuses costs 1.25x — a surcharge, not a wasted optimization.")
    print("  One reuse already pays for itself. The risk is never thin margins,")
    print("  it is prefixes written and never read.")

    # Which is decided by traffic shape, not by prefix hygiene. Stretch the gap
    # between calls past the TTL and every call becomes a write.
    print("\n  What actually flips it: how far apart the calls are\n")
    print("    %-22s %8s %8s %10s %11s"
          % ("mean gap", "writes", "reads", "cost", "vs no cache"))
    for g in (2, 10, 25, 45, 90):
        rng = random.Random(SEED)
        cost, w, r = simulate(INVALIDATE_EVERY["pinned everything"], rng, gap=g)
        delta = (cost / base - 1) * 100
        print("    %-19d min %8d %8d %9.2fx %10s"
              % (g, w, r, cost / CALLS, "%+.0f%%" % delta))
    print("\n  The saving erodes as the gap grows, but it does not reverse: gaps are")
    print("  bursty, so even at a %d-minute mean plenty of calls still land inside"
          % 90)
    print("  the %d-minute window and read a warm prefix." % TTL_MINUTES)
    print("\n  So slow traffic is not what makes caching cost money — it just stops")
    print("  paying much. The surcharge case is the row above: a prefix used")
    print("  exactly once, at 1.25x. Uniqueness reverses it, not latency.")


if __name__ == "__main__":
    main()
