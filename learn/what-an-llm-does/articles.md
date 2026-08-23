# Further Reading: The Model Only Ever Picks the Next Token

## Primary Sources

### 1. [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
**Source**: arXiv | **Read time**: ~40 min
> The 2017 paper that introduced the transformer: a sequence model that predicts the next token by letting every position attend to earlier ones, without a recurrent step. Read the abstract and §3 if you want the architecture; the rest of this Learn chapter does not depend on the matrices.

### 2. [Training language models to follow instructions with human feedback (InstructGPT)](https://arxiv.org/abs/2203.02155)
**Source**: arXiv | **Read time**: ~35 min
> OpenAI's write-up of the three-stage stack in product form: a pretrained completer, supervised fine-tuning on (prompt, reply) pairs, then preference ranking and reinforcement learning so the model prefers answers people actually like. This is the paper behind the "ChatGPT-shaped" assistant, not just a bigger base model.

### 3. [Illustrating Reinforcement Learning from Human Feedback (RLHF)](https://huggingface.co/blog/rlhf)
**Source**: huggingface.co | **Read time**: ~20 min
> A diagram-heavy walkthrough of reward models, preference pairs, and how the language model is updated. Use this when the chapter's "taste change" paragraph is clear but you want the training loop drawn.

## Background & Ecosystem

### 4. [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)
**Source**: jalammar.github.io | **Read time**: ~25 min
> Jay Alammar's visual explanation of attention and the transformer block. The right next click after "a transformer lets each position look at earlier positions" if you want pictures instead of a paper.

### 5. [nanoGPT](https://github.com/karpathy/nanoGPT)
**Source**: github.com/karpathy | **Read time**: ~15 min (browse)
> Andrej Karpathy's small, readable GPT training repo. The code is the claim of this chapter in executable form: tokenize, predict the next token, sample. Pair with his "Let's build GPT" lecture if you want the walkthrough.

## The one-line takeaway
Runtime is always next-token prediction. Pretraining, supervised fine-tuning, and preference training only change which token looks likely — they do not add a second machine that "understands."
