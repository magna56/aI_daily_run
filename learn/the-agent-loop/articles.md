# Further Reading: How the Agent Loop Works

## Articles

### 1. [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
**Source**: anthropic.com | **Read time**: ~20 min
> The "start with a loop" essay: most agent products are a model calling tools in a cycle, plus the engineering around permissions and evals. Use this when you are tempted to replace observe / think / act with an orchestration graph.

### 2. [Tools](https://modelcontextprotocol.io/docs/concepts/tools)
**Source**: modelcontextprotocol.io | **Read time**: ~8 min
> MCP's tool surface: names, descriptions, JSON Schema arguments, `tools/list` and `tools/call`. The HTTP-for-tools analogy in the protocol's own words — discovery is a catalog, invocation is a named call.

### 3. [Specification](https://modelcontextprotocol.io/specification/2025-11-25)
**Source**: modelcontextprotocol.io | **Read time**: ~20 min
> The normative JSON-RPC contract. Skim the lifecycle and tools chapters; you do not need the whole document to understand that a server is a process that lists and runs functions.

### 4. [Release: llm-coding-agent 0.1a0](https://simonwillison.net/2026/Jul/2/llm-coding-agent/)
**Source**: simonwillison.net | **Read time**: ~8 min
> A coding-agent loop in ~500 lines: `read_file`, `edit_file`, `execute_command`, approval gates. Proof the loop is commodity and the tool names are the interesting API.

### 5. [Building Coding Agents from Scratch — and the Tool Schema Trap](https://theaicommit.com/2026-07-05/)
**Source**: theaicommit.com | **Read time**: ~10 min
> The daily case study this lesson points at: newer models leak Claude Code's edit schema into third-party tools. Read after you understand the loop, when you are naming your own tools.

## The one-line takeaway
The agent is a loop. Tool names are the API. MCP is how that API travels across a process boundary.
