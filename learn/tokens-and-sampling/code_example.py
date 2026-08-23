#!/usr/bin/env python3
"""
Tokens are a codec. Temperature is a die, not a personality.

  1. Train a tiny byte-pair tokenizer on a short corpus and encode a string
  2. Treat token IDs as rows in a toy embedding table
  3. Softmax the SAME logits at several temperatures and sample them

No numpy. Run:  python3 code_example.py
"""

import math
import random
from collections import Counter


def pair_counts(tokens):
    c = Counter()
    for a, b in zip(tokens, tokens[1:]):
        c[(a, b)] += 1
    return c


def train_bpe(text, merges=8):
    tokens = list(text)
    vocab = sorted(set(tokens))
    rules = []
    for i in range(merges):
        pairs = pair_counts(tokens)
        if not pairs:
            break
        best, _ = pairs.most_common(1)[0]
        piece = "".join(best)
        rules.append(best)
        vocab.append(piece)
        out, j = [], 0
        while j < len(tokens):
            if j + 1 < len(tokens) and (tokens[j], tokens[j + 1]) == best:
                out.append(piece)
                j += 2
            else:
                out.append(tokens[j])
                j += 1
        tokens = out
        print(f"  merge {i + 1:2d}: {best[0]!r} + {best[1]!r} -> {piece!r}")
    return rules, vocab


def encode(text, rules):
    tokens = list(text)
    for a, b in rules:
        piece = a + b
        out, j = [], 0
        while j < len(tokens):
            if j + 1 < len(tokens) and tokens[j] == a and tokens[j + 1] == b:
                out.append(piece)
                j += 2
            else:
                out.append(tokens[j])
                j += 1
        tokens = out
    return tokens


def softmax(logits, temp):
    scaled = [z / temp for z in logits]
    m = max(scaled)
    exps = [math.exp(z - m) for z in scaled]
    s = sum(exps)
    return [e / s for e in exps]


def main():
    corpus = "low low low low lower lower newest newest newest widest widest wide"
    print("BPE on a tiny corpus (the classic textbook example)\n")
    rules, vocab = train_bpe(corpus, merges=8)
    probe = "lowest newest"
    pieces = encode(probe, rules)
    print(f"\nencode({probe!r}) = {pieces}")
    print(f"chars={len(probe)}  tokens={len(pieces)}  vocab={len(vocab)}")

    # Toy 2-d embeddings: just hash the token into a pair of ints so we can print.
    print("\nToy embeddings (deterministic hash, not trained):")
    for t in pieces:
        x = (sum(map(ord, t)) % 9) - 4
        y = (len(t) * 3) % 7 - 3
        print(f"  {t!r:10} -> ({x:+d}, {y:+d})")

    names = ["return", "raise", "retry", "rm"]
    logits = [3.4, 1.1, 0.6, -0.8]  # fixed — the "model" does not change
    print("\nSame logits:", dict(zip(names, logits)))
    print(f"{'T':>6}  " + "  ".join(f"{n:>8}" for n in names))
    for t in (0.2, 0.7, 1.0, 1.5):
        p = softmax(logits, t)
        print(f"{t:6.1f}  " + "  ".join(f"{x:8.1%}" for x in p))

    rng = random.Random(0)
    print("\n20 draws from those logits (counts):")
    for t in (0.2, 1.2):
        p = softmax(logits, t)
        picks = [rng.choices(names, weights=p, k=1)[0] for _ in range(20)]
        print(f"  T={t}: " + " ".join(f"{n}={picks.count(n)}" for n in names))
    print("\nThe scores never moved. Only the dice did.")


if __name__ == "__main__":
    main()
