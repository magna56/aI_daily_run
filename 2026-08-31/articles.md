# Further Reading: How an Agent Decides What to Remember

## Articles

### 1. [MEMTIER: Tiered Memory Architecture and the Retrieval Bottleneck in Long-Running LLM Agents](https://arxiv.org/abs/2605.03675)
**Source**: arXiv (Ben-Gurion University of the Negev) | **Date**: 25 May 2026 | **Read time**: ~25 min
> The session's primary source, and worth reading for Table 2 alone — the ablation where three of
> the authors' own five retrieval signals turn out to score negative and the reinforcement-learning
> weight tuner moves the result by exactly 0.000. Read it if you are about to build agent memory:
> it will save you from the signal-weighting sprint most teams do first. Skim sections 3.1–3.2 for
> the schema and the scoring function, then go straight to the ablation and the oracle analysis.

### 2. [LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory](https://arxiv.org/abs/2410.10813)
**Source**: arXiv (Wu, Wang, Yu, Zhang, Chang, Yu; ICLR 2025) | **Date**: Oct 2024 | **Read time**: ~20 min
> The clearest statement anywhere of *why* agent memory is three separate problems — indexing,
> retrieval, and reading — and the reason this session can talk about consolidation and scoring as
> distinct decisions. Its five ability types (extraction, multi-session reasoning, temporal
> reasoning, knowledge update, abstention) are a better bug taxonomy for your own system than
> anything you would invent. The reference to keep open while you design.

### 3. [xiaowu0162/LongMemEval](https://github.com/xiaowu0162/LongMemEval)
**Source**: GitHub (benchmark authors) | **Date**: maintained | **Read time**: ~30 min hands-on
> The thing to open in an editor. The 500 questions and their 53-session haystacks are released
> here, so you can point the harness at your own memory system and get a Recall@k number instead of
> an impression. Read first if you already have memory in production and have never measured it —
> the article's "how you know it worked" step is much easier with this than without.

### 4. [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560)
**Source**: arXiv (Packer, Wooders, Lin, Fang, Patil, Stoica, Gonzalez; UC Berkeley) | **Date**: Oct 2023 | **Read time**: ~20 min
> The paper that made tiered agent memory a standard idea, framing context as virtual memory with
> paging between fast and slow tiers. Useful here as the contrast: MemGPT moves content on an
> interrupt the agent raises mid-turn, where today's session consolidates asynchronously in the
> background. Read it to see which of the two fits your latency budget, not for a result to copy.
