"""Why the top-two of a ranking is not the best pair.

Builds a small system whose components interact, scores each one alone the way
a pruning pass does, then compares the top-two-by-score against every pair
evaluated as a pair.

The scores are honest. Adding them is what fails.

Pure standard library. The "layers" are synthetic, but the structure -- some
components carry redundant information, so removing one is cheap and removing
both is not -- is the one the paper measures.

Run: python3 code_example.py

Set COUPLING to 0.0 and the two methods agree, because nothing interacts.
"""

import itertools
import random

SEED = 11
N_LAYERS = 10
COUPLING = 0.75        # how much redundant capability overlapping layers share
TRIALS = 40            # probe runs averaged per candidate, to model probe noise
PROBE_NOISE = 0.12

# Each layer carries some capability. Layers sharing a GROUP are partly
# redundant with each other: losing one is survivable, losing both is not.
GROUPS = {0: "a", 1: "b", 2: "c", 3: "c", 4: "d",
          5: "e", 6: "e", 7: "f", 8: "e", 9: "g"}
CAPABILITY = {0: 1.0, 1: 0.9, 2: 1.3, 3: 1.2, 4: 1.1,
              5: 1.4, 6: 0.8, 7: 1.5, 8: 0.85, 9: 1.2}


def true_error(removed):
    """Error after removing a set of layers. Redundancy is the whole point:
    the first layer lost from a group is mostly absorbed, the second is not."""
    err = 4.8
    by_group = {}
    for l in removed:
        by_group.setdefault(GROUPS[l], []).append(l)
    for g, ls in by_group.items():
        for i, l in enumerate(sorted(ls, key=lambda x: -CAPABILITY[x])):
            # COUPLING governs ALL of the interaction, so that setting it to 0
            # makes the system genuinely additive and the ranking correct. The
            # first loss in a group is cushioned by its surviving partners;
            # later losses lose that cushion and take a penalty on top.
            cushion = 1.0 - 0.65 * COUPLING if i == 0 else 1.0
            err += CAPABILITY[l] * cushion
            if i > 0:
                err += COUPLING * CAPABILITY[l]
    return err


def probe(removed, rng):
    """A short matched run: the true error plus measurement noise."""
    return sum(true_error(removed) + rng.gauss(0, PROBE_NOISE)
               for _ in range(TRIALS)) / TRIALS


def main():
    rng = random.Random(SEED)
    layers = list(range(N_LAYERS))

    singles = {l: probe([l], rng) for l in layers}
    ranked = sorted(layers, key=singles.get)

    print("Scoring each layer alone (lower is more removable)\n")
    print("  %-8s %8s %8s" % ("layer", "group", "probe"))
    for l in ranked:
        print("  %-8d %8s %8.2f" % (l, GROUPS[l], singles[l]))

    top2 = tuple(sorted(ranked[:2]))
    pairs = {c: probe(list(c), rng) for c in itertools.combinations(layers, 2)}
    best = min(pairs, key=pairs.get)

    print("\n  %-34s %s  ->  %.2f" % ("top two by individual score", top2, pairs[top2]))
    print("  %-34s %s  ->  %.2f" % ("best pair, evaluated as a pair", best, pairs[best]))

    rank_of_top2 = sorted(pairs, key=pairs.get).index(top2) + 1
    print("\n  The top-two pair ranks %d of %d when pairs are actually measured."
          % (rank_of_top2, len(pairs)))
    print("  Gap: %.2f points of error, for the same number of layers removed."
          % (pairs[top2] - pairs[best]))

    same = "the same pair" if top2 == best else "a different pair"
    print("  Sorting and taking the top two picks %s." % same)

    print("\n  Why: the two best singles share a group\n")
    print("    %-12s %-8s %-10s %s" % ("pair", "groups", "sum alone", "measured"))
    for c in [top2, best] + [p for p in sorted(pairs, key=pairs.get)[:3]
                             if p not in (top2, best)][:2]:
        gs = "".join(sorted(GROUPS[l] for l in c))
        alone = singles[c[0]] + singles[c[1]] - true_error([])   # naive addition
        print("    %-12s %-8s %-10.2f %.2f" % (str(c), gs, alone, pairs[c]))

    print("\n  Read the last two columns. Where the groups differ, adding the")
    print("  singles predicts the pair well. Where they match, it does not —")
    print("  and a sorted list has no column for that.")


if __name__ == "__main__":
    main()
