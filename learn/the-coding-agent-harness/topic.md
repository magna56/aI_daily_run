# How a coding agent is built

**Category**: Building Agents & MCP
**Tags**: coding-agents, agents, mcp
**Date**: 2026-08-23
**Level**: Building
**For**: Building agents
**Hook**: The product is not the model. It is a loop that calls tools, checks permission, and parks big work in a child so the main chat stays small.
**Kind**: Learn
**Time to read**: ~10 minutes

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

## How It Connects to What You Know

A job queue, a worker pool, and a permissions service. The model is not the orchestrator. The harness is.

Previous: [How the forward pass runs](#learn/how-the-forward-pass-runs). That is the last lesson. The daily lab on the homepage is the ongoing case studies.

Labs that assume this map: [2026-08-22](#2026-08-22) (budget), [2026-07-05](#2026-07-05) (schema).

## Try It Yourself

`code_example.py` runs a parent loop that either reads a big file inline or parks the read in a child and keeps only a summary — and prints how the parent's prefix grows in each case.

## Glossary

- **Harness** — loop + tools + permissions + isolation + context policy.
- **Parent session** — the chat you type in.
- **Sub-agent** — a child session that returns a result and does not keep its reads in the parent.
- **Permission mode** — ask, allowlist, or bypass for side effects.
- **Isolation** — keeping a child's context out of the parent prefix.
