# How Diffusion Samplers Skip Steps Without Retraining

**Category**: Applied Research
**Date**: 2026-07-08
**Level**: Deeper
**For**: How models work
**Hook**: Image models can skip steps if the next frame is already readable — no retraining required.
**Time to read**: ~10 minutes
**Paper**: [arXiv:2607.06114](https://arxiv.org/abs/2607.06114) — Xin Peng, Ang Gao (July 2026)

## What It Is

Truncated Jump Sampling (TJS) is a technique that accelerates diffusion model inference by 20-70% with no retraining, no distillation, and no architecture changes. It works by stopping the ODE integration early and decoding the clean image directly from the intermediate state.

The key insight is deceptively simple: during training, diffusion models implicitly learn E[x₀|xₜ] — the minimum mean-square-error estimator of the clean sample given any noisy intermediate. Standard sampling ignores this and integrates the full ODE trajectory from noise to data. TJS instead halts at an early time t* and queries this already-learned decoder, jumping directly to x₀.

The mathematical foundation relies on the affine probability path structure that all standard diffusion and flow-matching models use. Given intermediate state xₜ on path xₜ = αₜx₀ + σₜε, you can decode:

```
x̂₀ = (σₜ · vθ(xₜ, t) - σ̇ₜ · xₜ) / Δₜ
```

where Δₜ = α̇ₜσₜ - αₜσ̇ₜ is the "path determinant" and vθ is the velocity prediction network. This formula requires only values already computed during normal ODE stepping — no additional neural forward pass.

## Why It Matters

**For production engineers deploying generative AI:**

1. **Drop-in speedup**: Works with existing checkpoints (SDXL, SD3.5, FLUX). No retraining budget needed. Change one line in your sampling loop.

2. **Compounds with existing optimizations**: Applied on top of already-distilled models (Z-Image-Turbo), TJS achieved 70% *additional* NFE savings. It's orthogonal to fast solvers like DPM-Solver++.

3. **Predictable quality-speed tradeoff**: The truncation fraction γ gives a single knob. At γ=0.83 (17% speedup), quality is nearly indistinguishable. At γ=0.43 (57% speedup), quality degrades gracefully.

4. **Theoretically grounded**: The "endpoint uncertainty" U(t) decays monotonically from data variance to zero, proving that later ODE steps have diminishing returns for image quality.

**Comparison to alternatives:**
| Method | Retraining | Model-specific | Composable |
|--------|-----------|----------------|------------|
| Progressive Distillation | Yes (expensive) | Yes | No |
| Consistency Models | Yes | Yes | No |
| DPM-Solver++ | No | No | Yes |
| **TJS** | **No** | **No** | **Yes** |

## Key Technical Details

- **Decoder formula**: x̂₀ = (σₜvθ - σ̇ₜxₜ) / Δₜ, where Δₜ is the path determinant
- **Algorithm**: Run k* = ⌈γK⌉ ODE steps (γ ∈ (0,1]), then decode. Done.
- **Truncation selection**: γ is a post-hoc hyperparameter. No adaptive selection needed — monotonic quality improvement as γ→1
- **Schedule compatibility**: VP diffusion, linear flow matching, VE/EDM — anything with affine paths
- **Results on SDXL (30-step baseline)**:
  - 25 NFEs (γ=0.83): PickScore 22.17, ImageReward 0.686 — essentially lossless
  - 19 NFEs (γ=0.63): PickScore 21.84, ImageReward 0.590 — 37% faster
  - 13 NFEs (γ=0.43): PickScore 21.41, ImageReward 0.314 — 57% faster with visible quality loss
- **Insight on trajectory straightness**: Rectified Flow works by straightening paths. TJS proves straightness is *sufficient* but *not necessary* — the decoder works regardless of path curvature

## How It Connects to What You Know

If you understand the ODE formulation of diffusion models (dx = vθ(x,t)dt from t=1→0), TJS is simply: stop at t=t* instead of t=0, and apply the closed-form Tweedie denoiser. The denoiser is what the model already learned during training — we're just using it at an intermediate timestep rather than forcing the ODE to converge all the way.

This connects to:
- **Classifier-free guidance**: TJS applies after guidance scaling, so CFG+TJS compose naturally
- **Latent diffusion**: Works in latent space (SDXL is latent), decode to pixels as normal after TJS
- **Consistency models**: Conceptually similar (predict x₀ from any xₜ) but consistency models require special training. TJS uses the existing model's implicit consistency.
- **Token pruning / early exit in transformers**: Same philosophy — later computation has diminishing returns, so stop early

## Try It Yourself

Run `code_example.py` to see:
1. A from-scratch implementation of the affine path decoder
2. TJS vs. full ODE integration on a 2D toy problem (mixture of Gaussians)
3. Quality-speed tradeoff curves showing the diminishing returns of late ODE steps
4. Visualization of endpoint uncertainty decay U(t)
