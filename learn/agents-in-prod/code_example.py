#!/usr/bin/env python3
"""
Toy agent loop: frozen prefix vs busted prefix, write tool, verifier.

Run:  python3 code_example.py
"""

PREFIX = "policy: never drop a table. tools: lookup, migrate."
STEPS = 3
PREFILL_COST = 12  # units for a full prefix
CACHED_COST = 2    # units when the prefix hits
DECODE_COST = 3


def run(bust_cache, verify):
    prefix = PREFIX + (" t=" + str(hash(bust_cache))[:4] if bust_cache else "")
    cache_key = None
    bill = 0
    log = []
    state = {"orders": 12, "dropped": False}

    def prefill():
        nonlocal cache_key, bill
        if (not bust_cache) and cache_key == prefix:
            bill += CACHED_COST
            hit = True
        else:
            bill += PREFILL_COST
            cache_key = prefix
            hit = False
        bill += DECODE_COST
        return hit

    plan = [
        ("lookup", {"table": "orders"}),
        ("migrate", {"sql": "alter table orders add column note text"}),
        ("migrate", {"sql": "drop table orders"}),
    ]
    for step, (tool, args) in enumerate(plan[:STEPS], 1):
        hit = prefill()
        if tool == "lookup":
            result = f"rows={state['orders']}"
            ok = True
        else:
            sql = args["sql"]
            dangerous = sql.startswith("drop")
            if verify and dangerous:
                result = "verifier rejected: drop"
                ok = False
            else:
                if dangerous:
                    state["orders"] = 0
                    state["dropped"] = True
                result = "applied"
                ok = True
        log.append((step, tool, result, hit, ok))
    return bill, state, log


def show(title, bust, verify):
    bill, state, log = run(bust, verify)
    print(title)
    print(f"  bill={bill}  orders={state['orders']}  dropped={state['dropped']}")
    for step, tool, result, hit, ok in log:
        cache = "cache-hit" if hit else "prefill"
        flag = "ok" if ok else "blocked"
        print(f"  step {step} {tool:<8} {cache:<10} {flag:<8} {result}")
    print()


def main():
    show("stable prefix, verifier on (ship this)", bust=False, verify=True)
    show("timestamp in the prefix busts the cache", bust=True, verify=True)
    show("no verifier — the model talks past the latch", bust=False, verify=False)
    print("the loop is three calls. the bill and the drop are the job.")


if __name__ == "__main__":
    main()
