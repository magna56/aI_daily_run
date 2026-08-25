# Further Reading: How Coding Agents Retrieve Code Without Loading the Whole Repo

## Papers

### [ContextSniper: Token-Efficient Code Memory for Repository-Level Program Repair](https://arxiv.org/abs/2607.01916)
**Authors**: Luk, Najafi, Jia, Yang, Li, Zhu, Ren, Chen, Cong | **Published**: July 2, 2026
> The primary paper. Introduces a retrieve → rank → filter → package pipeline that
> reduces Claude Code's token usage by 38.9% and OpenClaw's by 51.5% on SWE-bench Lite,
> with only a 2-point drop in bug resolution rate. Read this first.

### [SWE-bench: Can Language Models Resolve Real-World GitHub Issues?](https://arxiv.org/abs/2310.06770)
**Authors**: Jimenez et al. (Princeton) | **Published**: 2023-10
> The benchmark that ContextSniper is evaluated on. Understanding SWE-bench helps you
> appreciate what "32% resolution rate" means — these are real GitHub issues from popular
> Python repos, requiring multi-file edits and test validation. The standard bar for
> coding agent evaluation.

## Related Work (from today's arxiv)

### [Coding-Agents Can Replicate Scientific ML Papers](https://arxiv.org/list/cs.AI/recent)
**Authors**: Hans, Bilionis | **Published**: July 3, 2026
> Demonstrates that coding agents can autonomously reproduce scientific machine learning
> papers. Relevant because it shows the ceiling of what coding agents can do when they
> have enough context — ContextSniper's efficiency would help these agents tackle
> larger codebases.

### [Steerability via Constraints: A Substrate for Scalable Oversight of Coding Agents](https://arxiv.org/list/cs.AI/recent)
**Authors**: Winninger | **Published**: July 3, 2026
> Proposes constraint-based steering for coding agents. Complementary to ContextSniper —
> while ContextSniper optimizes what the agent sees, this paper optimizes what the agent
> is allowed to do. Both are about making coding agents more reliable.

## Blog Posts & Practical Resources

### 1. [llm-coding-agent: A Claude Code-style agent in Python](https://simonwillison.net/2026/Jul/2/llm-coding-agent/)
**Source**: Simon Willison | **Date**: July 2, 2026 | **Read time**: ~10 min
> Simon built a minimal coding agent with just 6 tools (read, edit, write, list, search,
> execute). Shows the minimal viable architecture for a coding agent — useful context for
> understanding where ContextSniper would plug in.

### 2. [Using Judgment with Claude Code](https://simonwillison.net/2026/Jul/3/using-judgment/)
**Source**: Simon Willison | **Date**: July 3, 2026 | **Read time**: ~5 min
> Tip from the Claude Code team about letting the model use its own judgment for tasks like
> testing. Relevant because ContextSniper's intention-aware filtering is essentially
> helping the agent exercise better judgment about what code to read.

### 3. [Better Models: Worse Tools](https://news.ycombinator.com/)
**Source**: pocoo.org (via Hacker News) | **Date**: July 4, 2026 | **Read time**: ~15 min
> Analysis of how more capable AI models don't automatically produce better tools.
> ContextSniper is a counter-example: it's a tool-level optimization that improves results
> regardless of the underlying model's capability.
