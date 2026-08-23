#!/usr/bin/env python3
"""
Test-time compute is a timeout on the same program, not a new weight file.

A lock of size N. A "fast model" gets one guess (P = 1/N). A "reasoning
model" spends a thinking budget on yes/no higher-lower questions — binary
search — then guesses. Each question is 80 billed thought tokens (output
rate). The weight file never changes; only the pad does.

Rates used in the write-up: $15 / million output tokens, 40 tokens/s.
Run:  python3 code_example.py
"""

THINK_PER_STEP = 80
ANSWER = 40
PRICE_OUT = 15.00 / 1_000_000
TOK_PER_S = 40
STEPS = (0, 4, 8, 12)


def remaining(n, steps):
    return max(1, (n + (1 << steps) - 1) >> steps)


def row(n, steps):
    left = remaining(n, steps)
    p = 1.0 / left
    think = steps * THINK_PER_STEP
    tokens = think + ANSWER
    return {
        "steps": steps,
        "p": p,
        "think": think,
        "usd": tokens * PRICE_OUT,
        "sec": tokens / TOK_PER_S,
        "left": left,
    }


def table(n, label):
    print(f"\n{label}: {n}-key lock  (one guess after {THINK_PER_STEP}-token questions)")
    print(f"{'steps':>6}  {'P(hit)':>8}  {'thought':>8}  {'cost':>8}  {'wait':>7}")
    for s in STEPS:
        r = row(n, s)
        print(
            f"{r['steps']:6d}  {r['p']:7.2%}  {r['think']:5d} tok  "
            f"${r['usd']:.4f}  {r['sec']:5.1f}s"
        )


def main():
    table(16, "Easy")
    table(4096, "Hard")
    fat = 8000
    print("\nSame weights, a sloppy 8,000-token pad (no extra questions that help):")
    print(f"  billed as output: ${fat * PRICE_OUT:.2f}  wait {fat / TOK_PER_S:.0f}s")
    print("  That is $0.12 of thought before the answer exists.")
    easy4, hard0, hard12 = row(16, 4), row(4096, 0), row(4096, 12)
    print("\nRouting:")
    print(f"  easy lock @ 4 steps:  {easy4['p']:.0%} hit, ${easy4['usd']:.4f}")
    print(f"  hard lock @ 0 steps:  {hard0['p']:.4%} hit  (fast SKU, wrong tool)")
    print(f"  hard lock @ 12 steps: {hard12['p']:.0%} hit, ${hard12['usd']:.4f}, {hard12['sec']:.1f}s")
    print("\nThe pad is a product choice. Spend it where a checker exists.")


if __name__ == "__main__":
    main()
