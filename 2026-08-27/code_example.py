"""
Layer-isolated evaluation: give each layer of an agent its own deterministic,
no-LLM assertion slice, then compare how much an AGGREGATE pass rate moves
against how much the MATCHING SLICE moves when that one layer regresses.
Reproduces the masking effect from arXiv:2606.11686 (Zhang, Wang & Lei, 2026):
break one layer completely and the aggregate score barely moves, because most
end-to-end test cases never exercise that layer -- while the slice built to
test exactly that layer craters.

Two layers -- ontology resolution and safety repricing -- are implemented as
real, liftable functions with their own pure-mode assertion slices. The other
five layers in the masking table use precomputed hit/slice counts (see
LAYER_COUNTS below) calibrated to reproduce the paper's *shape*, not its
literal ordering agent -- the real published deltas are quoted in topic.md.

Run: python3 code_example.py
"""
import json

TOTAL_SCENARIOS = 500  # size of the synthetic end-to-end "aggregate" eval suite

# ---- A real, liftable layer: ontology resolution (pure lookup, no LLM) ----
CANON = {"sku-42": "CANON-COLA-42", "sku-7": "CANON-CHIPS-7", "sku-9": "CANON-WATER-9"}

def ontology_resolve(sku: str, broken: bool) -> str | None:
    if broken:
        return None  # injected fault: "resolver -> empty/null"
    return CANON.get(sku)

ONTOLOGY_SLICE = [((sku,), expected) for sku, expected in
                  list(CANON.items()) * 7]  # 21 cases, same shape as production

# ---- A second real layer: safety repricing (also pure, also no LLM) ----
PRICEBOOK = {"sku-42": 199, "sku-7": 149}

def reprice(cart: tuple, broken: bool) -> tuple:
    if broken:
        return (sum(PRICEBOOK.get(s, 0) for s in cart), ())  # "allow-all": nothing rejected
    total, rejected = 0, []
    for sku in cart:
        if sku not in PRICEBOOK:
            rejected.append(sku)  # unknown SKU is rejected, never silently priced at 0
            continue
        total += PRICEBOOK[sku]
    return (total, tuple(rejected))

REPRICE_SLICE = [((("sku-42", "sku-7"),), (348, ())),
                 ((("sku-42", "bogus-sku"),), (199, ("bogus-sku",)))] * 10  # 20 cases

def run_slice(fn, cases, broken: bool) -> tuple[int, int]:
    """The reusable core: run every case in pure mode and count exact matches."""
    passed = sum(int(fn(*args, broken=broken) == expected) for args, expected in cases)
    return passed, len(cases)

# The other 5 non-foundational layers: (aggregate_hit_count, slice_size, slice_fail)
# aggregate_hit_count = how many of TOTAL_SCENARIOS actually exercise this layer.
LAYER_COUNTS = {
    "ood_gate":      (8,  11, 4),
    "intent":        (21, 40, 10),
    "escalation":    (23, 22, 11),
    "defense_scan":  (25, 19, 12),
    "reformulator":  (29, 20, 16),
    "decomposer":    (29, 22, 20),
}
ONTOLOGY_HIT = 132  # ontology is foundational -- most scenarios need a resolved SKU

def masking_table() -> list[dict]:
    rows = []
    for name, (hit, size, fail) in LAYER_COUNTS.items():
        agg_drop = 100 * hit / TOTAL_SCENARIOS
        slice_drop = 100 * fail / size
        rows.append({"layer": name, "agg_drop_pp": agg_drop, "slice_drop_pp": slice_drop,
                     "masking_ratio": slice_drop / agg_drop})
    passed_broken, size = run_slice(ontology_resolve, ONTOLOGY_SLICE, broken=True)
    fail = size - passed_broken
    agg_drop = 100 * ONTOLOGY_HIT / TOTAL_SCENARIOS
    slice_drop = 100 * fail / size
    rows.append({"layer": "ontology (foundational)", "agg_drop_pp": agg_drop,
                 "slice_drop_pp": slice_drop, "masking_ratio": slice_drop / agg_drop})
    return sorted(rows, key=lambda r: -r["masking_ratio"])

def gate_ci(baseline: dict, current: dict) -> list[str]:
    """CI check: block on any per-slice rate drop. A slice with 0 cases reports
    rate=None (uncovered), never 1.0 -- so an untested slice can't pass by default."""
    blocked = []
    for name, base in baseline.items():
        cur = current.get(name, {"total": 0, "rate": None})
        cur_rate = None if cur["total"] == 0 else cur["rate"]
        if cur_rate is None or cur_rate < base["rate"]:
            blocked.append(name)
    return blocked

def main():
    print("--- pure-mode slice: ontology resolution, no LLM involved ---")
    passed, size = run_slice(ontology_resolve, ONTOLOGY_SLICE, broken=False)
    print(f"healthy: {passed}/{size} pass ({100*passed/size:.1f}%)")
    passed, size = run_slice(ontology_resolve, ONTOLOGY_SLICE, broken=True)
    print(f"broken:  {passed}/{size} pass ({100*passed/size:.1f}%)")

    print("\n--- pure-mode slice: safety repricing ---")
    passed, size = run_slice(reprice, REPRICE_SLICE, broken=False)
    print(f"healthy: {passed}/{size} pass ({100*passed/size:.1f}%)")
    passed, size = run_slice(reprice, REPRICE_SLICE, broken=True)
    print(f"broken:  {passed}/{size} pass ({100*passed/size:.1f}%) -- 'allow-all' fault")

    print("\n--- masking table: one layer broken at a time, sorted by how well it hides ---")
    print(f"{'layer':<26}{'aggregate Δ':>13}{'slice Δ':>11}{'masking ratio':>16}")
    for r in masking_table():
        print(f"{r['layer']:<26}{-r['agg_drop_pp']:>12.1f}pp{-r['slice_drop_pp']:>10.1f}pp"
              f"{r['masking_ratio']:>14.1f}x")

    print("\n--- CI gate: escalation regresses, everything else holds ---")
    baseline = {"ontology": {"total": 21, "rate": 100.0}, "escalation": {"total": 22, "rate": 100.0},
                "memory": {"total": 0, "rate": None}}
    current = {"ontology": {"total": 21, "rate": 100.0}, "escalation": {"total": 22, "rate": 50.0},
               "memory": {"total": 0, "rate": None}}
    print("blocked slices:", gate_ci(baseline, current))

if __name__ == "__main__":
    main()
