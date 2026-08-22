# Further Reading: Building Coding Agents & The Tool Schema Trap

## Articles

### 1. [llm-coding-agent 0.1a0](https://simonwillison.net/2026/Jul/2/llm-coding-agent/)
**Source**: Simon Willison's Weblog | **Date**: July 2, 2026 | **Read time**: ~8 min
> Simon ships a minimal Claude Code clone as a Python library built on his LLM framework.
> The entire agent — 6 tools, approval gates, sandbox, CLI + Python API — was built via
> LLM-assisted TDD in an afternoon. Demonstrates that the agent loop is commodity code;
> the value is in tool design and safety boundaries.

### 2. [Better Models: Worse Tools](https://simonwillison.net/2026/Jul/4/better-models-worse-tools/)
**Source**: Simon Willison's Weblog | **Date**: July 4, 2026 | **Read time**: ~5 min
> Armin Ronacher discovers that newer Claude models (Opus 4.8, Sonnet 5) are worse at
> following third-party tool schemas because Anthropic's RL training optimizes for Claude
> Code's specific edit tool. Models inject invented fields from their training into
> non-matching schemas — a new form of behavioral vendor lock-in.

### 3. [llm-coding-agent on GitHub](https://github.com/simonw/llm-coding-agent)
**Source**: GitHub | **Date**: July 2, 2026 | **Read time**: ~10 min (reading source)
> Full source code of the coding agent. The `tools.py` module shows clean tool implementations
> with path sandboxing, and `agent.py` shows the chain-based dispatch loop with approval
> tiers. Good reference architecture for building your own agent tools.

### 4. [Pi Coding Harness](https://github.com/arminronacher/pi)
**Source**: GitHub (Armin Ronacher) | **Date**: 2026 | **Read time**: ~15 min
> The third-party coding harness that surfaced the tool schema compatibility issue.
> Uses a batched edits array design (different from Claude Code's flat old_string/new_string),
> which triggers the RL-trained schema leak in newer Claude models.

### 5. [Datasette Agent](https://agent.datasette.io)
**Source**: Datasette Project | **Date**: May 21, 2026 | **Read time**: ~5 min
> An agent that executes read-only SQL queries against databases, with system prompts
> being optimized using DSPy. Shows a different tool design philosophy — read-only tools
> with no mutation risk, where the agent's value is in query construction rather than
> code editing.

## Key Concepts to Search Next

- **Tool-use RL training** — how providers fine-tune models for their own tool schemas
- **apply_patch vs search-and-replace** — the two dominant edit tool paradigms
- **MCP tool schema conventions** — emerging standards for cross-model tool compatibility
- **Agent sandboxing patterns** — how different frameworks prevent sandbox escape
