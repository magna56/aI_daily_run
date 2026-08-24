#!/usr/bin/env python3
"""
Overconfident toy classifier → reliability bins + ECE → temperature scaling.

Run:  python3 code_example.py
"""

import math
import random

random.seed(3)
N = 400
BINS = 5


def softmax_pair(logit_true, logit_false, t=1.0):
    a = logit_true / t
    b = logit_false / t
    m = max(a, b)
    ea, eb = math.exp(a - m), math.exp(b - m)
    return ea / (ea + eb)


def make_set():
    rows = []
    for _ in range(N):
        # True class is 1 about half the time. Logits are shoved too far
        # from zero so the model is overconfident.
        y = 1 if random.random() < 0.5 else 0
        # Mix easy (shouted) and hard (near 0.5) so bins are not one spike.
        strength = 0.4 + 2.6 * random.random()
        if y == 1:
            p = softmax_pair(strength, -0.15 * strength)
        else:
            p = softmax_pair(-0.15 * strength, strength)
            if random.random() < 0.18:
                p = 1 - p
        # store confidence for predicted class and whether it was right
        pred = 1 if p >= 0.5 else 0
        conf = p if pred == 1 else 1 - p
        rows.append((conf, pred == y, p))
    return rows


def reliability(rows, t=1.0):
    # Re-scale stored pre-softmax-ish confidence via a stand-in: we stored p
    # at T=1. For temperature we recompute from a fake logit = log(p/(1-p)).
    bins = [{"n": 0, "acc": 0.0, "conf": 0.0} for _ in range(BINS)]
    for p, correct, _raw in rows:
        logit = math.log(min(max(p, 1e-6), 1 - 1e-6) / max(1 - p, 1e-6))
        conf = 1 / (1 + math.exp(-logit / t))
        if conf < 0.5:
            conf = 1 - conf
            correct_use = not correct if False else correct
        else:
            correct_use = correct
        # After temperature, predicted class is still the same if we only
        # scale; keep the original correctness.
        i = min(BINS - 1, int(conf * BINS))
        bins[i]["n"] += 1
        bins[i]["acc"] += 1.0 if correct_use else 0.0
        bins[i]["conf"] += conf
    out = []
    ece = 0.0
    for i, b in enumerate(bins):
        if not b["n"]:
            out.append((i, 0, 0.0, 0.0))
            continue
        acc = b["acc"] / b["n"]
        conf = b["conf"] / b["n"]
        ece += (b["n"] / len(rows)) * abs(acc - conf)
        out.append((i, b["n"], acc, conf))
    return out, ece


def main():
    rows = make_set()
    acc = sum(1 for _c, ok, _p in rows if ok) / N
    print(f"{N} predictions  accuracy {acc:.3f}  (can look fine while bins lie)\n")

    def show(title, t):
        table, ece = reliability(rows, t)
        print(f"{title}  T={t:.2f}  ECE={ece:.3f}")
        print(f"  {'bin':<10} {'n':>4}  {'acc':>6}  {'conf':>6}  gap")
        for i, n, a, c in table:
            lo, hi = i / BINS, (i + 1) / BINS
            gap = abs(a - c) if n else 0
            print(f"  {lo:.1f}-{hi:.1f}  {n:>4}  {a:6.3f}  {c:6.3f}  {gap:.3f}")
        print()
        return ece

    e0 = show("before temperature", 1.0)
    # Fit T on a coarse grid (held-out would be a split; this is the shape).
    best_t, best = 1.0, e0
    for step in range(8, 40):
        t = step / 10
        _, e = reliability(rows, t)
        if e < best:
            best, best_t = e, t
    show("after temperature", best_t)
    print(f"pick T={best_t:.1f} on a held-out set in real life, not the test set.")


if __name__ == "__main__":
    main()
