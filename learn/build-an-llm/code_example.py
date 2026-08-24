#!/usr/bin/env python3
"""
Tiny next-token model: tokenize, one attention-ish mix, train, sample.

Run:  python3 code_example.py
"""

import math
import random
from collections import Counter

random.seed(1)

CORPUS = [
    "refund the charge",
    "refund the invoice",
    "reset the password",
    "reset the charge",
    "download the invoice",
]
STEPS = 120
LR = 0.15


def tokenize(s):
    return s.split()


def main():
    toks = [tokenize(s) for s in CORPUS]
    vocab = sorted({w for row in toks for w in row})
    stoi = {w: i for i, w in enumerate(vocab)}
    n = len(vocab)
    # one-hot-ish table + a tiny residual mixer (no framework)
    embed = [[random.gauss(0, 0.2) for _ in range(n)] for _ in range(n)]
    unembed = [[random.gauss(0, 0.2) for _ in range(n)] for _ in range(n)]

    def vec(idx):
        return embed[idx][:]

    def logits(hidden):
        return [sum(unembed[i][j] * hidden[j] for j in range(n)) for i in range(n)]

    def softmax(xs):
        m = max(xs)
        ex = [math.exp(x - m) for x in xs]
        s = sum(ex)
        return [e / s for e in ex]

    def mix(ids):
        # mean of previous token embeddings — a stand-in for "look back"
        acc = [0.0] * n
        for i in ids:
            v = vec(i)
            for j in range(n):
                acc[j] += v[j]
        return [x / len(ids) for x in acc]

    pairs = []
    for row in toks:
        ids = [stoi[w] for w in row]
        for t in range(1, len(ids)):
            pairs.append((ids[:t], ids[t]))

    def nll():
        total = 0.0
        for ctx, y in pairs:
            p = softmax(logits(mix(ctx)))[y]
            total += -math.log(max(p, 1e-9))
        return total / len(pairs)

    print("vocab:", " ".join(vocab))
    print(f"start loss {nll():.3f}")
    for step in range(STEPS):
        ctx, y = random.choice(pairs)
        h = mix(ctx)
        lg = logits(h)
        p = softmax(lg)
        # grad of cross-entropy through unembed, then embed of context
        dlog = [p[i] - (1.0 if i == y else 0.0) for i in range(n)]
        for i in range(n):
            for j in range(n):
                unembed[i][j] -= LR * dlog[i] * h[j]
        dh = [sum(dlog[i] * unembed[i][j] for i in range(n)) for j in range(n)]
        scale = LR / len(ctx)
        for idx in ctx:
            for j in range(n):
                embed[idx][j] -= scale * dh[j]
        if (step + 1) % 40 == 0:
            print(f"  step {step + 1:3d}  loss {nll():.3f}")

    print("\nnext-token table after training (prompt → top guess)")
    for prompt in ("refund the", "reset the", "download the"):
        ids = [stoi[w] for w in prompt.split()]
        p = softmax(logits(mix(ids)))
        ranked = sorted(zip(p, vocab), reverse=True)[:3]
        shown = ", ".join(f"{w} {pr:.2f}" for pr, w in ranked)
        print(f"  {prompt:<14}  {shown}")

    # sample
    ctx = [stoi["refund"]]
    out = ["refund"]
    for _ in range(2):
        p = softmax(logits(mix(ctx)))
        # greedy for determinism
        nxt = max(range(n), key=lambda i: p[i])
        ctx.append(nxt)
        out.append(vocab[nxt])
    print("\ngreedy sample from 'refund':", " ".join(out))
    print("same five verbs as a real model: tokenize, embed, mix, score, pick.")


if __name__ == "__main__":
    main()
