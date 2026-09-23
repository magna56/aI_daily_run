# Further Reading: How to Cap What a Reasoning Model Spends on One Request

## Articles

### 1. [Reasoning — OpenAI API docs](https://developers.openai.com/api/docs/guides/reasoning)
**Source**: OpenAI | **Date**: September 2026 | **Read time**: ~10 min
> Read this first if you want the failure stated plainly by the people who built it. It documents `reasoning.effort` from none through max, and then the part that matters: hitting `max_output_tokens` returns `status: "incomplete"` and can happen during reasoning, before any visible output, while still costing you. Their advice to reserve 25,000 tokens when starting out is a useful sanity check against whatever number you were about to type.

### 2. [Extended thinking — Claude docs](https://platform.claude.com/docs/en/docs/build-with-claude/extended-thinking)
**Source**: Anthropic | **Date**: September 2026 | **Read time**: ~15 min
> The migration page, and required reading if you set `budget_tokens` once and moved on: it is deprecated on the 4.6 models and returns a 400 on 4.7 and later. Two things here are worth the visit on their own — the admission that the budget was always "a target rather than a strict cap", and a worked prompt-caching example showing a budget change invalidating 1,370 cached tokens on the third request.

### 3. [Thinking — Gemini API docs](https://ai.google.dev/gemini-api/docs/thinking)
**Source**: Google | **Date**: September 2026 | **Read time**: ~8 min
> The third vendor, and the clearest statement of the billing rule the other two leave implicit: you pay for the full thought tokens the model generates even though only a summary is returned. Also lists `thinking_level` support per model, which is the table to check before you assume a level exists on the model you are actually calling.

### 4. [Prompt cache diagnostics](https://developers.openai.com/api/docs/changelog)
**Source**: OpenAI changelog | **Date**: 2026-09-08 | **Read time**: ~3 min
> Skip unless you are tuning caps per request, in which case read it before you do. Cache-reuse diagnostics went generally available this month, and a per-request thinking configuration is one of the easier ways to destroy your own cache hit rate without noticing. This is the tool that tells you it happened.
