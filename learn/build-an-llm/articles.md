# Further Reading: The Stack Has Five Verbs

## Primary Sources

### 1. [nanoGPT](https://github.com/karpathy/nanoGPT)
**Source**: github.com/karpathy | **Read time**: ~15 min (browse)
> A readable GPT training repo. Tokenize, predict the next id, sample. Pair with the "Let's build GPT" lecture.

### 2. [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
**Source**: arXiv | **Read time**: ~40 min
> The block: attention, MLP, residual, norm. Depth is more copies of that block.

### 3. [Language Models are Unsupervised Multitask Learners](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)
**Source**: openai.com | **Read time**: ~25 min
> GPT-2: decoder-only next-token training as the whole trick. The product voice came later, as data.

## Background & Ecosystem

### 4. [The Illustrated GPT-2](https://jalammar.github.io/illustrated-gpt2/)
**Source**: jalammar.github.io | **Read time**: ~20 min
> Pictures of the five verbs. Use after you have run this folder's toy trainer.

### 5. [What an LLM does](https://theaicommit.com/#learn/what-an-llm-does)
**Source**: theaicommit.com | **Read time**: ~10 min
> Day-1 lesson: pick, append, repeat. This primer opens the box those picks come from.

## The one-line takeaway
A chat reply is tokenize → embed → mix → score → sample, looped. Training changes which id looks likely. It does not add a second machine.
