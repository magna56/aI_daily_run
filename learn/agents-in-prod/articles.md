# Further Reading: The Loop Is Not the Product

## Primary Sources

### 1. [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
**Source**: anthropic.com | **Read time**: ~20 min
> Loops, tools, and when a workflow beats an agent. Production starts where the demo's while-loop ends.

### 2. [Prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
**Source**: docs.anthropic.com | **Read time**: ~10 min
> A stable prefix is a bill. A timestamp at the top of the system prompt is a cache miss.

### 3. [Deterministic verification gates](https://theaicommit.com/#2026-07-09)
**Source**: theaicommit.com | **Read time**: ~10 min
> Wrap every tool in a check the model cannot talk past. The verifier in this primer is that habit in twenty lines.

## Background & Ecosystem

### 4. [Model Context Protocol](https://modelcontextprotocol.io/)
**Source**: modelcontextprotocol.io | **Read time**: ~15 min
> Tools as a typed interface. Still needs allowlists, timeouts, and tenant isolation.

### 5. [The agent loop](https://theaicommit.com/#learn/the-agent-loop)
**Source**: theaicommit.com | **Read time**: ~10 min
> Day-2 lesson: the loop itself. This primer is the cache, the bill, and the latch.

## The one-line takeaway
The loop is cheap. Freeze the prefix, cap the steps, and verify writes outside the model.
