# Further Reading: How to Shrink a Model's Wiring Diagram Until You Can Read It

## Articles

### 1. [Automatic-Circuit-Discovery (ACDC)](https://github.com/ArthurConmy/Automatic-Circuit-Discovery)
**Source**: Arthur Conmy | **Date**: ongoing | **Read time**: ~30 min to run
> The thing to open in an editor. This is the reference implementation of the frozen search that condensation is measured against, so it is the fastest way to see what "hundreds of edges" actually looks like on a model you can run locally. Clone it, reproduce the greater-than circuit, then re-read the condensation loop — the difference between the two is exactly the weight-update step. Start here if you intend to implement anything.

### 2. [Towards Automated Circuit Discovery for Mechanistic Interpretability](https://arxiv.org/abs/2304.14997)
**Source**: arXiv 2304.14997 (Conmy, Mavor-Parker, Lynch, Heimersheim, Garriga-Alonso) | **Date**: Apr 2023 | **Read time**: ~35 min
> The paper behind that repo, and the baseline the 30-of-32 result is measured against. Its headline is the useful calibration for today's piece: ACDC recovers a known GPT-2 circuit by selecting 68 edges out of roughly 32,000. Read it to understand what a frozen method can and cannot do before judging how much the weight updates are really buying.

### 3. [Have Faith in Faithfulness: Going Beyond Circuit Overlap When Finding Model Mechanisms](https://arxiv.org/abs/2403.17806)
**Source**: arXiv 2403.17806 (Hanna, Pezzelle, Belinkov) | **Date**: Mar 2024 | **Read time**: ~30 min
> Where EAP-IG comes from, and why the integrated-gradients path exists at all: plain attribution patching hits zero-gradient regions and produces circuits that are *less faithful* despite overlapping heavily with causally-discovered ones. Read this if you want to know why the scoring step in `code_example.py` interpolates rather than taking a single gradient — it is the difference between a ranking you can trust and one that merely looks plausible.

### 4. [Interpretability in the Wild: a Circuit for Indirect Object Identification in GPT-2 small](https://arxiv.org/abs/2211.00593)
**Source**: arXiv 2211.00593 (Wang, Variengien, Conmy, Shlegeris, Steinhardt — Redwood Research / UC Berkeley) | **Date**: Nov 2022 | **Read time**: ~45 min
> The hand-built circuit that condensation's IOI result is scored against: 26 attention heads in seven named classes, found by causal intervention rather than search. This is where the "documented roles" in the 17-of-24 comparison come from, so it is the paper that decides whether the condensed circuit is a cleaner view of a known mechanism or a different object wearing its name. The most demanding read here, and the one that makes the comparison meaningful.
