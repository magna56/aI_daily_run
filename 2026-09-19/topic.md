# AGENTS.md: One Rules File for Claude, Codex, Cursor and Copilot

**Category**: Coding Agents & Productivity
**Tags**: context-engineering, prompt-engineering, reliability
**Date**: 2026-09-19
**Level**: Start here
**For**: Using tools
**Hook**: Four tools, four instruction files, all saying the same thing. They have converged on one file, and the rules for which one wins are not the ones you would guess.
**Engineer's view**: This is the same config duplicated in four places. You have shipped it before: a port number in the compose file, the Helm chart, the env sample and the README. They agreed the day you wrote them and disagreed a month later, and the wrong one was the one nobody read.
**TLDR**: Every major coding agent now reads AGENTS.md. Which file it actually uses depends on where that file sits, what else is in the repo, and which platform you are on.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine a shared kitchen with four housemates. Each one keeps their own copy of the house rules on their own shelf.

The day you write them, all four copies match. Then someone changes one. Now there are four sets of rules and nobody knows which is current, because everyone only ever reads their own.

The fix is one list on the fridge that everybody reads. That is the easy part. The hard part is that some housemates still check their own shelf first.

## The Problem

You have shipped this bug before, and it had nothing to do with AI. A port number lived in four places: the compose file, the Helm chart, the env sample, and the README. All four agreed the day you wrote them.

A month later they did not, and the one that was wrong was the one nobody had read since.

Coding agent instructions are that bug with more copies. A repo that has met more than one tool tends to carry four of them — one per vendor, each in the place that vendor looks — saying roughly the same thing in four slightly different ways. Nobody edits all four. They drift, and each tool confidently follows the stalest copy it happens to own.

This is now fixable rather than merely annoying, because the tools have settled on one filename. All four read `AGENTS.md`, so the four copies can collapse into one without any agent losing its instructions.

So the fix is to keep one file. The part worth ten minutes is that "which file wins" has three different answers depending on the tool, the directory, and the platform you are billed through.

```figure
{ "kind": "system",
  "title": "The whole argument: one file, but three different lookup rules",
  "lanes": [
    { "t": "your repo has", "nodes": [
        { "id": "one", "t": "one AGENTS.md", "s": "ok" },
        { "id": "many", "t": "four drifting files", "s": "bad" } ] },
    { "t": "each tool looks for", "nodes": [
        { "id": "own", "t": "its own file first", "s": "bad" },
        { "id": "near", "t": "the nearest AGENTS.md", "s": "new" } ] },
    { "t": "so it reads", "nodes": [
        { "id": "stale", "t": "whichever copy it owns", "s": "bad" },
        { "id": "same", "t": "the same rules as everyone", "s": "ok" } ] }
  ],
  "edges": [
    { "from": "many", "to": "own", "s": "bad" },
    { "from": "own", "to": "stale", "s": "bad" },
    { "from": "one", "to": "near", "s": "ok" },
    { "from": "near", "to": "same", "t": "closest wins", "s": "ok" } ],
  "note": "Deleting the extra copies is the fix. Knowing the lookup order is what stops you deleting the wrong one." }
```

## The Fix: Keep One AGENTS.md and Learn Each Tool's Lookup Order

`AGENTS.md` is plain markdown with no required fields. A README for agents: build and test commands, code style, testing instructions, commit conventions. There is no schema to learn, which is most of why it spread. It came out of a collaboration between Codex, Amp, Jules, Cursor and Factory. The Agentic AI Foundation stewards it under the Linux Foundation, and it sits in over 60,000 public repositories. Claude Code added it in 2.1.277.

The lookup order is the part with teeth.

### Which file does each tool actually read?

```figure
{ "kind": "anatomy",
  "title": "What each tool looks for, in the order it looks",
  "lines": [
    "Claude Code    CLAUDE.md  →  AGENTS.md   (fallback only)",
    "GitHub Copilot .github/copilot-instructions.md",
    "               .github/instructions/*.instructions.md",
    "               AGENTS.md  (nested, nearest wins)",
    "               CLAUDE.md  or  GEMINI.md",
    "Codex, Cursor  AGENTS.md  (nested, nearest wins)",
    "everyone       an explicit instruction in chat"
  ],
  "callouts": [
    { "line": 0, "t": "The fallback is one-way: AGENTS.md is read only when CLAUDE.md is absent.", "s": "new" },
    { "line": 4, "t": "Copilot reads its competitors' files. Most people do not know this one.", "s": "ok" },
    { "line": 6, "t": "Chat beats every file, every time. Useful for testing, dangerous as a habit.", "s": "bad" }
  ],
  "note": "Two tools read four filenames between them, and only one of those filenames is read by all of them." }
```

The surprise is in the Copilot column. It supports `.github/copilot-instructions.md`, path-scoped files under `.github/instructions/`, `AGENTS.md`, **and** `CLAUDE.md` or `GEMINI.md` in the repository root. Copilot will read a file named after a competitor.

### What if I keep both CLAUDE.md and AGENTS.md?

Then you have rebuilt the original problem with two files instead of four, and it is worse than it looks. Claude Code reads `CLAUDE.md` and stops. Copilot reads both. Codex and Cursor read only `AGENTS.md`.

So the two files drift, and the drift is invisible. Each tool is behaving correctly. You get different behavior from different agents on one repository, with nothing in any log to explain it.

### Does this survive a monorepo?

Yes, and this is the part that is genuinely well designed. `AGENTS.md` nests, and the rule is **nearest wins**: the file closest to the one being edited is the one applied. A rule in `packages/api/AGENTS.md` applies when the agent touches the API and not when it touches the web app.

Copilot follows the same nearest-wins rule. Claude Code's own nesting behavior is its own, so a monorepo is exactly where keeping both files hurts most.

## What This Means for You

**When this matters.** It matters if more than one agent has ever touched your repository, which is most teams now. It matters more if anyone has ever fixed a rule in one file and not the others. It also matters at review time: an agent that ignored a convention may have been reading a file you forgot existed.

**How it affects you.** The cost is not the duplicated text. It is that the failure is silent and looks like the model being careless. Your agent uses the wrong test command, you assume it did not read the instructions, and it did — just not the copy you edited.

**What to do about it.** Start by finding out how many you have. One command, no configuration:

```bash
# every instruction file any agent might read, in one list
find . -maxdepth 3 \( -name AGENTS.md -o -name CLAUDE.md -o -name GEMINI.md \
  -o -name '.cursorrules' -o -path '*/.github/copilot-instructions.md' \) -not -path './node_modules/*'
```

If that returns more than one, diff them before you delete anything. The differences are usually corrections someone made in one tool and never carried across. That means the stale copies hold the only record of some real decisions.

Then decide which file is the real one before you move a single line. On most teams that is `AGENTS.md`, because three of the four tools read nothing else. If anyone runs through Bedrock, Vertex or Foundry it is `CLAUDE.md` instead, and the consolidation runs the other way. Getting that backwards is the one mistake here that deletes working instructions rather than duplicate ones.

## Implementing It

**The change.** Three situations, and which one you are in decides the answer.

*Role 1: one repo, one set of rules.* Consolidate into `AGENTS.md` and delete the rest. Claude Code only falls back to `AGENTS.md` when `CLAUDE.md` is absent, so leaving an empty `CLAUDE.md` behind silently disables the fallback:

```bash
git mv CLAUDE.md AGENTS.md              # keep the history on the file people wrote
git rm .cursorrules .github/copilot-instructions.md
# verify: there must be no CLAUDE.md left, not even an empty one
test ! -e CLAUDE.md && echo "fallback active"
```

*Role 2: a monorepo.* Put shared rules at the root and package rules next to the package. The nearest file to the edited file wins, so a rule only needs to live where it applies:

```
AGENTS.md                      # build, test, commit conventions
packages/api/AGENTS.md         # handlers live in handlers/, integration tests need docker
packages/web/AGENTS.md         # components are function components, no class components
```

*Role 3: you are on Bedrock, Vertex or Foundry.* The `AGENTS.md` fallback is **not yet available** there. Deleting `CLAUDE.md` on those platforms does not move your rules to `AGENTS.md`, it removes them. Keep `CLAUDE.md` as the real file and make `AGENTS.md` point at it rather than duplicating the text:

```markdown
<!-- AGENTS.md -->
@CLAUDE.md

Tools other than Claude Code read this file; Claude Code reads CLAUDE.md directly.
```

Which way round you do that matters. Import the file the platform can actually read, and never maintain two copies of the same prose in a repo where a human will eventually edit only one.

The same import trick is worth knowing even off Bedrock. A one-line `AGENTS.md` that reads `@CLAUDE.md` keeps every tool on one source of truth. Nobody has to remember which filename their tool wants, and it costs a single line to maintain.

**How you know it worked.** Do not judge this by whether the agent behaved well, because a followed rule and a never-loaded rule both look like ordinary output. Ask the tool what it loaded.

In Claude Code, `/context` lists the files under **Memory files**, and `/config` shows which project instructions are active. The check that actually proves it is a canary: put one unmistakable line in the file, start a session, and ask for it back.

```markdown
<!-- AGENTS.md, temporarily -->
When asked for the canary, reply exactly: ORANGE-7714.
```

Ask each tool for the canary in a fresh session. A tool that answers with anything else never read the file, and you have found the drift before it costs you a review cycle. Delete the line afterward.

## When One Rules File Is the Wrong Tool

It is the wrong move when your tools genuinely need different instructions. Guidance about a specific agent's permission model, hooks or subagents is not portable. Put it in a shared file and every other tool reads advice it cannot act on. Shared conventions belong in `AGENTS.md`; tool-specific operating instructions belong in that tool's own file, and the split is worth the second file.

It is also wrong as a way to make a long file shorter. If your instructions do not get followed today, one file will not fix it — a 900-line `AGENTS.md` is read by four tools instead of one and ignored by all of them. Under 200 lines is the target that actually changes behavior.

And a shared file is a shared blast radius. One bad edit now reaches every agent on the team at once, where four files at least failed independently. That is a real cost of consolidating, and the answer is to review that file like code rather than to keep the copies.

Three questions before you consolidate:

- Do my existing files actually agree, or is one of them carrying a decision the others lost?
- Is anyone on this team running through Bedrock, Vertex or Foundry?
- Is what I am about to move genuinely shared, or is it advice about one tool?

## Glossary

- **AGENTS.md** — a plain markdown file of project instructions that most coding agents now read
- **nearest wins** — in a monorepo, the instruction file closest to the edited file is the one applied
- **fallback** — reading a second filename only when the first is absent, which is how Claude Code treats AGENTS.md
- **drift** — two copies of the same rules that stop agreeing because nobody edits both
- **canary** — a deliberately unmistakable line used to prove a file was loaded
- **lookup order** — the list of filenames a tool tries in turn, stopping at the first one that exists
