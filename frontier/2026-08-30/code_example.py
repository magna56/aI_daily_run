"""Circuit condensation: why weight updates, not search, shrink the circuit.

condense() is the accept-or-restore controller from the paper — propose the
lowest-scoring 30% of remaining edges, accept only if BOTH gates hold, and on
failure restore and halve the cut down to a 5% floor.

The toy runs it twice on the same graph and the same scores: once with an
adapter allowed to re-route through surviving edges (condensation), once with
it frozen (classic circuit discovery). Frozen should end up LARGER — that is
the paper's own control, and the only check that separates a real reduction
from a lucky search.

Run: python3 code_example.py     (pure stdlib, deterministic, no network)

CAPACITY is the interesting knob: how much of a cut edge's task mass the
adapter can recover through what remains. Set it to 0.0 and condensation
collapses back into frozen discovery.
"""

import random
import statistics

CAPACITY = 0.72   # fraction of lost task mass an adapter can re-route. Try 0.0, 0.4, 0.9.
ACC_TOL = 0.05    # task accuracy must stay within this of the full-circuit baseline
PPL_TOL = 1.05    # adapter-on/off perplexity ratio ceiling on the capability probe


def condense(edges, score, evaluate, frac=0.30, floor=0.05):
    """Smallest edge set that still passes the gate. The paper's controller.

    `score(kept)` -> {edge: importance}, recomputed against what remains.
    `evaluate(trial)` -> (task_accuracy, perplexity_ratio) for that subgraph.
    A rejected proposal halves the step rather than ending the run, so the
    search gets gentler exactly as it approaches the accuracy boundary. The
    floor is a minimum cut size, not a stopping condition: the run ends when a
    cut AT the floor is rejected, which is the point the circuit stops giving.
    """
    kept = set(edges)
    base_acc, _ = evaluate(kept)
    rejects = 0
    while True:
        ranked = sorted(kept, key=lambda e: score(kept)[e])
        n = max(1, int(len(kept) * frac))
        trial = kept - set(ranked[:n])
        acc, ppl = evaluate(trial) if trial else (0.0, 99.0)
        if trial and base_acc - acc <= ACC_TOL and ppl <= PPL_TOL:
            kept = trial                      # accepted: keep cutting at this rate
            continue
        rejects += 1
        if frac <= floor:                     # rejected at the floor: done
            return kept, rejects
        frac = max(frac / 2, floor)           # restored: be gentler


# --- a toy circuit -----------------------------------------------------------

class ToyCircuit:
    """A behaviour spread over `n` edges, each carrying task mass and general mass.

    Cutting an edge loses its task mass. An adapter recovers CAPACITY of that
    loss by scaling surviving edges up — which is not free: the same scaling
    distorts everything the task does not measure, and that shows up as the
    perplexity ratio the capability gate watches.
    """

    def __init__(self, n=400, capacity=CAPACITY, seed=0, decay=28.0):
        rng = random.Random(seed)
        self.capacity = capacity
        # Real sprawl: a handful of components do the work and hundreds of edges
        # carry almost nothing. Exponential decay, then shuffled so the edge id
        # carries no information the attribution could cheat with.
        mass = [2.718 ** (-i / decay) for i in range(n)]
        rng.shuffle(mass)
        total = sum(mass)
        self.task = {i: m / total for i, m in enumerate(mass)}
        # Edges are not independent, and the dependencies run among the edges
        # that matter — a load-bearing component is entangled with the other
        # load-bearing ones, not with the noise floor.
        core = sorted(self.task, key=self.task.get, reverse=True)[:max(8, n // 8)]
        self.pairs = {i: set(rng.sample([j for j in core if j != i],
                                        k=min(rng.randint(4, 14), len(core) - 1)))
                      for i in range(n)}

    def evaluate(self, kept):
        lost = sum(v for e, v in self.task.items() if e not in kept)
        recovered = lost * self.capacity
        acc = 1.0 - (lost - recovered)
        # Re-routing distorts off-task behaviour in proportion to how hard the
        # surviving edges are being pushed. This is what the capability gate sees.
        strain = recovered / max(sum(self.task[e] for e in kept), 1e-9)
        ppl = 1.0 + 0.055 * strain
        return acc, ppl

    def score(self, kept):
        # Attribution recomputed against what remains, not the original graph.
        live = sum(self.task[e] for e in kept)
        return {e: self.task[e] / max(live, 1e-9) for e in kept}

    def interacting_partners(self, kept, eps=1e-9):
        """For each edge, count partners whose joint ablation differs from the
        sum of the two individual ablations. The paper does this exhaustively
        over every enumerable circuit and finds independence failing in all."""
        counts = []
        for e in kept:
            n = 0
            for f in kept:
                if f == e:
                    continue
                summed = self.task[e] + self.task[f]
                joint = summed
                if f in self.pairs[e]:
                    joint += 0.5 * min(self.task[e], self.task[f])
                if abs(joint - summed) > eps:
                    n += 1
            counts.append(n)
        return counts


def run(label, capacity):
    c = ToyCircuit(capacity=capacity)
    kept, rejects = condense(list(c.task), c.score, c.evaluate)
    acc, ppl = c.evaluate(kept)
    print(f"{label:<34}{len(kept):>6} edges   acc {acc:.3f}   ppl {ppl:.3f}"
          f"   rejects {rejects}")
    return c, kept


def main():
    print(f"start: 400 edges   gates: acc within {ACC_TOL}, perplexity ratio <= {PPL_TOL}\n")
    _, frozen = run("frozen search (no updates)", 0.0)
    c, cond = run(f"condensed (capacity {CAPACITY})", CAPACITY)

    print(f"\ncondensed is {len(frozen) / len(cond):.1f}x smaller than frozen search")
    print("the paper's control: frozen search returns LARGER circuits in 29 of 32 settings,"
          "\nso the reduction comes from the weight updates, not from the search.")

    counts = c.interacting_partners(cond)
    print(f"\npair ablation over the condensed circuit ({len(cond)} edges):")
    print(f"  median interacting partners per edge: {statistics.median(counts):.1f}")
    print(f"  edges with zero interacting partners: {counts.count(0)}/{len(counts)}")
    print("  minimal is not independent — the paper finds independence failing in"
          " every circuit tested.")

    print("\nsweep the adapter's re-routing capacity:")
    for cap in (0.0, 0.2, 0.4, 0.6, 0.8):
        cc = ToyCircuit(capacity=cap)
        k, _ = condense(list(cc.task), cc.score, cc.evaluate)
        print(f"  capacity {cap:.1f} -> {len(k):>4} edges")


if __name__ == "__main__":
    main()
