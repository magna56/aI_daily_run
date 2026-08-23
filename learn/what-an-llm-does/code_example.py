#!/usr/bin/env python3
"""
Next-token prediction is the whole runtime. The three training stages only
change which token looks likely.

This file builds a tiny count-based next-word table (no neural net, no API)
and applies the stages as data operations:

  1. Pretrain  — count next words on unlabeled sentences
  2. SFT       — add labeled (prompt, assistant-reply) pairs
  3. Preference — boost a preferred continuation, cut a rejected one

Run:  python3 code_example.py
"""

from collections import Counter, defaultdict

START, END = "<s>", "</s>"


def tokenize(text):
    return [START] + text.lower().replace(".", " .").split() + [END]


def add_counts(table, text, weight=1):
    toks = tokenize(text)
    for a, b in zip(toks, toks[1:]):
        table[a][b] += weight


def dist(table, prev):
    c = table[prev]
    total = sum(c.values()) or 1
    return {w: n / total for w, n in sorted(c.items(), key=lambda kv: -kv[1])}


def show(title, table, prev):
    print(f"\n=== {title}  P(next | {prev!r}) ===")
    for w, p in dist(table, prev).items():
        bar = "#" * int(round(p * 30))
        print(f"  {p:5.0%}  {bar:<30}  {w}")


def main():
    table = defaultdict(Counter)

    # --- 1. Pretrain: unlabeled internet-ish text ---
    web = [
        "the cat sat on the mat .",
        "the cat sat on the chair .",
        "users asked the model a question .",
        "the model sat on the question .",  # completer-ish nonsense
    ]
    for s in web:
        add_counts(table, s)
    print("PRETRAIN corpus (unlabeled next-word counts)")
    for s in web:
        print(f"  {s}")
    show("after pretrain", table, "the")
    show("after pretrain", table, "model")

    # --- 2. SFT: (prompt → assistant reply) as more next-word counts ---
    sft = [
        "user : what did the cat sit on ? assistant : the cat sat on the mat .",
        "user : what did the cat sit on ? assistant : the cat sat on the chair .",
    ]
    for s in sft:
        add_counts(table, s, weight=4)
    print("\nSFT pairs (labeled assistant replies, weight=4)")
    for s in sft:
        print(f"  {s}")
    show("after SFT", table, "the")
    show("after SFT", table, "assistant")

    # --- 3. Preference: chosen reply up, rejected reply down ---
    add_counts(table, "assistant : the cat sat on the mat .", weight=6)
    add_counts(table, "assistant : the model sat on the question .", weight=-3)
    # Keep counts non-negative so a "rejected" path can die.
    for prev, nxts in table.items():
        for w in list(nxts):
            if nxts[w] < 0:
                nxts[w] = 0
    print("\nPREFERENCE: boost 'mat' reply, penalize the nonsense completer")
    show("after preference", table, "the")
    show("after preference", table, "on")

    print("\nSame machine the whole way: pick the next word from a table.")
    print("Stages only changed the counts. Serving still samples one word.")


if __name__ == "__main__":
    main()
