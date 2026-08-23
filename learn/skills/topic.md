# What a skill is

**Category**: Building Agents & MCP
**Tags**: coding-agents, agents
**Date**: 2026-08-23
**Level**: Start here
**For**: Building agents
**Hook**: A skill is a markdown file the agent loads on demand. It is not a smaller model you train.
**Kind**: Learn
**Time to read**: ~10 minutes

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

## What It Is

A skill is a directory. The required file is `SKILL.md`: YAML frontmatter, then markdown, optionally scripts in the same folder. In Claude Code the directory name becomes a `/slash` command. Personal skills live in `~/.claude/skills/`; project skills in `.claude/skills/`. There is no training job and no endpoint. Installing a skill is putting a folder on disk.

The harness reads *only* the frontmatter at start and builds a catalog for the system prompt. When a user phrase matches, or they type `/name`, it loads the body. That two-stage load is the feature.

The same folder format is showing up as a shared convention (agentskills.io and cousins). Cursor can point at a rules/skills directory too. Portable instructions, not a vendor model.

## Why It Matters

Once "skill" means "lazy-loaded markdown," you stop scheduling a fine-tune for a commit-message format. You also stop treating `CLAUDE.md` as a junk drawer. Standing project facts stay in the briefing. Repeatable procedures become skills. Hard stops become hooks. Big detours become sub-agents (lesson 11).

## Key Technical Details

**Background first.** Frontmatter is the index. The markdown body is the implementation. The harness, not the model, decides when the body enters the context window.

- **Description is the API.** "Use when the user asks for a commit message" is a trigger. "Helps with git" is fog.
- **One job per skill.** A 4,000-line mega-skill is an always-on file with extra steps.
- **Hooks are code.** If you need "never `rm -rf /`," do not put it only in a skill. Put it in a hook the model cannot skip.
- **Skills are not memory.** They do not store last week's chat. They store a procedure.

## How It Connects to What You Know

pytest plugins: the core publishes verbs, packages register nouns. A skill is the instruction-pack version of that. MCP (lesson 8) is the same idea across a process boundary.

Previous: [Coding agents 101](#learn/coding-agents-101). Next: [How retrieval works](#learn/retrieval).

The daily lab on [2026-07-13](#2026-07-13) is the in-process plugin case study (`llm` + pluggy).

## Try It Yourself

`code_example.py` builds a tiny catalog of skill descriptions, picks one from a user phrase, and prints the token cost of "index only" vs "paste every body every turn."

## Glossary

- **Skill** — a folder of instructions the harness loads on demand.
- **SKILL.md** — the markdown file: frontmatter + body.
- **Frontmatter** — YAML at the top; becomes the catalog line.
- **Hook** — code that runs on an event, outside the model.
- **Sub-agent** — a child session with its own transcript.
