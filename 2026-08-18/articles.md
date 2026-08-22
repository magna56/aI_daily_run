# Further Reading: Prefill-Pressure Adaptive Scheduling

## Papers

### [P-PAS: Prefill-Pressure Adaptive Scheduling for Long-Context LLM Serving](https://arxiv.org/abs/2608.15171)
**Author**: Timo Sämann | **Published**: August 15, 2026 | **arXiv**: 2608.15171 (cs.DC)
> The primary source. Shows vLLM's max-batched-tokens parameter has load-dependent effects — large
> budgets reduce latency under low demand, small budgets win under high scheduling pressure — so no
> static configuration is optimal. Proposes a controller that adapts the budget from concurrent
> prefill and decode state. Code and reproduction artifacts on GitHub. Read the artifact rather than
> the abstract: the public abstract omits the head-to-head TTFT/TPOT numbers.

### [Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve](https://arxiv.org/abs/2403.02310)
**Authors**: Agrawal, Kedia, Panwar, Mohan et al. (MSR India) | **Published**: March 2024
> The foundation P-PAS builds on, and the single most important serving paper to have read. Introduces
> chunked prefills and stall-free scheduling: split prompts into uniform chunks so new requests join a
> batch without pausing ongoing decodes. Reports 2.6x (Mistral-7B/A100), 3.7x (Yi-34B/2xA100) and 5.6x
> (Falcon-180B) serving capacity over vLLM. Read this first if the prefill/decode distinction isn't
> already second nature.

### [Beyond Binary Priorities: Multi-Tier SLA Scheduling for LLM Serving](https://arxiv.org/abs/2608.16336)
**Authors**: Anders Vestrum, Arya Raeesi, Hanna Roed | **Published**: August 17, 2026
> The adjacent production problem, published two days after P-PAS. Llumnix's high/normal priority split
> is too coarse for real deployments spanning latency-critical API calls to background batch. Extends it
> with per-tier headroom plus exponential decay and tier-aware dispatch. Notable practical finding: four
> tiers is the cost-effectiveness sweet spot, and the system scales to ten without tail-latency collapse.
> Up to 8.3x prefill and 3.1x P99 speedup over INFaaS, 46-68% cost-per-latency improvement.

### [Discovering KV Cache Eviction Policies via LLM-Guided Program Evolution](https://arxiv.org/abs/2608.14555)
**Published**: August 2026
> The other half of the serving-memory story. Rather than hand-designing an eviction heuristic, uses an
> LLM to evolve candidate eviction *programs*. Worth skimming as a counterpoint: P-PAS hand-designs its
> pressure signal, and this line of work suggests that signal could itself be searched.

## Practical

### [vLLM Optimization and Tuning Guide](https://docs.vllm.ai/en/latest/configuration/optimization.html)
**Source**: vLLM docs | **Read time**: ~8 min
> The official guidance P-PAS is arguing against — or rather, completing. Documents `max_num_batched_tokens`,
> `max_num_seqs`, and the TTFT/ITL inversion ("smaller values e.g. 2048 achieve better ITL... higher values
> achieve better TTFT"), and notes chunked prefill is on by default in vLLM V1 with decode prioritization.
> Read it alongside the paper to see exactly which sentence becomes load-dependent.

### [FlashQuant: Sparse-Dense Fusion for Memory-Efficient Outlier-Aware LLM Inference](https://arxiv.org/abs/2608.15531)
**Published**: August 2026
> Orthogonal lever on the same objective. Where P-PAS buys latency through scheduling, this buys it
> through memory footprint — relevant because a smaller KV/weight footprint raises the decode population
> your GPU can hold, which is precisely the variable that makes large token budgets expensive.
