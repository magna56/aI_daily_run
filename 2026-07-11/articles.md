# Further Reading: LUMI & the Prediction–Compression Duality

## Papers

### [LUMI: Tokenizer-Agnostic LLM-Based Lossless Image Compression](https://arxiv.org/abs/2607.08221)
**Published**: July 2026 (arXiv:2607.08221)
> The primary source. Replaces text-tokenizer "pixel-as-text" schemes with a trainable pixel-embedding module, intra-patch positional encoding, and a 256-way prediction head over a *frozen* LLaMA/Qwen/Gemma backbone. Only the thin adapters train, so the same interface ports across model families. Evaluated on natural, medical, and remote-sensing images.

### [Language Modeling Is Compression](https://arxiv.org/abs/2309.10668)
**Authors**: Delétang et al. (DeepMind) | **Published**: Sept 2023
> The foundational result LUMI operationalizes. Proves predictors and lossless compressors are formally equivalent, then shows Chinchilla-70B compresses ImageNet patches to **43.4%** (PNG: 58.5%) and LibriSpeech audio to **16.4%** (FLAC: 30.3%) — a text-trained model beating domain-specific codecs. Read this first if the duality feels abstract.

### [DeepMind: A Language Model as a Compressor (blog/context)](https://arxiv.org/abs/2309.10668)
**Published**: 2023
> Same team's framing of "compression = intelligence" and how scaling laws, tokenization, and in-context learning all look different through a compression lens. Useful for the "why should I care as an engineer" angle.

## Articles & Background

### 1. [Arithmetic Coding, explained (Mark Nelson)](https://marknelson.us/posts/2014/10/19/data-compression-with-arithmetic-coding.html)
**Source**: marknelson.us | **Read time**: ~20 min
> The clearest walkthrough of the arithmetic/range coder used in `code_example.py`, including the E1/E2/E3 renormalization and underflow (pending-bits) handling. Read this to understand *why* the coder in the demo hits the Shannon bound to within ~1 bit for the whole message.

### 2. [Shannon source coding & entropy (Wikipedia)](https://en.wikipedia.org/wiki/Shannon%27s_source_coding_theorem)
**Source**: Wikipedia | **Read time**: ~8 min
> Refresher on why `-log2 p(symbol)` is the optimal code length and why the total file size equals the model's cross-entropy on the stream. This is the identity the whole approach rests on.

### 3. [Hugging Face + Cerebras: Gemma 4 for real-time voice AI](https://huggingface.co/blog)
**Source**: Hugging Face Blog | **Date**: July 1, 2026 | **Read time**: ~6 min
> Adjacent multimodal-engineering read from the same week — the serving/latency side of multimodal LLMs, a useful contrast to LUMI's compute-heavy per-pixel forward passes.

## The one-line mental model
Your LLM's cross-entropy (in bits) on any byte stream *is* that stream's compressed size under arithmetic coding. Sampling and compression are duals of the same distribution: text-gen samples it, LUMI encodes the known pixel against it.
