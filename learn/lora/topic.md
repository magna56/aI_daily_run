# How LoRA Works

**Category**: Hands-on Techniques
**Tags**: fine-tuning, training, cost
**Date**: 2026-08-23
**Level**: Building
**For**: How models work
**Hook**: Freeze the huge weight table and train two thin matrices you can merge back in.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

You have a giant printed dictionary. Rewriting every page to teach it your company's slang would take a truck of ink. Instead you slip two skinny bookmarks in each chapter: one says "look up this short code," the other says "write the new meaning." The dictionary stays put. The bookmarks are tiny. When you are done teaching, you can stamp the bookmarks into the pages and throw the bookmarks away.

## The Problem

Full fine-tuning updates every weight. A 7B model is billions of numbers. You need the VRAM, the checkpoint disk, and a merge story for every task you care about. Most teams do not have that, so they either skip adaptation or rent a cluster they cannot explain on Monday. The adapter idea is the other door: keep the pretrained matrix frozen and learn a small update that is cheap to store, swap, and serve.

## For a Software Engineer

Think of a frozen `W` as a compiled library you do not relink. LoRA adds `ΔW = B A` where `A` is `r × k` and `B` is `d × r`, with rank `r` far smaller than `d` or `k`. Trainable count is `2 · d · r` instead of `d · k`. On a 4096-wide layer, `r = 8` is 65,536 numbers instead of 16.7 million.

At serve time you fold: `W' = W + (α / r) B A`. No extra latency if you merge. If you keep the branch (many adapters, one base), the extra matmuls are the cost of swapping personalities without shipping 14GB per customer.

Monday morning: when someone says "we fine-tuned it," ask whether they trained `W` or an adapter. Ask the rank. Ask whether it is merged. Those three answers decide VRAM, download size, and whether two tasks can share one base.

## What This Means for You

**When this matters**: you are about to "fine-tune" a model on tickets, a style guide, or a tool schema.

**How it affects you**: a LoRA file is megabytes. A full checkpoint is the whole model again. Rank that is too small cannot express the change. Rank that is too large wastes the point of the adapter.

**What to do about it**: start at `r = 8` or `16` on attention projections. Measure the task. Raise rank only if the eval is still climbing. Merge before you serve a single adapter. Keep the branch only when you must hot-swap many adapters on one base.

## What It Is

LoRA (Low-Rank Adaptation) freezes pretrained weights `W` and learns a low-rank update. `A` is initialized like a normal linear layer. `B` starts at zero so `ΔW` is zero at step 0 — training begins from the pretrained model, not from a random kick. A scalar `α / r` keeps the update from exploding when you change rank.

You choose which modules get adapters. The original paper put them on query and value projections. Production PEFT stacks often hit more linears. Each choice is a VRAM and quality knob, not a moral stance.

## Why It Matters

This is why every host lets you upload a small adapter. It is why "we have a model per customer" can mean "one base, many LoRAs." It is why QLoRA can fine-tune a large model on one GPU: the base sits in 4-bit, the adapters stay in higher precision.

It is also why a LoRA is not a new brain. It can steer tone, format, and a narrow skill. It cannot cheaply install a fact the base never saw. If the eval needs new knowledge, retrieve it. If it needs a new voice, an adapter is the right tool.

## Key Technical Details

**Background first.** A *weight matrix* `W` maps an input vector of size `k` to an output of size `d`. *Rank* is how many independent directions an update can move. *Merge* means adding `ΔW` into `W` so inference looks like a normal linear layer.

- **Trainable size is `2dr`, not `d²`.** That is the whole budget story.
- **`B = 0` at init.** The first forward pass matches the base model.
- **`α / r` is the volume knob.** Changing `r` without retuning `α` changes the effective step size.
- **Merge is free latency.** Multi-adapter serving is not — you pay the extra multiply or a more clever kernel.
- **Where you attach it matters.** Query/value is the classic cheap default. MLP adapters cost more and sometimes help more.

## How It Connects to What You Know

A Git patch is a small delta on a frozen tree. LoRA is a patch on a matrix. A plugin that does not fork the host app is the product version of the same idea. You already accept that a 200-line adapter can change a 2-million-line product. This is that, for weights.

Next: [How Self-Attention Works](#learn/self-attention) — the layer LoRA most often sits on.

## Try It Yourself

`code_example.py` builds a tiny frozen `W` and a LoRA pair. It prints parameter counts as you change rank, shows that `B = 0` leaves the output unchanged, then trains `A` and `B` on one linear map so you can see the residual shrink.

## Glossary

- **LoRA** — low-rank adaptation: freeze `W`, train `B A`.
- **Rank (`r`)** — width of the skinny matrices; the capacity knob.
- **Adapter** — the trainable pair (and any scaling) you save instead of `W`.
- **Merge** — bake `ΔW` into `W` for single-adapter serving.
- **PEFT** — parameter-efficient fine-tuning; LoRA is the common instance.
- **QLoRA** — LoRA on a quantized (often 4-bit) frozen base.
- **α (alpha)** — scaling numerator; `α / r` multiplies the update.
