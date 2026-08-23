# A Language Model on a 6502: BitNet Ternary Weights as Hardware-Aware Design

**Category**: AI Hardware for Engineers
**Tags**: quantization, from-scratch, transformers
**Date**: 2026-08-03
**Level**: Deeper
**For**: How models work
**Hook**: Weights that are only −1, 0, or +1 turn multiply into add — a language model that could fit a 1980s chip.
**Time to read**: ~10 minutes

## What It Is

Matt Beton put an autoregressive language model on a **6502** — the 8-bit CPU from
the BBC Micro / Apple II / NES era, 32KB of RAM, **no hardware multiply, no FPU**. It
generates text, character by character, in the browser emulator. This isn't a stunt so
much as a forcing function: when the hardware gives you nothing, every architectural
choice has to be justified in clock cycles and bytes. The result is a compact case study
in *hardware-aware model design* — the same discipline that governs whether your model
saturates an H200's memory bandwidth or a phone's NPU.

The two load-bearing decisions: **BitNet ternary weights** and a **Mamba-style recurrent
core**. BitNet (Ma et al., 2024) quantizes every weight to one of {−1, 0, +1} — log₂(3) ≈
**1.58 bits** per weight. On a chip with no multiplier, that's transformative: a matmul
`Y = ΣₖXₖ·Wₖ` where every W ∈ {−1,0,+1} has *no multiplications at all* — you **skip** on 0,
**add** on +1, **subtract** on −1. An 8×8 multiply-accumulate on the 6502 costs ~150 cycles;
the ternary add/subtract accumulate costs ~30 — a **5× speedup** purely from choosing the
weight representation. The recurrent (Mamba) core is the other half: transformers carry a
KV cache that grows O(layers × dim) *per token*, which would blow the 25KB RAM budget in a
few tokens. A recurrent model keeps a single **fixed-size hidden state** that's overwritten
each step — constant memory, constant compute per token, forever.

Everything else is integer-only survival engineering: weights packed **4 per byte** (2 bits
each, unpacked with right-shifts — never a divide-by-3), **8-bit activations** accumulated in
**16-bit** to avoid overflow across up to 256 terms, a learned **right-shift** as the
activation "scale" (shifting by 1 doubles/halves magnitude — free on any CPU), and a
**lookup-table softmax** because the 6502 can't compute eˣ. The whole model is 52K params in
13KB, hidden dim 56, a 27-token char vocabulary (a-z + space).

## Why It Matters

- **Ternary is the extreme end of a spectrum you already care about.** You saw NVFP4 (4-bit
  *float*) on 2026-07-04-s2. BitNet is the other extreme: 1.58-bit *integer*, and its payoff
  isn't just compression — it's the *elimination of the multiplier*, which is what dominates
  area/energy in real accelerators. This is why there's a hardware co-design story: chips
  built for ternary don't need FP mul units at all.
- **"Memory-bound, not compute-bound" made visceral.** LLM inference is almost always limited
  by moving weights, not multiplying them. Pack weights 16–32× smaller and you move 16–32×
  fewer bytes per token. The 6502 just makes the bandwidth wall impossible to ignore.
- **KV cache is an architecture choice, not a law.** The recurrent core sidesteps the single
  biggest serving-memory headache. The same reasoning drives 2026's interest in Mamba/SSM and
  hybrid attention for long-context serving.
- **The tricks generalize up the stack.** Bit-packing + shift-unpack, integer accumulation
  widths, LUT-based nonlinearities, and shift-as-scale all reappear in production INT8/INT4
  kernels on GPUs and NPUs — just with wider lanes.

## Key Technical Details

- **absmean ternary quantization:** scale `s = mean(|W|)`, then `W_q = round(W/s)` clipped to
  {−1,0,+1}. Weight ≈ `s · W_q`. Train in float32, quantize only in the forward pass, pass
  gradients straight through (STE). The per-tensor scale `s` is the *only* float that survives.
- **Multiply-free matmul:** for ternary W, `Y_j = Σₖ (Wₖⱼ==0 ? 0 : Wₖⱼ==+1 ? +Xₖ : −Xₖ)`.
  Zeros are skipped entirely, so sparsity is *also* a speedup — a ~30% zero rate is ~30% fewer
  adds.
- **2-bit packing, 4/byte:** encode {−1,0,+1}→{…} in 2 bits; unpack with `(byte >> 2i) & 3`.
  They deliberately chose 4/byte over 5/byte to keep unpacking to shifts/masks (5/byte needs a
  divide by 3, which the 6502 hates).
- **8-bit activations, 16-bit accumulate:** up to 256 terms of magnitude ≤128 → max ~2^15,
  fits int16. Then `clip(acc >> shr, −128, 127)` with a *learned* `shr` per layer as the
  activation/scale in one op.
- **LUT softmax:** subtract max logit for stability, then `lookup[d] = round(255·e^(−d/T))`
  precomputed at temperature T; sample via a 16-bit PRNG. No exp, no division.
- **Recurrent stability by construction:** Mamba's per-channel decay ∈ [0,1) can't explode,
  which matters because aggressive quantization destabilizes GRU/LSTM-style gates.

## How It Connects to What You Know

Same question as the FP4 session — "what's the least numeric precision that still clears the
quality bar?" — pushed to the floor. The straight-through estimator is the identical trick used
to train through any hard/discrete op. Skipping zero-weights is structured sparsity, the
weight-side analogue of the confidence-gated *compute* skipping in yesterday's cascade session.
And the "no KV cache" recurrent core is the exact tradeoff behind Mamba/SSMs you'd weigh for
long-context serving: constant memory and per-token compute in exchange for a fixed-width state
bottleneck. The 6502 is just the most honest profiler you'll ever use.

## Try It Yourself

`code_example.py` implements a BitNet ternary linear layer from scratch in pure Python:
absmean quantization, 2-bit packing (4/byte) with shift-unpack, and a **multiply-free** matmul
that counts its own operations to *prove* zero multiplies. It reports the memory compression vs
float32, the accuracy delta vs the full-precision matmul, and a LUT-softmax sampler with no
`exp()`. A tiny recurrent step shows the fixed-state, no-KV-cache property.
