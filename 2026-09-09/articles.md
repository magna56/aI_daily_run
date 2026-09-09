# Further Reading: Why an Idle GPU Is the Wrong Place to Send a Request

## Articles

### 1. [vLLM x AgentX: Optimizing for Real-World Agentic Serving](https://vllm.ai/blog/2026-09-08-vllm-agentx)
**Source**: vLLM Team with Inferact | **Date**: 8 September 2026 | **Read time**: ~25 min
> The post this session is built on. Two sentences in it carry the argument — that load balance
> does not guarantee better performance, and that cache locality outweighs instantaneous load
> distribution — and everything else is the machinery that follows. The scheduling section has the
> `--long-prefill-token-threshold` result (up to 93% throughput, 2.3x P90 interactivity on
> DeepSeek V4 Pro). Read the hardware column before you borrow any number: twelve GB300s at 256
> concurrency is not your fleet.

### 2. [Serving Agentic Workloads at Scale with vLLM x Mooncake](https://vllm.ai/blog/2026-05-06-mooncake-store)
**Source**: vLLM Blog | **Date**: 6 May 2026 | **Read time**: ~20 min
> The background that makes the routing argument obvious rather than clever. It states the shape of
> agent traffic directly — massive shared prefixes, recomputed across turns — and then measures what
> a distributed KV store does about it. Read this first if "why is there anything to be local to"
> is still an open question for you.

### 3. [Automatic prefix caching](https://docs.vllm.ai/en/latest/design/prefix_caching.html)
**Source**: vLLM documentation | **Date**: current | **Read time**: ~15 min
> How the cache you are routing toward actually works: block-level hashing, when a prefix is reused,
> and crucially when it is evicted. Worth reading before you set a threshold, because the eviction
> policy is what decides whether a prefix survives the gap while a tool call runs — which is the
> difference between a warm replica and a replica that merely served you last time.

### 4. [Engine arguments](https://docs.vllm.ai/en/latest/configuration/engine_args.html)
**Source**: vLLM documentation | **Date**: current | **Read time**: ~10 min
> The reference for every flag in this session, and the place to check defaults before you copy a
> value out of a blog post. `--enable-prefix-caching`, `--long-prefill-token-threshold` and the
> scheduling knobs around them are all documented with their real defaults, which the write-ups
> tend to omit.

### 5. [Learning Agent Execution for KV-Cache Management in Agentic Serving](https://arxiv.org/html/2608.14624)
**Source**: arXiv | **Date**: August 2026 | **Read time**: ~30 min
> The research view of the same problem, and useful for one idea the engineering posts assume: that
> reactive cache management evicts exactly the prefix an agent is about to reuse, because the pause
> while a tool runs looks like idleness. Read it if you want the argument for *deliberate* retention
> rather than a bigger cache.
