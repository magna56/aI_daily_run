# Further Reading: What Actually Makes a Coding Agent Better: Planning, Tools, or Context?

## Articles

### 1. [An Empirical Study of Harness Design for Coding Agents](https://arxiv.org/abs/2609.20804)
**Source**: arXiv 2609.20804 | **Date**: 17 September 2026 | **Read time**: ~30 min
> The primary source. Read the abstract's four numbered findings first, because they are the whole paper in a paragraph and the fourth one is the one that will change what you build. Then go to the trajectory analysis, which is what turns four results into a model you can reason with: context management extends how far a run gets, planning changes where it stops, and the action space changes the granularity at which code is written. Note the design before you borrow the conclusions — the execution loop is held fixed so the components can be compared, which is also the boundary of what the paper can tell you.

### 2. [SWE-bench](https://www.swebench.com/)
**Source**: Princeton NLP | **Read time**: ~15 min
> The benchmark half of the setup, and worth knowing before you trust any coding-agent number. The Verified subset used here is the human-filtered one, which matters because the original set contained tasks that were underspecified or impossible. Open a few task instances in the viewer and you will calibrate quickly on what "solved" actually means, which is the thing most reported agent scores assume you already know.

### 3. [Terminal-Bench](https://www.tbench.ai/)
**Source**: Stanford and Laude Institute | **Read time**: ~10 min
> The other benchmark, and the reason the action-space finding has teeth. These are command-line-centric tasks, which is exactly the setting where a bash-capable model needs no tool layer to help it. If your agent's real work looks like this — build systems, migrations, log spelunking — this is the benchmark whose result transfers to you, and the SWE-bench number is the less relevant one.

### 4. [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
**Source**: Anthropic Engineering | **Read time**: ~20 min
> Read it against the paper rather than alongside it. This is the practitioner argument for curating context deliberately; the paper's finding is narrower and slightly deflationary — most of context management's measured benefit came from preventing overflow failures rather than from better-curated context. Both can be true, and holding them together is the useful state: curate because it helps the model, but expect the measurable win to show up as runs that finish.

### 5. [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
**Source**: Anthropic Engineering | **Read time**: ~25 min
> The counterweight on tools. It argues for careful tool design and clear interfaces, which is good advice and, per this paper, advice whose value depends on which model is behind it. Worth reading for the section on tool documentation as prompt engineering, then worth asking the question the paper raises: is this rescuing a model that cannot drive a shell, and is mine one of them?
