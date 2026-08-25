# Further Reading: How Model Cascades Route Cheap Calls vs Frontier Calls

## Articles

### 1. [FrugalGPT explained: how LLM cascades cut cost](https://simonwillison.net/tags/llm-pricing/)
**Source**: Simon Willison's Weblog | **Date**: ongoing (2023–2026) | **Read time**: ~8 min
> Willison's running coverage of LLM pricing and the economics of routing. The
> best practical vantage point on how the July-2026 price cuts (DeepSeek Flash,
> GPT-5.6 Luna) change the calculus for "which model do I actually call."

### 2. [DeepSeek-V4-Flash-0731 & the sub-$0.30 tier](https://api-docs.deepseek.com/)
**Source**: DeepSeek API docs | **Date**: July 31, 2026 | **Read time**: ~5 min
> Reference pricing and the OpenAI-compatible chat-completions surface that makes
> a flash tier a drop-in first stage of a cascade. Note the shared tool-call
> schema — the reason a cascade can span providers behind one interface.

### 3. [Routing vs Cascading: two ways to pick a model](https://www.latent.space/)
**Source**: Latent Space | **Date**: 2026 | **Read time**: ~10 min
> The engineering distinction that matters: a pre-router chooses a model *before*
> seeing an answer (fast, blind); a cascade chooses *after* (accurate, sometimes
> double-pays). Covers hybrid designs and where each wins.

### 4. [The AI Productivity Gap](https://bjorg.bjornroche.com/management/ai-productivity-gap/)
**Source**: bjornroche.com (HN front page, Aug 2026) | **Read time**: ~6 min
> Not about cascades directly, but a useful counterweight: cheaper tokens don't
> automatically become productivity. Framing for *why* you optimize cost per
> resolved task, not cost per token.

## Papers

### [FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance](https://arxiv.org/abs/2305.05176)
**Authors**: Lingjiao Chen, Matei Zaharia, James Zou (Stanford) | **Published**: May 2023
> The origin of the LLM-cascade technique. Introduces prompt adaptation, LLM
> approximation, and the LLM cascade, and shows you can match GPT-4 accuracy at
> up to 98% lower cost — or beat it 4% at equal cost. The theory this session's
> code makes concrete; read §3 (cascade) and the scoring-function discussion.

### [AI migrated legacy COBOL programs to Java, bugs included](https://arxiv.org/abs/2607.28271)
**Published**: July 2026
> Tangential but timely: a reminder that cheap frontier-adjacent models still
> propagate subtle errors — exactly the queries a well-calibrated escalation gate
> should catch and reroute. Motivates investing in the *judge*, not just the model.
