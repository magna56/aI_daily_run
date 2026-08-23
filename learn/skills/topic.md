# A Skill Is a Reusable Instruction Pack, Not a Smaller Model

**Category**: Building Agents & MCP
**Tags**: coding-agents, agents
**Date**: 2026-08-23
**Level**: Start here
**For**: Building agents
**Hook**: A skill is a markdown file the agent loads on demand. It is not a smaller model you train.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5
Imagine a kitchen wall covered in recipe cards. Each card has a short title you can read from across the room — "pancakes," "soup," "birthday cake." You do not memorize every recipe. When someone asks for pancakes, you take that one card down and follow it. A smoke alarm is different: it is not a recipe at all. It screams when something burns, whether anyone asked or not. And sending a friend to the store is different again: they leave with a list, do the work in another room, and come back with a bag. The wall of cards, the alarm, and the friend are three ways to get help. Mixing them up makes a mess.

## The Problem
"Skill" sounds like a smaller, smarter model — something you train, host, and swap in when the main model is not enough. That reading is wrong, and it sends people down the wrong build. The other failure is the opposite: dumping twenty long playbooks into one always-on instruction file so every turn pays for every recipe, whether today's task needs any of them. Both mistakes come from not having names for three different primitives: a pack of instructions you load when a phrase matches, a script that fires on an event, and a separate conversation that does a scoped job and reports back.

## For a Software Engineer
This is **lazy loading**, the same shape as a plugin catalog. The harness scans every skill folder at session start and keeps only the *index* — name plus a short description — in the prompt. That catalog is cheap. The body of `SKILL.md` is the implementation, and it is loaded only when the description looks relevant. You already do this with entry points: advertise a one-line hook spec, import the module when something actually calls it.

A **hook** is not a skill. A hook is an event listener — `PreToolUse`, `SessionStart`, a linter that rejects a shell command. It runs *outside* the model. It does not occupy prompt tokens. Use it when you need a guarantee the model cannot talk past.

A **sub-agent** is not a skill either. It is a forked process: new transcript, own tools, own budget. The parent pays for a summary, not for everything the child read. Use it when the work would pollute the main conversation.

The number worth feeling: a typical skill description is about **80 tokens**. The body is often **800–2,000**. Twenty skills in the catalog cost ~1,600 tokens every turn. Pasting all twenty bodies into the always-on file costs ~20,000 — and you pay that on turn 1, turn 40, and every turn between. Monday-morning action: if a workflow you repeat still lives as a paragraph you re-type, it wants a `SKILL.md` with a description that names *when* to load it.

## What This Means for You
**When this matters**: you keep pasting the same review checklist, commit-message format, or deploy steps into chat, or you are deciding whether a new capability should be a skill, a hook, or a sub-agent.

**How it affects you**: the wrong primitive wastes context, runs at the wrong time, or both. A skill stuffed into the always-on file is a permanent tax. A hook used as a playbook cannot teach the model a procedure — it can only allow or deny. A sub-agent used as a skill pays a full setup cost for work that should have been one loaded page.

**What to do about it**: write a folder with a `SKILL.md`. Put the trigger in the `description` — what it does *and* the phrases that should wake it ("use when the user asks for a commit message"). Keep the body out of the always-on file. Reach for a hook when you need enforcement. Reach for a sub-agent when the work should never land in the parent transcript.

## What It Is
A skill is a directory. The only required file is `SKILL.md`: YAML frontmatter between `---` markers, then markdown instructions, optionally plus scripts and reference files in the same folder. In Claude Code the directory name becomes the `/slash` command. Personal skills live in `~/.claude/skills/`; project skills live in `.claude/skills/`. There is no training job, no endpoint, no weights. Installing a skill is putting a folder on disk.

The harness — the program around the model, not the model itself — scans those folders when a session starts. It reads *only* the frontmatter and builds a catalog that goes into the system prompt. The model sees a list of names and descriptions. When a user phrase matches a description, or when the user types `/skill-name`, the harness loads the markdown body (and can run `!` command blocks inside it) into the conversation. That two-stage load is the whole feature.

The same folder format is now an open standard at agentskills.io. Cursor, Codex, and other harnesses can point at the same directory. A skill is portable instructions, not a vendor-specific model.

## Why It Matters
Agent products keep growing a junk drawer of "ways to customize": system prompts, rules files, hooks, MCP servers, sub-agents, plugins. Skills are the one that matches how software engineers already share procedure — a file in the repo, reviewed in a pull request, versioned with the code it describes.

They also fix a cost problem the always-on file cannot. Progressive disclosure (pay for the index always, the body only when needed) is why twenty skills do not cost twenty playbooks. Simon Willison's line is the right one: a skill is markdown plus optional scripts, and any agent that can read a filesystem can use one. That is closer to a README than to a fine-tune.

The failure mode is a vague description. If the catalog entry says "helps with code" it will either never fire or fire on everything. The description *is* the router.

A second failure is treating a skill as a smaller model you A/B test. There are no weights to swap. If the procedure is wrong, you edit the markdown. If the model ignores the procedure, the fix is a tighter checklist, an accompanying script the harness can run, or a hook that enforces the step the model keeps skipping — not a fine-tune of a specialist.

## Key Technical Details
**Background first.** Three objects sit in a coding-agent session. The *catalog* is the list of skill names and descriptions injected every turn. A *trigger phrase* is language in that description the model uses to decide a skill is relevant — there is no separate regex engine unless you write one. A *hook* is a command the harness runs at a lifecycle event; its stdout can be fed back as extra context, but the hook itself is not a prompt. A *sub-agent* is a nested model loop with its own messages.

- **`SKILL.md` is the unit of install.** Frontmatter must include a `description` (Claude's docs also require `name` on the API path). The body is ordinary markdown: steps, examples, checklists. Optional scripts in the same folder are what you run when a procedure should not be improvised.
- **The description is the trigger, not a slogan.** It has to say what the skill does *and* when to use it. "Summarizes uncommitted changes. Use when the user asks what changed, wants a commit message, or asks to review their diff." is a trigger. "Git helper." is not.
- **Only frontmatter is always in context.** Claude Code's scan does not load bodies at startup. `/skill-name` and model-invoked load are the two ways the body arrives. `disable-model-invocation: true` keeps a skill manual-only — useful for workflows you do not want firing from a loose phrase.
- **A hook is the wrong tool for a playbook.** Hooks (`PreToolUse`, `PostToolUse`, `SessionStart`, and the rest) run code. Use them to block `rm -rf`, inject `git diff`, or deny a network call. They cannot teach a twelve-step review format; they can only run at a named event.
- **A sub-agent is the wrong tool for a one-page procedure.** Spawning a child conversation re-pays system prompt and tools. That is worth it to keep a 6,000-token exploration out of the parent. It is waste for "use our commit-message template."
- **`allowed-tools` pre-approves a tool list for that skill.** That is a permission boundary, not a smaller model. The same model runs; it is just allowed to call `Bash(git:*)` without asking when the skill is active.
- **Put the trigger phrases you actually say.** If your team says "ship it" and the description only mentions "deploy," the catalog entry will sit idle. Read your own chat logs for the verbs; those are the triggers. The matcher in this session's code is a keyword stand-in — production harnesses let the model decide, which is *more* dependent on a description that names the situation.
- **Scripts beat improvised procedure.** If a skill says "run the test subset for this package," ship a `scripts/test.sh` next to `SKILL.md` and tell the model to run that file. A script has a stable exit code. A twelve-step list the model re-derives each time does not.
- **Project skills are the ones you review.** Personal skills in `~/.claude/skills/` are your muscle memory. Skills under `.claude/skills/` travel with the repo, show up in the pull request, and become the team's playbook. That is the whole point of "not a smaller model": the artifact is a file your teammates can argue with.

## How It Connects to What You Know
You already ship this as a plugin catalog (the 2026-07-13 session on the `llm` CLI is the same idea in-process: named hooks, discover implementers, call on demand). Skills move that pattern into markdown the model can read. Hooks are the closest relative of a CI check — they enforce. Sub-agents are the closest relative of `fork()` — they isolate. If you have been stuffing procedure into `CLAUDE.md` or Cursor rules, that file is the always-on catalog *and* the bodies glued together; splitting the bodies into skills is the lazy-load refactor.

## Try It Yourself
`code_example.py` is a tiny harness: four `SKILL.md` files in memory, a catalog built from frontmatter only, and a keyword matcher standing in for "the model decided this description fits." Type nothing — it runs three user phrases, prints which skill loaded, and compares the token bill of catalog-only vs body-loaded vs "dump every body into the always-on file" vs a hook vs a sub-agent. Pure Python, no API key.

## Glossary
- **Skill** — a folder with a `SKILL.md` instruction pack the harness can load when a task matches. Not a trained model.
- **`SKILL.md`** — the required file: YAML frontmatter (name, description, optional flags) plus markdown instructions.
- **Frontmatter** — the YAML block at the top of `SKILL.md`. The harness reads this at startup to build the catalog.
- **Catalog** — the list of skill names and descriptions sitting in the system prompt every turn.
- **Trigger phrase** — wording in the description that should make the skill relevant ("use when the user asks for a commit message").
- **Progressive disclosure** — keep the index cheap and load the body only when needed.
- **Hook** — a script the harness runs at a lifecycle event. Enforcement, not a playbook.
- **Sub-agent** — a nested conversation with its own context that returns a summary to the parent.
- **Harness** — the program around the model: it scans folders, builds the prompt, runs hooks, and spawns sub-agents.
- **`allowed-tools`** — frontmatter that pre-approves specific tools while a skill is active.
- **`disable-model-invocation`** — a flag that stops the model from auto-loading the skill; only `/name` will.
