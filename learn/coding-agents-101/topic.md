# The Chat Box Isn't the Agent — The Repo Is

**Category**: Coding Agents & Productivity
**Tags**: coding-agents, context-engineering
**Date**: 2026-08-23
**Level**: Start here
**For**: Using tools
**Hook**: A coding agent is useful because it can read your files and ask before it writes. A chat box only sees what you paste.
**Kind**: Learn
**Time to read**: ~10 minutes

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

## What It Is

Claude Code is a terminal (and IDE) loop that reads and writes files and runs commands. Cursor is an editor with a similar loop. Codex, Gemini CLI — same shape. The brand is not the lesson.

**Files as context.** The agent does not contain your repo. It lists, greps, reads; those bytes become tokens. `@`-mention a path when you want to force a file in.

**Project memory.** `CLAUDE.md` / `.claude/CLAUDE.md` / Cursor rules are the briefing you would give a new teammate: how to test, which package manager, what not to do. Small and high-signal beats a 2,000-line architecture dump.

**Permissions.** Read is cheap. Write and shell are gated. "Ask" is the default you want. An allowlist is for the five commands you trust. Bypass is for a throwaway VM.

CLI vs the chat box in the editor: the CLI is better when you want a long unattended loop, scripts, and explicit permission modes. The editor chat is better when you are already looking at the diff. Same agent idea. Different cockpit.

## Why It Matters

Once you see the repo as the workspace, a lot of "the model is dumb" is "the model never saw the file." A lot of "the model is dangerous" is "I auto-approved shell." Lesson 11 is the harness in more detail. This lesson is the split you need on Monday: chat vs agent, briefing vs paste, ask vs bypass.

## Key Technical Details

**Background first.** The *harness* is the program around the model: tools, permissions, how the repo gets into the prompt. The model only picks tokens (lesson 1). The harness decides what those tokens are allowed to *do*.

- **Start in the repo.** A session started in `~` will wander. `cd` first.
- **Briefing files are loaded every session.** Keep them short. A novel in `CLAUDE.md` is a tax on every turn (lesson 7).
- **Search before dump.** `grep` + a 40-line read beats pasting a package.
- **Approve writes until it is boring.** The first time it wants `rm` or `git push`, you want a prompt, not a policy you forgot you set.

## How It Connects to What You Know

This is the difference between a pure function and a process with I/O. The chat box is the pure function. The agent is the process. You already decide that split when you pick a library call vs a worker.

Previous: [Specs and examples](#learn/prompting-that-holds-up). Next: [A skill is a reusable instruction pack](#learn/skills).

## Try It Yourself

`code_example.py` contrasts a "paste the file" session with a "grep then read" session on a tiny fake repo, and prints how many lines you re-pay on turn 5 vs turn 1.

## Glossary

- **Coding agent** — a model loop with tools for files and commands, over a real repo.
- **Chat box** — a completion over whatever you pasted. No repo unless you paste it.
- **Harness** — the program around the model: tools, permissions, briefing.
- **CLAUDE.md** — Claude Code's project briefing file. Cursor rules are the cousin.
- **Allowlist** — commands that skip the ask. Keep it small.
