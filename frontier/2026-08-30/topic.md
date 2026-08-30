# How to Shrink a Model's Wiring Diagram Until You Can Read It

**Category**: AI Safety & Alignment
**Tags**: paper, transformers, from-scratch
**Date**: 2026-08-30
**Level**: Deeper
**For**: How models work
**Hook**: Explanations of what a model is doing usually come back too big to read. It turns out you can make them smaller by editing the model, not by searching harder.
**Time to read**: ~8 minutes

## Explain Like I'm 5

Imagine wanting to know which pipes carry water to one fountain. You trace the network and get four hundred pipes — correct, and unreadable.

So you try something else. You close one pipe at a time, and after each closure you let the plumbers re-route what remains. The only rule is that the fountain must still run exactly as before.

Do that enough times and forty pipes feed the fountain instead of four hundred — a map small enough to read.

## The Problem

Ask which parts of a language model produce one specific behaviour and the honest answer is hundreds of connections. That is not an explanation. You cannot inspect it, compare it against another model's, or check it exhaustively — which is what you wanted it for.

The reason is that the search is only allowed to *look*. It takes the model as fixed and hunts for the smallest set of connections that still reproduces the behaviour. If the model spreads that behaviour across four hundred connections, the smallest faithful answer is four hundred, and no cleverer search does better.

So the circuit measures two things at once and cannot separate them: how the behaviour works, and how diffusely this model happened to implement it.

## How Circuit Condensation Works

### What a circuit is

A transformer is a stack of attention heads and MLP blocks that all read from and write to one shared buffer, the residual stream. A **circuit** for a behaviour is a subgraph: the components that matter, plus the **edges** saying which reads which earlier one's output. Cutting an edge swaps that input for an activation from a corrupted prompt, so it stops carrying information.

Edges are ranked by **EAP-IG** — edge attribution patching with integrated gradients — which estimates importance from gradients instead of cutting and re-running each edge.

### The accept-or-restore loop

Each round:

1. Propose cutting the lowest-scoring **30%** of remaining edges.
2. Train a **rank-16** low-rank adapter (α = 32) across all residual-stream writers — 500 AdamW steps at `1e-4`.
3. Accept only if **both** gates hold: task accuracy within **0.05** of the full-circuit baseline, *and* an adapter-on/off perplexity ratio of at most **1.05** on a 320-prompt probe across five domains.
4. If either fails, restore the last accepted state and **halve** the cut, down to a 5% floor.

The adapter matches the original model's own output distribution, never the task labels — the distinction that decides whether the result explains anything.

### The finding

Across four behaviours and eight models, condensed circuits beat the strongest frozen baseline in **30 of 32** settings, by **8.1× on average** and up to **316×**.

The control is what makes it a result. Re-run the identical search with weight updates off and you get *larger* circuits in **29 of 32** settings. The shrinking comes from editing the model, not from searching better.

## For a Software Engineer

This is the difference between a linter and a compiler.

A linter may only delete code that is already unreachable. It cannot touch a function three callers still reference, however redundant those calls are, because it may not rewrite anything. A compiler that can inline, fold and rewrite call sites deletes far more — not because its analysis is sharper, but because it may change the program while preserving observable behaviour.

Frozen discovery is the linter. Condensation is the compiler, and the perplexity gate is the "preserving observable behaviour" clause.

The KL objective is the instinct you already have about characterisation tests. Refactoring something you do not understand, you pin the *current* output and refactor against that — you do not re-derive the answer from the spec, because then you are writing new code and calling it a refactor.

## What This Means for You

**When this matters.** Directly, when you read an interpretability result and want to know whether the circuit describes the mechanism or just that model's sprawl. Indirectly, whenever you simplify a system you do not fully understand.

**How it affects you.** Two things transfer. A size claim about a circuit means nothing without knowing whether weights could move — the 29-of-32 control exists because the authors knew that. And minimal is not independent: pair ablations across 48 enumerable circuits found independence failing in *every* one, median **7.4 interacting partners per edge**.

**What to do about it.** Take the controller. Any lossy simplification you run by hand — dropping features, deleting a cache layer, cutting a config surface — wants the same shape: a two-part gate where one half is what you are optimising and the other a broad guard you may not trade against it, plus a backoff that halves the step instead of giving up. Most hand-run simplifications have the first half and no second, which is why they overshoot.

## Implementing It

**The change.**

*The proposer.* The controller is the liftable piece, and it is small. The floor is a minimum cut *size*, not a stopping condition — the run ends when a cut at the floor is rejected, which is the point the circuit stops giving. Get that wrong and the loop exits while there is still room, returning wherever the schedule ran out.

```python
def condense(edges, score, train_adapter, gate, frac=0.30, floor=0.05):
    """Return the smallest edge set that still passes `gate`."""
    kept, accepted = set(edges), None
    while True:
        ranked = sorted(kept, key=score(kept).get)   # rescored against what remains
        trial = kept - set(ranked[:max(1, int(len(kept) * frac))])
        adapter = train_adapter(trial)               # 500 steps, KL to the original
        if trial and gate(trial, adapter):
            kept, accepted = trial, adapter          # keep cutting at this rate
            continue
        if frac <= floor:                            # rejected at the floor: done
            return kept, accepted
        frac = max(frac / 2, floor)                  # restored, so be gentler
```

*The scorer.* Attribution is a function of the graph you are standing on, not the one you started with, so it must be recomputed against what remains. Scoring once up front is the cheap mistake: it ranks edges by their importance in a graph that no longer exists, and the loop then cuts the wrong ones first.

```python
def score_edges(kept, clean, corrupt, steps=5):
    """EAP-IG: importance from gradients, averaged over an interpolation path."""
    total = {e: 0.0 for e in kept}
    for i in range(steps):                        # corrupted -> current
        acts = lerp(corrupt, clean, (i + 0.5) / steps)
        for e, g in edge_gradients(kept, acts).items():
            total[e] += g * (clean[e] - corrupt[e]) / steps
    return total                                  # recompute after every cut
```

*The guard.* Both halves are required, and the second one is what stops the loop cheating. Optimising task accuracy alone lets the adapter wreck everything the task does not measure:

```python
def gate(trial, adapter, base_acc, probe):
    acc = task_accuracy(trial, adapter)
    ppl = perplexity(probe, adapter_on=True) / perplexity(probe, adapter_on=False)
    return (base_acc - acc) <= 0.05 and ppl <= 1.05   # 320 prompts, 5 domains
```

*The objective.* This is the single line most likely to be got wrong, so write it as a contrast:

```python
# WRONG — the adapter re-learns the task through whatever path survived,
# and you end up with a small graph that explains nothing.
loss = cross_entropy(masked_logits, labels)

# RIGHT — pin the original model's distribution and match it through the cut graph.
loss = kl_div(log_softmax(masked_logits), softmax(orig_logits.detach()))
```

**How you know it worked.** Run the paper's own control, because it is the only check separating a real result from a lucky search: the same graph, the same scores, twice — once letting the adapter train, once with it frozen. Frozen must come out *larger*. In `code_example.py` it does, 84 edges against 50 from a 400-edge start. If yours does not, the adapter is not doing the work and your reduction came from the search.

The second signal is the rejection log, which tells you whether the run finished or merely stopped. A healthy run rejects: expect `frac` to halve two or three times, because each rejection is the loop finding where the accuracy boundary sits. A run that accepted every proposal never found that boundary, and re-running it with a smaller floor will keep shrinking it.

Watch which gate rejects, too. If accuracy always binds and the perplexity ratio never approaches 1.05, your capability probe is too narrow to catch the off-task damage — widen it before trusting the result.

## When Condensing a Circuit Is the Wrong Tool

The honest limit is the authors' own: the result is *a sufficient sub-circuit of the published mechanism rather than a reconstruction of it*. On indirect object identification, condensation isolates 24 heads with 17 carrying documented roles, against 61 heads of which 25 are documented — cleaner, but a claim about a model you have now modified, not the one you started with. If your question is "what does this shipped checkpoint do", condensation answers a different question.

It is also expensive: every proposed cut costs 500 training steps, where a frozen method returns a graph in one pass.

Three questions before reaching for it:

1. Do you need the mechanism, or the mechanism *in this checkpoint*? Only the first survives weight edits.
2. Can you state your capability guard as a number before you start? Without it the loop optimises into damage you are not measuring.
3. Would minimality help? At 7.4 interacting partners per edge, the small graph is still not a set of parts you can reason about one at a time.
