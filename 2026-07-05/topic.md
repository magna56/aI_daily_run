# Building Coding Agents from Scratch — and the Tool Schema Trap

**Category**: Building Agents & MCP
**Date**: 2026-07-05
**Time to read**: ~10 minutes

## What It Is

The past week produced two developments that together tell a cohesive story about the state
of building coding agents in mid-2026. First, Simon Willison shipped `llm-coding-agent` (0.1a0),
a minimal open-source coding agent built on his `llm` library — essentially a Claude Code clone
in ~500 lines of Python. It exposes six tools (read_file, write_file, edit_file, search_files,
list_files, execute_command), a chain-based agent loop with approval gates, and both CLI and
Python API access. The entire thing was built using LLM-assisted red/green TDD in a single
afternoon.

Second, Armin Ronacher (creator of Flask) discovered a paradox he calls **"Better Models: Worse
Tools"**: newer Claude models (Opus 4.8, Sonnet 5) are *worse* at following third-party tool
schemas than older ones. Specifically, they inject invented fields into nested arrays when calling
edit tools — because Anthropic's RL training has optimized these models to excel at *Claude Code's
specific* search-and-replace schema, inadvertently degrading performance on alternative schemas.

Together these reveal a fundamental tension: LLM providers are training models to be excellent
at their own agent tooling while accidentally making them worse at everyone else's.

## Why It Matters

If you're building any kind of agent — coding agent, data pipeline agent, infrastructure
automation — you need to understand three things happening right now:

1. **The agent loop is commodity code.** llm-coding-agent proves that the core loop (receive
   prompt -> call tools -> observe results -> decide next action) is straightforward to build.
   The value isn't in the loop; it's in the tool definitions, approval policies, and
   sandboxing.

2. **Tool schema design is the new API design.** The "Better Models: Worse Tools" finding shows
   that how you define your tool schemas matters enormously — not just for correctness, but for
   compatibility with how models have been RL-trained. An `edit_file(old_string, new_string)`
   schema will perform differently across model families because each has been trained on
   different edit primitives (search-and-replace vs. apply-patch vs. whole-file rewrite).

3. **RL training creates implicit tool coupling.** When Anthropic trains Claude to be better at
   Claude Code, they're implicitly training it to be worse at non-Claude-Code tool schemas.
   This is a new kind of vendor lock-in: not at the API level, but at the *behavioral* level.

## Key Technical Details

### llm-coding-agent Architecture

- **6 tools**: read_file (paginated, line-numbered), write_file (auto-mkdir), edit_file
  (exact-match replacement with diff output), execute_command (process tree kill on timeout),
  list_files (respects .gitignore), search_files (ripgrep with Python fallback)
- **Approval tiers**: read-only tools auto-approve; mutations require explicit approval
  unless `--yolo` mode; custom approval functions via Python API
- **Sandboxing**: all file ops resolve symlinks and reject path traversal (`..`, absolute paths)
- **Chain limit**: configurable max iterations to prevent runaway loops
- **Session persistence**: conversations log to SQLite, resumable via `llm code -c`

### The Tool Schema Trap (Technical Details)

- **Symptom**: Claude Opus 4.8 / Sonnet 5 add extra fields to `edits[]` array that aren't in
  the tool's JSON Schema definition. The edit content is usually correct, but the schema
  violation causes parsing failures in third-party frameworks.
- **Root cause hypothesis**: Anthropic's RL training for Claude Code optimizes the model's
  behavior specifically for Claude Code's `edit_file(file_path, old_string, new_string)` tool.
  When a third-party tool has a structurally different edit schema (e.g., Pi's batched edits
  array), the model's RL-trained instincts "leak" Claude Code's field names into the call.
- **Parallel in OpenAI**: Codex uses `apply_patch` with unified diff format. GPT models trained
  on Codex would similarly be biased toward that specific tool shape.
- **Implication**: third-party coding frameworks face a dilemma — match the provider's tool
  schema exactly (coupling to one provider) or implement provider-specific tool adapters.

### Design Patterns for Robust Agent Tools

From llm-coding-agent's approach and the schema trap analysis:

| Pattern | Purpose |
|---------|---------|
| Exact-match edit over regex | Prevents accidental modifications; model must quote code precisely |
| Diff output on mutations | Verification — model can confirm the change matched intent |
| Read-only auto-approve | Reduces friction for exploration; gates only on mutations |
| Containment via path resolution | Security boundary; prevents sandbox escape via symlinks |
| Process tree kill on timeout | Prevents zombie processes from execute_command |
| Chain limit | Bounded execution; prevents infinite tool-calling loops |

## How It Connects to What You Know

You already understand the ReAct loop (observe-think-act) and how Claude Code implements it.
llm-coding-agent is essentially a minimal ReAct agent with a fixed tool set — no planning phase,
no reflection, just a tight observe-act loop with approval gates. The key insight is that this
*works well enough* for many coding tasks because the model's internal reasoning (extended
thinking) handles the planning that explicit planning frameworks used to provide.

The tool schema trap connects directly to your knowledge of RL from the AI training course:
RLHF/RLAIF training doesn't just improve general capability — it creates *behavioral biases*
toward specific tool interactions. This is the same mechanism that makes Claude good at
following instructions (RL on helpfulness) but applied to tool-use patterns. The model develops
"muscle memory" for specific tool shapes, and that muscle memory can override the explicit
schema definition.

In practice: if you're building MCP servers or agent tools, this means your tool
schemas should be designed with awareness of how major models have been trained. Matching
Claude Code's tool naming conventions (file_path, old_string, new_string) may produce better
results than a novel schema, even if the novel schema is more elegant.

## Try It Yourself

Run `code_example.py` to see a minimal coding agent loop implemented from scratch. It
demonstrates:
- Tool registration with JSON Schema definitions
- The dispatch loop (prompt -> tool calls -> results -> next prompt)
- Approval gating with different permission levels
- How edit tool schema design affects model behavior (simulated)
- Chain limiting to prevent runaway execution
