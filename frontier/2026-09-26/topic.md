# Why Averaging Two Prompts Averages Their Answers

**Category**: Applied Research
**Tags**: transformers, paper, from-scratch
**Date**: 2026-09-26
**Level**: Deeper
**For**: How models work
**Hook**: Feed a model the average of two prompts' embeddings and it answers with roughly the average of the two answers, which a stack of nonlinear layers has no business doing.
**Engineer's view**: This is packing two counters into one integer. One in the low bits, one in the high bits, both incremented by a single add — because addition does not carry across the boundary, until one overflows and corrupts the other. Two prompts share a model the same way, and the carry is the nonlinearity.
**TLDR**: Mix a pair of prompts at the embedding layer and the next-token distribution comes back near the average of the answers you would have got separately. The effect is strongest in an untrained network and decays as pretraining proceeds.
**Time to read**: ~12 minutes

## Explain Like I'm 5

Two people talk into one microphone at the same time.

If the microphone is faithful, the recording is just their two voices added together, and a careful listener can still pull them apart. Nothing was lost — the sounds simply share the wire.

If the microphone distorts, they smear into each other and no amount of care separates them again.

A language model turns out to be closer to the faithful microphone than anyone expected, given how much distortion is built into it.

## The Problem

You have shipped this before, and it had nothing to do with AI.

You needed two counters and had one 64-bit field to put them in. So you packed them: one in the low thirty-two bits, one in the high thirty-two. Incrementing both was a single add, because addition does not carry across the boundary.

It worked beautifully until one counter overflowed its half and started corrupting the other.

That is a system carrying two signals on one channel, and it works exactly as long as the operation stays linear over the range you are using.

Now the question that shape raises about a transformer.

A transformer is a stack of things that are emphatically not linear — attention softmaxes, gated activations, normalization. So if you averaged the token embeddings of two unrelated prompts and ran the result through, you should get nonsense. There is no reason the output would relate in any simple way to what either prompt alone would have produced.

A group at AIRI and Skoltech checked, and it does. Mix two sequences at the embedding layer, `e_t = ½(E(x_t) + E(y_t))`, and the next-token distribution comes back close to `½(P(·|A) + P(·|B))` — the average of the two answers. They call it the Superposition Linearity Hypothesis.

So the fix, if you want to use this rather than admire it. Measure the effect against a baseline that makes "close" mean something. And know it is strongest in the network you have not finished training.

```figure
{ "kind": "system",
  "title": "The whole argument: two prompts, one channel",
  "lanes": [
    { "t": "you mix at", "nodes": [
        { "id": "emb", "t": "the embedding layer", "s": "new" } ] },
    { "t": "the stack is", "nodes": [
        { "id": "nonlin", "t": "emphatically nonlinear", "s": "bad" } ] },
    { "t": "yet you get back", "nodes": [
        { "id": "avg", "t": "about the average of both answers", "s": "ok" } ] },
    { "t": "and it weakens as", "nodes": [
        { "id": "train", "t": "pretraining proceeds", "s": "bad" } ] }
  ],
  "edges": [
    { "from": "emb", "to": "nonlin", "s": "neutral" },
    { "from": "nonlin", "to": "avg", "t": "should not survive, does", "s": "ok" },
    { "from": "avg", "to": "train", "t": "so it is architectural", "s": "bad" } ],
  "note": "The decay is the evidence. A learned behavior would improve with training, not erode." }
```

## The Fix: Normalize the Divergence, Then Read the Decay

A raw divergence between two distributions is uninterpretable. The whole method is in what you divide it by.

### What does "close to the average" actually mean?

It means closer than two unrelated answers are to each other. The paper defines a **Superposition Approximation Ratio**: the divergence between the target average and the mixed output, divided by the divergence between the two individual answers. Below 1.0 means the mix landed nearer the average than the two answers sit from one another.

They measure it three ways: KL at temperature 1.5, Jensen-Shannon, and a Wasserstein distance over the top 256 tokens. Three, because any single metric can be flattered by a distribution's shape.

The number worth carrying is the plainest one. Across Pythia, Llama, Qwen and OLMo, **30–40% of the target's top-10 tokens survive in the mixed output**. For the top-100 it is 60–65%.

### Why is a softmax already enough to break it?

Because superposition is never exact, and the output layer alone guarantees that. Run the Code tab with the nonlinearity set to zero. The body is then a linear map, and the ratio is still **0.110** rather than nought. `softmax(½(a+b))` is not `½(softmax(a) + softmax(b))`.

That is the floor. Everything the body adds stacks on top of it — turn the dial to 0.9 and the ratio climbs to 0.207 while top-10 survival falls from 53% to 46%.

### Why does more training make it worse?

This is the result that makes the paper interesting rather than cute. Hidden-state additivity error rises **monotonically** across pretraining checkpoints. A behavior the model was learning would sharpen with training; this erodes.

So the conclusion runs the other way: superposition is a property of the architecture that training gradually spends. The toy model reproduces the shape — scale the weights up as a crude stand-in for training and the ratio goes 0.090, 0.154, 0.216, 0.282.

## What This Means for You

**When this matters.** Today, almost never in production. This is a result about what transformers are, and the honest framing is that it changes how you think rather than what you deploy this quarter.

**How it affects you.** It undercuts a mental model most engineers carry — that a deeply nonlinear network mixes its inputs into something irrecoverable. Two prompts share the representation far more cleanly than that picture allows, which is a different starting point for reasoning about batching artifacts, prompt interference and anything that puts unrelated content in one context.

**What to do about it.** The one thing worth doing now costs an afternoon and needs no training: run the measurement on a model you actually use. Take pairs of unrelated prompts, average their embeddings, and compute the approximation ratio against the two separate distributions. If you have ever wondered whether unrelated content in one context window interferes, this is the instrument for asking.

Then read the number the right way round. A ratio near 1.0 says the mix is no closer to the average than the two answers are to each other, which is the null result. Below 1.0 is the claim, and how far below tells you how much room a technique built on this would have.

## Implementing It

**The change.** Three roles, and the first is where most attempts go wrong.

**Role 1 — whoever runs the measurement.** The mix happens at the **token embedding layer**, not at the hidden state and not at the logits. Getting that wrong measures something else entirely.

```python
e_a, e_b = model.embed_tokens(ids_a), model.embed_tokens(ids_b)
p_a = softmax(model(inputs_embeds=e_a).logits[:, -1])
p_b = softmax(model(inputs_embeds=e_b).logits[:, -1])

p_mix = softmax(model(inputs_embeds=(e_a + e_b) / 2).logits[:, -1])
p_target = (p_a + p_b) / 2          # what superposition predicts
```

**Role 2 — whoever reports the result.** A bare divergence is not a finding. Normalize it, or you cannot say whether 0.4 is impressive.

```python
ratio = kl(p_target, p_mix) / kl(p_a, p_b)   # < 1.0 is the claim
top10 = rank_overlap(p_target, p_mix, k=10)  # the number you can picture
```

Report rank survival beside the ratio. Divergences are abstract and easy to misjudge by an order of magnitude; "thirty-eight percent of the top ten survived" is a sentence anyone can argue with.

**Role 3 — whoever wants to use it rather than measure it.** Superposition out of the box is lossy, and the paper restores it by training for it: self-distillation with a frozen teacher, the student seeing mixed embeddings and matching the teacher's averaged predictions.

```python
loss = kl_div(teacher_avg_logprobs, student(mixed_embeddings))   # ~200k steps
```

On Pythia-2.8B that took KL from **1.86 to 0.27** and lifted top-5 probability from about 30% to over 60%. Their guided decoding then adds small per-stream contrastive terms to pull the two continuations apart, reaching roughly a **2x** throughput gain over running the prompts one after the other.

**How you know it worked.** Two signals, and the second is the one that catches a wrong setup.

First, the ratio should sit well below 1.0 on unrelated prompt pairs. If it hovers around 1.0, check where you mixed — combining hidden states or logits instead of embeddings produces exactly this null.

Second, the ratio should get **worse** on a more heavily trained checkpoint of the same family. That is the paper's signature finding, and reproducing it is the strongest evidence your measurement is reading the real effect rather than an artifact of your own pipeline. If your numbers improve with training, something in the setup is measuring the model's competence rather than its linearity.

## When Superposition Is the Wrong Thing to Build On

The two-streams-at-once result needs training to be useful. Out of the box only a third of the top-10 survives, which is an interesting measurement and not a decoding strategy. Getting to the paper's numbers meant 200k steps of self-distillation on FineWeb plus jointly trained contrastive terms, so "a free 2x" is not what is on offer.

The evidence is also about next-token distributions at one position. Nothing here shows two long generations stay coherent and separable over hundreds of tokens without the trained decoder, and the paper does not claim it does.

And this is a workshop paper, accepted at an EMNLP 2026 workshop rather than the main conference. That is not a reason to dismiss it. The measurement is careful and replicated across four model families. It is a reason to treat the guided-decoding throughput number as a promising early result rather than a settled one.

Three questions before building on it:

Am I measuring at the embedding layer, or somewhere that makes the result vacuous?

Does my use survive the effect being lossy, or does it need the fine-tuned version?

Would a 2x throughput gain justify maintaining a separately distilled model?

## Glossary

- **Superposition** — two inputs sharing one representation such that the output reflects both.
- **Embedding layer** — where token ids become vectors, and the only place this mixing is measured.
- **Superposition Approximation Ratio** — divergence to the averaged target over divergence between the two answers.
- **Rank survival** — how much of the target's top-k appears in the mixed output's top-k.
- **Self-distillation** — training a student to match a frozen copy of itself under altered inputs.
- **Guided decoding** — adding per-stream terms at decode time to pull two superposed continuations apart.
