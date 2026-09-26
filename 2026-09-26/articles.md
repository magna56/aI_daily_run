# Further Reading: How to Run a Quantized Model Without Expanding It First

## Articles

### 1. [Transformers now runs llama.cpp quants](https://huggingface.co/blog/transformers-llama-cpp-quants)
**Source**: Hugging Face | **Date**: 2026-09-22 | **Read time**: ~12 min
> The primary source. Read the kernel table rather than the benchmark charts: it names what each piece does — packed matrix operations, fused normalization, Metal flash attention, expert routing — which is the clearest available picture of what "reading the quantized weights directly" actually costs someone to build. The limitations section is short and unusually honest about batching and architecture coverage; read it before you plan around this.

### 2. [llama.cpp integration — Transformers docs](https://huggingface.co/docs/transformers/community_integrations/llama_cpp)
**Source**: Hugging Face | **Read time**: ~6 min
> The reference to keep open while you implement, and the place to check first when your load fails. The blog post explains why the integration exists; this says which arguments exist today. Between the two, this is the one that will still be correct in three months.

### 3. [unsloth/Qwen3.5-4B-GGUF](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF)
**Source**: Hugging Face | **Read time**: ~3 min
> The file the code in this session loads, and worth opening for the variant list alone. Seeing Q4_K_M, Q5_K_M and Q6_K side by side with their real sizes makes the trade concrete in a way a table in prose does not — you are choosing a row, and the row is a file you download.

### 4. [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp)
**Source**: ggml | **Read time**: as long as you like
> Where the kernels came from, and the one to open in an editor if you want to see what a quantization scheme looks like as code rather than as a format description. Read `ggml-quants.c` for the block layouts. Skip it entirely if you only need to load models — this is background, not a dependency of the article.
