# Further Reading: How to Run a Language Model With Zero Multiplies

## Articles

### 1. [Autoregressive Language Model on the 6502 Processor](https://mattbeton.com/blog/bitnet-6502.html)
**Source**: Matt Beton's blog | **Date**: July 2026 | **Read time**: ~15 min
> The primary source. Walks through running a Mamba-style, BitNet-ternary LM on a
> BBC Micro's 6502: 52K params in 13KB, multiply-free matmul (150→30 cycles), 2-bit
> packing, learned-shift activations, and a lookup-table softmax. The clearest
> hands-on treatment of "no multiplier, no FPU" model design you'll find.

### 2. [Why we write our own C and C++ inference engines](https://localai.io/blog/why-we-write-our-own-engines/)
**Source**: LocalAI blog | **Date**: 2026 | **Read time**: ~10 min
> Companion systems perspective: why generic runtimes leave performance on the table
> and when hand-written integer kernels pay off. Useful counterpoint on where the
> real inference bottlenecks live once you leave the toy scale.

### 3. [The Era of 1-bit LLMs (BitNet b1.58) — explainer](https://huggingface.co/blog)
**Source**: Hugging Face blog | **Date**: 2024–2026 | **Read time**: ~12 min
> Practical write-ups on training and running ternary models, including
> straight-through-estimator training, absmean quantization, and the kernel-level
> reasons ternary matmul beats INT8 on energy and area. Bridge from the 6502 toy to
> GPU/NPU-scale deployment.

### 4. [Mamba: Linear-Time Sequence Modeling with Selective State Spaces](https://arxiv.org/abs/2312.00752)
**Source**: arXiv (Gu & Dao) | **Date**: Dec 2023 | **Read time**: ~20 min
> Why a recurrent/SSM core has no KV cache: a fixed-width selective state replaces
> the growing attention cache. The architectural half of the 6502 story, and the
> reason SSM/hybrid models keep resurfacing for long-context serving.

## Papers

### [The Era of 1-bit LLMs: All Large Language Models are in 1.58 Bits](https://arxiv.org/abs/2402.17764)
**Authors**: Shuming Ma, Hongyu Wang, et al. (Microsoft Research) | **Published**: Feb 2024
> Defines BitNet b1.58: ternary {−1,0,1} weights (log₂3 ≈ 1.58 bits), absmean
> quantization, 8-bit activations, multiplication-free matmul. Claims parity with
> FP16 transformers on perplexity and downstream tasks while cutting latency, memory,
> throughput, and energy — and argues for ternary-native hardware. The foundation the
> 6502 demo builds on.
