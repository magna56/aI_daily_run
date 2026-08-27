# How Tool Order Breaks Your Agent's Cache

**Category**: AI in Production
**Tags**: caching, agents, inference-serving, paper
**Date**: 2026-08-27
**Level**: Deeper
**For**: Building agents
**Hook**: Your agent re-sends the same tool descriptions every request, and the cache throws them away — not because the text changed, but because they moved.
**Time to read**: ~8 minutes

## Explain Like I'm 5

Imagine you hand out the same stack of reference sheets with every request. Each sheet gets stamped with its page number — "page 3 of 12". Shuffle the stack and every stamp is wrong, so you reprint all of them, even though not a single word changed. That is what happens to an AI agent's tool descriptions. The computer did save itself the work of re-reading them. It just saved that work *together with where they sat*.

## The Problem

An agent with eight tools sends four of them on a typical request, picked by whatever retrieved them that turn. The text of each tool's schema never changes. The order does.

Prefix caching reuses saved work only while the prompt matches from the very first token. The moment one tool differs, reuse stops there — and every tool after it has shifted position, so all of it is recomputed. In a 200-request simulation with eight tools and four per request, prefix caching reused **3.0%** of the tool tokens.

You are paying to encode the same schemas again and again, because they moved.

## How Resource-Local Positions Make a Tool Cacheable

A new paper (arXiv:2608.19662, Fang, Wei, Hu & Shen, 20 August 2026) names this and fixes it, with code released.

### Position Is Baked Into the Cache

What gets cached is not the text. It is the key–value state the model computed for each token, and that state depends on **where the token sat**. The schema for `read_file` starting at offset 40 produces different tensors from the identical schema starting at offset 300. Same bytes, different cache entry. This is why reuse "rarely holds for dynamically composed resource contexts," in the paper's words — the composition is what changed, not the content.

### Resource-Local Indexing

The fix is to stop numbering tools by where they land. Each tool block gets positions starting at zero — `pos(t_i,j) = j` inside its own block — and attention links *between* different tools are removed, so a tool's tokens see the shared system prompt and their own tokens, nothing else.

Now the block is composition-invariant: identical bytes give an identical KV block, whatever order the tools arrive in. As a bonus, attention cost drops from O(D²) over the whole resource region to the sum of each block's own O(D²).

### What Actually Gets Stored

The paper then prunes hard, keeping only what a model needs to *invoke* a tool: the resource name, the argument names, the argument descriptions, and a final suffix token. Prose about when to use the tool is dropped.

### The Measured Result

On Qwen3-4B, that combination cuts KV-tensor memory by **92.43%** and time-to-first-token by **3.655×**. Accuracy pays for it: tool-invocation F1 falls from 82.4% to 80.3% in-distribution, and from 66.3% to 60.8% out-of-distribution.

## For a Software Engineer

This is cache-key design, and the bug is one you have shipped before: a key that includes something incidental. Caching a rendered component under `(component, scroll_offset)` gets you a near-zero hit rate and a store full of duplicates — not because rendering is expensive, but because the key encodes where the thing appeared rather than what it is.

**The number worth feeling:** in the simulation, caching each tool at each offset it appeared at needed 298 blocks for 8 tools and still only hit 62.8%. Dropping the offset from the key collapses that to **8 blocks and 99.0%** — one per tool, which is what your intuition said the answer should be all along.

## What This Means for You

**When this matters:** you run a tool-using agent, your tool list is assembled per request — retrieved, filtered, or merged from several MCP servers — and your prompt-cache hit rate is worse than you expected.

**How it affects you:** you are being billed to re-encode schema text that is byte-identical to last request's. The bigger your tool catalogue, the worse it gets, because more tools means more orderings and every ordering is a fresh layout.

**What to do about it:**
1. Log your actual cache-hit rate on the tool region specifically, not the whole prompt. Most people have never separated the two.
2. **Sort your tool list deterministically before you send it.** This needs no serving change and is the one fix available to you today — see below.
3. Only then consider the serving-side change, and only if you own the stack.

## Implementing It

**The change.** Two roles, and only one of them requires owning the model server.

*Agent author — make the prefix stop moving.* Almost all of the loss comes from the tool list being ordered by relevance score or by whatever order servers replied in. Sort it:

```python
# Before: order follows retrieval score, so it changes every request.
tools = [t for t, _score in retriever.top_k(query, k=4)]

# After: stable order -> the prefix is identical whenever the SET is.
tools = sorted(retriever.top_k(query, k=4), key=lambda ts: ts[0]["name"])
tools = [t for t, _score in tools]
```

Relevance order rarely matters to the model, and it destroys the prefix on every request. If your set is stable and only the order was churning, this alone recovers most of the cache.

*Serving engineer — drop the offset from the cache key.* This is the paper's actual contribution, and it is a key change before it is an attention change:

```python
def key(self, tool: str, offset: int):
    # Including `offset` is what forces one entry per (tool, position it landed in)
    return tool if self.resource_local else (tool, offset)
```

Making that key legal requires the other half: build each tool's block with positions restarting at zero, and mask attention between tools. `ResourceKVCache` in `code_example.py` is the full version, with the request simulation that produces the numbers above.

**How you know it worked.** Instrument the tool region's hit rate on its own and watch two numbers. Blocks stored should fall to roughly **one per tool** — if it is still climbing with traffic, the offset is still in your key. Hit rate should stop depending on request order: shuffle your tool list deliberately in staging and the rate should not move. `code_example.py` prints exactly this pair, going from 3.0% reuse under prefix caching to 99.0% with 8 blocks for 8 tools. Its 97.3% storage saving is a toy reproducing the paper's shape, not its measured 92.43% on a real model.

## When Resource-Local Caching Is the Wrong Tool

The accuracy cost is real and it is worst exactly where you can least afford it. Cutting attention between tools means the model can no longer compare one schema against another while reading them, and out-of-distribution invocation F1 fell 5.5 points — from 66.3% to 60.8%. If your agent picks between near-duplicate tools, or handles requests unlike its training distribution, that is a bad trade for memory you may not be short of.

The client-side half has no such cost, which is why it is ordered first above. Sorting your tool list is free, reversible, and needs nobody's permission.

Three questions before adopting the serving change: **Are you actually memory- or TTFT-bound**, measured, or just attracted to a 92% number? **Have you tried stable ordering first**, and what did it recover on its own? And **can you evaluate invocation accuracy on your own traffic** — because a 2-point in-distribution drop is invisible without an eval, and a 5.5-point out-of-distribution one will find you in production.
