# How Skills Work

**Category**: Building Agents & MCP
**Tags**: coding-agents, agents
**Date**: 2026-08-23
**Level**: Start here
**For**: Building agents
**Hook**: A skill is a markdown file the agent loads on demand. It is not a smaller model you train.
**Kind**: Learn
**Time to read**: ~13 minutes

> **You'll be able to:** write a `SKILL.md` whose description actually triggers, tell a skill apart from a hook and a subagent by what each one costs, and know when to reach for which.

## Explain Like I'm 5

A kitchen wall of recipe cards: you can read the titles from across the room — "pancakes," "soup." You do not memorize every recipe. When someone asks for pancakes, you take that card down. A smoke alarm is different — it screams when something burns, whether anyone asked. Sending a friend to the store is different again — they leave, do the work in another room, and come back with a bag. Recipe card, alarm, friend: three kinds of help. Mixing them up makes a mess.

## The Problem

"Skill" sounds like a smaller model you train and swap in. That reading is wrong, and it sends people to a fine-tune they do not need. The other failure is dumping twenty long playbooks into one always-on file so every turn pays for every recipe. Both come from not having names for three primitives: a pack you load when a phrase matches, a script that fires on an event, and a separate conversation that does a scoped job and reports back.

## For a Software Engineer

This is lazy loading — a plugin catalog. The harness scans skill folders at session start and keeps only the *index* (name + short description) in the prompt. The body of `SKILL.md` loads when the description looks relevant. You already do this with entry points: advertise a one-line hook, import the module when something calls it.

A **hook** is not a skill. It is an event listener (`PreToolUse`, a linter on shell). It runs outside the model. It does not occupy prompt tokens. Use it when you need a guarantee the model cannot talk past.

A **sub-agent** is not a skill. It is a forked process: new transcript, own tools, own budget. The parent pays for a summary, not for everything the child read.

The number worth feeling: a typical skill description is ~80 tokens. The body is often 800–2,000. Twenty skills in the catalog cost ~1,600 tokens every turn. Pasting all twenty bodies into the always-on file costs ~20,000 — on turn 1, turn 40, and every turn between. Monday morning: if a workflow you repeat still lives as a paragraph you re-type, it wants a `SKILL.md` whose description names *when* to load it.

## What This Means for You

**When this matters**: you keep pasting the same review checklist or deploy steps, or you are deciding skill vs hook vs sub-agent.

**How it affects you**: the wrong primitive wastes context or runs at the wrong time. A skill stuffed into the always-on file is a permanent tax. A hook cannot teach a procedure — it can only allow or deny.

**What to do about it**: write a folder with a `SKILL.md`. Put the trigger in `description`. Keep the body out of the always-on file. Hook for enforcement. Sub-agent when the work should never land in the parent transcript.

## The Folder, and What Loads When

A skill is a directory, and the required file is `SKILL.md` — YAML frontmatter, then markdown, optionally scripts in the same folder:

```
.claude/skills/check-health/
├── SKILL.md      ← required: frontmatter + instructions
├── scripts/      ← optional: code the agent can run
└── references/   ← optional: docs loaded on demand
```

```yaml
---
name: check-health
description: Verify the API is running. Use when the user says "check health" or "is it running".
---

1. Verify the server is running on localhost:8080
2. Test /api/health with a simple request
3. Report the status of each endpoint
```

In Claude Code the directory name becomes a `/slash` command. Personal skills live in `~/.claude/skills/`; project skills in `.claude/skills/`. There is no training job and no endpoint — installing a skill is putting a folder on disk.

**The two-stage load is the feature.** The harness reads *only* the frontmatter at session start and keeps the catalog — name plus description — in the system prompt. The body loads when a user phrase matches the description, or they type `/name`. That is why the description is the API, not documentation: "use when the user asks for a commit message" is a trigger; "helps with git" is fog that never fires.

| Field | Purpose |
|---|---|
| `name` | The slash-command name, kebab-case |
| `description` | What it does *and* the trigger phrases — this is what gets matched |
| `allowed-tools` | Pre-approve specific tools for this skill only |
| `model` | Override the model, e.g. `haiku` for pure formatting |
| `disable-model-invocation: true` | Only the user can trigger it — for deployments, migrations |
| `context: fork` | Run in an isolated subagent instead of the parent transcript |

## Skills vs Hooks vs Subagents

Three primitives get called "automation" and cost completely different things:

- **A skill is lazy-loaded markdown.** It occupies prompt tokens once it fires, and it runs *inside* the model's own turn — the model chooses to follow it, which means it can also choose to ignore or misread it.
- **A hook is code that runs on an event**, outside the model entirely: `PreToolUse`, `PostToolUse`, `Stop`. It costs no prompt tokens and the model cannot talk its way past it — but it can also only allow, deny, or run a side effect, never teach a procedure. [The daily lab on hooks](#2026-08-25) covers exactly how a hook decides to fire, and why it is still not a hard gate.
- **A subagent is a forked process** — its own transcript, its own tools, its own token budget. The parent pays only for the summary it returns, not for everything the child read. `Explore` is read-only search; `Plan` designs without touching code; `general-purpose` has full access. Route fetching to a cheap subagent and analysis to the expensive model — never pull raw search results directly into your most expensive context.

Confusing these wastes context or fires at the wrong time: a skill stuffed into the always-on file is a permanent tax; a hook cannot teach a multi-step procedure; a subagent used for something that belongs in the parent transcript throws away the context the parent actually needed.

## Quick Reference

| Term | Plain English |
|---|---|
| Skill | A folder of instructions the harness loads on demand. |
| SKILL.md | The required file: YAML frontmatter, then the procedure. |
| Frontmatter | The YAML header; becomes the always-loaded catalog line. |
| Hook | Code that runs on an event, outside the model, cannot be talked past. |
| Subagent | A child session with its own transcript, tools and budget. |
| `context: fork` | Frontmatter field that runs a skill as a subagent. |
| Catalog | The set of skill names + descriptions kept in every session's prompt. |

## Do It Today

**Step 1 — see the token gap, 2 minutes.**

```bash
python3 learn/skills/code_example.py
```

It builds a small catalog of skill descriptions, matches one against a user phrase, and prints the token cost of "index only" versus "paste every skill body into context every turn." **You know it worked** when the catalog-only cost stays roughly flat as you add skills, while the paste-everything cost grows with every one you add — that gap is the entire argument for lazy loading.

**Step 2 — write one real `SKILL.md`.** Pick a workflow you have re-typed at least three times — a deploy checklist, a review rubric, a standup format — and turn it into a skill with a description that names the trigger phrase explicitly, not just the topic.

**Step 3 — decide, out loud, whether it should be a skill.** If the answer to "would I be upset if this were skipped" is yes, it belongs in a hook, not a skill — a skill can always be ignored by the model reading it.

## Gotchas

- **A vague description never fires.** "Helps with git" matches nothing reliably; "use when the user asks for a commit message" does.
- **One job per skill.** A 4,000-line mega-skill is an always-on file with extra steps, and it costs the same whether the body is used once or never.
- **Skills are not memory.** They do not store last week's conversation. They store a repeatable procedure, checked back into the skill folder, not the transcript.
- **New skill directories need a restart.** Live-editing an existing `SKILL.md` is picked up on the next invocation; adding a brand-new skill directory is not.
- **A hard stop belongs in a hook, not a skill's prose.** "Never `rm -rf /`" written in a skill is a request the model can still misread. Written as a hook, it cannot be reached at all.

## How It Connects to What You Know

pytest plugins: the core publishes verbs, packages register nouns. A skill is the instruction-pack version of that — lazy registration, loaded only when its trigger matches. MCP, covered in [How the Agent Loop Works](#learn/the-agent-loop), is the same idea across a process boundary instead of a prompt boundary.

Previous: [How Coding Agents Work](#learn/coding-agents-101). Next: [How Retrieval Works](#learn/retrieval).
