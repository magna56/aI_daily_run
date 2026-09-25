# How to Tell Whether Text Came From Your Own Model

**Category**: AI in Production
**Tags**: inference-serving, security, benchmarks
**Date**: 2026-09-25
**Level**: Building
**For**: Shipping AI
**Hook**: A watermark can be added to a model's output without changing a single word of it, and checking for one later needs the key and the text but not the model.
**Engineer's view**: This is the seeded random you already use. You swapped the system random for one seeded from a value you logged, so a run could be replayed. Here the sampler still draws from the model's true distribution, but its randomness is a function of your secret — so you can replay it later.
**TLDR**: Adding Gumbel noise to logits and taking the argmax samples from the same distribution as ordinary sampling. Make that noise a function of a secret key and the output carries a mark that costs nothing in quality.
**Time to read**: ~12 minutes

## Explain Like I'm 5

You and a friend each shuffle a deck and turn over cards.

Yours looks as random as theirs. Nobody watching can tell the difference, because it genuinely is a fair shuffle — every card still comes up as often as it should.

But you shuffled using a rule only you know. Later, holding the pile, you can work backwards and see your rule in it.

The catch: if the deck was all one suit, there was nothing to arrange, and your rule left no trace at all.

## The Problem

You have shipped this before, and it had nothing to do with AI.

Your test suite failed intermittently and you could not reproduce it. The fixture data was randomized, so every run was a different run, and the failure vanished when you looked at it.

You fixed it by seeding the generator from a value you logged. The data stayed just as random; it simply became replayable.

That is the whole idea below, one scale up.

Now the AI version of the problem. Your model generates text, and it goes out into the world. Later somebody asks whether a particular passage came from your system — a support reply that was quoted back at you, a student's submission, a document in a compliance review. You cannot tell. Comparing against logs fails because the text has been edited, and running it back through the model tells you only that the model *could* have said it.

The usual fix is to degrade the output: push the sampler toward a set of preferred tokens, accept slightly worse text, and call the difference a watermark. Nobody wants to ship that.

So the fix, and vLLM shipped it yesterday: use the Gumbel-max trick. Sample by adding Gumbel noise to the logits and taking the argmax, which is provably the same distribution as ordinary sampling, then make that noise a pseudorandom function of a secret key. The words do not change. Only *which* of the model's equally valid choices wins, and that is now something you can recompute later.

```figure
{ "kind": "system",
  "title": "The whole argument: the mark is in the choice, not in the words",
  "lanes": [
    { "t": "you sample by", "nodes": [
        { "id": "rand", "t": "random noise + argmax", "s": "neutral" },
        { "id": "prf", "t": "keyed noise + argmax", "s": "new" } ] },
    { "t": "the distribution is", "nodes": [
        { "id": "same", "t": "identical either way", "s": "ok" } ] },
    { "t": "so later you can", "nodes": [
        { "id": "no", "t": "prove nothing", "s": "bad" },
        { "id": "yes", "t": "replay the noise and test it", "s": "ok" } ] }
  ],
  "edges": [
    { "from": "rand", "to": "same", "s": "neutral" },
    { "from": "prf", "to": "same", "t": "provably", "s": "ok" },
    { "from": "rand", "to": "no", "s": "bad" },
    { "from": "prf", "to": "yes", "t": "key + tokenizer, no model", "s": "ok" } ],
  "note": "Quality is untouched because the distribution is untouched. What changes is what you can check afterwards." }
```

## The Fix: Make the Sampler's Randomness a Function of Your Key

Three pieces: a way to sample that is equivalent to sampling, a source of noise only you can reproduce, and a test.

### Why doesn't this make the output worse?

Because of an identity. Take the log-probabilities, add an independent Gumbel sample to each, and pick the largest. The token you get is distributed *exactly* as if you had sampled from the softmax directly. This is the Gumbel-max trick, and it is an equality rather than an approximation.

This property has a name worth knowing, because it is what separates this from older schemes: the watermark is **distribution-preserving**, meaning every token's probability is exactly what it was before. Nothing is tilted. Run the Code tab: the true probability of the top token is 0.2000 and the watermarked frequency over 60,000 draws is 0.1991. vLLM reports the same at the level that matters operationally — matched throughput moved between −1.1% and +2.0% across batch sizes on a Qwen3.5-27B on one H100, which is noise.

### Where does the noise come from, if not from randomness?

From a pseudorandom function you seed yourself. For each candidate token the value is `PRF(key, recent_context, token_id)` — vLLM uses the last four tokens by default.

Every input is either public or yours. The tokens are in the text; the key is not. That is what makes the mark checkable later without the model, the prompt, or the logits.

### How does the test actually work?

For each token, recompute its own `u` and score it. A token the key nudged into first place carries a systematically large `u`, so its score runs high. Sum the scores across the passage: under the null hypothesis of unwatermarked text, that sum follows a Gamma distribution with shape equal to the token count, and the p-value falls straight out.

In the simulation, 25 watermarked tokens give a p-value around **1e-11** while unwatermarked text sits between 0.1 and 0.76. The signal accumulates with length.

## What This Means for You

**When this matters.** If you serve a model whose output anyone might later attribute to you — support replies, generated documentation, anything a customer republishes — and any time a policy conversation starts with "can we tell if this was AI".

**How it affects you.** The cost is close to zero, which is genuinely unusual, so the reason not to do it is not performance. The reason is that it does far less than the word "watermark" suggests. It tells you a passage is consistent with your key. It does not survive heavy paraphrase, it says nothing about who prompted the model, and its strength depends on properties of the text rather than on your configuration.

**What to do about it.** Start here, and it costs one flag: turn it on behind a server you already run, generate a few hundred tokens, and run the detector over both that and some text you wrote yourself. You will learn more from those two p-values than from any amount of reading, and you will see the false-positive behavior on your own data rather than on a benchmark.

Then measure the thing that decides whether it is useful to you: the entropy of your actual outputs. If your model mostly emits structured, predictable text, the next section is about you.

## Implementing It

**The change.** Three roles, and the third is the one that decides whether any of it was worth doing.

**Role 1 — whoever runs the server.** It is a flag, and the key is a secret like any other.

```bash
vllm serve mistralai/Mistral-7B-Instruct-v0.3 \
  --watermark-config '{"algorithm":"gumbel","key":42}'
```

Treat that key the way you treat a signing key. Anyone holding it can both detect your output and forge the mark on text you never generated, and rotating it orphans everything generated before the rotation.

**Role 2 — whoever writes the detector.** This is the half that has to live outside the serving path, because it runs on text somebody hands you months later.

```python
def detect(tokens, key, width=4):
    scores = []
    for i in range(width, len(tokens)):
        u = prf(key, tokens[i - width:i], tokens[i])   # same PRF as the sampler
        scores.append(-math.log(1 - u))                # Exp(1) under the null
    return gamma_sf(sum(scores), len(scores))          # p-value, shape = n tokens
```

It needs the tokenizer and the key. No weights, no prompt, no logs. That is the property worth protecting when you decide where this code runs.

**Role 3 — whoever sets the threshold.** A p-value under 0.01 flags about one unwatermarked passage in a hundred, and that is fine until you test more than one key.

```python
# Bonferroni: testing K candidate keys multiplies your false positives by K
threshold = 0.01 / len(candidate_keys)
```

That correction is Bonferroni, and vLLM's own numbers show what it costs. On MBPP at 400 tokens, true-positive rate falls from about **69%** with a single test to **43%** across 100 candidates. Creative writing at 100 tokens stays near 100% throughout. Same watermark, same length, different text.

**How you know it worked.** Two checks, and run the second before you trust the first.

First, the distribution really is unchanged. Generate with and without the key at the same settings and compare token frequencies; they should agree to the third decimal, as they do in the Code tab.

Second, measure detection on *your* output, not on prose. In the simulation a distribution with 5.49 bits of entropy per token detects at **1e-48** over 60 tokens, and one with 0.30 bits comes back at **0.23** — not detected, at any threshold you would be willing to set. If your traffic is closer to the second, the feature is on and doing nothing.

## When a Watermark Is the Wrong Tool

The signal is entropy, and entropy is not something you control. A model emitting JSON, code, SQL or boilerplate has almost no freedom at each step, so there is no room to encode anything. That is the uncomfortable part: the outputs most likely to be misattributed in a compliance argument are structured, and structured output is the case this handles worst.

Speculative decoding costs you too. vLLM keeps the acceptance rate intact by using two keys, one for accepted draft tokens and one for the target residual, and says plainly that combining both at detection time dilutes the signal from each.

And be clear about what a positive result means. It says the text is statistically consistent with your key. It does not identify a user, survive a determined rewrite, or carry weight as evidence on its own. If the question you actually need answered is "who generated this", this does not answer it.

Three questions before turning it on:

What is the entropy of my real output, measured rather than assumed?

Who holds the key, and what happens the day it leaks?

If a passage tests positive, what decision does that let me make?

## Glossary

- **Gumbel-max** — adding Gumbel noise to logits and taking the argmax; provably identical to sampling.
- **Pseudorandom function** — a keyed function returning values that look random but recompute exactly.
- **distribution-preserving** — a watermark that leaves every token's probability unchanged, so quality is untouched.
- **Entropy** — how much real choice the sampler had at a step, measured in bits. The watermark's carrying capacity.
- **Bonferroni** — dividing your threshold by the number of tests, so trying many keys does not manufacture hits.
- **Speculative decoding** — drafting tokens with a small model and verifying against the target, which needs two keys here.
