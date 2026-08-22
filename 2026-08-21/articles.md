# Further Reading: Pixels Are Not Tokens — Fixed Tiling vs. Native Resolution

## Articles

### 1. [OpenAI Vision Guide — Image Token Cost Calculation](https://developers.openai.com/api/docs/guides/images-vision)
**Source**: OpenAI Developer Docs | **Date**: current | **Read time**: ~8 min
> The primary source for the tiling formula: scale to fit 2048×2048, scale shortest side to 768,
> count 512px squares, bill `base + per_tile × tiles`. Read the per-model table carefully —
> GPT-4o-mini's 2833 + 5667 is a *different token unit*, not a pricing tier, so image cost does
> not scale from its text price the way you'd assume. This page is also where the ~93 dpi
> ceiling hides: it's implied by step 2 and stated nowhere.

### 2. [Meet North Micro Vision: A 2.4B Native-Resolution Vision-Language Model](https://huggingface.co/blog/CohereLabs/meet-north-micro-vision-instruct)
**Source**: Cohere Labs / HF Blog | **Date**: Aug 2026 | **Read time**: ~7 min
> This month's clearest statement of the native-resolution thesis, with the design target written
> as a physical object: 1654×2339, "an A4 page at 200 dpi." Notable for C-RoPE (2D RoPE plus
> bilinearly interpolated learned 1D embeddings) to keep position encoding coherent when every
> input is a different shape, and for DeepStack projection — injecting patch embeddings from
> several encoder layers into corresponding *early LLM layers* rather than one flat input-side
> concat. DocVQA 0.921, InfoVQA 0.652 at 2.4B.

### 3. [Qwen2-VL in HF Transformers — processor and vision config](https://huggingface.co/docs/transformers/main/en/model_doc/qwen2_vl)
**Source**: Hugging Face Docs | **Date**: current | **Read time**: ~6 min
> Where the constants actually live: `patch_size=14`, `spatial_merge_size=2`,
> `temporal_patch_size=2`, `min_pixels=56²`, `max_pixels=28²·1280`. The docs spell out that "the
> 28 comes from the fact that the model uses a patch size of 14 and a temporal patch size of 2."
> This is also the origin of the `min_pixels = 256*28*28` snippet that costs 28× on small UI
> assets — worth reading in context so you can see it's presented as a document-quality tip, not
> a universal default.

### 4. [Up to 3.2x Faster Inference with LFM2.5-DSpark](https://huggingface.co/blog/LiquidAI/lfm25-dspark)
**Source**: Liquid AI / HF Blog | **Date**: Aug 20, 2026 | **Read time**: ~8 min
> The other half of the multimodal serving story, published the day before this session: ~328M
> draft models giving 2.67× mean speedup on LFM2.5-2.6B (323→864 tok/s on H100), 2.27× on an M4
> Max. Useful contrast — speculative decoding attacks the *decode* phase while everything in this
> session is about *prefill*. If your VLM workload is document-heavy, prefill dominates and
> DSpark-style wins will disappoint you; that asymmetry is the practical takeaway.

## Papers

### [Patch n' Pack: NaViT, a Vision Transformer for any Aspect Ratio and Resolution](https://arxiv.org/abs/2307.06304)
**Authors**: Dehghani, Mustafa, Hartwig, et al. (Google DeepMind) | **Published**: Jul 2023
> The origin of native resolution and the direct answer to the batching problem it creates:
> concatenate patches from *multiple differently-sized images* into one packed sequence, and use
> masked attention plus per-image masked pooling to prevent cross-image interaction. Read it as a
> systems paper — it's LLM sequence packing applied to a vision encoder, and it's why "variable
> length" is a solved training problem but still a live *serving* problem.

### [Qwen2-VL: Enhancing Vision-Language Model's Perception of the World at Any Resolution](https://arxiv.org/abs/2409.12191)
**Authors**: Wang, Bai, Tan, et al. (Alibaba) | **Published**: Sep 2024
> Introduces Naive Dynamic Resolution and M-RoPE (unified positional encoding across text, image,
> and video). Caveat worth knowing before you go looking: neither the paper abstract nor the Qwen
> blog specifies the `smart_resize` algorithm or the token-scaling formula — those live only in
> the processor code and the HF config docs. A good example of load-bearing behavior documented
> nowhere near the model card.

### [How Far Are We to GPT-4V? Closing the Gap with Commercial Multimodal Models (InternVL 1.5)](https://arxiv.org/abs/2404.16821)
**Authors**: Chen, Wang, Tian, et al. (Shanghai AI Lab) | **Published**: Apr 2024
> The open-source reference implementation of *adaptive* tiling — 1 to 40 tiles of 448×448 chosen
> by aspect-ratio match, plus a downscaled thumbnail for global context, supporting up to 4K
> input. Sits between the two families in this session: it keeps a grid but lets the grid shape
> follow the image, which recovers much of the aspect-ratio waste while keeping fixed-size tiles.

### [Cambrian-1: A Fully Open, Vision-Centric Exploration of Multimodal LLMs](https://arxiv.org/abs/2406.16860)
**Authors**: Tong, Brown, Wu, et al. (NYU) | **Published**: Jun 2024
> Evaluates 20+ vision encoders and introduces the Spatial Vision Aggregator, a spatially-aware
> connector that feeds high-resolution features to the LLM *without* proportional token inflation
> — the third option beyond "more tiles" and "more patches." The paper's broader argument is the
> one this session is an instance of: vision-side design choices are under-explored relative to
> the language side, and they're where the cost actually is.
