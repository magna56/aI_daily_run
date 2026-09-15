"""A small service with a production-shaped bug, instrumented by the sensor.

The bug is deliberately the kind an AI coding agent CANNOT find by reading the repo, which is
the entire argument for a runtime sensor:

  - It depends on data, not on logic. `discount_bps` arrives as an int for most tenants and
    as a string for a few, because two different writers populate that config table.
  - It never fires in tests, because the fixtures are all well-formed.
  - The stack trace alone does not explain it. You need the VALUE of the local at the moment
    it failed to see that it is "150" and not 150.

Run:  python3 demo_app.py
Then: python3 -m hud_lite.mcp_server --data .hud-demo/runtime.json --demo
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hud_lite.hook import Sensor

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, ".hud-demo", "runtime.json")

TENANTS = ["acme", "globex", "initech", "umbrella", "hooli", "stark"]
# Traffic is not uniform. initech is a small tenant, which is exactly why nobody caught this.
TENANT_WEIGHTS = [34, 28, 5, 18, 12, 3]
# initech was configured through the legacy admin panel, which writes discount_bps as a string.
LEGACY_TENANTS = {"initech"}


# -- the "service" ----------------------------------------------------------------

def load_pricing_config(tenant):
    bps = 150 if tenant not in LEGACY_TENANTS else "150"
    return {"tenant": tenant, "currency": "USD", "discount_bps": bps}


def apply_discount(price_cents, config):
    # Looks fine. Is fine, for four tenants out of six.
    discount = price_cents * config["discount_bps"] // 10000
    return price_cents - discount


def normalize_cart(items):
    total = 0
    for item in items:
        total += item["qty"] * item["unit_cents"]
    return total


def build_recommendations(tenant, cart_total):
    # Stands in for an expensive call the sensor will flag as a latency outlier.
    scores = []
    for i in range(90000):
        scores.append((i * cart_total) % 9973)
    scores.sort()
    return scores[:5]


def checkout(tenant, items):
    config = load_pricing_config(tenant)
    subtotal = normalize_cart(items)
    total = apply_discount(subtotal, config)
    recommendations = build_recommendations(tenant, total)
    return {"tenant": tenant, "total_cents": total, "recommendations": recommendations}


# -- driver -----------------------------------------------------------------------

def main():
    random.seed(7)
    sensor = Sensor(app_root=HERE).install()

    ok = failed = 0
    for _ in range(250):
        tenant = random.choices(TENANTS, weights=TENANT_WEIGHTS)[0]
        items = [
            {"qty": random.randint(1, 4), "unit_cents": random.randint(500, 9000)}
            for _ in range(random.randint(1, 3))
        ]
        try:
            # In a real app this boundary is the framework's error handler, not a try block.
            with sensor.watching():
                checkout(tenant, items)
            ok += 1
        except Exception:
            failed += 1

    sensor.uninstall()
    path = sensor.store.save(DATA)

    snap = sensor.store.snapshot()
    print("traffic replayed : %d ok, %d failed" % (ok, failed))
    print("functions seen   : %d" % len(snap["functions"]))
    print("call edges       : %d" % len(snap["edges"]))
    print("exception groups : %d (unsampled)" % len(snap["exceptions"]))
    for fn in snap["functions"][:6]:
        print("  %-34s calls=%-5d timed=%-4d mean=%sms"
              % (fn["key"], fn["calls"], fn["timed"], fn["mean_ms"]))
    print("\nsensor data -> %s" % path)
    print("next: python3 -m hud_lite.mcp_server --data .hud-demo/runtime.json --demo")


if __name__ == "__main__":
    main()
