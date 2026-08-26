#!/usr/bin/env python3
"""
The control loop from AutoSaddler (arXiv:2608.23041), toy-sized: evaluate a
harness on a mini-batch, diagnose the failures, propose a typed patch, then
gate it on TWO checks before keeping it -- did it improve the mini-batch it
was written for, AND does it hold on a disjoint dev-set it never saw. The
paper's own ablation: removing the second gate alone drops GAIA2 Pass@1 from
62.0% to 50.6%. This implements why.

Two patch styles stand in for the paper's ablation: a shallow patch that
memorizes the specific failing task IDs (fixes the batch, generalizes to
nothing) versus a deep-diagnosis patch that learns the actual missing skill
(fixes the batch AND every future task needing that skill). Not the paper's
LLM diagnosis agent -- that needs a real model and codebase. This is the
loop and the gate around it, the part you can validate without one.

Run:  python3 code_example.py
"""

import random
from dataclasses import dataclass, field

random.seed(7)

SKILLS = ["read", "search", "write", "verify"]
TASKS = [(f"t{i}", frozenset(random.sample(SKILLS, k=random.randint(1, 2))))
         for i in range(40)]
MINI_BATCH = TASKS[:8]          # the failures that motivate this round's patch
DEV_SET = TASKS[8:28]           # disjoint -- never used to write the patch
HELD_OUT_TEST = TASKS[28:]      # only used for the final report


@dataclass
class Harness:
    capabilities: frozenset = field(default_factory=lambda: frozenset({"read"}))
    memorized_ids: frozenset = field(default_factory=frozenset)  # shallow-patch escape hatch

    def solves(self, task):
        task_id, needed = task
        return task_id in self.memorized_ids or needed <= self.capabilities

    def score(self, tasks):
        return sum(self.solves(t) for t in tasks) / len(tasks)


def diagnose(harness, batch_results):
    """What's actually missing vs. which specific tasks failed -- the toy
    stand-in for the paper's file-reading diagnosis agent finding a root
    cause instead of a symptom."""
    missing_skills, failing_ids = set(), set()
    for task, ok in batch_results:
        if not ok:
            missing_skills |= task[1] - harness.capabilities
            failing_ids.add(task[0])
    return missing_skills, failing_ids


def propose_patch(harness, missing_skills, failing_ids, shallow):
    """shallow=True: memorize the exact IDs that failed -- passes the batch
    it was written for, teaches the harness nothing transferable. shallow=
    False: add the actual missing capability -- the deep-diagnosis patch."""
    if shallow:
        return Harness(capabilities=harness.capabilities,
                        memorized_ids=harness.memorized_ids | failing_ids)
    return Harness(capabilities=harness.capabilities | missing_skills,
                    memorized_ids=harness.memorized_ids)


def should_accept(harness, candidate, mini_batch, dev_set):
    """The two-gate rule. Both must hold -- this single function is the
    entire gap between the paper's 62.0% and its 50.6% ablation."""
    batch_ok = candidate.score(mini_batch) > harness.score(mini_batch)
    dev_ok = candidate.score(dev_set) > harness.score(dev_set)  # must actually
    # generalize -- unchanged is not evidence the patch helps beyond its batch
    return batch_ok and dev_ok, batch_ok, dev_ok


def run_loop(shallow, rounds=4):
    harness = Harness()
    dev_history = []
    for r in range(rounds):
        results = [(t, harness.solves(t)) for t in MINI_BATCH]
        missing_skills, failing_ids = diagnose(harness, results)
        if not failing_ids:
            dev_history.append(harness.score(DEV_SET))
            continue
        candidate = propose_patch(harness, missing_skills, failing_ids, shallow)
        accepted, batch_ok, dev_ok = should_accept(harness, candidate, MINI_BATCH, DEV_SET)
        verdict = "ACCEPTED" if accepted else "REJECTED (overfits mini-batch)"
        change = (f"memorize {len(failing_ids)} task IDs" if shallow
                  else f"add capability {sorted(missing_skills)}")
        print(f"  round {r}: {change:32}  batch_ok={batch_ok} dev_ok={dev_ok}  -> {verdict}")
        if accepted:
            harness = candidate
        dev_history.append(harness.score(DEV_SET))
    return harness, dev_history


def main():
    print("=== Patch A: shallow -- memorizes the failing task IDs ===")
    shallow_harness, shallow_history = run_loop(shallow=True)
    print(f"dev-set score by round: {[f'{s:.0%}' for s in shallow_history]}")

    print("\n=== Patch B: deep diagnosis -- learns the missing skill ===")
    deep_harness, deep_history = run_loop(shallow=False)
    print(f"dev-set score by round: {[f'{s:.0%}' for s in deep_history]}")

    print("\nHeld-out test score, never touched by either loop:")
    print(f"  shallow (memorized IDs): {shallow_harness.score(HELD_OUT_TEST):.0%}")
    print(f"  deep diagnosis:          {deep_harness.score(HELD_OUT_TEST):.0%}")
    print("\nSame gate, same code, same starting harness. The only difference")
    print("is whether the proposed patch generalized -- gate 2 is what tells them apart.")


if __name__ == "__main__":
    main()
