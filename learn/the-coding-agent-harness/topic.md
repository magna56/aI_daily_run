# How a Coding-Agent Harness Is Built

**Category**: Building Agents & MCP
**Tags**: coding-agents, agents, mcp
**Date**: 2026-08-23
**Level**: Building
**For**: Building agents
**Hook**: The product is not the model. It is a loop that calls tools, checks permission, and parks big work in a child so the main chat stays small.
**Kind**: Learn
**Time to read**: ~16 minutes

> **You'll be able to:** draw a coding agent's physical architecture from memory, name the exact order a tool call is checked in before it runs, and explain why `Edit` requiring a prior `Read` is a safety property enforced by bookkeeping rather than by asking the model to be careful.

## Explain Like I'm 5

The workshop from lesson 4 has a manager. The manager decides who may touch the saw, when to send a helper into the other room, and when the main conversation has gotten too long and needs a new notepad. The friend who guesses words is still just guessing words. The manager is the product you actually bought.

## The Problem

People compare "Claude vs GPT vs Gemini" as if the coding product were a model picker. Then they are surprised that one tool asks before `rm`, another auto-applies diffs, a third isolates a sub-task on a VM. Those are harness differences. The model is the next-token engine (lesson 1). The harness is the loop, the tool list, the permission gate, the sub-agent, and the context policy (lesson 7). If you only swap models, you have not swapped products.

## For a Software Engineer

A coding-agent product is:

1. **Loop** — observe / think / act (lesson 8) with a cap.
2. **Tools** — read, edit, grep, terminal, sometimes MCP servers.
3. **Permissions** — ask / allowlist / bypass on writes and shell.
4. **Isolation** — sub-agents or VMs so a review or a research spike does not flood the parent transcript.
5. **Context policy** — briefing files, compaction, prompt cache.

The number worth feeling: a sub-agent that reads 6,000 tokens of logs keeps those 6,000 *out* of the parent. The parent pays for a summary plus the child's setup. The 2026-08-22 lab: that trade *loses* on a short session and wins when many parent turns remain. Isolation is not free. It is a process fork.

Monday morning: draw your tool's harness on one page — loop, tools, who can spawn children, what is on ask. Then change one thing: put long reads in a child, or put `rm` / `git push` back on ask, or shorten `CLAUDE.md`. Do not start with a model swap.

## What This Means for You

**When this matters**: you live in Cursor or Claude Code and you are debugging cost, surprise edits, or a context window that "forgot."

**How it affects you**: most of what you feel is harness policy. A "smarter" model with bypass-on and a bloated briefing will still smash the repo and the bill.

**What to do about it**: treat the product as a program. Read its permission UI. Use sub-agents for work you do not want in the main thread. Keep the parent prefix stable (lesson 7). Name tools the model already knows (lesson 8).

## What It Is

**Loop.** One function, conceptually: while not done and under cap, call the model, dispatch tools, append results.

**Tools.** File I/O and shell are the core. MCP adds out-of-process tools (lesson 8). Progressive discovery exists so you do not pin a hundred schemas at the front of every turn.

**Permissions.** The type system for side effects. Ask is the default. Allowlist is for `npm test`. Bypass is for a disposable environment.

**Sub-agents.** A child harness: own transcript, often own tools, returns a summary. Cursor's isolated VMs are the same idea with a stronger wall. Use them when the work is large and you want the parent to stay small.

**Context isolation.** The parent should not inherit a 20-file dump from an exploration. That dump is the child's problem.

Claude Code and Cursor differ in UI and defaults. They do not differ in kind. If you are building your own, copy this shape, not a brand.

## Why It Matters

Once you see the harness, changelogs stop looking random: background review, sub-agent caps, compact, "concise" output, fork-by-default. They are all "keep the parent notebook small and the prefix stable." This is the last lesson because it sits on 4, 5, 7, and 8. The daily lab stays the news. This page is the map.

## Key Technical Details

**Background first.** The *parent* is the session you type in. A *sub-agent* is a child session. *Isolation* means the child's reads do not become the parent's prefix.

- **One loop you can log.** If you cannot print observe/think/act, you cannot debug "why did it run that."
- **Permissions beat prompts.** "Please don't push" in markdown loses to an ask gate.
- **Children need a job spec.** A sub-agent with a vague prompt invents scope (lesson 3) in a room you are not watching.
- **MCP is optional.** Built-in read/edit/bash is enough to learn the shape.

## The Physical Architecture

Split the machine in half, and most of what feels mysterious stops being mysterious:

```
YOUR MACHINE                              THE PROVIDER'S DATA CENTER
────────────────────                      ──────────────────────────
Coding agent CLI          ──API call──►   GPU cluster
  conversation history                    weights live here
  permission state                        inference runs here
  file access                ◄──stream──  response comes back
  MCP server processes
  your shell
```

Your machine holds every piece of state and performs every side effect — the files, the shell, the permission decisions. The data center holds the weights and does the thinking. Nothing about your filesystem exists on the other side except the bytes you chose to send it. This is why a "smarter model" swap changes the *thinking*, and changes nothing about the loop, the tools, or the permissions running on your own machine.

## The Loop, Precisely

```python
while True:
    response = model.infer(system_prompt + conversation_history)

    if response is text only:
        display(text)
        break                       # wait for the next user input

    if response has tool_calls:
        for call in response.tool_calls:
            result = permission_check(call)
            result = execute(call) if allowed else "denied"
            conversation_history.append(call)
            conversation_history.append(result)
        continue                    # loop back with the new context
```

`stop_reason` is what drives it:

| `stop_reason` | Meaning | Harness action |
|---|---|---|
| `end_turn` | Model is done | Display text, wait for the user |
| `tool_use` | Model wants tools | Execute them, loop back |
| `max_tokens` | Hit the output limit | Continue in the next call |

## The Permission Pipeline, in Order

Every tool call runs this exact sequence before anything happens, and the order is the whole story:

```
Tool call arrives
    → Pre-tool hooks fire     (your code; can block outright, before anything else)
    → Allowlist check         (settings patterns; a match allows)
    → Permission mode check   (ask by default; plan mode blocks anything that writes)
    → Interactive prompt      (Allow / Deny / Always allow)
```

**Hooks fire first**, before the allowlist — which is why a hook is the closest thing to real enforcement here, and everything after it can be satisfied by a sufficiently permissive config. [The daily lab on hooks](#2026-08-25) is the deep version of exactly this claim: what a hook can and cannot actually guarantee. And **"Always allow" writes to a local settings file**, which is the accumulation lesson 7 measured directly costing tokens on every message from then on — the convenience has an ongoing price.

**Parallel tool calls are safe for an ordinary reason:** independent calls in one model response execute concurrently, and this is safe because a call in a batch cannot reference a sibling's result — the model had not seen any of them when it emitted the batch. Every call can only depend on *prior* turns. Same reason concurrency is safe anywhere: no data dependency between the parallel pieces.

## The State the Model Does Not Have

| State | Purpose |
|---|---|
| `cwd` | Current working directory |
| `conversation_history` | The full message array — the model's only memory |
| `files_read` | Which files were accessed this session |
| `permission_grants` | "Always allow" decisions already made |
| `active_agents` | Running subagents |
| `token_count` | Triggers compaction |

**`files_read` is the quietly clever one.** Requiring a prior `Read` before an `Edit` on the same file makes a blind edit structurally impossible — the harness enforces it by bookkeeping, not by asking the model to please look first. That is the pattern worth copying if you build your own: turn a safety property you want into a check the harness makes mechanically, rather than an instruction you hope the model follows.

## Quick Reference

| Term | Plain English |
|---|---|
| Harness | Loop + tools + permissions + isolation + context policy. |
| Parent session | The chat you actually type into. |
| Subagent | A child session that returns a result, its reads never entering the parent. |
| `stop_reason` | The field that tells the harness whether to loop again or stop. |
| Permission pipeline | Hooks, then allowlist, then mode, then interactive prompt — in that order. |
| `files_read` | Harness bookkeeping that makes a blind edit structurally impossible. |
| Autocompaction | Summarizing older turns when the window nears its limit. Lossy by design. |

## Do It Today

**Step 1 — watch the same reads cost differently depending on where they happen, 2 minutes.**

```bash
python3 learn/the-coding-agent-harness/code_example.py
```

**You know it worked** when three inline 6,000-token reads leave the parent at **2,560 tokens but peak at 9,630** before autocompaction kicks in and thrashes it back down, while parking the same reads in a subagent leaves the parent at a steady **4,590** with the bulk — **26,700 tokens** — living and dying in the child instead. Same three reads. Very different bill, purely from where the harness routed them.

**Step 2 — draw your own tool's harness on one page.** Loop, tools, who can spawn children, what sits on ask versus allowlist versus bypass. Most debugging sessions about "the model did something weird" are actually questions about one box on that page.

**Step 3 — change one thing, not the model.** Put a long read in a subagent instead of inline, or move something off an allowlist back onto ask, or shorten a briefing file. Model swaps get reached for first and explain the least.

## Gotchas

- **A "smarter" model with bypass-on and a bloated briefing will still smash the repo and the bill.** Most of what you feel session to session is harness policy, not model capability.
- **Hooks fire before the allowlist, and that is the whole reason they matter.** A rule in prose (a briefing file saying "please don't push") loses to an ask gate every time; a hook can at least run before either.
- **A subagent with a vague prompt invents scope in a room you are not watching.** Give a child the same spec discipline lesson 3 asks for a direct prompt.
- **Autocompaction is lossy by design, not a bug.** Files modified and decisions made survive; exact intermediate results and verbatim file contents often do not.
- **Isolation is not free.** Spawning a subagent costs its own setup; on a short session that cost can exceed what it saves.

## How It Connects to What You Know

A job queue, a worker pool, and a permissions service. The model is not the orchestrator — the harness is, and the permission pipeline above is the same shape as a request going through auth middleware before it ever reaches a handler: multiple gates, checked in a fixed order, and the first one that says no wins.

This lesson sits on top of 4, 5, 7 and 8 in this track — the loop, the tools, the context economics, the agent patterns. The daily lab on the homepage is where all of it keeps showing up as news; this page is the map underneath it.

Previous: [How the Forward Pass Runs](#learn/how-the-forward-pass-runs). That is the last lesson in this track.

Labs that assume this map: [2026-08-22](#2026-08-22) (budget), [2026-07-05](#2026-07-05) (schema trap), [2026-08-25](#2026-08-25) (hooks).
