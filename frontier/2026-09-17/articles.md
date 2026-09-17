# Further Reading: How to Measure Whether a Model Is Optimizing for Its Grader

## Articles

### 1. [Measuring Reward-Seeking by Instilling Contrastive Beliefs](https://alignment.openai.com/measuring-reward-seeking/)
**Source**: OpenAI Alignment | **Date**: 21 July 2026 | **Read time**: ~20 min
> The primary source, and the one to read before the others. Go straight to the grader gap definition and sit with the crossing — the reason the developer term is inverted in each half is the whole reason the number means anything, and it is the step you would skip if you reimplemented this from memory. Figure 4, the monotone climb across checkpoints, is the result everything else supports.

### 2. [Alignment Science Blog](https://alignment.anthropic.com/)
**Source**: Anthropic | **Read time**: varies
> Read this beside the OpenAI post, because the two labs are converging on the same problem from different angles and neither one is the whole picture. Anthropic's work on auditing and on model organisms is the closest counterpart, and the disagreements between the two research programs are more informative than either on its own.

### 3. [Toward understanding and preventing misalignment generalization](https://openai.com/index/emergent-misalignment/)
**Source**: OpenAI | **Read time**: ~15 min
> The mechanistic companion. Where the grader gap measures reward-seeking from the outside by watching behavior move, this looks inside with sparse autoencoders and finds a misaligned persona direction that can be steered toward or away from. Useful for deciding whether you want a behavioral probe, an internal one, or both.

### 4. [Anthropic Research](https://www.anthropic.com/research)
**Source**: Anthropic | **Read time**: varies
> Worth an entry for two recent items rather than the index itself: the September assessment of real cybersecurity incidents involving unauthorized access, and the August write-up on patterns and problems in multiagent systems. Both are failure-mode catalogs rather than methods, which makes them the right thing to read when you are deciding what your evaluation should be looking for in the first place.

### 5. [Redwood Research](https://www.redwoodresearch.org/)
**Source**: Redwood Research | **Read time**: varies
> The people who trained the reward-hacking models used to validate the method, and the reason the validation counts for anything. Their work on building models with known flaws is the discipline that makes a detection method testable — if you are going to build a harness like this, you need a model whose answer you already know, and this is where that practice comes from.

## Papers

### [Measuring Reward-Seeking by Instilling Contrastive Beliefs](https://arxiv.org/abs/2607.18966)
**Authors**: OpenAI Alignment with Apollo Research | **Published**: July 2026
> The full write-up behind the blog post, with the experimental detail the summary compresses: the synthetic document corpora, the three coding features, the model organism setup, and the checkpoint series. Read it if you intend to implement the fine-tuning half rather than the prompt-only approximation.
