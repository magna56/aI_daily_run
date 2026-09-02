# How Running Each Layer Twice Pays for Itself

**Category**: Applied Research
**Tags**: training, transformers, cost, paper
**Date**: 2026-09-02
**Level**: Deeper
**For**: How models work
**Hook**: Reusing a model's layers has always lost to simply making the model bigger. Changing the order the layers are reused in flips the result, and the reason is memory rather than maths.
**Time to read**: ~11 minutes

## Explain Like I'm 5

Imagine painting a fence with two coats. You could walk the whole fence putting on the first coat,
then walk it again for the second. Or you could give each plank both coats before moving to the
next one.

The same amount of paint goes on either way. But in the second version you carry your brush and
tin one plank at a time instead of hauling everything up and down the fence twice — and it turns
out that the carrying, not the painting, was the expensive part.

## The Problem

Looped Transformers are an old and appealing idea: instead of stacking fifty distinct layers,
store twenty-five and run each of them twice. You get the depth without storing the parameters.

The idea has a stubborn record of losing. Given an N-fold increase in pre-training compute,
making the model N times bigger has reliably beaten looping it N times. Looping saves parameters,
but recurrence is not free — loop a model N times and its training compute multiplies by roughly
N too, so the honest comparison is against a *bigger* model trained for the same cost, and against
that comparison recurrence kept coming second. If that sounds like a data structure that halves
your memory and doubles your cache misses, you have the right instinct.

IQuest Research's Loopie series claims to have flipped it, and the interesting part is where the
win comes from. **Loop each layer in place — layer 1, layer 1, layer 2, layer 2 — rather than
running the whole stack twice.** The arithmetic is identical either way. What changes is that all
the repeats of a layer now sit next to each other, and that turns out to decide how much memory
the training run needs.

## The Fix: Loop Each Layer in Place, Not the Whole Stack

Prior looped models — Ouro, Huginn — use what the paper calls **model-loop**: unroll the entire
stack, then run it again. For three layers and two steps the order is
`1 → 2 → 3 → 1 → 2 → 3`.

Loopie uses **layer-loop**: `1 → 1 → 2 → 2 → 3 → 3`. Each block iterates on the hidden state
locally and only then hands the result onward. Same layer applications, same nominal FLOPs,
different order.

### Why does the order of reuse matter at all?

Because activation checkpointing works per stored layer. All the recurrent applications of a layer
land inside the same checkpointed unit. So the dominant activation-memory term scales with **stored
depth, not executed depth** — the paper writes it `M_act ∝ s·b·D·L`, where `L` counts the layers
you keep, not the ones you run.

Halve the stored layers and you halve the activation memory. That headroom buys a doubled
per-device microbatch, and the gradient-accumulation count halves to match, so the tokens per
optimizer step are unchanged. Measured on Megatron-LM against a reproduction of Qwen3-30B-A3B:
**261.53 TFLOPS/s against 189.65**, from the same hardware.

There is a second, quieter reason. In a 48-layer model looped whole, physical layer 3 runs at
effective depths 3 and 51 — two places in the network that demand very different things of the
same weights. Layer-loop reuses a layer at adjacent depths instead, asking it to do one job rather
than two.

### So where does the extra compute come from?

It does not come from anywhere, and this is the honest part of the paper. Loopie performs about
**1.424×** the nominal block compute per token. The models are *not* matched on theoretical FLOPs;
they are matched on measured end-to-end optimizer-step time, which the authors state plainly. The
extra arithmetic is paid for by the throughput the memory headroom unlocked.

The ablation is the cleanest evidence. Take Loopie-6B-A0.6B, keep the looped compute budget
identical, and remove only the layer-loop ordering: the version that keeps it reaches the same
downstream average **2.14× faster**. Ordering alone, nothing else changed.

## For a Software Engineer

This is loop interchange, and you have shipped it.

Every performance engineer has taken a nested loop, swapped the order of iteration so the reused
data stays in cache, and watched the same arithmetic run several times faster. Nothing about the
computation changed — only the distance between a value's uses, and therefore whether it was still
resident when it was needed again.

Model-loop has a reuse distance of the whole stack; layer-loop has a reuse distance of one. In a
pipeline-parallel setup that difference is starker still, because model-loop routes the last
stage's output back to the first at every loop boundary, creating exactly the cyclic dependency
that fills a pipeline with bubbles.

The number worth holding onto: **2.14× from reordering alone**. Not a better optimiser, not more
parameters — the same operations, executed in a different sequence.

## What This Means for You

**When this matters.** You are choosing an architecture under a fixed training budget, or reading
claims that one model beats another "at the same compute" and trying to work out whether that
comparison means anything.

**How it affects you.** Mostly it changes what you should ask of a benchmark. "Compute-matched"
has two very different meanings here — theoretical FLOPs, or measured wall-clock — and Loopie
wins on the second while explicitly losing on the first. That is a legitimate choice, because
wall-clock is what you pay for, but a comparison that does not say which one it used is not
telling you much. The result also arrives late: Loopie trails its larger baseline until roughly
**600 billion tokens** and only then overtakes.

**What to do about it.** Nothing needs deploying today, and the honest read is that this is a
signal to watch rather than a change to make. What you can do now is cheap: next time you see a
compute-matched claim, look for whether the authors matched FLOPs or measured step time, and
whether they published a crossover point. Loopie does both, which is why it is worth reading. And
if you train anything at all, the underlying lever — activation memory scales with stored depth,
so architectural choices that shrink it convert directly into microbatch size — is worth knowing
regardless of whether you ever loop a layer.

## Implementing It

**The change.**

*Anyone reasoning about training memory.* The formula is the whole argument, and it is worth
writing down because the intuition it corrects is common:

```python
def activation_memory(seq_len, microbatch, hidden_dim, stored_layers):
    """The dominant term. Note the argument that is NOT here: executed depth.
    All recurrent applications of a stored layer share one checkpointed unit."""
    return seq_len * microbatch * hidden_dim * stored_layers
```

The term that is absent matters more than the ones present. Executed depth does not appear, which
is why running a stored layer twice costs you compute but not activation memory — and that
asymmetry is the entire lever the recipe pulls on.

*Anyone applying the recipe.* Three steps, in order, and the third is the one people skip:

```python
def loopie_recipe(reference):
    cfg = dict(reference)
    cfg["stored_layers"] //= 2          # (i)  halve stored depth
    cfg["loop_steps"] = 2               # (ii) run each stored layer twice
    cfg["microbatch"] *= 2              # (iii) spend the freed activation memory
    cfg["grad_accum"] //= 2             #       tokens per optimizer step unchanged
    return cfg
```

Step (iii) is what makes the first two pay. Halving stored depth without converting the memory
headroom into a bigger microbatch gives you a smaller, slower model and none of the benefit — the
recipe is not "loop the model", it is "loop the model *and spend what that frees*". The authors
then reinvest the measured efficiency gain into extra capacity until the optimizer-step time
matches the reference again, which is what makes it a compute-matched comparison rather than a
cheaper one.

*Anyone implementing the schedule.* The difference between the two loop patterns is one line of
iteration order, which is exactly why it is easy to get wrong and hard to attribute later:

```python
# model-loop: reuse distance = len(layers)
for _ in range(loop_steps):
    for layer in layers:
        h = layer(h)

# layer-loop: reuse distance = 1
for layer in layers:
    for _ in range(loop_steps):
        h = layer(h)
```

Two nested loops, interchanged. Under pipeline parallelism the consequence is larger than it looks:
in the first form every microbatch traverses the whole pipeline once per loop step and the final
stage feeds back to the first, so each loop boundary is a synchronisation point. In the second,
every repeat of a layer stays inside the pipeline stage that already holds it.

**How you know it worked.** The check is a throughput measurement, not a loss curve, and it comes
first — if the microbatch does not actually double, nothing downstream is worth running. Measure
peak activation memory before and after halving stored depth; it should fall by roughly half, and
if it does not, your checkpointing is not enclosing the recurrent applications in one unit and the
whole mechanism is absent. Then match on **measured optimizer-step time** rather than a FLOP
estimate, and expect to be behind on quality for a long stretch: the published crossover is around
600 billion tokens against a compute-matched vanilla baseline, and about 1.2 trillion for
layer-loop overtaking model-loop. An A/B stopped at 100B tokens would have concluded the opposite
of what the paper found.

## When Looping Is the Wrong Tool

The crossover is the catch. If your training run is shorter than the crossover — and most people's
are — you get the version of this that loses, and you will have paid extra nominal compute per
token to get there. This is a technique for runs measured in hundreds of billions of tokens.

It is also not a free lunch on quality. Loopie-20B-A2B wins AIME (92.10% against Qwen3-30B-A3B-
Thinking's 90.10%) and IFEval, but loses OlympiadBench to that same Qwen3 model (80.50% against
81.20%), and both ARC-Challenge and MMLU-Redux to Nemotron-Cascade2. Strong for two-thirds the
stored parameters, not a clean sweep.

And read the compute matching for what it is. Matching on measured wall-clock rather than FLOPs is
defensible and clearly disclosed, but it makes the comparison partly a statement about Megatron-LM,
one checkpointing implementation and one GPU; a different stack could recover less of the 1.424×.
Nor can anyone check yet: the linked repository returns 404 and both model pages return 401 at the
time of writing. The mechanism is fully specified — the ordering is four lines — but these numbers
are unreproduced.

Three questions before taking this as settled. Is my training run long enough to reach the
crossover, or would I only ever see the losing half of the curve? Does my checkpointing actually
enclose recurrent applications in one unit, without which the memory argument evaporates? And when
someone tells me two models were compute-matched, which of the two definitions did they use?
