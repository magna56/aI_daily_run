# How 4-Bit Floating Point Speeds Up LLM Inference

**Category**: AI Hardware for Engineers
**Date**: 2026-07-04
**Level**: Deeper
**For**: How models work
**Hook**: Four-bit numbers stay accurate when each block picks its own scale — that is the whole trick.
**Source**: NVIDIA Developer Blog (June 26, 2026)
**Time to read**: ~10 minutes

## What It Is

NVFP4 is NVIDIA's 4-bit floating-point format, introduced with the Blackwell GPU architecture
(B200/B300), designed specifically for compressing LLM weights. Unlike INT4 quantization
(which uses 16 evenly spaced integer values), NVFP4 uses a floating-point representation
with only **8 positive representable values**: 0, 0.5, 1, 1.5, 2, 3, 4, and 6.

Why floating-point instead of integer? Neural network weights follow bell-curve distributions
— most values cluster near zero, with few outliers. A floating-point grid concentrates
precision near zero (where most weights live) while still reaching large outliers. An
integer grid wastes half its values on a range where almost no weights exist.

NVIDIA demonstrated NVFP4 on Nemotron 3 Ultra (a 550B-parameter MoE model):
- **3.2x size reduction**: 1,121 GB (BF16) → 352 GB (NVFP4)
- **5.9x inference throughput** improvement on decode-heavy workloads
- **98.5% accuracy recovery** relative to BF16 across benchmarks

## Why It Matters

For any engineer deploying or serving LLMs:

- **Fit bigger models on fewer GPUs**: A 550B model that needed 15+ GPUs in BF16 now fits
  on 4-5 GPUs in NVFP4. This directly cuts your inference infrastructure cost.
- **Faster inference**: 5.9x throughput means your serving cluster handles 6x more requests
  at the same hardware cost — or you can slash latency.
- **Production-ready**: This isn't research — NVIDIA ships the quantization tooling
  (ModelOpt), the hardware support (Blackwell tensor cores), and the serving stack
  (TensorRT-LLM) together. It works today.
- **Mixed precision is the real pattern**: The Nemotron checkpoint doesn't use NVFP4
  everywhere. Embeddings stay BF16 (precision-critical), shared MoE experts use FP8
  (moderate compression), and routed experts use NVFP4 (most parameters, most compressible).
  Understanding per-layer sensitivity is the engineering skill.

## Key Technical Details

### The FP4 Number System
- **4 bits** = 1 sign bit + 3 mantissa/exponent bits
- **8 positive values**: {0, 0.5, 1, 1.5, 2, 3, 4, 6}
- Each block of weights (typically 32-128 values) gets a shared **scale factor** in FP8
- Effective bits per element: ~5.03 BPE (4 bits for value + amortized scale overhead)

### Three Scaling Strategies (the core engineering problem)
1. **Max scaling**: Set scale = max(|weights|) / 6. Simple but outlier-sensitive — one
   large weight stretches the grid, flushing small weights to zero.
2. **MSE scaling**: Minimize mean squared error between original and quantized weights.
   Better reconstruction but doesn't always improve downstream task accuracy.
3. **Four-over-six scaling** (best): Each block of weights chooses between two grids —
   M=4 (range [0,4], finer precision near zero) or M=6 (range [0,6], handles outliers).
   A single bit per block signals which grid. Achieves **98.5% median benchmark recovery**.

### Mixed Precision Policy
Not all layers tolerate the same quantization:
- **Embeddings**: BF16 (16-bit) — critical for token representation
- **Attention Q/K/V projections**: FP8 (8-bit) — moderate sensitivity
- **MoE shared experts**: FP8 — used for every token, needs higher precision
- **MoE routed experts**: NVFP4 (4-bit) — most parameters, only activated sparsely

### Quantization Pipeline
```
Original BF16 model
  → Calibration pass (forward on ~1000 samples)
  → Per-block scale computation (four-over-six)
  → Weight quantization to NVFP4
  → Export checkpoint
  → Deploy on TensorRT-LLM
```

## How It Connects to What You Know

From your LLM fundamentals (ai_thon section 1), you know that model parameters are stored
as floating-point tensors and that inference is memory-bound. NVFP4 directly attacks the
memory bottleneck: 4x fewer bytes to load from GPU memory per forward pass means the
memory bus isn't the bottleneck anymore.

The mixed-precision policy connects to MoE architecture — also from section 1. In a MoE
model, each token only activates a subset of "expert" layers. Since most expert weights sit
idle for any given token, they're perfect candidates for aggressive compression. The shared
experts (activated for every token) need higher precision because errors accumulate.

The scaling strategies connect to the tokenization concepts you know: just as a tokenizer
must decide how to partition continuous text into discrete tokens, quantization must partition
continuous weight values into discrete FP4 values. The "four-over-six" approach is analogous
to adaptive tokenization — different blocks get different grids based on their distribution.

## Try It Yourself

Run `code_example.py` to see FP4 quantization implemented from scratch:

```bash
python3 ~/ai_learning/2026-07-04-s2/code_example.py
```

The demo:
1. Generates realistic neural network weight distributions
2. Implements all three scaling strategies (max, MSE, four-over-six)
3. Quantizes weights to the 8 FP4 values and measures reconstruction error
4. Shows why four-over-six wins — with visual distribution comparison
5. Computes the effective compression ratio and accuracy impact
