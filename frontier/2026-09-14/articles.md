# Further Reading: How to Fine-Tune a Model When Some of Your Preference Labels Are Wrong

## Articles

### 1. [PLC-DPO: Posterior Label Correction in Noisy and Ambiguous Preference Optimization](https://arxiv.org/abs/2608.30597)
**Source**: Cho, Ahn and Yun (arXiv:2608.30597), Findings of EMNLP 2026 | **Date**: 31 August 2026 | **Read time**: ~35 min
> The paper this session is built on. Read Algorithm 1 first — it is the whole method on one page,
> and the three state-conditional losses are simpler than the surrounding notation suggests. The
> result to hold onto is the 60.5 against 55.5 mean win rate over 57 dataset-model-benchmark cells.
> Do not skip the self-confirmation diagnostics: the authors say plainly that the routing weights
> are not a ground-truth audit of the dataset, which is the easiest thing in the paper to misread.

### 2. [Direct Preference Optimization: Your Language Model is Secretly a Reward Model](https://arxiv.org/abs/2305.18290)
**Source**: Rafailov, Sharma, Mitchell, Ermon, Manning and Finn, Stanford (arXiv:2305.18290) | **Date**: 29 May 2023 | **Read time**: ~40 min
> The method everything above is correcting, and the source of the margin this session turns into
> evidence. Worth reading for section 4, where the implicit reward is derived in closed form — once
> you have seen that the margin is a reward difference, using it as a signal about the label stops
> feeling like a trick. It also states the reliability assumption that PLC-DPO exists to break.

### 3. [Provably Robust DPO: Aligning Language Models with Noisy Feedback](https://arxiv.org/abs/2403.00409)
**Source**: Chowdhury, Kini and Natarajan, Microsoft Research (arXiv:2403.00409) | **Date**: 1 March 2024 | **Read time**: ~35 min
> The prior generation of the same idea, and the right thing to read second. It assumes a known
> flip rate and de-biases the loss against it, with theoretical guarantees attached. Reading it
> makes clear what the newer work is actually buying: an estimate that adapts per pair during
> training, rather than one number you have to supply up front and cannot measure.

### 4. [TRL: DPO Trainer](https://huggingface.co/docs/trl/dpo_trainer)
**Source**: Hugging Face documentation | **Date**: continuously updated | **Read time**: ~20 min
> Where this lands in practice, and the file you subclass. The page documents the expected dataset
> columns and the `dpo_loss` method that any routing change has to live inside, plus the reference
> model plumbing you do not want to reimplement. Read the loss-type section to see how much of this
> family is already exposed as a parameter before you write your own.

### 5. [Tips for LLM Pretraining and Evaluating Reward Models](https://magazine.sebastianraschka.com/p/tips-for-llm-pretraining-and-evaluating-rms)
**Source**: Sebastian Raschka | **Date**: 31 March 2024 | **Read time**: ~20 min
> The gentler route in if reward models and DPO are new. It sets out how preference scoring works
> and why DPO removes the separate reward model, which is the context the rest of this reading list
> assumes. It does not cover label noise or annotator disagreement, so treat it as background
> rather than as a source on the problem this session is about.
