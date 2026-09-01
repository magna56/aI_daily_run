# Further Reading: How Keeping Four Tokens Beats Retraining a Model

## Articles

### 1. [Sliding-window beats linear attention](https://arxiv.org/abs/2608.28444)
**Source**: arXiv (Jolicoeur-Martineau, Sukthanker, Cameron & Gervais; Microsoft Applied Sciences Group) | **Date**: 28 Aug 2026 | **Read time**: ~25 min
> The session's primary source. Table 1 is the argument: a column for post-training tokens spent,
> next to a column for performance recovered, with the zero-token row at the top of both. Read
> section 3 for why the comparison had never been made — the linearizing papers all benchmarked
> against sink-free windows — and section 4.2 for the long-context numbers, which are the ones that
> should decide anything. Read first if you are being sold a linearized model.

### 2. [Efficient Streaming Language Models with Attention Sinks](https://arxiv.org/abs/2309.17453)
**Source**: arXiv (Xiao, Tian, Chen, Han & Lewis), ICLR 2024 | **Date**: Sep 2023 | **Read time**: ~20 min
> Where attention sinks were named and explained, and the paper today's result leans on. It is the
> clearest account of *why* the first few tokens matter — softmax has to put its weight somewhere,
> and a trained model learns to park the surplus on whatever was at the start. Their StreamingLLM
> handles up to 4 million tokens without retraining, at up to 22.2x the speed of the baseline. The
> reference to keep open while you implement, because the mechanism explains which knobs are safe
> to turn.

### 3. [LoLCATs: On Low-Rank Linearizing of Large Language Models](https://arxiv.org/abs/2410.10254)
**Source**: arXiv (Zhang, Arora, Chalamala, Wu, Spector, Singhal, Ramesh & Ré; Stanford), ICLR 2025 | **Date**: Oct 2024 | **Read time**: ~25 min
> The strongest of the linearizing methods, and the fair way to read today's result. LoLCATs
> recovers most of full attention's knowledge performance from only 40M tokens — 0.4% of what
> earlier linearizing methods needed, on models up to 405B where prior work stopped at 7B — which is
> a genuine achievement — and it is competitive with, or slightly ahead of, sliding windows at short context.
> Read it so the conclusion stays narrow: the finding is that the baseline was mis-run, not that
> this line of work was worthless.

### 4. [How Vision Models Turn Pixels Into Tokens](#2026-08-21)
**Source**: this site | **Date**: 2026-08-21 | **Read time**: ~10 min
> The on-ramp if the KV cache and why context costs what it does are not already familiar. That
> session works through what a token actually is and what each one costs to keep, which is the
> assumption everything here rests on.
