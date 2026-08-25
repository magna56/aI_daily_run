# Further Reading: How Memory Limits Move Coding-Agent Benchmark Scores

## Articles

### 1. [Quantifying infrastructure noise in agentic coding evals](https://www.anthropic.com/engineering/infrastructure-noise)
**Source**: Anthropic Engineering | **Date**: Feb 5, 2026 | **Read time**: ~12 min
> The primary source. Runs Terminal-Bench 2.0 across six GKE resource configurations and a
> SWE-bench cross-check, isolating how much of a coding-agent benchmark score is decided by
> container memory headroom rather than the model itself — 6 points of swing, more than the
> typical gap between top leaderboard entries.

### 2. [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
**Source**: Anthropic Engineering | **Date**: Jan 9, 2026 | **Read time**: ~15 min
> The companion piece on building the eval harness itself: starting from 20-50 real-failure
> tasks, writing unambiguous graders, watching for eval saturation, and the pass@k vs pass^k
> distinction for scoring non-deterministic agents. Read this for the harness-design half of the
> picture this session's article assumes.

### 3. [That Benchmark Lead Might Just Be a Bigger VM](https://medium.com/@AdithyaGiridharan/that-benchmark-lead-might-just-be-a-bigger-vm-anthropics-eye-opening-study-on-infrastructure-f487596de714)
**Source**: Medium | **Date**: Feb 2026 | **Read time**: ~6 min
> A practitioner's plain-language walkthrough of the same study, useful as a second pass over the
> `bn-fit-modify` example and the 3x-headroom inflection point if the primary source's framing
> doesn't land the first time.

### 4. [Anthropic finds infrastructure config can swing agentic coding benchmarks by 6+ percentage points](https://agent-wars.com/news/2026-03-15-anthropic-finds-infrastructure-config-can-swing-agentic-coding-benchmarks-by-6)
**Source**: Agent Wars | **Date**: Mar 15, 2026 | **Read time**: ~4 min
> Short industry write-up connecting the finding to the broader leaderboard-comparison problem
> across providers — useful for the "why don't public leaderboards already control for this"
> framing.

### 5. [Anthropic: Infrastructure Noise in Agentic Coding Evaluations](https://www.zenml.io/llmops-database/infrastructure-noise-in-agentic-coding-evaluations)
**Source**: ZenML LLMOps Database | **Date**: 2026 | **Read time**: ~5 min
> Files the study as an LLMOps case study rather than a research result — a useful frame for
> teams asking "what would I actually change in my own eval CI" rather than "is this interesting."
