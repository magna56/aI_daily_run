# Further Reading: How Diffusion Samplers Skip Steps Without Retraining

## Primary Paper

### [x-Prediction Is All You Need: Training-Free Accelerated Generation via Endpoint Decodability](https://arxiv.org/abs/2607.06114)
**Authors**: Xin Peng, Ang Gao | **Published**: July 8, 2026
> Introduces Truncated Jump Sampling (TJS) — stop ODE integration early and decode x₀ directly from intermediate state using a closed-form formula. Achieves 20-70% NFE reduction on SDXL, SD3.5, FLUX, and Z-Image-Turbo with no retraining. Key insight: standard training implicitly teaches models E[x₀|xₜ], and we can query this at any timestep.

## Related Papers

### [Flow Matching for Generative Modeling](https://arxiv.org/abs/2210.02747)
**Authors**: Yaron Lipman, Ricky T.Q. Chen, Heli Ben-Hamu, Maximilian Nickel | **Published**: 2022
> Foundational paper establishing the flow matching framework that TJS builds on. Shows how to train continuous normalizing flows via simple regression on conditional velocity fields, avoiding costly ODE simulation during training. TJS exploits the affine path structure this framework defines.

### [Consistency Models](https://arxiv.org/abs/2303.01469)
**Authors**: Yang Song, Prafulla Dhariwal, Mark Chen, Ilya Sutskever | **Published**: 2023
> Maps any point on the ODE trajectory to the origin (x₀) — conceptually similar to TJS's decoder. Key difference: requires specialized training or distillation to learn the consistency function. TJS proves the standard velocity model already contains this mapping implicitly, making retraining unnecessary.

### [DPM-Solver++: Fast Dedicated High-Order Solver for Diffusion ODE](https://arxiv.org/abs/2211.01095)
**Authors**: Cheng Lu, Yuhao Zhou, Fan Bao, Jianfei Chen, Chongxuan Li, Jun Zhu | **Published**: 2022
> State-of-the-art fast ODE solver using exponential integrators with high-order corrections. TJS is orthogonal to solver choice — you can use DPM-Solver++ for the truncated trajectory and still decode at the end. Combining both gives compound speedups.

## Blog Posts & Explanations

### [Understanding Diffusion Models: A Unified Perspective](https://arxiv.org/abs/2208.11970)
**Authors**: Calvin Luo | **Published**: 2022 (updated 2024)
> The canonical tutorial connecting score-based models, DDPM, and continuous-time diffusion. Section 8 covers the relationship between ε-prediction, x₀-prediction, and v-prediction — the exact parameterization choices that make TJS's decoder formula work across model types.

### [Elucidating the Design Space of Diffusion-Based Generative Models (EDM)](https://arxiv.org/abs/2206.00364)
**Authors**: Tero Karras, Miika Aittala, Timo Aila, Samuli Laine (NVIDIA) | **Published**: 2022
> Systematically decomposes diffusion model design into orthogonal choices (schedule, network parameterization, sampler). TJS adds a new axis to this design space: "where to stop" is now independent of "how to step" and "how to predict." EDM's clean framework makes it easy to slot TJS into any configuration.
