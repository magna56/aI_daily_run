# How the Forward Pass Runs

**Category**: New Models & APIs
**Tags**: transformers, caching
**Date**: 2026-08-23
**Level**: Building
**For**: How models work
**Hook**: Each new word only needs a small query; the cache keeps the keys and values so the model does not rebuild the whole past.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

When your friend guesses the next word, they glance back at everything already said. The first time through a long story, that glance is slow — they have to look at every page. The trick: they keep a stack of sticky notes for pages they already looked at. The next word, they only write a new sticky for the new sentence and flip through the old stickies. Those stickies are the cache. If you change page one of the story, the stickies are wrong and they start over.

## The Problem

"The model attends to the context" is true and useless. Engineers hit the real object when a 100K prompt is fast on token 1 and then cheap per extra token — or when a one-character edit at the start makes the next request expensive again. That is not magic. That is a cache of keys and values from earlier positions. If you do not know it exists, you cannot reason about prompt caching (lesson 7), about why long prefixes cost memory on the GPU, or about why "features" in a paper are not a debugger you can attach.

## For a Software Engineer

A forward pass is one step of next-token prediction (lesson 1). Inside, each layer does attention: every new position writes a *query* and compares it to *keys* from earlier positions, then mixes the corresponding *values*. For a new token, you do not recompute keys and values for the whole past if you still have them. You store them. That store is the **KV cache**.

This is memoizing the left-hand side of a sliding-window join. Prefill (the prompt) is the expensive build of the cache. Decode (each new token) is an O(past) lookup with a tiny new query — cheap in compute, hungry in memory, because the cache grows with sequence length × layers × heads.

The number worth feeling: decode is why chat feels instant after a long paste, and why a 200K window needs a lot of GPU RAM even when you generate one token. Prompt-cache discounts on the API are the product version of "we kept your KV (or a prefix of it) around." A prefix edit throws it away. Same invalidation rule as lesson 7, one layer down.

Monday morning: you do not need to implement attention. You need to stop doing things that bust the cache you already pay for — clocks at the front, shuffled tools — and to read "KV cache hit" in serving docs as "we did not re-prefill."

## What This Means for You

**When this matters**: you care why long prompts have a big first-token latency and a small per-token latency, or why a serving chart talks about KV memory.

**How it affects you**: memory, not math, is the usual ceiling on context. A "million token window" is a statement about cache size and price as much as about intelligence.

**What to do about it**: treat the prompt prefix as a cache key (lesson 7). When you read a paper about "features," translate it to "directions in these hidden vectors" — useful for research, not a stack trace in Cursor.

## What It Is

**Attention** — for each new position, a weighted sum of past values, weights from query·key scores (then softmax, lesson 2). "The model pays attention" means those weights, not a person in the weights.

**KV cache** — the per-layer keys and values for positions already processed. Hit: append one position. Miss: prefill again.

**Features** (in interpretability) — reusable directions in activation space. For an engineer: they are not named variables you can print in prod. They are a research lens on why a token was likely. Do not wait on a circuits paper to ship. Do use the cache story to ship cheaper prefixes.

## Why It Matters

Two budgets: compute (prefill vs decode) and memory (KV grows with length). Product knobs — batch size, prefix cache, "fast mode" — are almost always these two. Lesson 7 is the API-shaped version. This is the machine-shaped version.

## Key Technical Details

**Background first.** *Prefill* processes the prompt and fills the KV cache. *Decode* emits one token at a time using that cache. *A head* is one attention slice; models have many, in parallel.

- **First token waits on prefill.** That is why a huge paste hiccups once.
- **Later tokens wait on decode + cache read.** That is why they are cheaper.
- **Cache is per request (or per prefix) on the server.** Your laptop is not holding it unless you run locally.
- **Changing token 0 invalidates everything after** in that cache, same as a prefix ETag.

## How It Connects to What You Know

A materialized view or a prefix-sum: you keep the work for 1..n and only add n+1. Edit index 2 and you recompute.

Previous: [How Reasoning Models Work](#learn/reasoning-models). Next: [How a Coding-Agent Harness Is Built](#learn/the-coding-agent-harness).

## Try It Yourself

`code_example.py` runs a toy attention step with and without a cached K/V and prints how much work you repeat when the prefix is stable vs when token 0 changes.

## Glossary

- **Forward pass** — one run of the network to score the next token.
- **Attention** — mix past values using query·key weights.
- **Query / key / value** — the three projections each position makes.
- **KV cache** — stored keys and values for past positions.
- **Prefill** — process the prompt; build the cache.
- **Decode** — emit the next token using the cache.
- **Feature** — a research word for a direction in activations; not a product debugger.
