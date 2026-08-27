# Further Reading: How Tool Order Breaks Your Agent's Cache

## Articles

### 1. [ReCache: Efficient KV Cache Reuse and Compression for Tool-Augmented LLM Agents](https://arxiv.org/abs/2608.19662)
**Source**: arXiv | **Date**: 20 August 2026 | **Read time**: ~25 min
> The primary source, and the one to read first. Fang, Wei, Hu & Shen show why prefix caching cannot reuse tool schemas that arrive in different combinations, then fix it with resource-local positions and cross-resource masking. Read Section 3 for the attention change and the results table for the accuracy you pay — the out-of-distribution drop is the number the abstract's 92.43% does not mention.

### 2. [EIT-NLP/ReCache](https://github.com/EIT-NLP/ReCache)
**Source**: GitHub | **Read time**: ~20 min
> The thing to open in an editor. The released implementation is the only place the recomposition step is fully specified — the paper describes resource-local indexing but never writes out how blocks are stitched back together at generation time, which is exactly the detail you need if you are porting this to another serving stack.

### 3. [Prompt caching — Anthropic API documentation](https://docs.claude.com/en/docs/build-with-claude/prompt-caching)
**Source**: Anthropic | **Read time**: ~10 min
> The reference to keep open while you do the client-side half. It states the constraint this whole session is about — caching matches on an exact prefix — so it tells you precisely why a reordered tool list costs you everything after the first change, and where your breakpoints should go if you cannot touch the serving stack.

### 4. [Towards Efficient Large Language Model Serving: A Survey on System-Aware KV Cache Optimization](https://arxiv.org/pdf/2607.08057)
**Source**: arXiv | **Date**: July 2026 | **Read time**: ~40 min
> Read this only if you are choosing between approaches rather than implementing one. It places resource-level reuse next to eviction, quantization and compression, which is the comparison you need before committing to a change that costs invocation accuracy — several of the alternatives cost none.
