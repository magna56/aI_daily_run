# Further Reading: How Predicting a Whole Idea Beats Predicting the Next Token

## Articles

### 1. [NCP-ArchPreview Technical Report](https://arxiv.org/abs/2609.10715)
**Source**: The Intern-NCP Team (arXiv:2609.10715) | **Date**: 9 September 2026 | **Read time**: ~35 min
> The scale result, and the number to read carefully is not the benchmark lift. Reaching
> OLMo-3-7B's final pretraining loss on 51.3% of the tokens is the claim that matters, and the
> compute figure beside it — about 85% of standard computation — is what turns a token saving into
> a real one. Read the training setup before the tables; 8.9B over 5.73T tokens of Dolma-3 is what
> the comparison rests on.

### 2. [Next Concept Prediction in Discrete Latent Space](https://arxiv.org/abs/2602.08984)
**Source**: LUMIA Lab (arXiv:2602.08984) | **Date**: February 2026 | **Read time**: ~30 min
> The mechanism, and the one to read first if you want to build this. It carries what the technical
> report assumes you know: how the concept vocabulary is constructed by product quantization over
> intermediate hidden states, what a concept spans, and how the three loss terms fit together. The
> ablations on concept span are the practical part — they are why the span is a tuning decision
> rather than a constant.

### 3. [Product Quantization for Nearest Neighbor Search](https://inria.hal.science/inria-00514462/document)
**Source**: Jégou, Douze and Schmid, INRIA | **Date**: 2011 | **Read time**: ~40 min
> The original paper for the technique doing the work here, and worth reading even though it is
> about retrieval. It explains why splitting a vector and quantizing the slices independently
> buys an enormous effective vocabulary for a small table — the property this session
> depends on, arrived at for a completely different reason fifteen years earlier.

### 4. [OLMo 3](https://allenai.org/olmo)
**Source**: Allen Institute for AI | **Date**: current | **Read time**: ~20 min
> The baseline every number in the technical report is measured against. Worth knowing what it is
> before you accept a comparison to it: a fully open model with published data, code and
> checkpoints, which is precisely why it gets used as a reference point. The comparison is only as
> meaningful as the match in training data, and that is checkable here.

### 5. [Dolma](https://allenai.org/dolma)
**Source**: Allen Institute for AI | **Date**: current | **Read time**: ~15 min
> The corpus, and the reason to look is the span-level structure question this session ends on.
> Whether a concept can carry anything depends on whether the data has structure above the token,
> and a web-scale mixed corpus is a very different shape from the phrase-structured toy in
> `code_example.py`. Read the composition section if you want to reason about where the gain comes
> from.
