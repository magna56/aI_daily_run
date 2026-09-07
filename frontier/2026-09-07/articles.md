# Further Reading: Why Your KV Cache Eviction Policy Is Doing Nothing

## Articles

### 1. [Random Attention: Rethinking KV Cache Eviction for Efficient Reasoning](https://arxiv.org/abs/2609.03430)
**Source**: Salesforce AI Research (arXiv:2609.03430) | **Date**: 3 September 2026 | **Read time**: ~35 min
> The paper this session is built on, and the two tables worth your time are the prompt-protection
> ablation and the planted-fact probe. The first shows SnapKV gaining up to 22.5 points from a rule
> it never wrote down; the second shows why a coin flip is enough once that rule is explicit. Read
> the ablation first — it is the argument, and the method is three lines underneath it.

### 2. [The Random-Attention implementation](https://github.com/SalesforceAIResearch/Random-Attention)
**Source**: Salesforce AI Research on GitHub | **Date**: current | **Read time**: ~20 min
> The policy ships as `random_pp` and every baseline in the paper is here as an eviction mode, which
> makes this the cheapest way to A/B them against each other. Start in `kvcompress/engine/cache_utils.py`,
> where the whole policy is a keep-set built from the prefill range plus a per-head sample. Worth
> opening even if you never run it, because the code is shorter than the description of it.

### 3. [SnapKV: LLM Knows What You are Looking for Before Generation](https://arxiv.org/abs/2404.14469)
**Source**: University of Illinois Urbana-Champaign and Cohere (arXiv:2404.14469) | **Date**: April 2024 | **Read time**: ~25 min
> The method that started the ranking race, and the one that gains most from the pin. Read it for
> the honest reason its score works — attention from the last few queries is a good proxy for what
> the model is using *now* — and then notice that "now" drifts away from the prompt as generation
> runs. That drift is the entire failure the newer paper isolates.

### 4. [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180)
**Source**: UC Berkeley (arXiv:2309.06180) — the vLLM paper | **Date**: September 2023 | **Read time**: ~30 min
> Background for the throughput half, and the reason the 32-43% number is measured the way it is.
> PagedAttention explains why cache capacity converts into concurrent requests rather than into
> latency, which is what makes an eviction policy a serving decision instead of a quality one. Read
> it if the capacity-planning paragraph in this session felt like it skipped a step.

## Papers

### [Random Attention: Rethinking KV Cache Eviction for Efficient Reasoning](https://arxiv.org/abs/2609.03430)
**Authors**: Heng Wang, Jielin Qiu, Wenting Zhao, Cheng Qian, Liangwei Yang, Jiawei Han, Heng Ji, Silvio Savarese, Shelby Heinecke, Huan Wang | **Institution**: Salesforce AI Research | **Date**: 3 September 2026
> Evaluated on Qwen3-4B, Qwen3-14B, Qwen3-32B and Phi-4-reasoning across MATH500, GPQA-Diamond,
> AIME 2025 and 2026, HMMT and LiveCodeBench-v6, at per-task budgets from 1024 to 4096 positions.
> The serving numbers come from vLLM on an H200 with 32k-token generations and 128 concurrent
> requests. The claim to hold onto is narrow and well supported: once the prompt is protected, the
> selection signal contributes almost nothing.
