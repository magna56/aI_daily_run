"""Why the busier GPU is the cheaper one.

Simulates a fleet serving agent sessions and routes the same traffic three
ways: least-connections, sticky-by-session, and sticky with a spill valve.
Then prices each turn the way a server does -- a cache hit skips the prefill,
a miss pays for every token in the prefix.

No torch, no server, no network. The point is the routing rule and the bill.

Run: python3 code_example.py

Set SHARED_PREFIX = False to drop the shared system prompt. Sticky routing still
wins, by about half as much -- the conversation history is per-session locality
on its own, which is why this applies to plain chat and not only to agents.
"""

import hashlib
import random

REPLICAS = 8
SESSIONS = 40
TURNS = 12                 # turns per session
SYSTEM_TOKENS = 2_400      # system prompt + tool definitions, sent every turn
TURN_TOKENS = 180          # what each turn adds to the conversation
DECODE_TOKENS = 220
PREFILL_COST = 1.0         # per token, relative
DECODE_COST = 4.0          # per token: decode is dearer per token, but there are fewer
LOAD_WINDOW = 24           # dispatches counted as "recent load"
SPILL_FACTOR = 2.0         # spill when home carries this multiple of a fair share
SHARED_PREFIX = True
SEED = 11


def home(session, n):
    """Hash, not a lookup table: no shared state, survives a router restart."""
    h = hashlib.blake2b(str(session).encode(), digest_size=8).hexdigest()
    return int(h, 16) % n


def route_least(session, caches, inflight):
    return min(range(len(inflight)), key=lambda r: inflight[r])


def route_sticky(session, caches, inflight):
    return home(session, len(inflight))


def route_spill(session, caches, inflight):
    """Sticky, until the home replica is carrying more than its share of
    recent traffic. Without this valve one heavy session pins a replica and
    the rest of the fleet watches."""
    h = home(session, len(inflight))
    fair = LOAD_WINDOW / len(inflight)
    if inflight[h] < fair * SPILL_FACTOR:
        return h
    return min(range(len(inflight)), key=lambda r: inflight[r])


def run(router):
    """One pass of the whole workload. Returns cost, hit rate, and spread."""
    from collections import deque
    caches = [dict() for _ in range(REPLICAS)]   # replica -> {session: cached prefix len}
    inflight = [0] * REPLICAS                    # dispatches inside the recent window
    recent = deque()                             # so load is instantaneous, not cumulative
    served = [0] * REPLICAS
    rng = random.Random(SEED)
    total, prefill_paid, prefix_total, hits = 0.0, 0, 0, 0

    turns = [(s, t) for s in range(SESSIONS) for t in range(TURNS)]
    rng.shuffle(turns)

    for session, t in turns:
        prefix = (SYSTEM_TOKENS if SHARED_PREFIX else 0) + t * TURN_TOKENS
        r = router(session, caches, inflight)
        cached = caches[r].get(session, 0)
        # A hit covers the tokens this replica has already seen for this session.
        reuse = min(cached, prefix)
        to_prefill = prefix - reuse

        total += to_prefill * PREFILL_COST + DECODE_TOKENS * DECODE_COST
        prefill_paid += to_prefill
        prefix_total += prefix
        if reuse > 0:
            hits += 1

        caches[r][session] = prefix + DECODE_TOKENS
        served[r] += 1
        inflight[r] += 1
        recent.append(r)
        if len(recent) > LOAD_WINDOW:            # the oldest dispatch has finished
            inflight[recent.popleft()] -= 1

    spread = (max(served) - min(served)) / (sum(served) / REPLICAS)
    hit_rate = 1 - prefill_paid / prefix_total if prefix_total else 0
    return total, hit_rate, hits / len(turns), spread


def main():
    print("%d replicas, %d sessions x %d turns, shared prefix %s\n"
          % (REPLICAS, SESSIONS, TURNS, "on" if SHARED_PREFIX else "off"))

    print("  %-22s %12s %11s %12s %11s"
          % ("routing", "total cost", "vs least", "prefix reuse", "load spread"))

    base = None
    for label, fn in (("least-connections", route_least),
                      ("sticky by session", route_sticky),
                      ("sticky + spill valve", route_spill)):
        cost, hit_rate, _, spread = run(fn)
        if base is None:
            base = cost
        print("  %-22s %12s %10.0f%% %11.0f%% %10.2f"
              % (label, "{:,.0f}".format(cost), (cost / base - 1) * 100,
                 hit_rate * 100, spread))

    print("\n  Read the last two columns together. Sticky routing is deliberately less")
    print("  even — a higher spread is the price of the reuse, not a bug in it.")
    print("  The spill valve gives back a little reuse to stop one session pinning")
    print("  a replica, which is the failure that turns this into an incident.")

    print("\n  Where the cost actually goes, per turn (sticky):\n")
    prefix_late = SYSTEM_TOKENS + (TURNS - 1) * TURN_TOKENS
    print("    %-26s %8s" % ("prefix at the last turn", "{:,}".format(prefix_late)))
    print("    %-26s %8s" % ("prefilled on a miss", "{:,}".format(prefix_late)))
    print("    %-26s %8s" % ("prefilled on a hit", "{:,}".format(TURN_TOKENS + DECODE_TOKENS)))
    print("\n  That ratio is the whole argument: a miss re-does the entire conversation,")
    print("  a hit pays only for what is new. The queue you skipped was never that big.")


if __name__ == "__main__":
    main()
