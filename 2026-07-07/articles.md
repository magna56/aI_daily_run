# Further Reading: How Listwise Pruning Shrinks RAG Context

## Articles

### 1. [How We Prune RAG Context Down to What the Answer Actually Needs](https://www.kapa.ai/blog/how-we-prune-rag-context)
**Source**: Kapa.ai Engineering Blog | **Date**: July 2026 | **Read time**: ~8 min
> Primary source. Explains why pointwise reranker thresholds fail (can't detect inter-chunk dependencies), introduces their 5-level listwise LLM grading scheme, and shares production numbers: 68% chunks pruned at 96% recall, 34% net cost reduction, 0.7s added latency. Deployed by default in their Product Agent SDK.

### 2. [Pruning RAG Context (Hacker News Discussion)](https://news.ycombinator.com/item?id=44485891)
**Source**: Hacker News | **Date**: July 6, 2026 | **Read time**: ~10 min
> Community discussion with 123+ points. Engineers share alternative approaches: token-level pruning, sliding window compression, and debate whether the pruner LLM should be fine-tuned or prompt-engineered. Several commenters report similar savings in their own RAG systems.

### 3. [Retrieval-Augmented Generation for NLP: A Survey](https://arxiv.org/abs/2407.13193)
**Source**: arXiv (Accepted at Artificial Intelligence Review) | **Date**: May 2026 (v4) | **Read time**: ~20 min (skim sections 4-5)
> Comprehensive taxonomy of retrieval fusion methods: query-based, logits-based, latent, and parametric. Sections 4-5 cover post-retrieval processing including context compression, which provides the academic foundation for Kapa's production approach.

### 4. [ContextSniper: Token-Efficient Code Memory for AI Coding Agents](https://arxiv.org/abs/2607.01916)
**Source**: arXiv | **Date**: July 2, 2026 | **Read time**: ~12 min
> Related work from our July 4 session. Uses a 4-stage retrieve→rank→filter→package pipeline for code context, achieving 39% token reduction. The "filter" stage is analogous to Kapa's pruner but uses heuristics rather than LLM grading. Comparison shows the tradeoff: heuristics are faster but LLM grading handles edge cases better.

### 5. [What Happened After 2,000 People Tried to Hack My AI Assistant](https://www.fernandoi.cl/posts/hackmyclaw/)
**Source**: Fernando Islas Blog (via Simon Willison) | **Date**: June 26, 2026 | **Read time**: ~7 min
> Tangential but relevant: real-world testing of production RAG system resilience. 6,000 prompt injection attempts, frontier models resisted all. Relevant because a pruner sitting between retrieval and generation is also an attack surface — adversarial chunks could be crafted to survive pruning or manipulate the pruner's grades.

## Papers

### [Listwise Reranking with Large Language Models](https://arxiv.org/abs/2312.16714)
**Authors**: Xueguang Ma, Xinyu Zhang, Ronak Pradeep, Jimmy Lin | **Published**: Dec 2023 (foundational)
> The academic foundation for listwise LLM evaluation of document sets. Shows that LLMs performing listwise comparison outperform pointwise and pairwise approaches on TREC benchmarks. Kapa's pruner extends this from reranking (reordering) to pruning (removing).
