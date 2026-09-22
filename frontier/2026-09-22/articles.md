# Further Reading: How to Stop Agent Auto-Tuning From Memorizing Your Benchmark

## Articles

### 1. [google-research/rrsi](https://github.com/google-research/rrsi)
**Source**: Google Research | **Date**: September 2026 | **Read time**: ~15 min
> The one to open in an editor, and the reason this session exists rather than being a paper summary. The search itself lives in `rrsi/` with separate modules for proposal, selection, scheduling and history, and three domain adapters ship with it. Start at `domains/<name>/adapter.py` — implementing that class for your own tasks is the entire integration, and reading one is the fastest way to see what the method assumes about your eval setup.

### 2. [RRSI: Regularized Recursive Self-Improvement of Agent Harnesses](https://arxiv.org/abs/2609.24972)
**Source**: arXiv, Google Research | **Date**: September 2026 | **Read time**: ~40 min
> The primary source. Read the results table before the method: it is the argument, and it shows RRSI taking the smallest gain on the split it evolved against while winning the out-of-distribution average. Worth the time if you are deciding whether to run any self-improvement loop at all, because the baseline column quietly shows how far these harnesses are from transferring in the first place.

## Papers

### [Dream-RSI: Recursive Self-Improvement through Evolving Worlds](https://arxiv.org/html/2609.14858v1)
**Published**: September 2026
> The contrast case, and useful precisely because it takes the opposite approach: instead of constraining the search, it varies the environment the agent is evolved against. Read it after RRSI to see the same overfitting problem attacked from the data side rather than the optimizer side — the two are complementary and the comparison sharpens both.

### [Gödel Agent: A Self-Referential Agent Framework for Recursive Self-Improvement](https://arxiv.org/pdf/2410.04444)
**Published**: 2024
> Background, for how this line of work started. Read it only if you want the earlier framing where recursive self-improvement was treated as a capability question rather than a generalization one. It is the paper RRSI's regularizers are implicitly arguing with.
