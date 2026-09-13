# Further Reading: How to Choose What to Cut When You Shrink a Model

## Articles

### 1. [X-AuT: Progressive Audio-Encoder Compression for Speech LLMs with Cross-Scale Distillation](https://arxiv.org/abs/2609.11412)
**Source**: XPENG Inc. (arXiv:2609.11412) | **Date**: 10 September 2026 | **Read time**: ~30 min
> The paper this session is built on. Go to the layer-selection ablation first and read the two
> pairs against each other: {6,8} holds the two strongest single removals and lands at 7.78%,
> while {5,6} scores slightly worse individually and reaches 6.93%. Everything else in the paper
> is machinery around that observation. The progressive result is the second thing worth having —
> 5.75% against 6.73% for the identical final architecture, winning on all ten benchmarks.

### 2. [The Lottery Ticket Hypothesis](https://arxiv.org/abs/1803.03635)
**Source**: Frankle and Carbin, MIT (arXiv:1803.03635) | **Date**: 2018 | **Read time**: ~40 min
> The paper that made iterative pruning standard practice, and useful here as the lineage. Its
> central move is the same one X-AuT reaches for: prune a little, retrain, prune again, rather
> than cutting to the target in one step. Reading it shows that the progressive half of this
> session is a well-established result being applied to a new layer of the stack, while the
> combination-scoring half is the newer claim.

### 3. [Distilling the Knowledge in a Neural Network](https://arxiv.org/abs/1503.02531)
**Source**: Hinton, Vinyals and Dean, Google (arXiv:1503.02531) | **Date**: 2015 | **Read time**: ~25 min
> The origin of the recovery step, and worth reading for what it says about teachers. The 1.7B
> teacher here produced 5.55% mean error where self-distillation produced 8.45% — a gap larger
> than the one between good and bad layer choices, which is easy to miss when the attention is on
> what was removed rather than on what taught it afterwards.

### 4. [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
**Source**: Hu et al., Microsoft (arXiv:2106.09685) | **Date**: 2021 | **Read time**: ~30 min
> What makes the behavioral probe affordable. The selection method depends on being able to run a
> 0.3-epoch warm-up per candidate combination, and that is only cheap because the warm-up adapts a
> small number of parameters. Read it if you want to judge whether the same probe budget would
> transfer to a setting where full fine-tuning is the only option.

### 5. [Qwen3-ASR Technical Report](https://arxiv.org/abs/2601.21337)
**Source**: Qwen team, Alibaba Cloud (arXiv:2601.21337) | **Date**: January 2026 | **Read time**: ~25 min
> The model being compressed, and worth reading before trusting any of the error rates. Knowing
> the baseline — an 18-layer AuT audio encoder in front of the decoder, with the 0.6B and 1.7B
> variants differing in encoder width as well as depth — is what turns "removed layers 1 and 18,
> then 5 and 6" into a concrete statement. It also sets the floor those percentages are measured
> against, which no summary of the compression paper will give you.
