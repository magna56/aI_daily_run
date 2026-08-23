# Claude Code / Cursor Is a Loop With Tools, Permissions, and Sub-Agents

**Category**: Building Agents & MCP
**Tags**: coding-agents, agents, mcp
**Date**: 2026-08-23
**Level**: Building
**For**: Building agents
**Hook**: The product is not the model. It is a loop that calls tools, checks permission, and parks big work in a child so the main chat stays small.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine a very fast intern who can only talk, plus a toolbox, plus a grown-up who says yes or no before anything dangerous happens. The intern looks at your request, picks a tool, the grown-up checks the rulebook, the tool runs, the intern sees what came back, and they do it again until the job is done or the notebook is full. If the notebook gets messy, someone writes a short summary and throws the old pages away. If the intern needs to read a whole filing cabinet, they send a helper into another room; the helper comes back with a sticky note, not the cabinet.

## The Problem

People talk about Claude Code and Cursor as if the model *is* the product — pick a smarter SKU, get a better intern. That misses the machine you actually use. The model only emits text (and structured tool calls). Everything that makes it a coding agent — the while-loop, the tool list in the prompt, the allow/ask/deny gate, the child agents, the compact-when-full pass — is a **harness**: ordinary software around the model. If you do not see the harness, you cannot debug a runaway bill, a denied `rm`, a context window that "suddenly" forgot the plan, or why a sub-agent seemed to start from zero. Anthropic's own evals write-up says it plainly: when they evaluate "an agent," they evaluate the harness and the model together.

## For a Software Engineer

This is an **event loop with a capability system and a memory budget** — closer to a game loop plus `seccomp` plus a ring buffer than to "chat." One turn is:

1. Send messages + tool schemas to the model.
2. If the model returns text only, show it and stop (or wait for the user).
3. If it returns tool calls, run each through **allow / ask / deny**.
4. Append tool results to the transcript.
5. If the transcript is near the window, **autocompact** (summarize old turns).
6. Go to 1.

The tool inventory is not a sidebar feature. It is **prompt prefix**. Every MCP server you left connected is schema tokens you re-pay on every turn (you already met that tax on the context page). Permissions are not politeness: `deny` wins over `allow`, hooks can still deny in a "skip permissions" mode, and a missing `ask` in headless mode is a failed tool call, not a popup.

Sub-agents are **process isolation for context**. A child gets its own window, does the 6,000-token grep, and returns a 200-token note. The parent's KV cache (last page) never ingested the dump. Autocompaction is the GC when you did not isolate in time.

The number worth feeling: three 6,000-token reads want ~18,000 tokens in the parent. The code example's harness hits the 8,000-token compact line after the first dump (peak 9,630) and thrashes; the same reads behind a child leave the parent at a 4,590 peak with three 200-token notes. That is not a model upgrade. That is a harness choice. Monday-morning action: draw *your* loop — tools, permission file, where compact fires, what a child is allowed to do — before you add another MCP server.

## What This Means for You

**When this matters**: you use Claude Code or Cursor every day, or you are about to wrap an API in `while tool_calls:` and ship it as "an agent."

**How it affects you**: most production failures are harness failures — a tool schema that is ambiguous, a permission rule that asks 40 times, a compact that dropped the failing test, a child that cannot see the parent's plan, a loop that never hits a stop. The model gets blamed because the model is visible.

**What to do about it**: read your `permissions.allow` / `ask` / `deny` (Claude Code: project and user `settings.json`; Cursor: its auto-run / protection settings) and treat them as a capability list, not defaults you never opened. Move read-heavy exploration to a sub-agent. Watch for autocompact in long sessions and write down anything you cannot afford to summarize (the failing assertion, the file path, the decision). If you build your own agent, copy this shape — loop, typed tools, a real deny path, isolated children — before you copy a framework.

## What It Is

A **coding-agent harness** is the program that turns a language model into something that can touch a repo. Claude Code and Cursor are two implementations of the same skeleton:

- **Agentic loop** — model in, tool calls out, host executes, results back, repeat.
- **Tool inventory** — built-in tools (read, edit, bash, search) plus MCP servers advertised as extra tools. The model sees JSON schemas, not your feelings about what is safe.
- **Permissions** — a policy that maps each call to allow, ask the human, or deny. This is host-side. The model cannot bypass a deny by asking nicely.
- **Sub-agents** — nested harnesses with their own transcript (and usually a tighter tool list). They return a message, not their whole history.
- **Autocompaction** — a summarization pass when the window is nearly full, so the loop can continue without a hard context error.

The Agent SDK is Claude Code's loop sold as a library. Cursor's agent is the same idea in a different host: editor tools, its own approval UX, its own children (including isolated VMs in later builds). The brand is the chrome. The loop is the product.

## Why It Matters

This page is the Learn-track capstone because every earlier page is a piece of this machine. If you only "learn the model," you will keep being surprised by bills, refusals, and amnesia. If you learn the harness, you can *change* it: fewer tools, stricter deny, children for big reads, compact before the window cliffs, a reasoning SKU only on the hard inner step.

Anthropic's "Building effective agents" advice still holds: start with a loop, not a graph framework; make the agent-computer interface (tool names, arguments, errors) as careful as a public API. The teams that fail are usually the ones that hid the loop behind magic.

## Key Technical Details

**Background first.** The model never "runs bash." It emits a structured tool call (name + arguments). The host validates, applies permission rules, executes, and appends a tool-result message. MCP (Model Context Protocol) is how an external process *adds* tools to that inventory at runtime — capability discovery over a socket, the cross-process cousin of in-process plugins. Sub-agents are another host-invoked model session, not threads inside the weights. Autocompact is a separate model call that rewrites history into a shorter prefix.

- **The loop is the entire control plane.** There is no hidden planner. Stop conditions are: the model emits no tool call, the user cancels, a max-turn cap, or a permission deny the model cannot work around. If your custom agent "gets stuck," log this state machine first.
- **Tool schemas sit in the prompt and are re-sent every turn.** A chatty MCP server with 40 tools can cost thousands of tokens before the user speaks. Progressive disclosure (few tools first, more on demand) exists because of this, not because of fashion. `disallowedTools` in the SDK removes a tool from the model's context entirely; a deny rule blocks execution but may still leave the schema visible.
- **Allow / ask / deny is ordered like a firewall.** Deny wins. Ask means a human (or an SDK `canUseTool` callback) must decide. Allow is skip-the-prompt. Claude Code also has permission *modes* (`default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, …). A `PreToolUse` hook that returns deny still blocks even when the user tried to skip permissions — that is how orgs keep a real policy.
- **Headless changes the meaning of ask.** In `claude -p` / Agent SDK without a callback, there is no popup. An unresolved ask is a deny. Background sub-agents in non-interactive mode likewise cannot prompt; no hook decision means the call is denied. Design for that or your CI agent will look "dumber" than the IDE.
- **Sub-agent isolation is a context cut, not a security sandbox by itself.** A child starts a fresh transcript (unless you fork). It does not automatically inherit the parent's last 40 turns. It *may* still have bash. Isolation for *bytes* is why you spawn one; isolation for *damage* still needs permissions, a VM, or a sandbox flag. Cursor's isolated-VM children are the explicit version of that second cut.
- **Autocompaction is lossy GC.** When the window is near full, the harness summarizes older turns and keeps a recent tail. If it then immediately re-reads a huge file, compact *thrashes* — Claude Code will stop and tell you rather than burn a loop of summarize-and-refill. The fix is the same as the context page: read less, or read in a child.
- **The model in the loop is swappable.** Fast vs reasoning (two pages ago) is a per-step SKU. Some hosts use a cheap model for routing and a reasoner for the hard inner call. That is still this harness.

## How It Connects to What You Know

This is the whole Learn track, assembled:

- **What an LLM does** — the intern only predicts the next token (or tool-call tokens).
- **Tokens and sampling** — every loop iteration is a generate; temperature still applies.
- **Prompting that holds up** — `CLAUDE.md` / rules / system text are the static prompt the loop wraps.
- **Coding agents 101** — you have been driving this harness already; this page is the chassis.
- **Skills** — packaged instructions the loop can load, not new verbs in the weights.
- **Retrieval** — one more tool (search, grep, MCP) feeding rows into the transcript.
- **Context and the harness** — the transcript *is* the budget; tools and MCP are prefix.
- **The agent loop** — the abstract observe–act cycle; this page is the production one.
- **Reasoning models** — extra inner tokens before the first tool call, billed as output.
- **How the forward pass runs** — every appended tool result becomes KV-cache rows you will reread until compact or a child keeps them out.

If you build agents for a living, this is the checklist. If you only use them, this is why the product behaves the way it does.

## Try It Yourself

`code_example.py` is a tiny host: four tools, an allow/ask/deny table, a parent loop, an optional sub-agent for big reads, and autocompact when the parent crosses 8,000 tokens. It prints the permission decisions and the parent token bill with and without the child so you can see the harness, not the brand.

## Glossary

- **Harness** — the host program around the model: loop, tools, permissions, children, compact. Claude Code and Cursor are harnesses.
- **Agentic loop** — the repeat of "model → (optional) tool execution → append result" until stop.
- **Tool inventory** — the list of schemas the model is allowed to see this turn, including MCP.
- **MCP** (Model Context Protocol) — a standard for exposing external tools/resources to a host over a process boundary.
- **Allow / ask / deny** — the three permission outcomes for a tool call. Deny is highest priority.
- **Permission mode** — a session-wide default (e.g. accept edits, never ask, bypass) that still sits under deny rules and hooks.
- **Hook** — host-side code that runs at a lifecycle point (before a tool, on compact, …) and can force allow/ask/deny.
- **Sub-agent** — a nested model session with its own transcript, used to keep bulky work out of the parent.
- **Fork** — a child that *does* inherit the current conversation, used when you want continuity rather than isolation.
- **Autocompaction** — automatic summarization of old turns when the context window is nearly full.
- **Agent SDK** — libraries that expose Claude Code's loop for scripts and CI, including a `canUseTool` callback instead of a GUI prompt.
- **ACI** (agent-computer interface) — Anthropic's name for the tool surface: names, arguments, errors — as important as the prompt.
