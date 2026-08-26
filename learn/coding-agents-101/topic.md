# How Coding Agents Work

**Category**: Coding Agents & Productivity
**Tags**: coding-agents, context-engineering
**Date**: 2026-08-23
**Level**: Start here
**For**: Using tools
**Hook**: A coding agent is useful because it can read your files and ask before it writes. A chat box only sees what you paste.
**Kind**: Learn
**Time to read**: ~14 minutes

> **You'll be able to:** pick chat vs agent for a given task, choose a model on purpose instead of by default, and know which of Claude Code's tools ask permission before they run.

## Explain Like I'm 5

Texting a friend a photo of a broken shelf is different from inviting them into the workshop. In the text they guess from the photo. In the workshop they can open drawers, read the label on the glue, and — if you set the rule — ask before they turn on the saw. Cursor and Claude Code are the workshop. The web chat box is the text thread. The friend is not smarter in the workshop. They can just see the room.

## The Problem

You paste a function into a chat box, get a plausible rewrite, paste it back, and break three callers you forgot. You switch to Cursor, type the same sentence, and either it finds the callers — or it also runs the tests, or it asks to delete a file. Same model family, different product. A coding agent is a model plus your repository plus a permission gate. Use it like a chat box and you leave the repo on the table. Use a chat box like an agent and *you* are the filesystem.

## For a Software Engineer

A chat completion is `f(prompt) -> text`. A coding agent is a loop: read the briefing, pick a tool, wait for permission, run it, observe, repeat. The intelligence you feel is mostly *state* — files, git status, test output — stuffed back into the prefix each turn.

The number worth feeling: a 400-line file you paste into chat costs ~400 lines on every follow-up, and still misses the other 40 files that import it. An agent that greps and reads 40 lines of a caller pays for what it needs. That is why the same model "knows your codebase" in Cursor and invents an API in a paste box.

Monday morning: chat for questions that do not need the tree. Agent when the answer depends on *this* repo. Start the agent in the project directory. Put build/test commands and the few rules you actually enforce in `CLAUDE.md` or Cursor rules — not in a paste you will forget. Leave write and shell on ask until the command is routine.

## What This Means for You

**When this matters**: you have both a chat product and a coding agent and you keep reaching for the wrong one.

**How it affects you**: chat fails by hallucination. The agent fails by action — real edits, real commands, a real `git push` if you said yes too fast. Permissions are the type system for side effects.

**What to do about it**: no repo needed → chat. Repo needed → agent, in the project, with a short briefing file. Do not dump the tree. Let it search. Never "bypass permissions" on a machine with production credentials.

## The Loop Underneath

Claude Code, Cursor, Codex and Gemini CLI are the same shape: read the briefing, pick a tool, wait for permission if the tool needs it, run it, observe the result, repeat. The brand is not the lesson — the loop is.

**Files as context.** The agent does not contain your repo. It lists, greps, reads; those bytes become tokens against the budget from lesson 2. `@`-mention a path when you want to force a file in rather than trust it to search.

**Project memory.** `CLAUDE.md`, `.claude/CLAUDE.md`, or Cursor rules are the briefing you would give a new teammate — how to test, which package manager, what not to do — loaded into *every* session automatically.

```markdown
Project language and framework: "Python 3.11, FastAPI, Postgres"
Testing convention: "pytest. Never mock the database in integration tests."
Build / test commands: "make test. Build: make -j8"
Architecture: "API layer in /src/api, models in /src/db"
Team rules: "Never commit to main. Always write tests."
```

| Level | Location | Scope |
|---|---|---|
| Global | `~/.claude/CLAUDE.md` | Every project — personal preferences, model habits |
| Project | `/your-repo/CLAUDE.md` | This repo — stack, architecture, team conventions |
| Subdirectory | `/your-repo/src/CLAUDE.md` | This folder — module-specific patterns |

**Keep it short.** Every line loads into context on every turn — a novel here is a tax paid all session, and lesson 7 turns that into an actual bill.

## Permissions Are the Type System for Side Effects

Every action the agent takes is a *tool call*, and tools split cleanly by whether they can hurt you:

| No permission needed (read-only) | Requires permission (writes / execution) |
|---|---|
| `Read` — file contents | `Edit` / `Write` — modify or create files |
| `Grep` — search patterns | `Bash` — run shell commands |
| `Glob` — find files by pattern | `Agent` — spawn a subagent |

"Ask" is the default you want. An allowlist in `.claude/settings.json` is for the handful of commands you actually trust — `git status`, your test runner. Bypassing permissions entirely is for a throwaway VM with nothing to lose, never for a machine with production credentials.

## Which Model for Which Task

Switch mid-session with `/model`. The number worth internalizing: **Opus burns roughly 9× the tokens of the default model** for the same task. A vague prompt sent to the expensive model is the worst combination available — you pay the most for an answer you will likely still redo.

| Model | Best for |
|---|---|
| **Haiku** | Data formatting, boilerplate, subagent tasks |
| **Sonnet** | Default — everyday coding, feature implementation |
| **Opus** | Architecture decisions, multi-file refactors, subtle debugging, genuinely ambiguous problems |

Start with the default. Reach for the expensive model only when the task actually needs the extra reasoning — and fix the prompt (lesson 3) before you reach for it, since a precise prompt to a cheap model regularly beats a vague prompt to an expensive one.

## Plan Mode

Plan mode makes the agent design *before* it writes any code — it explores, proposes an approach, and waits for you to approve it. Use it for multi-file changes, refactors that touch existing behaviour, architectural decisions, or anything where the requirement is still unclear enough that you want to see the plan before you see a diff.

## The Decision Tree

```
No repo needed                    → chat
Repo needed, one-off              → agent, in the project directory
Repeatable workflow               → build a skill (lesson 5)
Needs external data / a system    → configure an MCP server
Multi-file or architectural       → plan mode first
Genuinely parallel work           → subagents
```

## Quick Reference

| Term | Plain English |
|---|---|
| Coding agent | A model loop with tools for files and commands, over a real repo. |
| Chat box | A completion over whatever you pasted. No repo unless you paste it. |
| Harness | The program around the model: tools, permissions, how the repo enters the prompt. |
| CLAUDE.md | The project's permanent briefing file, loaded every session. |
| Allowlist | Commands that skip the permission prompt. Keep it small. |
| Plan mode | The agent proposes an approach and waits for approval before editing. |
| `/model` | Switches the active model mid-session. |
| `/compact` | Summarises the conversation to free context. |

## Do It Today

**Step 1 — measure what a paste actually costs, 2 minutes.**

```bash
python3 learn/coding-agents-101/code_example.py
```

It contrasts a "paste the whole file" session with a "grep then read" session on a small fake repo. **You know it worked** when you can see the pasted-file approach re-paying the same lines on every follow-up turn, while the search-based approach only ever pays for what it actually reads.

**Step 2 — write or shorten your own `CLAUDE.md`.** If you do not have one, run `/init` and cut it to the build command, the test command, and the two rules you have actually had to repeat to an agent. If you have one over 50 lines, cut it in half — it is loaded every turn, on every session, forever.

**Step 3 — pick one command you approve every single time** (your test runner, `git status`) and add it to the allowlist. Leave everything that writes or deletes on "ask."

## Gotchas

- **A session started outside the repo will wander.** `cd` into the project first, or the agent has no tree to search.
- **Search before you dump.** `grep` plus a 40-line read beats pasting a 400-line file — the 40-line version is what you re-pay on every follow-up turn.
- **Bypassing permissions is not a productivity setting.** The first time an agent wants `rm` or `git push --force`, you want a prompt, not a policy you forgot you set weeks ago.
- **A CLAUDE.md nobody prunes becomes a tax nobody notices.** Every stale line still gets resent on every turn.
- **Plan mode is not free either** — it is still tokens spent exploring. Skip it for changes you could describe in one sentence.

## How It Connects to What You Know

This is the difference between a pure function and a process with I/O. The chat box is the pure function. The agent is the process. You already decide that split when you choose between a library call and a worker — repo access is exactly the "does it need I/O" question, aimed at a model instead of a subroutine.

Previous: [How to Write Prompts That Hold Up](#learn/prompting-that-holds-up). Next: [How Skills Work](#learn/skills).
