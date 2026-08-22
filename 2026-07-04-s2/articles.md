# Further Reading: NVFP4 Quantization & LLM Inference Hardware

## Primary Source

### [Creating the NVIDIA Nemotron 3 Ultra NVFP4 Checkpoint with NVIDIA Model Optimizer](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/)
**Source**: NVIDIA Developer Blog | **Date**: June 26, 2026 | **Read time**: ~16 min
> The definitive guide to NVFP4 quantization. Covers the FP4 number system (only 8 positive
> values), three scaling strategies (max, MSE, four-over-six), mixed-precision policies for
> MoE models, and the full quantization pipeline using NVIDIA Model Optimizer. Shows 3.2x
> compression and 5.9x throughput improvement on Nemotron 3 Ultra 550B. Start here.

## Related NVIDIA Posts

### [Scaling AI Inference Across Multiple GPUs Using TensorRT with Multi-Device Inference](https://developer.nvidia.com/blog/scaling-ai-inference-across-multiple-gpus-using-nvidia-tensorrt-with-multi-device-inference-support/)
**Source**: NVIDIA Developer Blog | **Date**: June 25, 2026 | **Read time**: ~11 min
> How to distribute inference across multiple GPUs when a quantized model still doesn't
> fit on one GPU. Covers tensor parallelism, pipeline parallelism, and the TensorRT runtime
> API. Useful companion to the NVFP4 post — quantize first, then distribute.

### [Maximize AI Factory Energy Efficiency Through Full-Stack Inference and Training Optimizations](https://developer.nvidia.com/blog/maximize-ai-factory-energy-efficiency-through-full-stack-inference-and-training-optimizations/)
**Source**: NVIDIA Developer Blog | **Date**: June 23, 2026 | **Read time**: ~10 min
> The energy cost angle: how quantization plus hardware-aware scheduling reduces power
> consumption across an inference cluster. Relevant context for the business case behind
> FP4 — it's not just about fitting on fewer GPUs, it's about power bills.

## Hardware Architecture Papers

### [3DLS: A 3D Logic-Stacked Architecture for Disaggregated LLM Serving](https://arxiv.org/list/cs.AR/recent)
**Authors**: Lee, Jung, Kim | **Published**: July 3, 2026
> A novel chip architecture that physically stacks compute and memory layers for LLM
> inference. Addresses the same memory-bandwidth bottleneck that NVFP4 attacks from the
> software side. Shows where hardware design is heading.

### [HBM Is Not All You Need: Efficient Disaggregated LLM Serving](https://arxiv.org/list/cs.AR/recent)
**Authors**: Wei, Wang, Yen, Xia, Qi | **Published**: June 30, 2026
> Argues that the industry's HBM (High Bandwidth Memory) focus is incomplete. Proposes
> using memory-heterogeneous accelerators where different memory tiers serve different
> roles. Complementary to quantization — even with FP4, memory architecture matters.

## Practical Guides

### [Ornith-1.0: Running a 35B Model Locally at 103 tok/s](https://simonwillison.net/)
**Source**: Simon Willison | **Date**: June 29, 2026 | **Read time**: ~5 min
> Practical report of running a quantized 35B-parameter model locally via LM Studio (GGUF
> format). Shows that quantization makes serious models runnable on consumer hardware.
> The GGUF quantization here is INT4-based — NVFP4 would be even better but requires
> Blackwell GPUs.
