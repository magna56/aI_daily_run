#!/usr/bin/env python3
"""
RAG without mystique: chunk, retrieve, stuff the prompt.

Two short docs, bag-of-words embeddings (no API), cosine rank, then the exact
concatenated prompt the model would see. Sweep chunk_size x top_k so a small
slice misses the answer, a medium slice catches it, and a large top_k buries it.

Run:  python3 code_example.py
"""

import math
from collections import Counter

DOCS = {
    "billing.md": (
        "Refunds are available for thirty days after purchase. Open the billing "
        "portal, pick the invoice, and submit the refund form. Credits apply to "
        "the original payment method within five business days."
    ),
    "search.md": (
        "The index stores one embedding per chunk. Chunk size is the record size. "
        "A one-hundred-fifty word window with thirty percent overlap held the "
        "finance answer. Raising top-k added words, not new facts."
    ),
}

QUERY = "how long is the refund window and where do I submit it?"
ANSWER = "thirty days after purchase"


def tokenize(text):
    return [w.strip(".,!?").lower() for w in text.split() if w.strip(".,!?")]


def chunk(text, size, overlap=0.25):
    words = text.split()
    step = max(1, int(size * (1 - overlap)))
    out, i = [], 0
    while i < len(words):
        out.append(" ".join(words[i : i + size]))
        if i + size >= len(words):
            break
        i += step
    return out


def embed(text):
    counts = Counter(tokenize(text))
    norm = math.sqrt(sum(v * v for v in counts.values())) or 1.0
    return counts, norm


def cosine(a, b):
    (ca, na), (cb, nb) = a, b
    return sum(ca[k] * cb[k] for k in ca if k in cb) / (na * nb)


def retrieve(size, k, overlap=0.25):
    q = embed(QUERY)
    items = []
    for src, text in DOCS.items():
        for i, c in enumerate(chunk(text, size, overlap)):
            items.append((cosine(q, embed(c)), src, i, c))
    items.sort(reverse=True)
    return items[:k]


def stuff(hits):
    parts = ["You answer only from Context.", "", "Context:"]
    for score, src, i, c in hits:
        parts.append(f"## {src} #chunk-{i} ({score:.2f})")
        parts.append(c)
        parts.append("")
    parts.append("Question: " + QUERY)
    return "\n".join(parts)


def main():
    print(f"QUERY: {QUERY}\n")
    print(f"{'size':>5} {'k':>3}  {'words':>5}  {'hit':>3}  note")
    for size in (8, 20, 40):
        for k in (1, 2, 3):
            hits = retrieve(size, k)
            prompt = stuff(hits)
            n = sum(len(h[3].split()) for h in hits)
            hit = any(ANSWER in h[3] for h in hits)
            if not hit:
                note = "miss — fact split across slices"
            elif n > 40:
                note = "hit, but extra padding stuffed"
            else:
                note = "hit — enough and no more"
            print(f"{size:5d} {k:3d}  {n:5d}  {'yes' if hit else 'no ':3s}  {note}")

    print("\n--- stuffed prompt, chunk_size=20, top_k=2 ---\n")
    print(stuff(retrieve(20, 2)))
    print("--- end of prompt ---")
    print("\nThe model does not search. It reads that string.")
    print("Daily lab 2026-08-23: same recall at 165 words vs a naive 1,367.")


if __name__ == "__main__":
    main()
