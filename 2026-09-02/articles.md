# Further Reading: How the Same Model Gives Two Different Answers

## Articles

### 1. [IsoExec: Unified Execution to Eliminate Trainer-Inference Mismatch in SkyRL](https://vllm.ai/blog/2026-08-21-isoexec)
**Source**: vLLM blog (Alexander Jiang and the SkyRL team) | **Date**: 21 Aug 2026 | **Read time**: ~20 min
> The session's primary source. Read it for two things the write-up here compresses: the
> **execution contract** — the actual list of rounding-relevant choices they pin, down to the
> kernel name and architecture — and the honesty of the results table, which reports a 25.3%
> overhead and *no meaningful reward improvement* at 50 steps. A post that publishes the
> disappointing half of its own experiment is one you can use the rest of.

### 2. [zanderjiang/SkyRL-IsoExec](https://github.com/zanderjiang/SkyRL-IsoExec)
**Source**: GitHub (Apache-2.0) | **Date**: released with the post | **Read time**: ~30 min hands-on
> The thing to open in an editor, and unusually low-risk to try: the whole stack stays inactive
> unless `SKYRL_ISOEXEC=1` is set, so you can run a matched pair against native execution from
> `examples/isoexec/` without adopting anything. Read the contract adapters even if you never run
> an RL job — they are a worked example of writing down execution conditions, which is the
> transferable idea.

### 3. [Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)
**Source**: Thinking Machines Lab (Horace He) | **Date**: 10 Sep 2025 | **Read time**: ~25 min
> The clearest published explanation of *batch invariance*, and it argues the usual suspect is
> wrong: individual kernels are run-to-run deterministic and mostly free of atomics, so the real
> cause is that "the load (and thus batch-size) nondeterministically varies". It works through why your request's result
> depends on who else was in the batch with it, which is the single most counterintuitive claim in
> today's session. Read this before you try to fix anything, because it determines which knobs
> matter.

### 4. [How Memory Limits Move Coding-Agent Benchmark Scores](#2026-08-23-s2)
**Source**: this site | **Date**: 2026-08-23 | **Read time**: ~10 min
> The companion case. That session is about infrastructure changing a benchmark score through
> resource limits; this one is about infrastructure changing the *output itself* through arithmetic
> order. Read them together if you own an eval — they are the two ways a number moves without
> anybody changing the model.
