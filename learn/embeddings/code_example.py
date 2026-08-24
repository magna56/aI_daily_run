#!/usr/bin/env python3
"""
Bag-of-words embeddings, cosine rank, paraphrase vs shared stopword.

Run:  python3 code_example.py
"""

import math
from collections import Counter

DOCS = {
    "refund.md": "refund the purchase within thirty days",
    "password.md": "reset your password from the security settings page",
    "invoice.md": "download the invoice pdf from the billing portal",
    "weather.md": "the weather tomorrow is rain in the afternoon",
    "charge.md": "undo the charge within the money-back window",
}
QUERY = "undo a charge and get a refund"
STOP = {"the", "a", "an", "from", "are", "is", "in", "to", "for", "your"}


def toks(text):
    return [w.strip(".,?").lower() for w in text.split() if w.strip(".,?")]


def vocab(texts):
    v = sorted({w for t in texts for w in toks(t) if w not in STOP})
    return v


def embed(text, vocab):
    c = Counter(w for w in toks(text) if w not in STOP)
    return [float(c[w]) for w in vocab]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def main():
    v = vocab(list(DOCS.values()) + [QUERY])
    q = embed(QUERY, v)
    print("query:", QUERY)
    print("vector dim:", len(v), "(stopwords dropped)\n")
    ranked = []
    for name, text in DOCS.items():
        s = cosine(q, embed(text, v))
        ranked.append((s, name, text))
    ranked.sort(reverse=True)
    print(f"{'cos':>6}  doc")
    for s, name, text in ranked:
        print(f"{s:6.3f}  {name:<12} {text}")
    winner = ranked[0][1]
    print(f"\nnearest is {winner} — 'undo the charge' beats 'the weather' even")
    print("though both share the word 'the'. Distance is the retrieve decision.")


if __name__ == "__main__":
    main()
