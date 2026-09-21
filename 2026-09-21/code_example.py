"""Does your model's confidence score mean anything? Measure it.

A typed schema guarantees an answer's SHAPE. Nothing guarantees its TRUTH.
The confidence returned beside it is the only signal that touches the second
problem, and it is worthless until you have checked that it is calibrated:
of all the cases where it claimed 90%, was it right 90% of the time?

This implements the check from scratch -- reliability buckets, expected
calibration error, and the temperature fit that repairs an overconfident
model. It needs logits or a probability and nothing else, so it works on any
model, including one you did not train.

Run: python3 code_example.py
"""

import math
import random

# --- The knob. Change this and watch the whole conclusion move. ---------------
# How sharply the model is pushed toward a decisive answer. 1.0 is untouched.
# Higher sharpens every distribution toward 0 or 1 -- which is what training a
# model to sound confident actually does to the number you branch on.
OVERCONFIDENCE = 2.5

SEED, CASES, BUCKETS = 11, 4000, 10
THRESHOLD = 0.90   # the "only act when it is sure" line teams actually ship


# --- Liftable core: paste these three into your own repo ----------------------

def softmax(logits, t=1.0):
    """t>1 softens, t<1 sharpens. Never changes which option wins."""
    scaled = [z / t for z in logits]
    m = max(scaled)
    exps = [math.exp(z - m) for z in scaled]
    return [e / sum(exps) for e in exps]


def reliability_buckets(confidences, correct, n_buckets=BUCKETS):
    """Group predictions by the confidence they carried.

    Returns (count, claimed, actual) per bucket. A calibrated model puts
    claimed == actual in every row. That equality is the whole definition.
    """
    rows = []
    for i in range(n_buckets):
        lo, hi = i / n_buckets, (i + 1) / n_buckets
        hits = [(c, k) for c, k in zip(confidences, correct) if lo < c <= hi]
        if hits:
            rows.append((len(hits),
                         sum(c for c, _ in hits) / len(hits),
                         sum(1 for _, k in hits if k) / len(hits)))
    return rows


def calibration_error(confidences, correct, n_buckets=BUCKETS):
    """One number for how far the claims are from the truth. Lower is better.

    Weighted by bucket size on purpose: a wild bucket holding four cases must
    not outvote a tight one holding four thousand.
    """
    total = len(confidences)
    return sum(n / total * abs(claimed - actual)
               for n, claimed, actual in reliability_buckets(confidences, correct, n_buckets))


# --- The demonstration --------------------------------------------------------

def simulate(n, rng):
    """A four-way typed Choice -- the shape a structured-decision API returns.

    True skill is fixed here. OVERCONFIDENCE only distorts the reported
    number, which is exactly why accuracy can never tell you the score broke.
    """
    out = []
    for _ in range(n):
        truth = rng.randrange(4)
        logits = [rng.gauss(0, 1.0) for _ in range(4)]
        logits[truth] += rng.gauss(0.6, 1.3)   # real but noisy signal
        out.append((truth, logits))
    return out


def evaluate(cases, t):
    confs, correct = [], []
    for truth, logits in cases:
        probs = softmax(logits, t)
        pick = max(range(4), key=lambda i: probs[i])
        confs.append(probs[pick])
        correct.append(pick == truth)
    return confs, correct


def fit_temperature(cases):
    """Sweep for the t minimizing calibration error on HELD-OUT cases.

    Fitting on the cases you report would just memorize them.
    """
    return min((calibration_error(*evaluate(cases, s / 10)), s / 10)
               for s in range(1, 81))[1]


def report(label, confs, correct):
    ece = calibration_error(confs, correct)
    print(f"\n{label}")
    print(f"  accuracy {sum(correct) / len(correct):.1%}   calibration error {ece:.3f}")
    print("   claimed   actual    cases")
    for n, claimed, actual in reliability_buckets(confs, correct):
        if n >= 25:
            gap = " <- claims far more than it delivers" if claimed - actual > 0.15 else ""
            print(f"    {claimed:5.1%}    {actual:5.1%}   {n:6d}{gap}")
    return ece


def threshold_check(label, confs, correct):
    above = [(c, k) for c, k in zip(confs, correct) if c > THRESHOLD]
    if not above:
        print(f"  {label:<12} nothing claims above {THRESHOLD:.0%}")
        return
    wrong = 1 - sum(1 for _, k in above if k) / len(above)
    print(f"  {label:<12} {len(above):5d} cases claim >{THRESHOLD:.0%} confident, "
          f"and {wrong:.1%} of them are wrong")


def main():
    rng = random.Random(SEED)
    holdout, live = simulate(CASES, rng), simulate(CASES, rng)
    shipped = 1 / OVERCONFIDENCE

    before = evaluate(live, shipped)
    ece_before = report(f"As shipped (sharpened {OVERCONFIDENCE}x)", *before)

    t = fit_temperature(holdout)
    after = evaluate(live, t)
    ece_after = report(f"After fitting temperature t={t:.1f} on held-out cases", *after)

    print(f"\ncalibration error {ece_before:.3f} -> {ece_after:.3f} "
          f"({ece_before / max(ece_after, 1e-9):.1f}x better)")
    print(f"accuracy is identical either way -- temperature never changes which option wins.")
    print(f"\nWhat the {THRESHOLD:.0%} threshold actually buys you:")
    threshold_check("as shipped", *before)
    threshold_check("calibrated", *after)
    print("\nSame model, same answers. Only the number you branch on changed.")


if __name__ == "__main__":
    main()
