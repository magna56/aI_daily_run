# Further Reading: Why a Model Fixes the Gap It Cannot Find

## Articles

### 1. [IdeaAMBIG: Benchmarking Implementation-Critical Gaps in Research-Idea Specifications](https://arxiv.org/abs/2609.10539)
**Source**: Yale NLP Lab (arXiv:2609.10539) | **Date**: 9 September 2026 | **Read time**: ~30 min
> The paper this session is built on, and the table to find is the one splitting localization from
> clarification. Read the two numbers next to each other — 9.6% recovery on real gaps against 80.6%
> success once the gap is given — because the gap between them is the finding, not either figure
> alone. Note also the split in the dataset: 163 real gaps from reproducibility reports and GitHub
> issues, 497 injected. The real half is the one to trust.

### 2. [The oracle study, in the same paper](https://arxiv.org/html/2609.10539)
**Source**: Yale NLP Lab, HTML edition | **Date**: 9 September 2026 | **Read time**: ~15 min
> Worth its own visit because it is the part that says the effort is worth spending. Handing the
> model correct resolutions for every gap moves codification readiness from 14% to 98% — so the
> gaps really are the whole obstacle, and nothing else about the specification needed fixing. Read
> it before deciding how much to invest in detection.

### 3. [The Two Things Missing From Most Coding Agent Requests](https://theaicommit.com/#2026-09-06)
**Source**: The AI Commit | **Date**: 6 September 2026 | **Read time**: ~10 min
> The other half of this problem, from six days ago and worth rereading alongside. That session
> measured *which* fields are missing from real agent requests and what each one costs. This one
> explains why the agent will not tell you they are missing. Together they are the same finding
> approached from opposite ends: the fields are absent, and absence is the thing nobody notices.

### 4. [Codification readiness and reproducibility reports](https://reproducibility-challenge.github.io/)
**Source**: ML Reproducibility Challenge | **Date**: current | **Read time**: ~20 min
> Where a third of the benchmark's real gaps come from, and useful for calibrating what a
> "specification gap" looks like in the wild. Reading a few reports is the fastest way to see that
> these are rarely exotic — a missing hyperparameter, an unstated initialization, an ordering that
> only one reading of the text supports.

### 5. [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
**Source**: Anthropic Engineering | **Date**: current | **Read time**: ~25 min
> The design-side companion. Its argument is that the interface should make the right action
> obvious rather than relying on the model to infer it, which is the same move this session makes
> one level up: put the required fields in the structure instead of hoping the reader notices they
> are missing.
