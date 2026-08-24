#!/usr/bin/env python3
"""
LoRA on a tiny frozen linear map: count parameters, prove B=0 is a no-op,
then train A and B until the residual drops.

Run:  python3 code_example.py
"""

import random

random.seed(7)

D_IN, D_OUT = 8, 8
RANKS = (1, 2, 4, 8)
STEPS = 80
LR = 0.08


def zeros(rows, cols):
    return [[0.0] * cols for _ in range(rows)]


def randn(rows, cols, scale=0.3):
    return [[random.gauss(0, scale) for _ in range(cols)] for _ in range(rows)]


def matvec(m, x):
    return [sum(row[j] * x[j] for j in range(len(x))) for row in m]


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def scale(xs, s):
    return [x * s for x in xs]


def lora_delta(a, b, x, alpha, rank):
    # x @ A^T -> r, then @ B^T -> d_out; A is r x d_in, B is d_out x r
    mid = [sum(a[r][j] * x[j] for j in range(len(x))) for r in range(rank)]
    return scale(matvec(b, mid), alpha / rank)


def param_count(d_in, d_out, rank):
    full = d_in * d_out
    adapter = rank * d_in + d_out * rank
    return full, adapter, full / adapter


def main():
    w = randn(D_OUT, D_IN, 0.4)
    target = randn(D_OUT, D_IN, 0.4)
    x = [random.gauss(0, 1) for _ in range(D_IN)]
    y_star = matvec(target, x)

    print(f"frozen W is {D_OUT}x{D_IN}")
    print(f"{'rank':>6} {'full':>8} {'adapter':>8} {'savings':>8}")
    for r in RANKS:
        full, adapter, ratio = param_count(D_IN, D_OUT, r)
        print(f"{r:>6} {full:>8} {adapter:>8} {ratio:>7.1f}x")

    a = randn(4, D_IN, 0.2)
    b = zeros(D_OUT, 4)
    base = matvec(w, x)
    with_zero_b = add(base, lora_delta(a, b, x, alpha=4, rank=4))
    drift = sum((p - q) ** 2 for p, q in zip(base, with_zero_b))
    print(f"\nB=0 output drift vs frozen W: {drift:.2e} (should be 0)")

    rank = 2
    a = randn(rank, D_IN, 0.15)
    b = zeros(D_OUT, rank)
    print(f"\ntrain rank-{rank} adapter for {STEPS} steps")
    for step in range(STEPS + 1):
        pred = add(matvec(w, x), lora_delta(a, b, x, alpha=rank, rank=rank))
        err = [p - t for p, t in zip(pred, y_star)]
        loss = sum(e * e for e in err) / D_OUT
        if step % 20 == 0:
            print(f"  step {step:3d}  mse {loss:.4f}")
        # tiny SGD on A and B only
        mid = [sum(a[r][j] * x[j] for j in range(D_IN)) for r in range(rank)]
        for i in range(D_OUT):
            for r in range(rank):
                b[i][r] -= LR * err[i] * mid[r]
        for r in range(rank):
            for j in range(D_IN):
                back = sum(err[i] * b[i][r] for i in range(D_OUT))
                a[r][j] -= LR * back * x[j]

    print("W stayed frozen. Only A and B moved.")


if __name__ == "__main__":
    main()
