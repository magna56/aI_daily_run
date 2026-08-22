"""
Model Cascades in the Price-Collapse Era
========================================
A pure-Python simulation of a two-tier LLM cascade (flash -> frontier) with an
imperfectly-calibrated escalation gate. No API keys, no network. Stdlib only.

Run:
    python3 code_example.py

What it demonstrates
--------------------
1. Always-flash vs always-frontier vs cascade on cost AND accuracy.
2. Sweeping the escalation threshold traces the cost/accuracy Pareto frontier.
3. Two levers that move the frontier: the PRICE SPREAD (Aug-2026 economics) and
   the GATE CALIBRATION (how well confidence predicts correctness). Kill the
   calibration and the cascade collapses toward a coin-flip router.

Model of the world (deliberately simple, but captures the real tradeoff):
- Each query has a hidden difficulty d ~ U(0,1).
- A tier answers correctly with prob = sigmoid(k*(competence - d)); frontier is
  more competent, so its curve sits to the right.
- The flash tier also emits a CONFIDENCE in [0,1] that is correlated with whether
  it was actually correct -- but only as strongly as `calibration` allows.
- The gate escalates to frontier when confidence < threshold. Escalated queries
  pay BOTH tiers (the double-pay tax).

Pricing (per 1M tokens, blended, Aug 2026 order-of-magnitude):
    flash    : ~$0.20   (e.g. DeepSeek-V4-Flash / GPT-5.6 Luna class)
    frontier : ~$10.00  (e.g. Claude Opus 5 / Qwen3.8-Max class)
"""

import math
import random

random.seed(20260803)

# ---- world constants ---------------------------------------------------------
N = 5000
FLASH_COMPETENCE, FRONTIER_COMPETENCE = 0.62, 0.88
SLOPE = 10.0
FLASH_COST, FRONTIER_COST = 0.20, 10.00      # $ / 1M tokens, blended
TOKENS_PER_Q = 1500 / 1_000_000              # assume ~1.5k tokens/query


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def answer_correct(competence: float, difficulty: float) -> bool:
    return random.random() < sigmoid(SLOPE * (competence - difficulty))


def flash_confidence(correct: bool, calibration: float) -> float:
    """Confidence correlated with correctness. calibration in [0,1]:
    1.0 = confidence perfectly separates right/wrong; 0.0 = pure noise."""
    signal = 0.80 if correct else 0.20            # ideal, separated means
    noisy = calibration * signal + (1 - calibration) * random.random()
    return min(1.0, max(0.0, noisy + random.gauss(0, 0.10)))


# ---- pre-generate a fixed query workload so all strategies see the same data --
Queries = []
for _ in range(N):
    d = random.random()
    f_correct = answer_correct(FLASH_COMPETENCE, d)
    fr_correct = answer_correct(FRONTIER_COMPETENCE, d)
    Queries.append((d, f_correct, fr_correct))


def dollars(n_flash_calls: int, n_frontier_calls: int) -> float:
    return (n_flash_calls * FLASH_COST + n_frontier_calls * FRONTIER_COST) * TOKENS_PER_Q


def run_cascade(threshold: float, calibration: float):
    """Return (accuracy, cost_usd, escalation_rate)."""
    correct = flash_calls = frontier_calls = escalated = 0
    for d, f_correct, fr_correct in Queries:
        flash_calls += 1
        conf = flash_confidence(f_correct, calibration)
        if conf < threshold:                      # gate says: don't trust flash
            frontier_calls += 1
            escalated += 1
            correct += fr_correct                 # frontier's answer wins
        else:
            correct += f_correct
    return correct / N, dollars(flash_calls, frontier_calls), escalated / N


def baseline(competence_correct_field: int):
    correct = sum(q[competence_correct_field] for q in Queries)
    calls = N
    return correct / N


# ---- 1. headline comparison --------------------------------------------------
print("=" * 68)
print("MODEL CASCADE SIMULATION  (N=%d queries, ~1.5k tokens each)" % N)
print("flash=$%.2f/M  frontier=$%.2f/M  spread=%.0fx" %
      (FLASH_COST, FRONTIER_COST, FRONTIER_COST / FLASH_COST))
print("=" * 68)

flash_acc = baseline(1)
frontier_acc = baseline(2)
flash_cost = dollars(N, 0)
frontier_cost = dollars(0, N)

casc_acc, casc_cost, esc = run_cascade(threshold=0.5, calibration=0.75)

print(f"{'strategy':<20}{'accuracy':>10}{'cost($)':>12}{'vs frontier':>14}")
print("-" * 68)
print(f"{'always-flash':<20}{flash_acc:>9.1%}{flash_cost:>12.4f}"
      f"{flash_cost/frontier_cost:>13.0%}")
print(f"{'always-frontier':<20}{frontier_acc:>9.1%}{frontier_cost:>12.4f}"
      f"{'100%':>14}")
print(f"{'cascade @0.5':<20}{casc_acc:>9.1%}{casc_cost:>12.4f}"
      f"{casc_cost/frontier_cost:>13.0%}")
print(f"\ncascade escalated {esc:.0%} of traffic, recovered "
      f"{(casc_acc-flash_acc)/(frontier_acc-flash_acc):.0%} of the "
      f"flash->frontier accuracy gap for {casc_cost/frontier_cost:.0%} of the cost.")

# ---- 2. Pareto frontier by sweeping the threshold ----------------------------
print("\n" + "=" * 68)
print("PARETO FRONTIER  (sweep escalation threshold, calibration=0.75)")
print("=" * 68)
print(f"{'thresh':>7}{'escal%':>8}{'accuracy':>10}{'cost($)':>10}   frontier (accuracy vs cost)")
for t in [i / 10 for i in range(0, 11)]:
    acc, cost, e = run_cascade(threshold=t, calibration=0.75)
    # bar position scaled between flash_cost and frontier_cost
    frac = (cost - flash_cost) / (frontier_cost - flash_cost)
    bar = "#" * int(frac * 30)
    print(f"{t:>7.1f}{e:>7.0%}{acc:>10.1%}{cost:>10.4f}   |{bar:<30}|")

# ---- 3. calibration is the whole ballgame ------------------------------------
print("\n" + "=" * 68)
print("LEVER: GATE CALIBRATION  (threshold fixed at 0.5)")
print("=" * 68)
print(f"{'calibration':>12}{'escal%':>9}{'accuracy':>10}{'cost($)':>10}")
for cal in [1.0, 0.75, 0.5, 0.25, 0.0]:
    acc, cost, e = run_cascade(threshold=0.5, calibration=cal)
    tag = "  <- perfect judge" if cal == 1.0 else ("  <- coin flip" if cal == 0.0 else "")
    print(f"{cal:>12.2f}{e:>8.0%}{acc:>10.1%}{cost:>10.4f}{tag}")

print("\nTakeaway: with a well-calibrated gate the cascade escalates mostly the")
print("queries flash gets WRONG -- near-frontier accuracy at a fraction of cost.")
print("With a random gate it overpays on easy queries and still misses hard ones:")
print("same cost, worse accuracy. The model is commodity; the JUDGE is the moat.")
