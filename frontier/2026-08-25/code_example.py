"""
Tile-level precision routing in attention, from scratch.

Implements the core mechanism of TileMix (arXiv 2608.17336, Zhang et al.,
18 Aug 2026): instead of SKIPPING the tiles a sparse-attention template calls
unimportant, compute them in INT8 and keep every token connected.

Three pieces, all here:
  * blockwise INT8 with the paper's max-abs scale, delta = max|x| / 127
  * a STATIC, data-free routing template packed one bit per tile group, so a
    query-tile row's whole map is a single integer (the paper caps groups at 64
    so it fits one 64-bit word regardless of context length)
  * tiled online softmax where BOTH precision paths update one running state --
    the piece that makes this a single fused kernel rather than two passes

Then it runs the experiment that carries the paper's claim: the same routing
map used to SKIP tiles vs used to CHEAPEN them, both measured against FP16.

    Edit BAND / GROUP / N_KEYS below and re-run.

Run:  python3 code_example.py     (pure stdlib, no network, no API key)
"""

import math
import random

# ------------------------------------------------------------- liftable core

def quantize_block(xs):
    """delta = max|x| / 127, as specified. Returns (int8 codes, scale)."""
    peak = max((abs(x) for x in xs), default=0.0) or 1e-9
    delta = peak / 127.0
    return [max(-127, min(127, int(round(x / delta)))) for x in xs], delta


def dequantize_block(codes, delta):
    return [c * delta for c in codes]


def routing_bits(n_q_tiles, n_k_groups, band=1, n_global=1):
    """1 = INT8, 0 = FP16, one bit per key-tile group, one integer per row.

    A BigBird-shaped template: full precision on the diagonal band and the
    global prefix, INT8 everywhere else. Nothing here looks at the data --
    that is the paper's actual design, not a simplification made here.
    """
    rows = []
    for m in range(n_q_tiles):
        bits = 0
        for g in range(n_k_groups):
            if not (abs(g - m) <= band or g < n_global):
                bits |= (1 << g)
        rows.append(bits)
    assert n_k_groups <= 64, "grouping factor too small: map no longer fits one word"
    return rows


def attend_row(q, keys, values, row_bits, group_size, mode="int8"):
    """Online softmax over key tiles, mixing precision paths into one state.

    Scores are quantised a TILE AT A TIME, sharing one scale across the tile --
    that shared scale is where precision is actually lost. Quantising a single
    score is lossless (delta = |x|/127 round-trips exactly), so a per-element
    version of this would silently measure nothing at all.

    mode="int8" cheapens routed tiles (TileMix). mode="skip" drops them
    (sparse attention). mode="fp16" ignores routing (the reference).
    """
    running_max, running_sum = float("-inf"), 0.0
    acc = [0.0] * len(values[0])

    for start in range(0, len(keys), group_size):
        tile = list(range(start, min(start + group_size, len(keys))))
        routed = (row_bits >> (start // group_size)) & 1
        if routed and mode == "skip":
            continue                                   # sparse: the tokens are gone

        scores = [sum(a * b for a, b in zip(q, keys[j])) for j in tile]
        if routed and mode == "int8":
            codes, delta = quantize_block(scores)      # ONE scale for the whole tile
            scores = dequantize_block(codes, delta)

        for j, score in zip(tile, scores):
            new_max = score if score > running_max else running_max
            rescale = 1.0 if running_max == float("-inf") else math.exp(running_max - new_max)
            w = math.exp(score - new_max)
            running_sum = running_sum * rescale + w
            acc = [a * rescale + w * vi for a, vi in zip(acc, values[j])]
            running_max = new_max

    if running_sum == 0.0:
        return [0.0] * len(values[0])
    return [a / running_sum for a in acc]


def mean_abs_dev(a, b):
    flat = [(x - y) for ra, rb in zip(a, b) for x, y in zip(ra, rb)]
    return sum(abs(d) for d in flat) / max(1, len(flat))


# ------------------------------------------------------------------ the setup

random.seed(7)
D, N_QUERIES, N_KEYS = 16, 8, 64
GROUP = 8                      # key tiles per routing bit (the grouping factor g)
BAND, N_GLOBAL = 1, 1

queries = [[random.gauss(0, 1) for _ in range(D)] for _ in range(N_QUERIES)]
keys = [[random.gauss(0, 1) for _ in range(D)] for _ in range(N_KEYS)]
values = [[random.gauss(0, 1) for _ in range(D)] for _ in range(N_KEYS)]

# Plant a strong signal in a key the template will call boring, so the
# skip-vs-cheapen comparison is measuring something real.
PLANTED = N_KEYS - 3
keys[PLANTED] = [x * 2.4 for x in queries[0]]
values[PLANTED] = [9.0] * D

n_groups = (N_KEYS + GROUP - 1) // GROUP


def run(mode, rows):
    return [attend_row(queries[m], keys, values, rows[m % len(rows)], GROUP, mode)
            for m in range(N_QUERIES)]


def coverage(rows, n_groups):
    bits = sum(bin(r & ((1 << n_groups) - 1)).count("1") for r in rows)
    return bits / (len(rows) * n_groups)


def main():
    rows = routing_bits(N_QUERIES, n_groups, band=BAND, n_global=N_GLOBAL)
    ref = run("fp16", [0] * N_QUERIES)

    print("=" * 74)
    print("A. The routing map is one integer per query-tile row")
    print("=" * 74)
    print(f"  {N_KEYS} keys / {GROUP} per group = {n_groups} groups  ->  fits one 64-bit word: "
          f"{n_groups <= 64}")
    for m in range(min(4, len(rows))):
        print(f"    row {m}: {rows[m]:#0{n_groups+2}b}   (1 = INT8)")
    print(f"  INT8 coverage: {coverage(rows, n_groups) * 100:.0f}%  -- static, data-free")

    print()
    print("=" * 74)
    print("B. Same map: skip the tiles, or cheapen them?")
    print("=" * 74)
    d_int8 = mean_abs_dev(run("int8", rows), ref)
    d_skip = mean_abs_dev(run("skip", rows), ref)
    print(f"  cheapen to INT8 (TileMix)   mean abs deviation from FP16: {d_int8:.5f}")
    print(f"  skip entirely   (sparse)    mean abs deviation from FP16: {d_skip:.5f}")
    ratio = d_skip / d_int8 if d_int8 else float("inf")
    ratio_txt = f"{ratio:.0f}x" if ratio != float("inf") else "infinitely"
    print(f"  -> skipping is {ratio_txt} worse at the SAME coverage and the same cost.")
    print("     A planted signal sat in a group the template calls boring. INT8 still")
    print("     saw it, coarsely. Skipping erased it, and no budget knob brings it back.")

    print()
    print("=" * 74)
    print("C. Deviation vs INT8 coverage budget")
    print("=" * 74)
    print("  paper reports 1.10e-3 at 10% coverage, 1.78e-3 at 25% (real kernel, A100)")
    print()
    for band in range(n_groups, -1, -1):
        r = [x for x in routing_bits(N_QUERIES, n_groups, band=band, n_global=0)]
        cov = coverage(r, n_groups)
        dev = mean_abs_dev(run("int8", r), ref)
        bar = "#" * int(dev * 400)
        print(f"  coverage {cov * 100:5.1f}%   deviation {dev:.5f}  {bar}")
    print()
    print("  Monotone and gentle is the shape to check for. A discontinuity here")
    print("  means the online-softmax rescale is wrong, not that INT8 is bad.")


if __name__ == "__main__":
    main()
