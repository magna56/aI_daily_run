# Further Reading: The Coding-Agent Harness

## Primary Sources

### 1. [Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents)
**Source**: Anthropic Engineering | **Date**: December 19, 2024 | **Read time**: ~15 min
> The canonical "it's a loop, not a framework" post: gather context, take action, check a stop condition. Introduces the agent-computer interface — tool names and errors as a public API — which is the design of Claude Code's built-ins and of every MCP server you add.

### 2. [How Claude Code works](https://docs.anthropic.com/en/docs/claude-code/how-claude-code-works)
**Source**: Claude Code docs | **Date**: current | **Read time**: ~10 min
> The product's own description of the host: context window contents, the agentic loop, and where tools, memory, and compact sit. Read this as the map of the chassis, not as marketing.

### 3. [Configure permissions](https://docs.anthropic.com/en/docs/claude-code/permissions)
**Source**: Claude Code docs | **Date**: current | **Read time**: ~12 min
> Allow / ask / deny as a real policy: precedence, workspace trust, what "Yes, and don't ask again" writes, and why a project `ask` can still beat a local `allow`. This is the capability system the visualizer is modeling.

## Background & Ecosystem

### 4. [Sub-agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
**Source**: Claude Code docs | **Date**: current | **Read time**: ~10 min
> Isolated vs forked children, what a child loads at startup, and why big reads belong in another transcript. Pair with the troubleshooting note on autocompact thrash — the fix is often "spawn a child," not "buy a bigger window."

### 5. [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
**Source**: Anthropic Engineering | **Date**: 2025 | **Read time**: ~15 min
> The sentence this capstone leans on: evaluating "an agent" means evaluating the harness and the model together. Claude Code is named as a flexible harness; the Agent SDK is that harness without the TUI.

## The one-line takeaway
Claude Code and Cursor are not a smarter weight file — they are a permissioned tool loop with children and a garbage collector for the transcript. Change those, and you change the product.
