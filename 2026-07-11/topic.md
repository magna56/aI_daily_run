# How an LLM Compresses Images Without Its Tokenizer

**Category**: Multimodal Engineering
**Date**: 2026-07-11
**Level**: Deeper
**For**: How models work
**Hook**: A model that predicts the next pixel well is already a compressor.
**Time to read**: ~10 minutes
**Paper**: [arXiv:2607.08221](https://arxiv.org/abs/2607.08221) — LUMI (July 2026)

## What It Is

LUMI is a lossless image compressor built on top of a **frozen** LLM backbone (LLaMA / Qwen / Gemma). The insight it exploits is old and exact: **a good next-symbol predictor *is* a good lossless compressor.** If your model assigns probability `p` to the symbol that actually occurs, an arithmetic coder can encode that symbol in `-log2(p)` bits. A model that predicts pixels well therefore compresses images well — with *zero* loss, because the decoder re-runs the identical model to recover the exact same probabilities.

The problem with naively pointing an LLM at an image is the **tokenizer**. Text tokenizers (BPE) were never designed for pixels: byte-pair merges learned on English prose fragment pixel streams in arbitrary ways, destroy 2D spatial locality, and differ across model families so you can't swap backbones. LUMI's contribution is to **throw the text tokenizer away entirely** for the image path. Instead of "pixel → text token → embedding", it uses a small trainable **pixel embedding module** that maps raw intensity + channel info directly into the LLM's continuous embedding space, adds **intra-patch position encoding** to preserve 2D structure, and ends in a **256-way prediction head** producing a probability distribution over the native pixel alphabet (0–255). Only these thin adapter layers are trained; the transformer stack stays frozen. That's what "tokenizer-agnostic" means: the same interface bolts onto any backbone regardless of its native tokenizer.

At compression time the frozen model emits, pixel by pixel, a 256-way distribution; that distribution drives an arithmetic (range) coder. At decompression time the decoder feeds already-decoded pixels back in, reproduces the identical distributions, and inverts the arithmetic coder. Evaluated across natural, medical, and remote-sensing images, LUMI shows the approach generalizes cross-domain from a single frozen backbone.

## Why It Matters

- **It operationalizes prediction=compression for a real modality.** DeepMind's 2023 "Language Modeling Is Compression" already showed Chinchilla-70B compresses ImageNet patches to **43.4%** (vs PNG's 58.5%) and LibriSpeech to **16.4%** (vs FLAC's 30.3%) — a text model beating domain-specific codecs. LUMI turns that curiosity into a *reusable, backbone-portable* engineering component.
- **Frozen backbone = cheap to adopt.** You train a handful of adapter params, not a 7B model. The same recipe rides along whenever the base model improves.
- **Lossless matters in regulated/scientific domains.** Medical imaging and remote sensing (and, by analogy, any archival financial/document scan) can't tolerate lossy artifacts. A learned lossless codec that adapts to *your* data distribution can beat general-purpose PNG/FLIF/JPEG-XL.
- **It's a clean mental model for anyone shipping LLMs.** Understanding that your model's log-loss on a token stream *is literally its compressed size in bits* reframes evals, tokenization choices, and even "which model is better" as compression questions.

## Key Technical Details

- **Compression identity**: ideal code length for a symbol `s` under model `P` is `-log2 P(s)` bits (Shannon). Total file ≈ cross-entropy of the model on the pixel stream.
- **Arithmetic coding** achieves that bound to within ~1 bit for the *whole* message (not per-symbol rounding like Huffman), which is why it pairs perfectly with a probabilistic model.
- **Losslessness is free** given determinism: encoder and decoder run the *same frozen model* on the *same already-seen context*, so they compute identical distributions. No probability tables are transmitted.
- **Pixel embedding module** replaces BPE: raw intensity/channel → continuous embedding; **intra-patch positional encoding** restores 2D locality the LLM's 1D positions would lose.
- **256-way head** predicts over the native byte alphabet — no vocabulary mismatch, no out-of-distribution "text" tokens.
- **Only adapters train; backbone frozen** → tokenizer-agnostic, portable across LLaMA/Qwen/Gemma.
- **Cost caveat**: a transformer forward pass *per pixel* (or per small patch) is orders of magnitude slower than PNG. This is the central limitation — great ratios, poor throughput. Batching, patch-parallel prediction, and KV-cache reuse are the levers.

## How It Connects to What You Know

You already know an autoregressive LM outputs `P(next | context)` and is trained to minimize cross-entropy. That cross-entropy, in bits, **is** the compressed length under arithmetic coding — the training objective and the compression objective are the same number. LUMI is just: keep the transformer, swap the *front* (pixel embedding instead of BPE) and the *back* (256-way head instead of a 50k vocab head), and route the output logits into a range coder instead of a sampler. It's the same decode loop you use for text generation, except instead of *sampling* from the distribution you *encode the known symbol against* it. Sampling and arithmetic-coding are duals of the same distribution.

## Try It Yourself

`code_example.py` implements a **complete lossless arithmetic codec in pure Python** and drives it with a tiny adaptive pixel predictor — no ML libraries, no GPU. It compresses a synthetic "image", verifies byte-exact round-trip, and shows: (1) file size tracks `-Σ log2 p` almost exactly, (2) a *better* predictor produces a *smaller* file with the same coder, and (3) how a frozen-model + arithmetic-coder decode loop mirrors LLM text generation.
