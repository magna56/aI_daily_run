"""Why the harness that scored worst on your benchmark generalized best.

An agent harness -- prompts, control flow, tools, memory -- can be evolved
automatically: propose edits, keep whatever scores higher. That loop is an
optimizer, and an unconstrained optimizer will happily learn your benchmark
instead of the task.

This is RRSI's argument reduced to something you can run. Two searches over the
same toy harness: one unregularized, one with a leakage critic, a pruner and a
cosine-annealed edit budget. Watch the unregularized run win the set it evolves
against and lose on tasks it never saw.

Run: python3 code_example.py
"""

import math
import random

# --- The knob. Change this and watch the conclusion move. --------------------
# How much of the benchmark a "leaky" component can memorize. At 0.0 leaky
# edits are useless and both searches behave the same -- which is the case
# where none of this machinery earns its keep.
LEAK_STRENGTH = 0.9

SEED, ROUNDS, CANDIDATES = 7, 10, 8
B_MAX, B_MIN = 4, 1          # edits a proposal may bundle, early vs late


# --- Liftable core: the three regularizers -----------------------------------

def edit_budget(t, rounds=ROUNDS, b_max=B_MAX, b_min=B_MIN):
    """Cosine-annealed bundle size, straight from the paper.

    Early rounds may bundle several coordinated edits; later rounds are sparse,
    so a late gain is attributable to one change instead of four.
    """
    return math.ceil(b_min + (b_max - b_min) * 0.5 * (1 + math.cos(math.pi * t / rounds)))


def critic_rejects(component):
    """Leakage screen: reject anything that names the evaluation.

    The paper rejects task names, entity names, task-specific values and
    answers. Generic improvements to a prompt stay. This is the single cheapest
    regularizer here and it does most of the work.
    """
    return component["kind"] == "leaky" or component["inert"]


def pruner_rejects(component, history, window=3):
    """Drop a component that has stopped paying: no strictly positive gain in
    the recent window, or an earlier benefit that has since evaporated."""
    recent = history.get(component["id"], [])[-window:]
    return len(recent) >= window and max(recent) <= 0.0


# --- A toy harness and a toy benchmark ----------------------------------------

def make_tasks(n, rng, family, hi=1.0):
    """Each task has a feature a GENERAL component can exploit, and a UNIQUE id
    a LEAKY component can memorize.

    Ids must not repeat across splits or a memorizing component scores on the
    held-out set too, which silently hides the whole effect. Out-of-distribution
    tasks additionally draw their feature from a narrower range, so a general
    component tuned to a high threshold transfers only partly.
    """
    return [{"id": f"{family}-{i}", "feature": rng.uniform(0, hi), "family": family}
            for i in range(n)]


def score(harness, tasks):
    """Fraction of tasks solved. General components help everywhere; leaky ones
    only help the exact task ids they memorized."""
    solved = 0
    for task in tasks:
        p = 0.35                                   # the frozen model alone
        for c in harness:
            if c["kind"] == "general" and task["feature"] > c["threshold"]:
                p += c["lift"]
            elif c["kind"] == "leaky" and task["id"] in c["memorized"]:
                p += LEAK_STRENGTH
        solved += min(p, 1.0)
    return solved / len(tasks) * 100


def propose(rng, evolve, budget, counter):
    """Generate one candidate: `budget` edits, some general, some leaky."""
    edits = []
    for _ in range(budget):
        counter[0] += 1
        if rng.random() < 0.5:
            edits.append({"id": counter[0], "kind": "general", "inert": False,
                          "threshold": rng.uniform(0.2, 0.8), "lift": rng.uniform(0.02, 0.10)})
        else:
            edits.append({"id": counter[0], "kind": "leaky", "inert": rng.random() < 0.2,
                          "memorized": {t["id"] for t in rng.sample(evolve, 4)}})
    return edits


def evolve_harness(evolve, regularized, rng):
    harness, history, counter = [], {}, [0]
    for t in range(ROUNDS):
        budget = edit_budget(t) if regularized else B_MAX
        best, best_score = None, score(harness, evolve)
        for _ in range(CANDIDATES):
            edits = propose(rng, evolve, budget, counter)
            if regularized:
                edits = [e for e in edits if not critic_rejects(e)]
            if not edits:
                continue
            s = score(harness + edits, evolve)
            if s > best_score:
                best, best_score = edits, s
        if best:
            for e in best:
                gain = score(harness + [e], evolve) - score(harness, evolve)
                history.setdefault(e["id"], []).append(gain)
                harness.append(e)
        if regularized:
            harness = [c for c in harness if not pruner_rejects(c, history)]
    return harness


def main():
    rng = random.Random(SEED)
    evolve = make_tasks(40, rng, "evolve")
    held_in = make_tasks(40, rng, "heldin")          # same distribution, unseen tasks
    ood = make_tasks(40, rng, "ood", hi=0.6)         # a genuinely different mix

    print(f"leak strength {LEAK_STRENGTH}, {ROUNDS} rounds, {CANDIDATES} candidates per round")
    print(f"\n{'harness':<22}{'evolve':>9}{'held-in':>10}{'OOD':>8}{'size':>7}")
    print("-" * 56)
    base = []
    print(f"{'frozen model only':<22}{score(base, evolve):>9.1f}{score(base, held_in):>10.1f}"
          f"{score(base, ood):>8.1f}{len(base):>7}")

    rows = []
    for label, reg in (("unregularized", False), ("RRSI-style", True)):
        h = evolve_harness(evolve, reg, random.Random(SEED))
        e, i, o = score(h, evolve), score(h, held_in), score(h, ood)
        rows.append((label, e, i, o))
        print(f"{label:<22}{e:>9.1f}{i:>10.1f}{o:>8.1f}{len(h):>7}")

    (_, e_un, _, o_un), (_, e_rr, _, o_rr) = rows
    print(f"\nthe unregularized search wins the set it tuned against by "
          f"{e_un - e_rr:+.1f} points")
    print(f"and loses on tasks it never saw by {o_un - o_rr:+.1f}")
    print("\nThe evolve-set number is the one that cannot be trusted, because it is\n"
          "the only one the optimizer was allowed to read.")


if __name__ == "__main__":
    main()
