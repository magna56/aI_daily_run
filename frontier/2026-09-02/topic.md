# How Running Each Layer Twice Pays for Itself

**Category**: Applied Research
**Tags**: training, transformers, cost, paper
**Date**: 2026-09-02
**Level**: Deeper
**For**: How models work
**Hook**: Reusing a model's layers has always lost to simply making the model bigger. Changing the order the layers are reused in flips the result, and the reason is memory rather than math.
**Engineer's view**: This is loop interchange. You swap two nested loops so that a layer's reuses sit next to each other, and the arithmetic does not change at all. Here the saving shows up as memory rather than speed, and that memory is then spent on a bigger microbatch.
**TLDR**: Looping a model has always lost to just making it bigger at the same cost. Running each layer twice in place, rather than the whole stack twice, flips the result.
**Time to read**: ~11 minutes

## Explain Like I'm 5

Imagine painting a fence with two coats. You could walk the whole fence putting on the first coat,
then walk it again for the second. Or you could give each plank both coats before moving to the
next one.

The same amount of paint goes on either way. But in the second version you carry your brush and
tin one plank at a time. You are not hauling everything up and down the fence twice. It turns out
the carrying, not the painting, was the expensive part.

## The Problem

You have made this optimization before, in a loop that had nothing to do with machine learning.

You had two nested loops walking a matrix. You swapped which one sat on the outside. The
arithmetic was identical and the output was identical, but the program ran several times faster.
The version that won kept the data it was reusing close together, so the machine stopped fetching
the same rows over and over.

Looped Transformers are that trick one level up. Instead of stacking fifty distinct layers, you
store twenty-five and run each of them twice. You get the depth without storing the parameters.

The idea has a stubborn record of losing. Recurrence is not free. Loop a model N times and its
training compute multiplies by roughly N, so the honest comparison is against a *bigger* model
trained for the same cost. Against that comparison, looping kept coming second. Given an N-fold
increase in pre-training compute, making the model N times bigger has reliably won.

**IQuest Research's Loopie series flips it by changing the order of reuse.** Run layer 1 twice,
then layer 2 twice, rather than running the whole stack twice. The arithmetic is identical either
way. What changes is how much memory the training run needs.

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
depth, not executed depth**. The paper writes it `M_act ∝ s·b·D·L`, where `L` counts the layers you
keep, not the ones you run.

Halve the stored layers and you halve the activation memory. That headroom buys a doubled
per-device microbatch. The gradient-accumulation count halves to match, so the tokens per optimizer
step are unchanged. Measured on Megatron-LM against a reproduction of Qwen3-30B-A3B:
**261.53 TFLOPS/s against 189.65**, from the same hardware.

There is a second, quieter reason. In a 48-layer model looped whole, physical layer 3 runs at
effective depths 3 and 51. Those are two places in the network that demand very different things
of the same weights. Layer-loop reuses a layer at adjacent depths instead, asking it to do one job
rather than two.

### So where does the extra compute come from?

It does not come from anywhere, and this is the honest part of the paper. Loopie performs about
**1.424×** the nominal block compute per token. The models are *not* matched on theoretical FLOPs.
They are matched on measured end-to-end optimizer-step time, which the authors state plainly. The
extra arithmetic is paid for by the throughput the memory headroom unlocked.

The ablation is the cleanest evidence. Take Loopie-6B-A0.6B and keep the looped compute budget
identical. Now remove only the layer-loop ordering. The version that keeps it reaches the same
downstream average **2.14× faster**. Ordering alone, nothing else changed.

## What This Means for You

**When this matters.** You are choosing an architecture under a fixed training budget. Or you are
reading claims that one model beats another "at the same compute" and trying to work out whether
that comparison means anything.

**How it affects you.** The headline number is 2.14× from reordering alone. Not a better optimizer,
not more parameters — the same operations in a different sequence. Mostly, though, it changes what
you should ask of a benchmark. "Compute-matched" has two very different meanings here: theoretical
FLOPs, or measured wall-clock. Loopie wins on the second while explicitly losing on the first. That
is a legitimate choice, because wall-clock is what you pay for. But a comparison that does not say
which one it used is not telling you much. The result also arrives late. Loopie trails its larger
baseline until roughly **600 billion tokens** and only then overtakes.

**What to do about it.** Nothing needs deploying today. The honest read is that this is a signal to
watch rather than a change to make. What you can do now is cheap. Next time you see a
compute-matched claim, look for whether the authors matched FLOPs or measured step time, and
whether they published a crossover point. Loopie does both, which is why it is worth reading. And
if you train anything at all, one lever is worth knowing regardless: activation memory scales with
stored depth, so any architectural choice that shrinks it converts directly into microbatch size.

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

The term that is absent matters more than the ones present. Executed depth does not appear. That is
why running a stored layer twice costs you compute but not activation memory, and that asymmetry is
the entire lever the recipe pulls on.

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

Step (iii) is what makes the first two pay. Halve stored depth without converting the memory
headroom into a bigger microbatch and you get a smaller, slower model and none of the benefit. The
recipe is not "loop the model". It is "loop the model *and spend what that frees*". The authors
then reinvest the measured efficiency gain into extra capacity, until the optimizer-step time
matches the reference again. That is what makes it a compute-matched comparison rather than a
cheaper one.

*Anyone implementing the schedule.* The difference between the two loop patterns is one line of
iteration order. That is exactly why it is easy to get wrong and hard to attribute later:

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

Two nested loops, interchanged. Under pipeline parallelism the consequence is larger than it looks.
In the first form every microbatch traverses the whole pipeline once per loop step, and the final
stage feeds back to the first, so each loop boundary is a synchronization point. In the second,
every repeat of a layer stays inside the pipeline stage that already holds it.

**How you know it worked.** The check is a throughput measurement, not a loss curve, and it comes
first. If the microbatch does not actually double, nothing downstream is worth running. Measure
peak activation memory before and after halving stored depth. It should fall by roughly half. If it
does not, your checkpointing is not enclosing the recurrent applications in one unit, and the whole
mechanism is absent. Then match on **measured optimizer-step time** rather than a FLOP estimate.
Expect to be behind on quality for a long stretch: the published crossover is around 600 billion
tokens against a compute-matched vanilla baseline, and about 1.2 trillion for layer-loop overtaking
model-loop. An A/B stopped at 100B tokens would have concluded the opposite of what the paper found.

## When Looping Is the Wrong Tool

The crossover is the catch. If your training run is shorter than the crossover, you get the version
of this that loses — and most people's runs are shorter. You will also have paid extra nominal
compute per token to get there. This is a technique for runs measured in hundreds of billions of
tokens.

It is also not a free lunch on quality. Loopie-20B-A2B wins AIME (92.10% against Qwen3-30B-A3B-
Thinking's 90.10%) and IFEval. But it loses OlympiadBench to that same Qwen3 model (80.50% against
81.20%), and both ARC-Challenge and MMLU-Redux to Nemotron-Cascade2. Strong for two-thirds the
stored parameters, not a clean sweep.

And read the compute matching for what it is. Matching on measured wall-clock rather than FLOPs is
defensible and clearly disclosed. But it makes the comparison partly a statement about Megatron-LM,
one checkpointing implementation and one GPU. A different stack could recover less of the 1.424×.
Nor can anyone check yet: the linked repository returns 404 and both model pages return 401 at the
time of writing. The mechanism is fully specified — the ordering is four lines — but these numbers
are unreproduced.

Three questions before taking this as settled. Is my training run long enough to reach the
crossover, or would I only ever see the losing half of the curve? Does my checkpointing actually
enclose recurrent applications in one unit, without which the memory argument evaporates? And when
someone tells me two models were compute-matched, which of the two definitions did they use?

## Glossary

- **Looped Transformers** — store fewer layers and run each of them more than once.
- **model-loop** — run the whole stack, then run it again. The prior pattern.
- **layer-loop** — run each layer twice in place before moving on. Loopie's pattern.
- **Activation memory** — what a training step holds for the backward pass; scales with stored depth.
- **Compute-matched** — same training cost. Here it means measured step time, not theoretical FLOPs.
