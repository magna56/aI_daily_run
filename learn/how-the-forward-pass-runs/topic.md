# How the Forward Pass Runs

**Category**: New Models & APIs
**Tags**: transformers, caching
**Date**: 2026-08-23
**Level**: Building
**For**: How models work
**Hook**: Each new word only needs a small query; the cache keeps the keys and values so the model does not rebuild the whole past.
**Kind**: Learn
**Time to read**: ~15 minutes

> **You'll be able to:** read `Attention(Q, K, V) = softmax(QK^T / √d_k) V` as a soft dictionary lookup rather than a wall of symbols, explain the division of labour between attention and the MLP, and say precisely what a KV cache does and does not save you.

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

## Attention Is a Soft Dictionary Lookup

The formula that intimidates people is this:

```
Attention(Q, K, V) = softmax(QK^T / √d_k) V
```

Read it the way you already read a hash map, with one change. In a normal map you match one key exactly and take its value. Here, every key gets a match *score* against your query, softmax turns those scores into weights that sum to 1, and you take a weighted blend of *all* the values — not one winner-take-all lookup, a graded one.

- **Q (query)** — what this position is looking for.
- **K (key)** — what each other position offers, to be matched against a query.
- **V (value)** — what actually gets mixed in, once a position is matched.
- **`√d_k`** — divides the raw scores down before softmax, so they do not grow large enough to saturate softmax into a hard one-hot pick. It is the same job as `temperature` in lesson 2, applied one layer down.

**A concrete case that makes it real:** in *"The animal didn't cross the street because it was too tired,"* the token "it" attends strongly to "animal." In *"The street was closed because it flooded,"* the same word "it," same weights, attends strongly to "street" instead — because attention is computed fresh against whatever else is in the window. Nothing about the word "it" changed; the sentence around it did.

## Multi-Head Attention, and What the MLP Is For

A real layer does not run one attention computation — it runs `h` of them in parallel, each with its own Q/K/V projections, then concatenates and mixes the results. Each head tends to specialize: one on syntax, another on coreference (like the "it" example), another on something with no clean English name. Multiple graded lookups running at once, not one.

After attention, every token position passes through a small two-layer network on its own — the **MLP**, or feed-forward block:

```
FFN(x) = ReLU(xW1 + b1)W2 + b2
```

**The division of labour is the thing worth keeping:** attention moves information *between* positions — it is how "it" finds "animal." The MLP does the thinking *at* each position once the right information has arrived — it is closer to where factual association lives. Up-projection asks tens of thousands of implicit questions, activation gates which ones match, down-projection assembles the answer.

A full transformer block is those two pieces plus the plumbing that makes deep stacks trainable at all: `x → LayerNorm → Attention → +residual → LayerNorm → MLP → +residual`, repeated N times — on the order of a hundred layers in a frontier model. The residual connections are what let gradients reach the earliest layers at all in a network this deep; without them, depth alone would make the network untrainable.

## Quick Reference

| Term | Plain English |
|---|---|
| Forward pass | One run of the network to score the next token. |
| Query / key / value | The three projections each position computes for attention. |
| Attention | A weighted, softmax-normalised blend of past values — a soft lookup, not a hard match. |
| Head | One parallel attention computation; a layer runs several. |
| MLP / feed-forward | The per-position network after attention. Where fact association happens. |
| Residual connection | Adding a sub-layer's output back to its input, so gradients can reach early layers. |
| KV cache | Stored keys and values for positions already processed. |
| Prefill | Processing the prompt; building the cache from nothing. |
| Decode | Emitting one new token using the existing cache. |
| Feature | A research term for a reusable direction in activation space, not a product debugger. |

## Do It Today

**Step 1 — see the cache's actual saving, 2 minutes.**

```bash
python3 learn/how-the-forward-pass-runs/code_example.py
```

**You know it worked** when generating 16 tokens after a 16-token prompt does **392 key/value projections without a cache and 32 with one** — a 12× difference — and the same accounting at a realistic 4,096-token prompt plus 512 new tokens shows **2,228,480 vs 4,608**, a **484×** gap. The cache does not make attention cheaper per step; it stops you rebuilding the index for tokens you already processed.

**Step 2 — connect this to lesson 7's cache story.** A prompt-cache hit in an API's billing is the product version of exactly this: "we kept your KV state around instead of re-prefilling." A one-character edit at the start of your prompt invalidates it for the same reason changing token 0 here forces a full rebuild — the ETag analogy holds at both layers.

**Step 3 — next time you read a paper mentioning "features" or "circuits," translate it as "a direction in these hidden vectors."** It is a research lens on why a token was likely, not something you will ever `print()` in production.

## Gotchas

- **The first token always waits on prefill.** That is the one hiccup a huge paste causes — after that, decode is cheap per token by construction.
- **Attention still reads every past row.** The KV cache stops you *rebuilding* the keys and values; it does not shrink how much each new token has to attend over. Decode cost still grows with sequence length, just far more slowly than full re-prefill would.
- **The cache lives on the server, not your laptop**, unless you are running the model locally yourself.
- **"It thinks" is not one mechanism.** Attention moves information; the MLP does the association. A model that fails to connect two facts might be failing at either step, and they are debugged differently.
- **A feature is not a variable.** It is a direction discovered by research tooling after the fact, not something the model's own code exposes.

## How It Connects to What You Know

A materialized view or a prefix-sum: you keep the work for `1..n` and only add `n+1`. Edit index 2 and you recompute. Multi-head attention is the same shape as running several independent indexes over the same data, each tuned to a different query pattern, then merging the results — which is also why one head learning syntax and another learning coreference is not a coincidence, it is what running several specialized lookups in parallel produces.

Previous: [How Reasoning Models Work](#learn/reasoning-models). Next: [How a Coding-Agent Harness Is Built](#learn/the-coding-agent-harness).
