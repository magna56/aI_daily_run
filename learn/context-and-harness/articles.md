# Further Reading: How the Chat Is Re-Read Every Turn

## Articles

### 1. [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
**Source**: anthropic.com | **Read time**: ~15 min
> Anthropic's harness-level write-up: context is a finite resource you curate each turn, not a pile you grow. Covers writing to memory, just-in-time retrieval, compaction, and isolating work so the main transcript stays small. The model-vs-harness split in essay form.

### 2. [Prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
**Source**: docs.anthropic.com | **Read time**: ~12 min
> The prefix-match contract: cache reads at 0.1×, writes at 1.25×, exact bytes, limited breakpoints. If `cache_read_input_tokens` is zero on repeated calls, something in the prefix is changing.

### 3. [Prompt caching with Claude](https://claude.com/blog/prompt-caching)
**Source**: claude.com | **Read time**: ~6 min
> The product announcement with the numbers that made caching default advice: long prompts dropping to a fraction of the cost and time-to-first-token when the prefix is stable. Pair with the docs above for the invalidation rules.

### 4. [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
**Source**: anthropic.com | **Read time**: ~20 min
> Why a straightforward loop plus good context beats an elaborate graph. Useful here for the reminder that the harness (tools, permissions, what you put in the prefix) is the product; the model is the function.

### 5. [Context Is a Budget You Re-Pay Every Turn](https://theaicommit.com/2026-08-22/)
**Source**: theaicommit.com | **Read time**: ~10 min
> The daily lab this lesson points at: lifetime cost of a token is size times remaining turns, cache thrashing loses to no cache, compaction is a cliff. Read after this page, not instead of it.

## The one-line takeaway
The model is stateless. The harness rebuilds the notebook, caches a stable prefix, and compact-rewrites when the window fills.
