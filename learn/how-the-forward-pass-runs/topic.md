# Attention and the KV Cache, in Engineer Terms

**Category**: New Models & APIs
**Tags**: transformers, caching
**Date**: 2026-08-23
**Level**: Building
**For**: How models work
**Hook**: Each new word only needs a small query; the cache keeps the keys and values so the model does not rebuild the whole past.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine you are writing a story one word at a time, and before you pick the next word you look back at every word you already wrote. The slow way is to re-read the whole story from the first letter every time. The smart way is to keep a card for each old word — what it was about, and what it contributed — and only write a new card for the word you just added. The stack of cards grows. That stack is why a long chat needs more memory even when you type a short new sentence.

## The Problem

A transformer does not have a hidden state it can update in O(1) like an old recurrent net. To pick token *t*, every layer needs a look-back over tokens 1…*t−1*. Naive serving would rebuild that look-back from scratch on every new token — reread the prompt, reread the answer so far, re-project every past token into the form attention needs. That is accidentally quadratic in the worst way: the tenth token is cheap, the ten-thousandth is a tax on everything that came before. The KV cache is the memoization that makes chat and agents possible. Without it, "context window" would be a research demo, not a product.

## For a Software Engineer

This is **incremental computation with a growing memo table** — closer to a prefix-sum you extend than to a magic neural trick. Attention is a batched lookup: for the token you are writing now, you ask a question (query), you compare it to a label on every past token (key), and you mix the payloads (values) using those similarity scores.

- **Query (Q)** — the lookup key for *this* step. "What am I trying to bind to?"
- **Key (K)** — the index entry each past token published. "What would match me?"
- **Value (V)** — the payload you actually mix in if there is a match. "What do I contribute?"

A **feature**, in this voice, is not a circuit-paper character. It is an intermediate vector a layer computed — like a field on an object after a map-reduce. Later layers read those fields. That is all "the model represents X" has to mean on a Monday.

The KV cache stores each past token's K and V (per layer, per head) so the next step only projects the *new* token and attends over the table. The number worth feeling: on a 70B-class model with grouped-query attention, the cache is often **on the order of 300 KB per token** in 16-bit. An 8,000-token prompt is then ~2.4 GB of cache *before* you generate anything. That is why long context is a memory product, why batch size collapses as sessions grow, and why vLLM's paged cache exists. Monday-morning action: when someone says "just use the 128k window," ask what the cache weighs and whether decode is memory-bound on your GPU.

## What This Means for You

**When this matters**: you are debugging "why is the second token slow / why did the batch die at 8k / why did prompt cache miss" — or you are reading a blog that says "attention" and "features" as if those were vibes.

**How it affects you**: prefill (reading the prompt) is a big parallel matmul. Decode (writing the answer) is a loop that *reads the growing cache*. Extra input tokens make every later output token more expensive in memory bandwidth. A reasoning model that writes 8,000 thought tokens (previous page) grows the same cache 8,000 times.

**What to do about it**: treat prompt length as a memory allocation, not a quality slider. Prefer prefix-stable prompts so provider prompt-cache and engine KV pages can hit. If you serve locally, look at KV pages / prefix cache in vLLM (or the equivalent), not only at "tokens per second" on a 128-token toy prompt.

## What It Is

The **forward pass** is one step of the decoder: embed the new token (or the whole prompt, on the first step), run it through N layers of self-attention + feed-forward, produce logits, sample. Self-attention inside a layer is:

`scores = softmax(Q Kᵀ / √d) ; out = scores · V`

Q, K, and V are linear projections of the current residual stream — the same hidden vector, three different maps, like three indexes over one row.

Because generation is left-to-right, K and V for tokens 1…*t−1* do not change when you write token *t*. So you append one new row to the cache instead of recomputing the table. That memo is the **KV cache**. It is the reason "streaming a reply" is a memory-bandwidth problem more than a FLOP problem.

## Why It Matters

Every product number you already care about — tokens per second, max batch, max context, the cost of a reasoning pad, the cost of an agent transcript — is a statement about this table. Prompt caching at the API layer is a *prefix* of this idea sold as a price. PagedAttention in vLLM is this table broken into OS-style pages so you do not preallocate a giant contiguous slab per request and waste half the GPU. If you only remember one sentence: **the model does not reread your words as text; it rereads a growing binary index of keys and values.**

## Key Technical Details

**Background first.** A transformer layer keeps a residual stream — a vector per token, width `d`. Attention looks across tokens; the feed-forward looks at one token. Multi-head attention splits the width into several smaller lookups so one token can bind to several past facts at once. Grouped-query attention (GQA) lets many query heads share one key/value head, which shrinks the cache. **Prefill** runs attention over the whole prompt in parallel and *writes* the cache. **Decode** reads that cache, appends one row, repeats.

- **Q, K, V are three projections of the same vector.** There is no separate "meaning store." The key is "how I want to be found"; the value is "what I hand over if found." If that sounds like a hash map, good — the scores are just a soft, many-way join.
- **Features are layer outputs, not lore.** When someone says a layer "detects a variable name," they mean some coordinates of that vector are useful to later layers for that job. You do not need a circuits paper to use the idea: it is cached state, like attributes after a compiler pass.
- **Without a KV cache, each new token re-projects the entire prefix.** For a prompt of length `n` and `T` new tokens, projection work grows like `Σ (n+t)` instead of `n + T`. The code example's 16-token prompt + 16-token answer does **392** token-projections without a cache and **32** with one. Scale that to a 4,096-token prompt and 512 new tokens and the same accounting is **2,228,480** vs **4,608** — a 484× cut on that slice of the work. Attention itself still touches every past row; the cache does not make attention O(1).
- **Decode is usually memory-bound.** Each step loads QKV weights plus the whole cache for that layer. As the cache grows, tokens/s fall even if FLOPs look fine. That is why a long agent session feels slower at the end, and why a thought-heavy reasoning call is a cache-growth event, not just a token-bill event.
- **Cache bytes are why 128k is not free.** Rough size: `2 (K and V) × layers × kv_heads × head_dim × seq_len × bytes_per_param`. GQA, 8-bit KV, and sliding windows exist to shrink this. vLLM's PagedAttention (SOSP 2023) stores the cache in fixed-size pages with a block table — virtual memory for GPU tensors — so variable-length sequences do not fragment a giant preallocated arena.
- **API prompt cache ≠ engine KV cache, but they rhyme.** If the *byte prefix* of tools + system + early messages is unchanged, a provider can reuse a billed prefix (often 0.1× input). The engine can likewise keep KV pages for that prefix. Edit the start of the prompt and both miss. That is the same invalidation story as the context-budget Learn page, one layer down.

## How It Connects to What You Know

You already know memoization, indexes, and "don't reparse the file on every keystroke." Q/K/V is an index join; the KV cache is the memo. From earlier Learn pages: **tokens and sampling** are what this loop emits. **Context and the harness** is why the table is huge — tools and history are prefix rows. **Reasoning models** (previous page) write thousands of extra rows before the answer. **The agent loop** appends tool results, which become more rows you will reread on every later token. The capstone — **the coding-agent harness** — is this machine plus permissions and sub-agents, which exist *because* the cache and the bill grow with every row you keep.

## Try It Yourself

`code_example.py` runs a tiny one-head attention step on a 4-token prompt so you can see Q, K, V and the softmax weights as numbers, then counts projection work for a 16+16 generate with and without a KV cache. No numpy, no GPU — just the accounting that makes serving real.

## Glossary

- **Forward pass** — one decoder step: from current token (or prompt) through the layers to logits. Training also has a backward pass; serving is forward-only.
- **Transformer** — the stack of attention + feed-forward layers almost every modern chat model uses. No recurrent hidden state; look-back is attention.
- **Residual stream** — the per-token vector that each layer reads and writes. Q, K, and V are projections of it.
- **Query / key / value** — the three projected views used by attention: lookup, index, payload.
- **Attention** — softmax of query–key scores, used as weights to mix values. Soft, many-way lookup — not a hard pointer.
- **Head** — one parallel attention lookup. Multi-head means several lookups whose outputs are concatenated.
- **GQA** (grouped-query attention) — several query heads share one key/value head so the cache is smaller.
- **Feature** — an intermediate vector (or a slice of one) a layer computed. Useful state for later layers, not a mystical circuit name.
- **KV cache** — stored keys and values for past tokens, per layer (and head), so decode does not recompute them.
- **Prefill** — the first, parallel pass over the prompt that fills the KV cache.
- **Decode** — the token-by-token loop that reads the cache and appends one new row.
- **PagedAttention** — vLLM's page-table scheme for storing KV in non-contiguous GPU blocks, like virtual memory.
- **Logits** — the raw scores over the vocabulary before sampling the next token.
- **FLOP** (floating-point operation) — a raw arithmetic count. Decode can look cheap in FLOPs and still be slow because it is waiting on memory bandwidth to load the KV cache.
