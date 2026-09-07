# Why Your KV Cache Eviction Policy Is Doing Nothing

**Category**: AI in Production
**Tags**: inference-serving, caching, latency, paper
**Date**: 2026-09-07
**Level**: Building
**For**: Shipping AI
**Hook**: Every method for deciding which cached tokens to throw away computes a score. Dropping them at random does just as well, runs 32% faster, and the only thing that ever mattered was one rule none of them wrote down.
**Engineer's view**: You have written an eviction heuristic for a cache in front of a slow service, then found in a load test that it tied with random. The real win was one entry you had to pin. This is that, on a GPU, and the pin is the prompt.
**TLDR**: Serving a reasoning model means throwing tokens out of its cache, and every published method scores them first. Pin the prompt and evict the rest at random, and the score stops earning its keep.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine a small desk. You are working through a long problem, and the desk holds your notes.
The desk fills up, so you have to sweep some notes onto the floor. You could spend time
deciding which note is most valuable. It turns out you do not need to. As you work you keep
copying down the numbers you still need, so most notes exist several times over. Sweeping at
random is fine. There is only one page you must never sweep away, and that is the original
question, because you wrote it down once and never again.

## The Problem

You have shipped this bug, and it had nothing to do with a model. You put a cache in front of a
slow service. It filled up, so you wrote an eviction heuristic. You spent a week on the scoring
function, tuning weights for recency and hit count. Then you load-tested it against a random
policy and the two came out inside the noise. The heuristic was not wrong. It was solving a
problem you did not have, and the thing that actually mattered was one entry you had to pin.

A reasoning model has the same desk. Its KV cache holds one key and one value per token per
attention head, so it grows with every token the model generates. A long chain of reasoning
runs tens of thousands of tokens, and the cache is what stops you fitting more requests on the
box. So you evict.

Every published method picks what to evict by computing a score. SnapKV ranks tokens by how much
attention recent queries paid them. R-KV adds a redundancy term over key similarity. VaSE ranks
by value magnitude. TriAttention scores by distance from the current query. All four cost you
work on every token, forever, and the ranking is the part everybody competes on.

**The fix is to stop ranking and start pinning.** Keep the prompt, drop the rest at random, and
you match the best of them.

## The Fix: Pin the Prompt, Then Stop Choosing

Researchers at Salesforce AI Research tested this. Their policy, Random Attention, gives every
prompt position an infinite score so it is never evicted, then gives every generated position a
uniform random number and keeps the top K per head. It reads no signal at all.

It matches the strongest scorer across four models and six reasoning tasks, and in a vLLM
serving stack it runs 32 to 43% faster.

```figure
{ "kind": "system",
  "title": "The whole argument: same cache, same budget, two ways to choose",
  "lanes": [
    { "t": "over budget", "nodes": [
        { "id": "cache", "t": "a full KV cache" } ] },
    { "t": "you evict by", "nodes": [
        { "id": "score", "t": "a learned score", "s": "bad" },
        { "id": "rand",  "t": "pin, then coin flip", "s": "ok" } ] },
    { "t": "and you get", "nodes": [
        { "id": "same", "t": "the same accuracy", "s": "ok" },
        { "id": "fast", "t": "32-43% more throughput", "s": "ok" } ] }
  ],
  "edges": [
    { "from": "cache", "to": "score", "t": "cost per token", "s": "bad" },
    { "from": "cache", "to": "rand",  "t": "no signal read", "s": "ok" },
    { "from": "score", "to": "same" },
    { "from": "rand",  "to": "fast", "s": "ok" } ],
  "note": "Both paths land on the same accuracy. Only one of them pays for the ranking." }
```

### Why does dropping notes at random not lose the thread?

Because the reasoning trace is written down more than once, in two separate ways.

The first is in the text. A model working through a problem restates what it is still using. It
writes the intermediate value again in the next step, and again in the step after that. Losing
one mention costs nothing while the other mentions survive.

The second is across attention heads, and it is the surprising one. Each head keeps its own copy
of the cache and evicts independently. The researchers planted a fact in a long prompt and then
measured whether the model could retrieve it, varying how many heads still held it.

```figure
{ "kind": "bars",
  "title": "Retrieving a planted fact, by how many heads still hold it",
  "bars": [
    { "label": "1 head", "v": 3, "d": "3%", "s": "bad" },
    { "label": "2 heads", "v": 60, "d": "60%", "s": "neutral" },
    { "label": "3 heads", "v": 83, "d": "83%", "s": "ok" },
    { "label": "8 heads", "v": 99, "d": "99%", "s": "ok" }
  ],
  "note": "Pooling is superadditive: two copies are worth far more than twice one copy." }
```

That is why a coin flip per head is enough. A draw that keeps a token in even three heads
keeps it usable, and eight heads draw independently.

### So what was the score ever doing?

Protecting the prompt, by accident.

The prompt is the fragile part. It is stated once, it is never restated, and the model needs it
until the last token. The researchers forced every baseline to keep the whole prompt and then
re-measured.

| Method | Points gained by pinning the prompt |
| --- | --- |
| SnapKV | +12.6 to +22.5 |
| VaSE | +4.2 to +10.2 |
| R-KV | up to +1.9 — it was already keeping most of the prompt |

That table is the whole finding. The gap between the published methods was mostly whether
their score happened to retain the prompt. R-KV looked best because its redundancy term kept it;
SnapKV looked worst because recent attention drifts away from it. Pin the prompt for everyone and
every learned score still trails the policy that ranks nothing.

```figure
{ "kind": "route",
  "title": "What the policy actually decides",
  "source": "the KV cache, over budget",
  "parts": [
    { "t": "the prompt", "to": 0, "via": "said once", "s": "new" },
    { "t": "the reasoning trace", "to": 1, "via": "restated", "s": "ok" }
  ],
  "dests": [
    { "t": "never evicted", "s": "new" },
    { "t": "uniform draw, per head", "s": "ok" }
  ],
  "note": "Two classes of token, one rule each. The deciding property is whether it is ever said twice." }
```

## What This Means for You

**When this matters.** You are serving a reasoning model, you already compress the KV cache, and
throughput is what you are short of. If you run short prompts, or a model that does not produce
a long chain of reasoning, this finding does not reach you — the redundancy it depends on is not
there.

**How it affects you.** It removes a component rather than adding one. The scoring path in your
serving stack costs work on every token and, on this evidence, buys nothing that pinning the
prompt does not buy more cheaply. That is a rare shape for a research result and it is worth
acting on, because the change is small and reversible.

It also changes how you read the next eviction paper. A method that does not say whether it
protects the prompt has not told you where its numbers come from, and the honest baseline for
any new scorer is now a random draw with the prompt pinned, not the previous scorer.

**What to do about it.**

1. Look up whether your current policy pins the prompt. That is one grep, and it is the whole
   finding if the answer is no.
2. Add the pin if it is missing, change nothing else, and re-measure. Most of the reported gains
   in the table above came from this alone.
3. Then run the random policy against your scorer at a matched budget, on your own traffic. If
   accuracy holds, delete the scoring path.
4. Re-check the budget after the scorer is gone, because you have just freed the compute it was
   using.

## Implementing It

**The change.** Three places, and only the first one is code you write today.

*The eviction hook.* The policy in full. There is no training step, no calibration pass and no
statistics to collect:

```python
import random

def evict(cache_len, prompt_len, budget, recency=64, rng=random.Random(0)):
    """Return the positions to KEEP for one KV head, given a token budget."""
    keep = set(range(prompt_len))                      # the prompt is never a candidate
    keep |= set(range(max(prompt_len, cache_len - recency), cache_len))
    room = budget - len(keep)
    if room <= 0:
        return sorted(keep)
    pool = [i for i in range(prompt_len, cache_len - recency) if i not in keep]
    keep |= set(rng.sample(pool, min(room, len(pool))))
    return sorted(keep)
```

The recency window is kept unconditionally; everything between it and the prompt is the draw.
Call it **once per KV head, with a different draw each time**. That independence is the
mechanism, not an implementation detail — it is what produces the three-heads-out-of-eight effect
above. Sharing one draw across heads throws it away and the policy stops working.

*The evaluation.* Compare at a matched budget, on your own traffic, and do not use the paper's
benchmarks to decide:

```python
for policy in (current_scorer, random_pinned):
    acc = grade(run(prod_sample, policy, budget=K))
    tps = throughput(run(prod_sample, policy, budget=K))
    print(f"{policy.__name__:16} acc={acc:.3f}  tok/s={tps:,.0f}")
```

The budget must be identical across both rows. Most of the reported throughput gain in this
paper comes from capacity, which every eviction method shares — so an unmatched budget will
show you a large improvement that has nothing to do with the policy.

*The capacity plan.* Throughput of 32 to 43% over your current scorer is roughly a quarter to a
third off your box count for the same load, and it arrives without a model change or a quality
regression to argue about. Book it after the A/B, not before.

**How you know it worked.** Accuracy is flat against your current scorer at the same budget, and
the scoring code no longer appears in a profile of the decode path. Those are two separate
checks and you need both: the first says you lost nothing, the second says you actually gained
something. If accuracy moves, look at whether your prompt is genuinely pinned before you blame
the random draw — that is the failure this whole result is about.

The slower signal is the one that decides it. Run both policies over a week of real traffic at
your production budget and compare the accuracy distributions, not the means. A policy that ties
on average and loses badly on the tail is not a tie.

**When not to.** If your traffic is short prompts with short answers, the trace has no room to
restate itself and the redundancy is absent. Measure before you switch.

## When Random Eviction Is the Wrong Tool

The result rests on redundancy, so it fails exactly where redundancy fails.

Short generations are the clearest case. If the model answers in two hundred tokens, nothing has
been restated and every token is close to unique. The same applies to workloads where the
answer is a long structured document rather than a chain of reasoning — a token in the middle of
a generated file is said once, like a prompt token, and dropping it is a real loss.

There is also a class of workload where the prompt is not the only thing said once. Retrieval
that injects long passages mid-generation, or a tool that returns a large block the model must
quote exactly, both put unrepeated content outside the prefill. The pin covers positions up to
the end of the prompt. It does not know about anything you insert later, and if you have such a
workload you need a pin that does.

Finally, this is four models on six reasoning benchmarks. It is a strong result and not a law,
and the claim is about these models and these traces.

Three questions before you adopt it:

- Does my current policy already pin the prompt? If yes, the ceiling here is throughput, not
  accuracy.
- Is anything in my requests said exactly once and needed late, other than the prompt?
- Am I comparing at a matched budget, or am I about to credit the policy for extra capacity?

## Glossary

- **KV cache** — the keys and values a transformer stores for every token it has already
  processed, per attention head, so it does not recompute them. It grows as the model generates,
  and it is what limits how many requests fit on a box.
- **Eviction** — dropping entries from that cache once it exceeds a budget, so generation can
  continue in fixed memory.
- **Budget** — how many token positions a head may keep, written K in the code. Two policies are only comparable at
  the same budget.
- **Prefill** — the pass over the prompt before the first generated token. "Pinning the prompt"
  means those positions are never eviction candidates.
- **Attention head** — one of the parallel attention computations in a layer. Each keeps its own
  KV cache and evicts independently of the others, which is where the redundancy comes from.
- **Recency window** — the newest positions, kept unconditionally because the model is actively
  using them.
