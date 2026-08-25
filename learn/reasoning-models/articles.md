# Further Reading: How Reasoning Models Work

## Primary Sources

### 1. [Learning to reason with LLMs](https://openai.com/index/learning-to-reason-with-llms/)
**Source**: OpenAI | **Date**: September 12, 2024 | **Read time**: ~12 min
> The o1 announcement that named the split this page is about: the same model improves with more reinforcement-learning training *and* with more time spent thinking at inference. Includes the AIME / GPQA / Codeforces charts and the note that published scores used a maximal test-time compute setting — quality was a serving choice, not only a weight file.

### 2. [Introducing OpenAI o1-preview](https://openai.com/index/introducing-openai-o1-preview/)
**Source**: OpenAI | **Date**: September 12, 2024 | **Read time**: ~6 min
> The product post next to the research one: a model that "thinks before it responds," plus o1-mini as an 80%-cheaper reasoning SKU aimed at coding. Useful for the routing lesson — even OpenAI shipped a *small* reasoner rather than one smart file for every call.

### 3. [Extended thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)
**Source**: Anthropic (Claude API docs) | **Date**: current | **Read time**: ~15 min
> How thinking is actually sold on Claude: `budget_tokens` (manual, minimum 1,024), the move to adaptive thinking / effort on newer models, interleaved thinking with tools, and the billing rule that thinking tokens count as output and toward the context window. The engineer-facing version of "you pay for the pad."

## Background & Ecosystem

### 4. [What is test-time compute and how to scale it?](https://huggingface.co/blog/Kseniase/testtimecompute)
**Source**: Hugging Face | **Date**: 2025 | **Read time**: ~12 min
> A survey of the knob after o1: longer chains of thought, extra samples plus a verifier, search, and distillation. Good for seeing that "reasoning model" is a family of serving policies, not one vendor trick.

### 5. [Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents)
**Source**: Anthropic Engineering | **Date**: December 2024 | **Read time**: ~15 min
> Why an inner thinking budget is not a substitute for an outer agent loop. Use this when you are tempted to "just turn on reasoning" instead of giving the model tools and a stop condition — the capstone page picks up here.

## The one-line takeaway
The smart SKU is often the same decoder allowed to emit more tokens before it answers. Treat that as a timeout you pay for, and route it like you would extra CPU — only on work a verifier can score.
