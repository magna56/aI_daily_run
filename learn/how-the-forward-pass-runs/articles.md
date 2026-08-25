# Further Reading: How the Forward Pass Runs

## Primary Sources

### 1. [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
**Source**: arXiv (Vaswani et al., NeurIPS 2017) | **Date**: June 2017 | **Read time**: ~20 min
> The paper that defined scaled dot-product attention — `softmax(QKᵀ / √d) V` — and the multi-head transformer. Read the attention subsection; you do not need the machine-translation experiments to use Q, K, and V as an engineer.

### 2. [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)
**Source**: Jay Alammar | **Date**: 2018 | **Read time**: ~20 min
> Still the clearest picture of one forward pass: embeddings, Q/K/V projections, heads, and the residual stream, without circuits-paper vocabulary. Pair with this session's "feature = intermediate vector" stance.

### 3. [vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention](https://vllm.ai/blog/2023-06-20-vllm)
**Source**: vLLM Blog | **Date**: June 20, 2023 | **Read time**: ~8 min
> Why the KV cache is the serving bottleneck and how paging it like virtual memory (blocks + a block table, copy-on-write for shared prefixes) stops you from preallocating a giant contiguous slab per request. This is the KV cache as a systems problem.

## Background & Ecosystem

### 4. [PagedAttention design notes](https://docs.vllm.ai/en/latest/design/paged_attention/)
**Source**: vLLM docs | **Date**: current | **Read time**: ~12 min
> The kernel-level layout: KV stored in fixed-size blocks, key cache vs value cache shapes, and how a decode step gathers non-contiguous pages. Read this after the blog post if you serve models yourself.

### 5. [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180)
**Authors**: Kwon et al. | **Published**: SOSP 2023
> The paper behind vLLM. Use it for the fragmentation numbers and the OS analogy (tokens as bytes, blocks as pages, sequences as processes) when you need to explain cache waste to someone who already knows `mmap`.

## The one-line takeaway
Attention is a soft join over an index you build as you go; the KV cache is the memo that stops you rebuilding that index on every next token.
