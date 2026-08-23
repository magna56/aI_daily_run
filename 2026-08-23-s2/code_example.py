"""
Infrastructure noise in agentic coding evals — a pure-Python simulation.

Anthropic found that agentic coding benchmarks (SWE-bench, Terminal-Bench) can swing several
percentage points based purely on container memory limits, not model capability:
https://www.anthropic.com/engineering/infrastructure-noise

This script reproduces the same two-phase pattern with synthetic tasks:
  - Below ~3x memory headroom: raising the limit mostly RESCUES tasks that were failing from
    spurious out-of-memory kills, not genuine mistakes. Infra error rate drops sharply while
    success rate among COMPLETED runs barely moves — the gap is noise, not capability.
  - Above ~3x headroom: extra memory starts enabling a genuinely different (heavier, more
    reliable) problem-solving strategy, so success rate among completed runs jumps for real.

Run: python3 code_example.py
"""

import random
import math

random.seed(7)

N_TASKS = 300
TRIALS_PER_TASK = 8
MULTIPLIERS = [1, 2, 3, 5, 999]  # 999 stands in for "uncapped"
BASE_ALLOC = 1.0                 # each task's nominal ("1x") memory budget

HEAVY_FOOTPRINT_SHARE = 0.06  # tasks like bn-fit-modify: only solvable by installing the full
                              # stack, which needs real headroom no matter how the agent is written


class Task:
    __slots__ = ("demand_mu", "demand_sigma", "light_success_p", "heavy_success_p")

    def __init__(self):
        if random.random() < HEAVY_FOOTPRINT_SHARE:
            # median demand ~2.7x the base allocation — genuinely needs headroom, not a
            # coding mistake
            self.demand_mu, self.demand_sigma = 1.0, 0.35
        else:
            # median demand ~0.14x the base allocation — essentially never trips even a
            # tight limit
            self.demand_mu, self.demand_sigma = -2.0, 0.4
        # "light" strategy: what the agent does inside a tight budget — genuine per-task
        # capability, independent of how much memory happens to be available.
        self.light_success_p = random.betavariate(6, 4)
        # "heavy" strategy: only reachable once headroom clears ~3x (installing the full
        # data-science stack instead of hand-rolling the math, etc.) — its own, separately
        # better success rate.
        self.heavy_success_p = min(1.0, self.light_success_p + random.uniform(0.10, 0.25))


TASKS = [Task() for _ in range(N_TASKS)]


def run(multiplier):
    limit = BASE_ALLOC * multiplier
    heavy_available = multiplier >= 3
    infra_fail = 0
    successes = 0
    completed = 0
    total = 0
    for task in TASKS:
        for _ in range(TRIALS_PER_TASK):
            total += 1
            # a fresh demand sample per trial — memory spikes aren't deterministic across
            # repeated runs of the same task
            demand = random.lognormvariate(task.demand_mu, task.demand_sigma) * random.lognormvariate(0.0, 0.15)
            if demand > limit:
                infra_fail += 1
                continue
            completed += 1
            p = task.heavy_success_p if heavy_available else task.light_success_p
            if random.random() < p:
                successes += 1
    return infra_fail, successes, completed, total


def wilson_ci(successes, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return center - half, center + half


print(f"{'headroom':>10} | {'infra fail %':>13} | {'success % (completed)':>22} | 95% CI")
print("-" * 74)
results = []
for m in MULTIPLIERS:
    infra_fail, successes, completed, total = run(m)
    infra_rate = infra_fail / total
    success_rate = successes / completed
    lo, hi = wilson_ci(successes, completed)
    label = "uncapped" if m == 999 else f"{m}x"
    print(f"{label:>10} | {infra_rate*100:12.1f}% | {success_rate*100:21.1f}% | [{lo*100:.1f}, {hi*100:.1f}]")
    results.append((label, infra_rate, success_rate, lo, hi))

print()
print("Reading the two phases:")


def overlaps(a, b):
    lo_a, hi_a = a[3], a[4]
    lo_b, hi_b = b[3], b[4]
    return not (hi_a < lo_b or hi_b < lo_a)


below = overlaps(results[0], results[1])  # 1x vs 2x — both below the strategy-unlock threshold
crossing = overlaps(results[1], results[2])  # 2x vs 3x — crosses it
above = overlaps(results[2], results[-1])  # 3x vs uncapped — both above it

print(
    f"  1x -> 2x        (below threshold) : infra failures {results[0][1]*100:.1f}% -> {results[1][1]*100:.1f}%, "
    f"success-among-completed CIs {'OVERLAP (the infra fix bought nothing extra)' if below else 'DIVERGE'}"
)
print(
    f"  2x -> 3x        (crossing it)      : success-among-completed CIs "
    f"{'OVERLAP' if crossing else 'DIVERGE (the heavy strategy unlocks — real capability gap)'}"
)
print(
    f"  3x -> uncapped   (above threshold) : success-among-completed CIs "
    f"{'OVERLAP (no further real gain)' if above else 'DIVERGE'}"
)

print("\nSame model and task set at every row above — every point of movement came from the container, not the agent.")
