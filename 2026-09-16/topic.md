# What a Coding Agent Loads Into Every Subagent You Spawn

**Category**: Coding Agents & Productivity
**Tags**: context-engineering, cost, agents
**Date**: 2026-09-16
**Level**: Start here
**For**: Using tools
**Hook**: Handing work to a helper agent gives it a clean context window, not an empty one. Your project instructions load into every helper first, every time.
**Engineer's view**: This is a cold-start config read with no cache. Every helper agent you spawn re-loads your whole instruction hierarchy before it sees the task. Fan out to ten searchers and you buy ten copies of your coding standards, delivered to agents that will never write a line of your code.
**TLDR**: A helper agent starts with a fresh context window, but it is not empty. Your instruction files load into every one of them before the task arrives.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine a helper who forgets everything between jobs. Every time you ask for help, you hand them the company handbook first. Then you tell them the actual job.

For a big job, reading the handbook is worth it. For "count how many files mention the word billing", it is forty pages of rules about writing code, handed to someone who is only going to count.

Now ask five helpers at once. That is five handbooks. The handbook is not free, and you pay for it every single time.

## The Problem

You have shipped this bug before, in a system with no AI anywhere near it. A service reads its config file at startup. That is fine, because startup happens once. Then someone moves the service to Lambda. Now "startup" happens on every request. Nobody changed the config read. It just went from happening once to happening two thousand times an hour.

Handing work to a helper agent has the same shape.

Your instruction files load into the main session once. Everyone knows that part. What is less obvious is that they load again into every helper you spawn, in full, before the helper reads a word of its task.

The pile is bigger than most people think. Claude Code reads `CLAUDE.md` from your working directory and every directory above it. It also reads `.claude/rules/*.md`, your personal `~/.claude/CLAUDE.md`, and any `CLAUDE.local.md` sitting beside them. Anything those files import with `@path` is expanded too, up to four hops deep. Splitting a long file into imports organizes it and shrinks nothing, because imports load at launch as well.

Then you ask for a repo-wide search and five helpers go out in parallel. Five copies of all of it, delivered to five agents that are about to run `grep`.

The fix is one line in the helper's definition file. `omitClaudeMd: true` launches that agent without your user, project, and local instructions. Your organization's managed policy file still loads, so this is a context decision rather than a way around one.

```figure
{ "kind": "system",
  "title": "The whole argument: what each helper pays for before it starts",
  "lanes": [
    { "t": "one fan-out", "nodes": [
        { "id": "spawn", "t": "5 helpers spawned" } ] },
    { "t": "each one loads, by default", "nodes": [
        { "id": "yours", "t": "your instruction hierarchy", "s": "bad" },
        { "id": "policy", "t": "managed policy", "s": "neutral" },
        { "id": "task", "t": "the actual task", "s": "ok" } ] },
    { "t": "with omitClaudeMd: true", "nodes": [
        { "id": "after", "t": "policy and task only", "s": "new" } ] }
  ],
  "edges": [
    { "from": "spawn", "to": "yours", "t": "paid 5x", "s": "bad" },
    { "from": "spawn", "to": "policy", "s": "neutral" },
    { "from": "spawn", "to": "task", "s": "ok" },
    { "from": "yours", "to": "after", "t": "dropped", "s": "new" },
    { "from": "policy", "to": "after", "s": "neutral" } ],
  "note": "The middle lane is paid once per helper. Only one of its three rows is the job you asked for." }
```

## The Fix: Launch the Helper Without Your Instruction Files

A subagent gets a fresh context window. Fresh is not empty. Six things are already in it before your task arrives:

its own system prompt, the task message the parent wrote, **your CLAUDE.md hierarchy**, a git status snapshot, the full text of any skill named in the agent's `skills` field, and a roster of the other agents in the session.

The list of what does *not* arrive is the more surprising half. A subagent gets none of the conversation history. It does not see files the parent already read, skills the parent already ran, your output style, or the parent's auto memory. It cannot see how much context the parent has left.

So the helper knows your entire coding standard and nothing about the last twenty minutes of work.

### Why doesn't splitting it into imports help?

Because `@path` imports are expanded at launch, not read on demand. The docs are explicit that imports help organization and do not reduce context. A 600-line `CLAUDE.md` broken into six 100-line imports is the same 600 lines in the window. Path-scoped rules in `.claude/rules/` are the mechanism that actually defers loading, and they defer until Claude touches a matching file.

```figure
{ "kind": "anatomy",
  "title": "Everything that loads at launch, and what each lever reaches",
  "lines": [
    "/Library/Application Support/ClaudeCode/CLAUDE.md",
    "~/.claude/CLAUDE.md",
    "~/.claude/rules/*.md",
    "<repo>/CLAUDE.md   (and every parent directory)",
    "<repo>/.claude/rules/*.md",
    "<repo>/CLAUDE.local.md",
    "  @imports from any of the above, 4 hops deep"
  ],
  "callouts": [
    { "line": 0, "t": "Managed policy. omitClaudeMd keeps this, and claudeMdExcludes cannot remove it either.", "s": "neutral" },
    { "line": 3, "t": "Every ancestor directory counts, which is why a monorepo picks up other teams' files.", "s": "bad" },
    { "line": 6, "t": "Expanded at launch, so splitting a long file into imports shrinks nothing.", "s": "bad" }
  ],
  "note": "omitClaudeMd drops lines 2-7 for one agent. claudeMdExcludes drops named files for everything." }
```

### Wait, doesn't the helper need my conventions?

It depends entirely on what the helper does. An agent that writes code in your repo needs them. An agent that searches, counts, extracts, or summarizes does not. Anthropic already made this call for its own built-ins: the `Explore` and `Plan` agents skip your instruction files, and they are the two that read rather than write.

### Can I use this to skip my company's policy file?

No, and this is the honest boundary. `omitClaudeMd` drops user, project, and local files. A managed policy `CLAUDE.md` still loads into the agent. The same is true of `claudeMdExcludes`, the glob setting for skipping specific files: managed policy cannot be excluded by it either.

## What This Means for You

**When this matters.** It matters in proportion to two numbers multiplied together: how big your instruction hierarchy is, and how many helpers you spawn. A 40-line `CLAUDE.md` and no subagents is nothing. A monorepo where you launch three directories deep, picking up ancestor files from two other teams, and a workflow that fans out to ten agents, is the same cost paid ten times.

**How it affects you.** Every token of instruction in a helper is a token that is not available for the helper's actual job, and it is charged on every spawn. It also works against you on quality. An agent told to count occurrences, then handed two thousand tokens of guidance about test naming and commit style, has been given a worse signal-to-noise ratio for the one thing you asked.

**What to do about it.** Start by looking, because most people have never seen this number. Run `/context` in a session and read the **Memory files** line. That is what loads once for you and again for every helper.

Then measure the hierarchy directly, which takes one command and no configuration:

```bash
# every instruction file that loads at launch, and what it weighs
wc -c CLAUDE.md .claude/CLAUDE.md CLAUDE.local.md .claude/rules/*.md ~/.claude/CLAUDE.md 2>/dev/null
```

Then add `omitClaudeMd: true` to the agents that read rather than write. If you cannot edit the agent files, the monorepo case has its own answer below.

`code_example.py` resolves this hierarchy for you and prices the fan-out. On its demo monorepo, one agent carries 1,553 tokens of instructions before its task, and a five-way search pays that six times over. Point `START_DIR` at your own checkout to get your number instead of its number.

```figure
{ "kind": "bars",
  "title": "One five-way search, three settings (demo monorepo)",
  "bars": [
    { "label": "default", "v": 100, "d": "9,318 tok", "s": "bad" },
    { "label": "claudeMdExcludes on the ancestor file", "v": 61, "d": "5,688 tok", "s": "ok" },
    { "label": "omitClaudeMd on the helpers", "v": 21, "d": "1,978 tok", "s": "new" }
  ],
  "note": "Instruction tokens only, before any task or result. The two levers stack, and neither touches managed policy." }
```

## Implementing It

**The change.** Three roles touch this, and only the first is the one the changelog entry was written for.

*Role 1: whoever owns the agent file.* This is a single frontmatter key in `.claude/agents/<name>.md`. Add it to agents that search, summarize, extract, or review prose, and leave it off agents that write code:

```markdown
---
name: repo-searcher
description: Finds where a symbol is defined and used across the repo.
tools: Read, Grep, Glob
model: haiku
omitClaudeMd: true
---

Search the repository and report file paths with line numbers.
Report what you found. Do not edit any file.
```

*Role 2: whoever launches agents programmatically.* The same key exists in the `--agents` JSON, which is where SDK callers and CI jobs define agents. The field name is identical, so a definition can move between the two forms unchanged:

```bash
claude --agents '{
  "repo-searcher": {
    "description": "Finds where a symbol is defined and used.",
    "tools": ["Read", "Grep", "Glob"],
    "model": "haiku",
    "omitClaudeMd": true,
    "prompt": "Search and report paths with line numbers. Do not edit."
  }
}' -p "where is retry backoff configured?"
```

*Role 3: whoever cannot edit the agent files.* In a monorepo you often inherit ancestor instruction files you did not write and cannot delete. `claudeMdExcludes` takes globs matched against absolute paths, and it cuts the file out of the main session and every helper at once. Put it in `.claude/settings.local.json` so it stays on your machine:

```json
{
  "claudeMdExcludes": [
    "**/monorepo/CLAUDE.md",
    "/Users/you/monorepo/other-team/.claude/rules/**"
  ]
}
```

Note the asymmetry between roles one and three. `omitClaudeMd` is per agent and keeps the file for your main session. `claudeMdExcludes` is per file and removes it from everything. Reach for the first when the file is good and the agent does not need it, and the second when the file should not have been in your context at all.

**How you know it worked.** Do not guess at this, because there is a hook built to answer it. `InstructionsLoaded` fires whenever an instruction file enters context, and it carries a matcher for *why* it loaded: `session_start`, `nested_traversal`, `path_glob_match`, `include`, or `compact`. Hook payloads arrive on standard input, so the cheapest useful version appends the whole event and lets you read the shape yourself:

```json
{
  "hooks": {
    "InstructionsLoaded": [
      { "matcher": "session_start",
        "hooks": [{ "type": "command", "command": "cat >> /tmp/adl-loaded.jsonl" }] }
    ]
  }
}
```

Run one task that spawns a helper, then count the events. Before the change you get a burst per agent launch, including the helpers. After it, the helper launches stop producing them and the main session's burst is unchanged. If the helper still logs your files, the key is in the wrong file or the agent is a `fork`, which inherits the parent conversation by design and ignores this.

The cheaper check is `/context` before and after on the main session, which catches a `claudeMdExcludes` change but not an `omitClaudeMd` one, because that key only affects helpers.

## When Skipping Your Instructions Is the Wrong Tool

The obvious failure is putting this on an agent that writes code. Your instructions exist because you got tired of correcting the same thing. An agent that does not have them will pick a different test framework, a different import style, and a naming convention you abandoned two years ago. You will spend more time in review than you saved in tokens, and the tokens were the cheap part.

It is also not a fix for a bloated `CLAUDE.md`. If your instruction file is 900 lines, hiding it from helpers leaves the main session paying for it on every single turn, which is the larger bill. Fix the file first. The docs suggest 200 lines per file as a target, `/doctor` will propose trims, and path-scoped rules in `.claude/rules/` load only when Claude opens a matching file.

And it is not a compliance boundary. Managed policy still loads. If you were hoping to quiet an organization-wide instruction, this is the wrong lever and a conversation with whoever deployed it is the right one.

Three questions before you add the key:

- Does this agent write files in my repository? If yes, stop.
- Would I be comfortable if this agent had never read my conventions?
- Is the real problem that my instruction file is too big for the main session too?

## Glossary

- **subagent** — a second agent the main one hands a task to, with its own context window and tools
- **context window** — the total text a model can see at once, including instructions, task, and history
- **CLAUDE.md** — a markdown file of standing instructions, loaded at the start of every session
- **managed policy** — an organization-deployed instruction file that individual settings cannot exclude
- **fork** — a subagent that inherits the parent's full conversation instead of starting fresh
- **path-scoped rules** — instruction files that load only when Claude opens a file matching their globs
