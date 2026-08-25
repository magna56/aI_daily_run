# How the Agent Loop Works

**Category**: Building Agents & MCP
**Tags**: agents, mcp
**Date**: 2026-08-23
**Level**: Start here
**For**: Building agents
**Hook**: An agent is a loop that looks, decides, and calls a named tool. The name is the API.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

A helper who can only act by filling out forms: "read this file," "change these lines." The loop is simple — look, decide, fill a form, look again. If they were trained on *your company's* form and you hand them a different one, they keep writing the old field names. The work looks done. The form is invalid.

## The Problem

Anyone can write the observe-think-act loop in an afternoon. Teams then invent a nicer tool schema than the one the model was trained on, and newer models get *worse* at calling it. The failure is silent: extra fields, parse errors, retries that look like flakiness. People upgrade the model and the tools break.

## For a Software Engineer

An agent is a `while` loop with a cap. Observe (prefix + last tool result). Think (the model emits a thought or a tool call). Act (your code runs the named function and appends the result). Stop when it says it is done or you hit `max_iters`.

The tool list is not documentation. It is the surface area of the API the model can call. Names matter the way route paths matter. Models that were reinforced on a vendor's coding agent emit `edit_file(path, old_string, new_string)` or `apply_patch` with a unified diff. If your schema uses `mutate_buffer` with a different shape, the model is worse at filling it — and may invent fields from the schema it was trained on.

The number worth feeling: the 2026-07-05 lab is that failure in the wild — newer Claude models injected extra keys into a third-party edit array because Claude Code's schema had leaked into their reflexes. The loop was fine. The labels on the kitchen drawers were not.

Monday morning: keep the loop in one function you can print. Name tools after the verbs models already emit, or write a thin adapter. Use MCP to *expose* tools, not to replace the loop.

## What This Means for You

**When this matters**: you are wiring tools into an LLM, or a "better" model started failing your schema.

**How it affects you**: this is lock-in at the *behavior* layer, not the HTTP layer. Matching `path` / `old_string` / `new_string` is closer to matching a public contract the other side already implements than to taste.

**What to do about it**: log every observe / think / act line. When someone asks "why did it call `execute_command` twice?", the answer should be a log line, not a framework callback maze. Prefer trained names; adapt if you cannot.

## What It Is

**Observe** — build the prefix: system, tools, messages, last result.

**Think** — one model call. The output is either text (stop) or a structured tool call (name + arguments).

**Act** — dispatch on the name. Validate arguments in *your* code. Return a string the model will see next turn.

**MCP** (Model Context Protocol) is a standard way to list tools and call them over a process boundary — JSON-RPC, a server that says "I have `search_docs`." The host (Cursor, Claude Code) is the loop. MCP is the plugin bus. It does not think. It does not replace observe/think/act.

A tool schema is a JSON Schema (or equivalent) the model sees in the prefix. That is why a hundred tools are expensive (lesson 7): they sit at the front and are re-read every turn.

## Why It Matters

Frameworks hide the cycle and then you cannot debug it. The 2026-07-05 `llm-coding-agent` write-up is ~500 lines because the authors refused to hide it. Once the loop is visible, the remaining hard part is the contract — names, required fields, what happens on a bad call. Lesson 9 is when "think longer" is a different product. This lesson is the kitchen.

## Key Technical Details

**Background first.** *Tool calling* means the model emits a structured call instead of (or before) user-facing text. *MCP* is a host/server protocol for exposing those tools. *Schema trap* means the model's likely arguments match a vendor's tools, not yours.

- **Cap the loop.** `max_iters` is a fuse. Infinite observe/act is a bill.
- **Validate in code.** Shape checks belong in the act step. Lesson-adjacent: 2026-07-09 puts policy gates in front of the call.
- **One result, one observation.** Do not swallow errors. The model cannot fix what it cannot see.
- **MCP is transport.** If you do not have a loop, a server does nothing.

## How It Connects to What You Know

A worker that reads a queue, calls a service by name, writes the result. The name *is* the API. MCP is microservices for tools; the loop is the worker.

Previous: [How the Chat Is Re-Read Every Turn](#learn/context-and-harness). Next: [How Reasoning Models Work](#learn/reasoning-models).

Lab: [Building coding agents from scratch — and the tool schema trap](#2026-07-05).

## Try It Yourself

`code_example.py` runs a tiny observe/think/act loop over a fake `read_file` / `edit_file` pair and shows a "wrong schema" call injecting an extra key — the trap without an API.

## Glossary

- **Agent loop** — observe → think → act → observe, with a stop condition.
- **Tool** — a named function the model can request.
- **Schema** — the argument contract for a tool.
- **MCP** — a protocol for listing and calling tools out of process.
- **Host** — the app that runs the loop (Cursor, Claude Code, your script).
