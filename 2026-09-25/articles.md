# Further Reading: How to Tell Whether Text Came From Your Own Model

## Articles

### 1. [Watermarking in vLLM](https://vllm.ai/blog/2026-09-24-watermarking-in-vllm)
**Source**: vLLM | **Date**: 2026-09-24 | **Read time**: ~15 min
> The primary source, and the reason this session exists. Read it for two tables the write-up above leans on: the throughput comparison, which shows matched change between −1.1% and +2.0% across batch sizes, and the detection-power table, where true-positive rate on code falls from 69% to 43% once the detector has to try 100 candidate keys. The speculative-decoding section is the part most likely to surprise you — it needs two keys, and says plainly that this dilutes the signal.

### 2. [Inside vLLM: Anatomy of a High-Throughput LLM Inference System](https://vllm.ai/blog/2025-09-05-anatomy-of-vllm)
**Source**: vLLM | **Date**: 2025-09-05 | **Read time**: ~40 min
> Background, and the one to read if the sampling path in the article felt like a black box. It walks the scheduler, the batching and the sampler as an actual system rather than a diagram, which is the context that makes "add noise at sampling time" land as an engineering decision rather than a maths trick.

## Papers

### [A Watermark for Large Language Models](https://arxiv.org/abs/2301.10226)
**Authors**: Kirchenbauer, Geiping, Wen, Katz, Miers, Goldstein | **Published**: 2023
> The paper that started this line, and worth reading precisely because it takes the *other* approach — it biases the sampler toward a green list and accepts a quality cost. Reading it first makes clear what distribution-preserving schemes bought and why it mattered. The statistical test here is also the ancestor of the one in the Code tab.

### [Robust Distortion-free Watermarks for Language Models](https://arxiv.org/abs/2307.15593)
**Authors**: Kuditipudi, Thickstun, Hashimoto, Liang | **Published**: 2023
> The distortion-free branch, which is what vLLM implemented. Read the robustness section rather than the construction: it is honest about how much editing a watermark survives, which is the question anyone will ask you within a minute of hearing the word.
