# How to Choose What to Cut When You Shrink a Model

**Category**: Multimodal Engineering
**Tags**: distillation, multimodal, paper
**Date**: 2026-09-13
**Level**: Deeper
**For**: How models work
**Hook**: Cutting a model down means choosing which parts to lose. Score each part on its own and take the best two, and you get a worse model than if you had taken two that scored lower — because the scores were right and adding them was the mistake.
**Engineer's view**: You have profiled a service, found the two slowest functions, optimized both, and got far less than the sum of the two wins — because they shared a lock. Ranking items independently is only valid when the items are independent, and you found that out afterwards.
**TLDR**: Choosing what to remove from a model by ranking parts individually picks combinations that interact badly. Scoring the combinations instead, and cutting in stages, beat the obvious approach on every benchmark tested.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine taking two bricks out of a wall. You test each brick on its own and both seem
easy to remove — the wall barely moves. So you take out both. The wall sags, because those
two were holding each other's weight. A different pair, each of which looked slightly worse
on its own, comes out cleanly. Testing bricks one at a time never told you which ones were
leaning on each other.

## The Problem

You have made this mistake with no model involved. You profiled a service, found the two
slowest functions, optimized both, and the total win was far less than the two measured
wins added together. They shared a lock. The measurements were correct; the addition was
not.

Pruning a network invites the same error, and the setup makes it feel rigorous. Score each
layer for how much removing it costs. Sort. Remove the cheapest two. Every step is defensible
and the result is a pair nobody evaluated as a pair.

The cost of getting this wrong is not abstract. An audio encoder sits in front of a speech
model, and its depth is inference cost on every request. Cutting it is worth real money, and
cutting the wrong two layers produces a model that is both smaller and meaningfully worse —
the outcome that makes a team abandon compression entirely.

What makes it hard to catch is that nothing looks wrong on the way. Each score was measured
honestly, the sort is correct, and the failure only shows up in a model you have already
built.

**The fix is to score combinations rather than layers**, and to remove them in stages rather
than all at once.

## The Fix: Evaluate Pairs, and Cut in Two Hops

Researchers at XPENG published this on 10 September 2026, compressing the audio encoder of a
speech model. Their layer-selection result is the whole argument in two numbers.

```figure
{ "kind": "bars",
  "title": "Two pairs of layers, and what each costs when removed together",
  "bars": [
    { "label": "{6,8} — best individually", "v": 778, "d": "7.78%", "s": "bad" },
    { "label": "{5,6} — worse individually", "v": 693, "d": "6.93%", "s": "ok" }
  ],
  "note": "Error rate after removing the pair. Individual means were 6.04% for {6,8} and 6.13% for {5,6}." }
```

Layers 6 and 8 are the two strongest single removals. Their individual scores average 6.04%,
better than the 6.13% of layers 5 and 6. Remove them **as a pair** and the model lands at
7.78%, against 6.93% for the pair that looked worse. The ranking was accurate and
non-additive, which is the property a sort silently assumes away.

### How do you score a combination without training it?

With a deliberately short run, and the shortness is the design.

Each candidate combination gets a fixed 0.3-epoch LoRA warm-up on a five-benchmark
development suite, under identical initialization, data and optimization. That behavioral probe is not an attempt to recover the model. It is a matched comparison,
and it measures **recoverability** — how well this combination comes back — rather than
importance, which is a property the method never assigns to a layer at all.

### Why remove them in two hops rather than one?

Because the second decision is better made by the repaired model than the original one.

```figure
{ "kind": "system",
  "title": "The whole argument: same four layers gone, two ways of getting there",
  "lanes": [
    { "t": "18 layers", "nodes": [
        { "id": "start", "t": "the encoder as shipped" } ] },
    { "t": "removed", "nodes": [
        { "id": "direct", "t": "all four at once", "s": "bad" },
        { "id": "prog",   "t": "two, recover, two more", "s": "ok" } ] },
    { "t": "14 layers", "nodes": [
        { "id": "worse", "t": "6.73% error", "s": "bad" },
        { "id": "better", "t": "5.75% error", "s": "new" } ] }
  ],
  "edges": [
    { "from": "start",  "to": "direct" },
    { "from": "start",  "to": "prog", "t": "recover between", "s": "ok" },
    { "from": "direct", "to": "worse", "s": "bad" },
    { "from": "prog",   "to": "better", "s": "new" } ],
  "note": "Identical final architecture. Better on all ten benchmarks, by up to 2.73 points." }
```

The first hop removes layers 1 and 18, then runs the full recovery. The second hop removes 5
and 6 from that repaired model. Doing all four at once reaches 6.73%; doing it in two hops
reaches 5.75%, and wins on every one of the ten benchmarks.

Recovery is distillation from a larger teacher, which needs cross-scale matching because the
teacher is wider than the student. The teacher choice is not a detail either: a 1.7B teacher
gives 5.55% mean error where self-distillation gives 8.45%.

## What This Means for You

**When this matters.** You are removing capacity from something and choosing what to remove
by ranking. That is pruning, and it is also feature selection, cache eviction, dead-code
removal and dependency trimming. The failure has nothing to do with audio.

**How it affects you.** It gives you a specific thing to distrust: a sorted list used to pick
more than one item. The sort is fine for choosing one. The moment you take the top *k*, you
have assumed the items do not interact, and nothing in the ranking procedure tests that.

It also suggests the cheap fix. You do not need a theory of which components interact — you
need to evaluate the combination you are about to ship, once, under matched conditions. That
is one extra short run per candidate pair, which is affordable exactly because it is short.

**What to do about it.**

1. Find the place in your system where a ranked list picks more than one thing to remove.
   Most teams have one and have never questioned it.
2. Evaluate the top two or three *combinations* rather than the top individual items. A short
   matched run is enough; you are comparing, not recovering.
3. If you are removing several things, do it in stages with a repair step between, and make
   each later decision against the repaired system.
4. When you repair by distillation, check the teacher. The gap between a real teacher and
   self-distillation here was larger than the gap between good and bad layer choices.

## Implementing It

**The change.** Three pieces, and the first is the one that generalizes beyond models.

*Score combinations, not items.* The search is over pairs, and it is deliberately shallow:

```python
from itertools import combinations

def pick_pair(layers, budget=2, probe_epochs=0.3):
    """Evaluate the k candidate PAIRS, not the k best singles.

    Every run uses identical init, data and optimizer so the numbers are
    comparable. The run is short on purpose: this measures recoverability,
    not final quality.
    """
    singles = {l: probe(remove=[l], epochs=probe_epochs) for l in layers}
    shortlist = sorted(singles, key=singles.get)[:6]        # a cheap prefilter
    scored = {c: probe(remove=list(c), epochs=probe_epochs)
              for c in combinations(shortlist, budget)}
    return min(scored, key=scored.get), scored
```

The prefilter uses the ranking for what it is good at — narrowing — and then stops trusting
it. Six singles give fifteen pairs, which is a bounded number of short runs, and the bound is
the reason this is affordable: the search is quadratic in the shortlist, not in the model.

*Remove in hops, repairing between.* Each decision is made against the current model, not the
original:

```python
def progressive_prune(model, target_depth, per_hop=2):
    while depth(model) > target_depth:
        pair, _ = pick_pair(prunable_layers(model), budget=per_hop)
        model = remove_layers(model, pair)
        model = recover(model, teacher=TEACHER)      # full recovery, every hop
    return model
```

*Recover against a real teacher.* The teacher is larger than the student, so the layers do
not line up. Group them and project:

```python
def distill_loss(student_hidden, teacher_hidden, proj):
    """Uniformly group the teacher's layers to match the student's count, then
    project the wider teacher features down through a learned bottleneck."""
    groups = chunk(teacher_hidden, into=len(student_hidden))
    loss = 0.0
    for s, g in zip(student_hidden, groups):
        t = proj(mean(g))                             # wider teacher -> narrower student
        loss += mse(s, t) + cosine_distance(s, t)
    return loss
```

The bottleneck is a two-layer MLP at 256 dimensions, and both a squared-error and a cosine
term are used — the first matches magnitude, the second matches direction, and dropping
either leaves one of them free to drift. The projection is learned rather than fixed, which
matters because the teacher's features are not a scaled copy of the student's; there is no
correct static mapping to write down.

**How you know it worked.** Compare the chosen combination against the top-ranked singles on
the same held-out set. If they agree, your components do not interact and the sort was fine;
if they disagree, you have just avoided shipping the worse model and you now know this system
needs combination scoring permanently.

The slower signal is the one that justifies the machinery: measure on every benchmark, not the
mean. Progressive pruning here won on all ten, and a method that wins on average while losing
on two is a different and much weaker result.

**When not to.** Skip the combination search when you are removing exactly one thing. The
whole failure is an artifact of adding scores together, and with one item there is nothing to
add.

## When Ranking Individually Is Fine

The sorted list is not wrong, it is narrow, and it is worth knowing where it holds.

It holds when the items genuinely do not interact. Removing two independent feature columns,
two unrelated dependencies, two cache entries with no shared parent — the scores add because
the things do. If you can argue independence, the ranking is the whole answer and the
combination search is wasted compute.

It also holds when evaluation is expensive relative to the decision. Fifteen short probe runs
is affordable at this scale; fifteen full retrainings is not. If your only measurement is a
complete training run, the honest move is to remove one thing at a time rather than to pretend
a cheap proxy exists.

And this is one encoder, on one model family, on speech benchmarks. The non-additivity is the
transferable claim. The specific layers, the two-hop schedule and the 0.3-epoch probe are
tuned to that setting, and the probe length in particular is the first thing to re-check
elsewhere.

Three questions before adopting it:

- Does my ranking get used to pick more than one item?
- Can I afford a short matched run per candidate combination?
- If I am repairing after removal, is my teacher actually better than the thing I am repairing?

## Glossary

- **Pruning** — removing parts of a trained network to cut inference cost. Here whole encoder
  layers, chosen as combinations rather than individually.
- **Recoverability** — how well a model comes back after a given removal, measured by a short
  matched training run. Deliberately not the same as a layer's importance.
- **Progressive pruning** — removing capacity in stages with a repair between, so each later
  decision is made against the repaired model rather than the original.
- **Distillation** — training a smaller model to match a larger one's internal representations
  as well as its outputs. The teacher's quality dominated every other choice here.
- **Cross-scale matching** — aligning a wider teacher to a narrower student by grouping the
  teacher's layers and projecting its features through a learned bottleneck.
- **Behavioral probe** — the short, fixed-budget run used to compare candidates under
  identical conditions. It exists to rank options against each other, not to produce a model.
