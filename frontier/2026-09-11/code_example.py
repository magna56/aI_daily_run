"""Next concept prediction, built from scratch.

Product-quantizes a stream of hidden states into a discrete concept vocabulary,
then measures the only thing that decides whether the idea can work: does the
current concept tell you more about the next token than the previous token does?

Pure standard library -- k-means, entropy and all. No numpy, no torch.

Run: python3 code_example.py

Raise SPAN past the structure in the corpus and the concept stops carrying
anything, which is what the paper's span ablation is guarding against.
"""

import math
import random

# --- knobs ---------------------------------------------------------------
DIM = 16              # hidden state width
M_BOOKS = 2           # product quantization: independent sub-codebooks
K = 4                 # centroids per sub-codebook (the paper uses 256)
# Deliberately tiny. With more concepts than spans, every concept sees one
# example and the entropy below reads 0 for a reason that is memorization,
# not structure. Keep concepts << spans or you are measuring your own noise.
SPAN = 4              # tokens per concept; the paper reports 4-8
SEQ, SEED = 4000, 5

# Four phrase families with choices inside them. The family is span-level
# structure; the choices are not. A concept can identify the family and still
# leave real uncertainty about the token -- a corpus where the concept fixes
# the token exactly would only prove we encoded the answer into the input.
FAMILIES = [
    [["the"], ["cat", "dog"], ["sat", "lay"], ["down", "still"]],
    [["the"], ["bird", "bat"], ["flew", "rose"], ["north", "high"]],
    [["a"], ["fish", "eel"], ["swam", "dove"], ["south", "deep"]],
    [["a"], ["car", "van"], ["drove", "sped"], ["east", "past"]],
]


def build_corpus(rng, n):
    """Tokens plus a stand-in hidden state that knows family and position.

    That is what a trained model's intermediate layer would carry. It does
    not know which alternative was chosen, and neither will the concept.
    """
    toks, states = [], []
    while len(toks) < n:
        f = rng.randrange(len(FAMILIES))
        for i, choices in enumerate(FAMILIES[f]):
            toks.append(choices[rng.randrange(len(choices))])
            v = [0.0] * DIM
            v[f % DIM] = 1.0
            v[(4 + i) % DIM] = 1.0
            states.append([x + rng.gauss(0, 0.25) for x in v])
    return toks[:n], states[:n]


# --- product quantization ------------------------------------------------
def dist2(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))

def kmeans(points, k, rng, iters=15):
    cents = [list(p) for p in rng.sample(points, min(k, len(points)))]
    for _ in range(iters):
        groups = [[] for _ in cents]
        for p in points:
            groups[min(range(len(cents)), key=lambda i: dist2(p, cents[i]))].append(p)
        for i, g in enumerate(groups):
            if g:
                cents[i] = [sum(c) / len(g) for c in zip(*g)]
    return cents

def fit_pq(vectors, rng, m_books=M_BOOKS, k=K):
    """Split each vector into m_books slices; cluster each slice on its own."""
    dim = len(vectors[0]) // m_books
    books = []
    for b in range(m_books):
        slices = [v[b * dim:(b + 1) * dim] for v in vectors]
        books.append(kmeans(slices, k, rng))
    return books, dim

def encode(vec, books, dim):
    """A concept id: one codebook index per slice."""
    return tuple(min(range(len(bk)), key=lambda i: dist2(vec[b * dim:(b + 1) * dim], bk[i]))
                 for b, bk in enumerate(books))

def mean_vector(vs):
    return [sum(c) / len(vs) for c in zip(*vs)]

# --- the measurement that decides -----------------------------------------
def conditional_entropy(pairs):
    """H(next | context), in bits, from observed (context, next) pairs."""
    by_ctx = {}
    for ctx, nxt in pairs:
        by_ctx.setdefault(ctx, {}).setdefault(nxt, 0)
        by_ctx[ctx][nxt] += 1
    total = len(pairs)
    h = 0.0
    for ctx, counts in by_ctx.items():
        n = sum(counts.values())
        inner = -sum((c / n) * math.log2(c / n) for c in counts.values())
        h += (n / total) * inner
    return h


def main():
    rng = random.Random(SEED)
    toks, states = build_corpus(rng, SEQ)

    # One concept per span, from the span's pooled hidden state.
    pooled = [mean_vector(states[i:i + SPAN])
              for i in range(0, len(states) - SPAN + 1, SPAN)]
    books, dim = fit_pq(pooled, rng)
    concepts = [encode(v, books, dim) for v in pooled]

    print("corpus %d tokens, span %d, %d books x %d centroids\n" % (SEQ, SPAN, M_BOOKS, K))
    print("  distinct concepts: %d of %d possible, %.0f spans each"
          % (len(set(concepts)), K ** M_BOOKS, len(concepts) / len(set(concepts))))

    # Baseline: what does the previous token tell you about the next one?
    tok_pairs = list(zip(toks, toks[1:]))
    h_token = conditional_entropy(tok_pairs)

    # The concept: what does the span's code tell you about the tokens in it?
    con_pairs = []
    for ci, c in enumerate(concepts):
        for j in range(SPAN):
            idx = ci * SPAN + j
            if idx < len(toks):
                con_pairs.append(((c, j), toks[idx]))
    h_concept = conditional_entropy(con_pairs)

    h_none = conditional_entropy([(0, t) for t in toks])
    print("\n  %-34s %8s" % ("context", "H(next token)"))
    print("  %-34s %7.3f bits" % ("nothing", h_none))
    print("  %-34s %7.3f bits" % ("the previous token", h_token))
    print("  %-34s %7.3f bits" % ("the concept + position in span", h_concept))

    print("\n  The concept removes %.3f bits the previous token leaves behind."
          % (h_token - h_concept))
    print("  That gap is the claim: span-level structure a next-token target")
    print("  never asks about, so a second target can carry it.")

    if h_token - h_concept < 0.05:
        print("\n  NOTE: the concept carries almost nothing — what the paper's span")
        print("  ablation guards against, and training cannot repair it.")


if __name__ == "__main__":
    main()
