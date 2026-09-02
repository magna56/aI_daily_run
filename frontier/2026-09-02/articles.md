# Further Reading: How Running Each Layer Twice Pays for Itself

## Articles

### 1. [Loop the Loopies!](https://arxiv.org/abs/2607.16051)
**Source**: arXiv (Gao, Chen, Xiao, Yang, Tao, Zhou & Dai; IQuest Research) | **Date**: 17 Jul 2026, v2 20 Jul | **Read time**: ~40 min
> The session's primary source, and unusually worth reading in full because the interesting
> sections are the unglamorous ones. Section 2.2 explains why layer-loop beats model-loop on three
> separate grounds — scaling, execution locality, and what a shared layer is being asked to do at
> two very different depths. Section 2.4 is the recipe, and it is candid that the models are
> matched on measured step time rather than theoretical FLOPs. Section 2.7's ablation is the
> cleanest evidence in the paper: same looped compute budget, ordering removed, 2.14x slower to
> the same score.

### 2. [NVIDIA/Megatron-LM](https://github.com/NVIDIA/Megatron-LM)
**Source**: GitHub (NVIDIA) | **Date**: maintained | **Read time**: ~30 min hands-on
> The thing to open in an editor, and not the obvious choice. Loopie's whole memory argument rests
> on activation checkpointing enclosing all recurrent applications of a stored layer in one unit —
> so the code worth reading is the checkpointing implementation this was measured in, not the
> architecture. Find where a transformer block is wrapped for recomputation and you can see for
> yourself whether the property holds, which is the check anyone reimplementing the schedule would
> otherwise skip.
>
> **Note on the paper's own artifacts.** It links Loopie-20B-A2B and Loopie-6B-A0.6B on Hugging
> Face and a `loopie` repo with `megatron` and `vllm` subtrees. At the time of writing the repo
> returns 404 and both model pages return 401. Treat the weights and forks as announced rather
> than available, and the mechanism — which is fully specified in the paper — as the part you can
> act on today.

### 3. [Scaling Latent Reasoning via Looped Language Models](https://arxiv.org/abs/2510.25741)
**Source**: arXiv (Zhu et al., 41 authors including Yoshua Bengio) — the Ouro family | **Date**: Oct 2025, revised Jul 2026 | **Read time**: ~25 min
> The model-loop line of work Loopie defines itself against, and the fair way to read today's
> result. Ouro established that recurrent depth buys real parameter efficiency; the claim being
> corrected is narrower — that parameter efficiency alone was never enough to win a
> compute-matched comparison. Read it to keep the conclusion honest: the ordering is the new part,
> not the idea of looping.

### 4. [How Vision Models Turn Pixels Into Tokens](#2026-08-21)
**Source**: this site | **Date**: 2026-08-21 | **Read time**: ~10 min
> The on-ramp if activation memory, microbatches and gradient accumulation are not already
> familiar vocabulary. Today's argument is entirely about where memory goes during a training
> step, and that session builds the underlying picture of what the model is holding and why.
