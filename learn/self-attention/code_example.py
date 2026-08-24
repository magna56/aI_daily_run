#!/usr/bin/env python3
"""
4-token causal self-attention by hand: scores, mask, softmax, weighted V.

Run:  python3 code_example.py
"""

import math

TOKENS = ["refund", "not", "the", "charge"]
# Hand-set 2-d Q/K/V so the story is readable: "not" should weigh on the query
# at the last position when we ask about negation.
Q = {
    "refund": [1.0, 0.1],
    "not": [0.2, 1.2],
    "the": [0.4, 0.0],
    "charge": [0.9, 0.8],
}
K = {
    "refund": [1.1, 0.0],
    "not": [0.1, 1.4],
    "the": [0.5, 0.0],
    "charge": [1.0, 0.2],
}
V = {
    "refund": [1.0, 0.0],
    "not": [0.0, 1.0],
    "the": [0.2, 0.0],
    "charge": [0.8, 0.1],
}
D = 2


def softmax(xs):
    m = max(xs)
    ex = [math.exp(x - m) for x in xs]
    s = sum(ex)
    return [e / s for e in ex]


def attend(query_tok, upto):
    q = Q[query_tok]
    scores = []
    for i, tok in enumerate(TOKENS):
        if i > upto:
            scores.append(float("-inf"))
            continue
        scores.append(sum(q[j] * K[tok][j] for j in range(D)) / math.sqrt(D))
    finite = [s if s != float("-inf") else -1e9 for s in scores]
    w = softmax(finite)
    if upto < len(TOKENS) - 1:
        for i in range(upto + 1, len(TOKENS)):
            w[i] = 0.0
        z = sum(w)
        w = [x / z for x in w]
    mixed = [0.0, 0.0]
    for tok, wt in zip(TOKENS, w):
        mixed[0] += wt * V[tok][0]
        mixed[1] += wt * V[tok][1]
    return scores, w, mixed


def main():
    print("tokens:", " ".join(TOKENS))
    print("causal: each row may only see itself and the left\n")
    print(f"{'query':<8} {'weights → refund  not   the  charge':<42} mix")
    for i, tok in enumerate(TOKENS):
        scores, w, mixed = attend(tok, i)
        bar = " ".join(f"{p:5.2f}" for p in w)
        print(f"{tok:<8} {bar:<42} [{mixed[0]:.2f}, {mixed[1]:.2f}]")

    print("\nlast-token scores before softmax (masked future is -inf):")
    scores, w, _ = attend("charge", 3)
    for tok, s, p in zip(TOKENS, scores, w):
        print(f"  {tok:<8} score {s:6.2f}  weight {p:.3f}")
    print("softmax is a competition: the largest score eats the mix.")


if __name__ == "__main__":
    main()
