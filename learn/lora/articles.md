# Further Reading: How LoRA Works

## Primary Sources

### 1. [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
**Source**: arXiv | **Read time**: ~35 min (paper)
> Hu et al., 2021. Frozen `W`, trainable `B A`, merge at serve time. Read §4 for why rank stays small and why they put adapters on Q and V.

### 2. [PEFT: Parameter-Efficient Fine-Tuning](https://huggingface.co/docs/peft)
**Source**: huggingface.co | **Read time**: ~15 min
> The library most teams actually call. Config knobs — rank, alpha, target modules — mapped onto the matrices in this primer.

### 3. [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314)
**Source**: arXiv | **Read time**: ~30 min
> 4-bit frozen base plus LoRA adapters. The reason a 7B-class fine-tune fits on one GPU.

## Background & Ecosystem

### 4. [Adapter methods in PEFT](https://huggingface.co/docs/peft/conceptual_guides/adapter)
**Source**: huggingface.co | **Read time**: ~10 min
> How a saved adapter is loaded, swapped, and (optionally) merged. The product form of "do not ship 14GB per customer."

### 5. [How Many Bits Can an Adapter Write?](https://theaicommit.com/#2026-07-26)
**Source**: theaicommit.com | **Read time**: ~10 min
> Daily-lab follow-on: adapter capacity is a few bits per parameter, and *where* you attach it beats *how big* it is.

## The one-line takeaway
Freeze the big matrix. Train two skinny ones. Merge if you serve one adapter; keep the branch only when you must swap many.
