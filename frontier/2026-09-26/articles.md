# Further Reading: Why Averaging Two Prompts Averages Their Answers

## Papers

### [Your Transformer Can Hold Two Thoughts at Once: Evidence of Linear Superposition in LLMs](https://arxiv.org/abs/2609.29845)
**Authors**: Tikhonov, Korznikov, Mikhalchuk, Dragunov, Rahmatullaev, Druzhinina, Razzhigaev, Oseledets, Tutubalina | **Published**: 2026-09
> The primary source. Read Figure 2 before anything else: hidden-state additivity error rising monotonically across pretraining checkpoints is the finding the rest of the paper is built to explain, and it is the part that survives disagreement about the decoding results. The normalization in the metrics section is worth copying whatever you think of the conclusion — it is the difference between a divergence number and a claim.

### [Toy Models of Superposition](https://arxiv.org/abs/2209.10652)
**Authors**: Elhage et al., Anthropic | **Published**: 2022
> Background, and the one to read if the word superposition was doing unexamined work for you. It is a different sense of the term — features sharing directions inside a layer, rather than two inputs sharing a forward pass — and knowing which is which stops a whole class of confusion. Read it as the vocabulary, not as the same result.

## Articles

### [Toy Models of Superposition — interactive version](https://transformer-circuits.pub/2022/toy_model/index.html)
**Source**: Transformer Circuits | **Read time**: ~45 min
> The one to open in a browser rather than an editor. Same content as the paper above with figures you can manipulate, which is the faster route into the geometry if you are meeting it for the first time. Skip if you already know it; this is an on-ramp, not a second result.
