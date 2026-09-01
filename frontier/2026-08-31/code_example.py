"""
Three axes of confidence agreement, and why they diverge.

A model's spoken confidence and its internal confidence are separate channels.
This builds a reporter whose only flaw is a COLLAPSED output range -- it is
otherwise perfectly informed -- and shows association falling to zero while
magnitude agreement and calibration still look acceptable.

That is the failure in arXiv:2608.28382 (Zhang et al., Dartmouth/Oakland, Aug
2026): instance-level Pearson r = 0.135 across 30 models, and r = -0.0048 for
instruction-tuned ones. Nothing here is fitted to those numbers; the point is
that a single distributional defect reproduces the shape.

Pure stdlib. Run: python3 code_example.py
"""

import math, random, statistics

# Knobs. COLLAPSE is the one that matters -- drag it and watch association die.
COLLAPSE = 0.0     # 0 = reporter uses the full range; 1 = one number for everything
N = 2000
SEED = 11


# --- The liftable core: three axes, computed separately, never averaged -------

def pearson(xs, ys):
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else 0.0


def spearman(xs, ys):
    """Rank-only association. Survives any monotone rescaling of the spoken
    number, which is exactly what a differently-worded prompt does to it."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):                      # average ties, or a collapsed
            j = i                                   # channel scores spuriously high
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2.0
            i = j + 1
        return r
    return pearson(ranks(xs), ranks(ys))


def magnitude_gap(verbal, internal):
    """Are the two numerically close? Says nothing about ranking."""
    return statistics.fmean(abs(v - i) for v, i in zip(verbal, internal))


def expected_calibration_error(conf, correct, bins=10):
    """Does a stated 80% come out right 80% of the time? Says nothing about
    whether the model knew WHICH answers were the shaky ones."""
    total, err = len(conf), 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, c in enumerate(conf) if (lo < c <= hi or (b == 0 and c == 0))]
        if not idx:
            continue
        acc = statistics.fmean(correct[i] for i in idx)
        avg = statistics.fmean(conf[i] for i in idx)
        err += (len(idx) / total) * abs(acc - avg)
    return err


# --- A reporter whose only defect is its range --------------------------------

def simulate(collapse, rng, n=N):
    """internal: the model's own probability, calibrated by construction.
    verbal:  the same information, squeezed toward its OWN MEAN by `collapse`.

    Squeezing toward the mean rather than an arbitrary number is the honest
    version of what instruction tuning does: it narrows the range without
    shifting the centre. That matters, because it leaves the reporter looking
    *well calibrated* the whole way down -- a single number equal to the overall
    accuracy has almost no calibration error, and almost no information."""
    internal = [rng.betavariate(5, 2) for _ in range(n)]   # skewed high, like logits
    centre = statistics.fmean(internal)
    verbal, correct = [], []
    for p in internal:
        said = p + (centre - p) * collapse
        said += rng.gauss(0, 0.01)                          # phrasing noise
        verbal.append(round(min(0.99, max(0.01, said)), 2)) # models speak in round numbers
        correct.append(1 if rng.random() < p else 0)
    return verbal, internal, correct


def axes(collapse, rng):
    v, i, c = simulate(collapse, rng)
    return {
        "pearson": pearson(v, i),
        "spearman": spearman(v, i),
        "gap": magnitude_gap(v, i),
        "ece": expected_calibration_error(v, c),
        "spread": statistics.pstdev(v),
        "distinct": len(set(v)),
    }


def gate_overlap(collapse, rng, decile=0.10):
    """The number that decides whether the gate is doing anything: how much does
    the bottom decile by SPOKEN confidence overlap the bottom decile by INTERNAL?
    At chance this is ~10%."""
    v, i, _ = simulate(collapse, rng)
    k = int(len(v) * decile)
    by_v = set(sorted(range(len(v)), key=lambda x: v[x])[:k])
    by_i = set(sorted(range(len(i)), key=lambda x: i[x])[:k])
    return len(by_v & by_i) / k


def main():
    print(f"n={N} items, reporter is perfectly informed at every collapse level\n")
    print("collapse  spread  distinct  pearson  spearman   gap    ECE   gate overlap")
    for collapse in (0.0, 0.5, 0.75, 0.9, 0.97, 0.99, 1.0):
        rng = random.Random(SEED)
        a = axes(collapse, rng)
        rng = random.Random(SEED)
        ov = gate_overlap(collapse, rng)
        print(f"  {collapse:<6.2f}  {a['spread']:.3f}  {a['distinct']:>6}   "
              f"{a['pearson']:>6.3f}   {a['spearman']:>6.3f}  {a['gap']:.3f}  "
              f"{a['ece']:.3f}      {ov:5.0%}")

    print("\nThe reporter never loses information about the ordering — it only stops")
    print("saying it out loud. Read the ECE column against the association columns:")
    print("calibration is at its BEST where the channel is most useless, because a")
    print("single number equal to the overall accuracy is almost perfectly calibrated")
    print("and tells you nothing about which answers were shaky. Any check that reports")
    print("one number would sign this off. The gate-overlap column is the honest one:")
    print("at 10% your threshold is selecting a random tenth of your traffic.")


if __name__ == "__main__":
    main()
