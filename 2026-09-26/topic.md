# How to Run a Quantized Model Without Expanding It First

**Category**: AI Hardware for Engineers
**Tags**: quantization, inference-serving, production
**Date**: 2026-09-26
**Level**: Building
**For**: Shipping AI
**Hook**: A four-billion-parameter model is under three gigabytes on disk and over eight once it is unpacked to run, and until now you needed room for the second number.
**Engineer's view**: This is streaming a tar instead of extracting it. You wrote a job that downloaded an archive, unpacked it, read one member and deleted the rest — then the archive outgrew the disk. You fixed it by reading members out of the stream. The unpacked form was never what you needed.
**TLDR**: Quantized weights used to be expanded back to full precision before the first multiply, so the file size was never the memory you needed. The kernels now read the packed bytes directly and the expanded tensor is never built.
**Time to read**: ~11 minutes

## Explain Like I'm 5

You want one recipe from an enormous cookbook, and the cookbook arrives in a box, flat-packed.

The old way was to assemble the whole thing on your desk first. Every page, every chapter, just to read one. If your desk was small, you were stuck before you started.

The new way is to pull out one page at a time, read it, and slide it back. You still read the same words in the same order.

The difference is that now the desk only has to hold a page.

## The Problem

You have shipped this before, and it had nothing to do with AI.

A job downloaded a compressed archive, extracted it to a scratch directory, read one file out of it, and deleted the rest. It worked for a year. Then the archive grew past the size of the disk and the job started failing on a machine nobody had touched.

The fix was not a bigger disk.

You changed it to read the member straight out of the stream, never writing the whole thing down. The data was identical. What changed was the peak — the most you had to hold at once.

Now the same shape, with model weights.

A quantized checkpoint stores **quantized weights** in small blocks, each carrying its own scale, at four bits per weight. Qwen3.5-4B at Q4_K_M is 2.74 GB. You download it, it fits comfortably, and then loading it needs **8.42 GB**, because the old read path expanded every block back to sixteen-bit floats before the first multiply could happen.

So the file you could fit was never the thing that had to fit. The expanded tensor was, and it is roughly three times larger.

So the fix, which Hugging Face shipped into Transformers this week: read the packed bytes directly. Kernels from ggml take the quantized blocks as they are, unpack one block at a time into a small reusable buffer, and multiply. The full tensor is never built, so the peak is a block rather than a model.

```figure
{ "kind": "system",
  "title": "The whole argument: what you have to hold at once",
  "lanes": [
    { "t": "on disk", "nodes": [
        { "id": "file", "t": "2.74 GB packed", "s": "ok" } ] },
    { "t": "the read path", "nodes": [
        { "id": "old", "t": "expand every block first", "s": "bad" },
        { "id": "new", "t": "unpack one block at a time", "s": "ok" } ] },
    { "t": "peak you must fit", "nodes": [
        { "id": "big", "t": "8.42 GB", "s": "bad" },
        { "id": "small", "t": "one block", "s": "ok" } ] }
  ],
  "edges": [
    { "from": "file", "to": "old", "s": "bad" },
    { "from": "file", "to": "new", "s": "ok" },
    { "from": "old", "to": "big", "t": "3x the file", "s": "bad" },
    { "from": "new", "to": "small", "t": "does not grow with the model", "s": "ok" } ],
  "note": "Same weights, same arithmetic, same answer. Only the peak changed." }
```

## The Fix: Read the Packed Bytes, and Expand Only When You Have To

Two paths over one file, and knowing which one you are on decides what hardware you need.

### Why doesn't the multiply need the whole tensor?

Because a matmul consumes weights in order and never looks back. Nothing in it requires every weight to exist at the same moment — that was a property of how the loader worked, not of the arithmetic.

So the kernel walks blocks, unpacks each into a buffer it reuses, accumulates, and moves on. Run the Code tab: over the same 64x512 matrix, dequantizing first holds **131,072 bytes** at its peak and the packed path holds **128** — the size of one block, which does not grow with the model. The two outputs agree to within 2.66e-15, because they are doing identical arithmetic in a different order of materialization.

### What does that actually buy on a machine you own?

Room for a model roughly three and a half times larger. At four bits plus scales you get about 0.56 bytes per parameter against two for bfloat16, so a 16 GB laptop holds about a 6B model expanded, or about **21B** packed.

That is the entire reason people run models locally at all, and it is why the local ecosystem standardized on this format years before the research stack could read it.

### When do you still want them expanded?

When you are training. Gradients need real floats, so fine-tuning has to **dequantize** first, and Transformers exposes that as a flag rather than a different loader. Inference reads packed; training asks for dequantized. Choosing the wrong one is a memory error rather than a wrong answer, which is the good kind of mistake.

## What This Means for You

**When this matters.** Any time you are deciding whether a model fits on hardware you already have — a laptop, a small cloud box, a CI runner — and any time you are choosing between running something locally and paying for an API.

**How it affects you.** Your sizing arithmetic was probably wrong in a way that made you buy or rent more than you needed. If you estimated from the download size you were too optimistic, and if you estimated from parameter count times two bytes you were too pessimistic for anything quantized. Neither number was the peak.

**What to do about it.** Start here, and it costs one command: take a model you already decided was too big for your machine and check its quantized file size against the table in the Code tab. A 32 GB box that you thought topped out around 12B parameters holds something closer to 40B once the weights stay packed. That changes which experiments are free.

Then, when you actually load one, be deliberate about which path you are on. If you are running inference, do nothing and you get the packed path. If you are fine-tuning, ask for dequantization explicitly, and size the machine for the expanded number rather than the file.

## Implementing It

**The change.** Three roles, and the third is the one that will surprise a team.

**Role 1 — whoever loads the model for inference.** Point at the file inside the repository. There is no conversion step and no second runtime.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id, filename = "unsloth/Qwen3.5-4B-GGUF", "Qwen3.5-4B-Q4_K_M.gguf"
tokenizer = AutoTokenizer.from_pretrained(model_id, gguf_file=filename)
model = AutoModelForCausalLM.from_pretrained(model_id, gguf_file=filename)
```

The tokenizer comes from the same file. That is a property of the format rather than of this integration: a quantized checkpoint packs weights, tokenizer and an optional chat template together, which is why a single path is enough.

Nothing here converts anything. The bytes on disk are the bytes the kernel reads, so there is no intermediate artifact to cache, invalidate or get out of step with the original download.

**Role 2 — whoever fine-tunes it.** Gradients need real floats, so this is the one case where you ask for the expansion.

```python
from transformers import AutoModelForCausalLM, GgufConfig
import torch

model = AutoModelForCausalLM.from_pretrained(
    model_id, gguf_file=filename,
    quantization_config=GgufConfig(dequantize=True),   # 2.74 GB becomes 8.42 GB
    dtype=torch.bfloat16,
)
```

**Role 3 — whoever decides where it runs.** The packed path is **Metal only** today. On anything else the loader falls back to dequantizing, silently and correctly, and your memory estimate is suddenly three times too small.

```bash
pip install -U "git+https://github.com/huggingface/transformers.git" kernels
```

That means a laptop and a Linux CI runner loading the same file have different memory profiles. Size the runner for the expanded number until the packed path reaches your platform, or pin the job to the machine that supports it.

**How you know it worked.** Two checks, and the second is the one that catches the fallback.

First, measure resident memory after loading and before generating. It should sit near the file size plus activations, not near three times the file size. If it lands at the larger number on a machine you expected to be fast, you are on the dequantized path.

Second, compare output against the same prompt run through llama.cpp. They should agree closely, because the kernels are the same ggml kernels. A large divergence means something dequantized and re-rounded on the way through, which is a correctness signal rather than a performance one.

## When Packed Weights Are the Wrong Tool

Architecture coverage is narrow. Today it is Qwen3.5 dense and mixture-of-experts checkpoints, plus compatible Qwen3.8 ones, and the maintainers say so plainly rather than burying it. If your model is not on that list, this changes nothing for you yet.

Batching is the weaker half. Unpadded inputs benefit from the mask optimizations, padded batches measurably degrade, and batched generation is named as needing work. This is an interactive, one-request-at-a-time design, and serving many concurrent users is what vLLM and llama.cpp servers are already for.

And quantization itself is not free. Four bits with per-block scales is a good trade, not a lossless one, and the honest comparison is against the same model at higher precision rather than against nothing. Q4_K_M is the practical starting point precisely because it is a compromise.

Three questions before relying on it:

Is my model actually in the supported set, or am I planning around a roadmap?

Will this run on Metal in production, or only on the laptop I tested it on?

Am I serving one request at a time, or many?

## Glossary

- **quantized weights** — model weights stored at reduced precision, here four bits with a scale per block.
- **Block** — a small run of weights sharing one scale, so an outlier cannot flatten the rest of the tensor.
- **dequantize** — expand packed weights back to full-precision floats, which training needs and inference no longer does.
- **Peak** — the most memory held at one moment, which decides whether a model loads at all.
- **Metal** — Apple's GPU interface, the only platform the packed read path supports today.
- **Kernels** — the low-level routines that do the arithmetic, here reading packed bytes without unpacking the tensor.
