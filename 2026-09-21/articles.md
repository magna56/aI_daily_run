# Further Reading: How to Check Whether a Model's Confidence Score Means Anything

## Articles

### 1. [Introduction — TypeSafe AI docs](https://docs.typesafe.ai/introduction)
**Source**: TypeSafe AI | **Date**: September 2026 | **Read time**: ~6 min
> The primary source, and the right one to read rather than the launch post. It defines the three primitives and the response fields each returns, and it states the property the article leans on: every question is evaluated independently against the same state, so adding a tenth does not degrade the first. Read this first if you are deciding whether typed decisions fit your workflow.

### 2. [Building a harness with Jev](https://www.langchain.com/blog/building-a-harness-with-jev)
**Source**: LangChain, by Sydney Runkle and Hunter Lovell | **Date**: 2026-09-17 | **Read time**: ~8 min
> The one to open in an editor. Snippets for three real shapes — classification, model routing middleware, and a guardrail that blocks a risky tool call before it runs. It is also the most honest framing available on fit: the authors say plainly that this is not a drop-in replacement for a language model, and that the pairing is an LLM for generation with a structured model for the decisions along the way. Read it after you have decided the idea is worth trying.

### 3. [Workflow evals](https://evals.typesafe.ai/)
**Source**: TypeSafe AI | **Date**: September 2026 | **Read time**: ~5 min
> The numbers, and the reason to read them carefully. Four workflows — security triage, trace observability, invoice processing, customer service — across roughly ten models. Read the methodology note before the charts: the reference answers are an average of two frontier models rather than human labels, and TypeSafe's own team wrote the workflows. That makes the accuracy figure a measure of agreement with an expensive model, which is a different claim from correctness.

### 4. [Introducing System One Models and Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
**Source**: TypeSafe AI | **Date**: 2026-09-15 | **Read time**: ~7 min
> The launch announcement. Included for the training method — Reinforcement Learning for Calibrated Decisions — and the parallel sampler that produces every output in one query instead of autoregressively, neither of which the docs explain. Skip the comparison figures; the evals page above carries the same numbers with the caveats attached.

## Papers

### [On Calibration of Modern Neural Networks](https://arxiv.org/abs/1706.04599)
**Authors**: Guo, Pleiss, Sun, Weinberger | **Published**: 2017
> The paper that named this problem and introduced temperature scaling, which is the repair implemented in the Code tab. Read it for the finding underneath this whole article: modern networks became *less* calibrated as they got more accurate, so confidence and correctness genuinely did come apart. The reliability diagram in the Visualize tab is theirs.
