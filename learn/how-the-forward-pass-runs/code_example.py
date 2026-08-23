#!/usr/bin/env python3
"""
Attention is a soft join. The KV cache is the memo so decode does not
rebuild the index.

1) A 4-token, 1-head toy step: print Q, K, V and the softmax weights.
2) Count how many tokens we re-project to build K/V while generating,
   with and without a cache.

Pure stdlib.  Run:  python3 code_example.py
"""

from math import exp, sqrt


def softmax(xs):
    m = max(xs)
    es = [exp(x - m) for x in xs]
    s = sum(es)
    return [e / s for e in es]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def matvec(M, v):
    return [dot(row, v) for row in M]


def attention(tokens, Wq, Wk, Wv):
    Q = [matvec(Wq, t) for t in tokens]
    K = [matvec(Wk, t) for t in tokens]
    V = [matvec(Wv, t) for t in tokens]
    d = len(Q[0])
    weights = []
    out = []
    for q in Q:
        scores = [dot(q, k) / sqrt(d) for k in K]
        w = softmax(scores)
        weights.append(w)
        out.append([sum(wi * vj[j] for wi, vj in zip(w, V)) for j in range(d)])
    return Q, K, V, weights, out


def projections(n, t, cache):
    """Token-projections of K and V needed to emit `t` new tokens after a
    prompt of length n. With a cache: once per token. Without: every
    decode step re-projects the whole prefix."""
    if cache:
        return n + t
    return sum(n + i for i in range(1, t + 1))


def main():
    # Tiny residual streams (4 tokens × dim 2). Weights are fixed so the
    # printed scores are deterministic — features, not folklore.
    tokens = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.5, 0.2]]
    Wq = [[1.0, 0.2], [0.0, 1.0]]
    Wk = [[0.8, 0.1], [0.1, 0.9]]
    Wv = [[1.0, 0.0], [0.0, 1.0]]
    Q, K, V, weights, _ = attention(tokens, Wq, Wk, Wv)
    print("Toy forward step (4 tokens, 1 head)")
    print("Q (what this token looks for):", [[round(x, 2) for x in q] for q in Q])
    print("K (how each token wants to be found):", [[round(x, 2) for x in k] for k in K])
    print("V (payload mixed in):          ", [[round(x, 2) for x in v] for v in V])
    print("Attention weights (rows = query token):")
    for i, w in enumerate(weights):
        print(f"  t{i}: " + " ".join(f"{x:.2f}" for x in w))
    print("A feature is one of these vectors — cached state for the next layer.\n")

    n, t = 16, 16
    no, yes = projections(n, t, False), projections(n, t, True)
    print(f"Generate {t} tokens after a {n}-token prompt")
    print(f"  K/V token-projections without cache: {no}")
    print(f"  with KV cache:                       {yes}   ({no / yes:.1f}× less work)")

    n2, t2 = 4096, 512
    no2, yes2 = projections(n2, t2, False), projections(n2, t2, True)
    print(f"\nSame accounting at 4,096-token prompt + 512 new tokens")
    print(f"  without cache: {no2:,}")
    print(f"  with cache:    {yes2:,}   ({no2 / yes2:.0f}×)")
    print("Attention still reads every past row. The cache only stops you")
    print("rebuilding the index. Decode is a memory-bandwidth loop on that table.")


if __name__ == "__main__":
    main()
