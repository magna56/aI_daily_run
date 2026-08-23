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
There is a difference between texting a friend a photo of a broken shelf and inviting them into the workshop. In the text they can only guess from the photo. In the workshop they can open drawers, read the label on the wood glue, and — if you set the rule — ask before they turn on the saw. Claude Code and Cursor are the workshop. The web chat box is the text thread. The friend is not smarter in the workshop. They can just see the room and touch the tools.

## The Problem
People paste a function into ChatGPT, get a plausible rewrite, then paste it back and break three callers they forgot about. They switch to Cursor or Claude Code, type the same sentence, and wonder why *this* time the tool found the callers — or why it also ran the tests, or why it asked permission to delete a file. The model family might even be the same. The product is not. A coding agent is a model plus your repository plus a permission gate. If you use it like a chat box, you leave the repo on the table. If you use a chat box like an agent, you are the one who has to be the filesystem.

## For a Software Engineer
This is the difference between a pure function and a process with I/O. A chat completion is `f(prompt) -> text`. A coding agent is a loop: read the project briefing, decide a tool, wait for permission, run the tool, observe, repeat. The "intelligence" you feel is mostly *state* — files, git status, test output — stuffed back into the prefix each turn.

The number worth feeling: a 400-line file you paste into chat costs ~400 lines on *every* follow-up in that thread, and still misses the other 40 files that import it. An agent that runs `grep` and reads 40 lines of a caller pays for what it needs. That is why the same model "knows your codebase" in Cursor and "makes up an API" in a paste box.

Monday-morning action: use chat for questions that do not need the tree (design, API shape, "what does this error usually mean?"). Use the coding agent when the answer depends on *this* repo — multi-file edits, tests, refactors, "where is this set?" Put standing conventions in `CLAUDE.md` (or Cursor rules), not in a paste you will forget tomorrow. Leave permissions on ask for writes and shell until you trust the loop.

## What This Means for You
**When this matters**: you have both a chat product and a coding agent (Claude Code, Cursor, Codex, Gemini CLI) and you keep reaching for the wrong one — or you opened the agent and it still behaves like it cannot see the project.

**How it affects you**: wrong surface, wrong failure. Chat fails by hallucination: it invents a helper that exists in some other codebase. The agent fails by action: it can edit the real helper, run a real command, and — if you said yes too fast — push that to a branch. Permissions are not ceremony. They are the type system for side effects.

**What to do about it**: decide per task. No repo needed → chat. Repo needed → agent, started *in the project directory*, with a short `CLAUDE.md` that names build/test commands and the few rules you actually enforce. Do not dump the whole tree into the prompt. Let the agent search. Approve writes and shell until the command is routine enough to allowlist. Never turn on "bypass permissions" on a machine with credentials and production access.

## What It Is
Claude Code is Anthropic's coding agent: a terminal (and IDE) loop that can read and write files, run commands, and keep a session over your working tree. Cursor is an editor with a similar loop baked into the UI — chat that can see open files, an agent that can apply diffs, rules files for standing instructions. Other tools (Codex, Gemini CLI) are the same shape. The brand is not the lesson. The shape is.

Three pieces make the shape work.

**Files as context.** The agent does not magically contain your repo. It lists directories, greps, and reads files, then those bytes become tokens in the context window. You can also `@`-mention a path to force a file in. The skill is pointing, not pasting.

**Project memory (`CLAUDE.md` and friends).** Claude Code reads `CLAUDE.md` or `.claude/CLAUDE.md` at the start of a session — the briefing you would give a new teammate: how to test, which package manager, what not to do. Cursor's rules files play the same role. This is context engineering: a small, high-signal document beats a 2,000-line dump of "architecture."

**Permissions.** The model *proposes* a tool call. The harness decides whether to run it. Claude Code's rules are allow / ask / deny, plus modes (manual, plan, accept-edits, bypass). Cursor has review-before-apply for diffs and its own terminal approvals. The policy is enforced by the product, not by the model's good intentions.

## Why It Matters
Once you separate the model from the harness, a lot of "this tool is smarter" talk gets quieter. The model in the chat box and the model in the agent may be cousins. The agent wins on *grounding* (it can read `src/auth.ts`) and *closure* (it can run `pytest` and read the failure). The chat box wins on *isolation* (it cannot `rm` your home directory) and on tasks that are not about this tree.

It also changes how you write instructions. A chat prompt that includes a 200-line paste is doing the agent's job by hand. An agent prompt that says "figure it out" with an empty `CLAUDE.md` is doing the chat's job in a workshop full of power tools. The next chapter in spirit is prompting (the previous Learn page): the agent still only continues a prefix. `CLAUDE.md` is the part of the prefix you do not want to retype.

Teams feel this when they skip the briefing. The agent uses `npm` in a `pnpm` repo, writes tests in the wrong folder, or "helps" by reformatting a generated file. That is not a model failure. That is a missing project README aimed at the agent.

## Key Technical Details

**Background first.** A *chat box* is a single request/response (or a thread of them) with no filesystem unless you upload a file. A *coding agent* is a model plus tools, run in a loop by a harness (Claude Code, Cursor, and so on). *Context* is whatever tokens the model can see this turn — system prompt, `CLAUDE.md`, conversation, file contents the tools just returned. *Permissions* are harness rules that allow, ask, or deny a proposed tool call. *CLAUDE.md* is a markdown file the Claude Code harness loads as standing instructions; Cursor rules are the same idea under a different filename.

- **Pick the surface by whether the tree matters.** Design a retry policy, compare two APIs, or learn a concept → chat (or this Learn track). Change `retry()` and update callers, bisect a test, or add a flag that already exists in three files → agent, in the repo root.
- **Start the agent where the git root is.** Claude Code's working directory is the project's world. If you launch it in `~/Downloads`, it will not "know" the service in `~/src/payments`. Cursor is the same: open the workspace, not a single orphan file.
- **`CLAUDE.md` is a briefing, not a novel.** Put commands (`pnpm test`, `make lint`), layout (`handlers in src/http/`), and hard noes (`never commit .env`, `do not edit codegen/`). Anthropic's own guidance: keep it high-signal; a long file becomes noise. Run `/init` if you want a starter, then cut. Cursor: project rules with the same content.
- **Hierarchy exists.** Claude Code can load a user-level `~/.claude/CLAUDE.md` (your preferences), a project `CLAUDE.md` (the team's), and on-demand subdirectory files. If two files fight, you will see random compliance — the same conflict as two system prompts. Prefer one project file plus a short personal file.
- **Permissions are allow / ask / deny, plus a mode.** Default/manual: writes and shell usually ask. Plan mode: look, do not edit. Accept-edits: apply file diffs without asking, still ask for many shell commands. Bypass: skip prompts — only in a throwaway sandbox. Deny rules still apply even when you are sloppy. `/permissions` is the live editor; check rules into the repo for the team.
- **The model cannot bypass a deny.** Preference training makes models *cooperative*, not *sandboxed*. Sandboxing and permission rules are the harness. Treat "the model said it wouldn't" as a comment, not a control.
- **Context is a budget the agent spends on files.** Every `Read` is tokens. A good agent greps, then reads a slice. A bad habit is `@`-mentioning the whole `src/` tree "just in case." That is the paste-into-chat mistake with extra steps. Point at the entry file and the test; let search do the rest.
- **You are still the reviewer.** The agent can open a PR. CI and you decide if it lands. Use the agent to produce the diff; do not skip `git diff` because the UI summarized it.

## How It Connects to What You Know
A chat box is `curl` plus a JSON body. A coding agent is a REPL with `open()`, `subprocess`, and `sudo` — except `sudo` is the permission prompt. `CLAUDE.md` is an onboarding doc that happens to be in the system prefix, the same role as `CONTRIBUTING.md` except the new hire actually reads it every session. Permissions are IAM for tools: default deny, allowlist the boring paths, never `*`.

This page is a chapter in the Learn track. The prompting chapter told you to write specs; this one tells you *where those specs live* (the agent, `CLAUDE.md`, rules) and when to stay in a chat box. The daily lab is the case-study feed — later dated posts about a Claude Code changelog, a harness bug, or a team workflow are applications of this chapter, not a new product category.

## Try It Yourself
`code_example.py` builds a fake mini-repo and runs the same request two ways: a chat box that only sees a pasted snippet, and an agent that can list/read files but must request permission to write. It also toggles a `CLAUDE.md` that says "use pnpm, never edit codegen." The printout is the whole lesson: same model-shaped policy, different world, different diff.

## Glossary
- **Chat box** — a text interface that sends prompts and shows replies, with no live access to your working tree unless you paste or upload.
- **Coding agent** — a model plus tools (read, write, shell, search) run in a loop by a harness, usually rooted in a repository.
- **Harness** — the product around the model: Claude Code, Cursor, Codex, Gemini CLI. It loads memory, runs tools, and enforces permissions.
- **CLAUDE.md** — a markdown briefing Claude Code loads at session start; project conventions, commands, and constraints.
- **Cursor rules** — Cursor's equivalent standing instructions (project or user rules the agent sees every turn).
- **Context** — the tokens in the current request: instructions, memory files, chat, and file contents the tools returned.
- **Context engineering** — choosing what enters that window (briefing, `@` files, search results) instead of pasting everything.
- **Permissions** — harness policies: allow a tool, ask the user, or deny it. Modes change the default (manual, plan, accept-edits, bypass).
- **Allowlist** — a specific command or path that may run without asking, e.g. `pnpm test`.
- **Bypass permissions** — a mode that skips most approval prompts; unsafe on a trusted machine with real credentials.
- **Plan mode** — a mode that explores and proposes without applying edits.
- **Working tree** — the checkout the agent can see; usually the git root you launched from.
- **IAM** (Identity and Access Management) — the usual allow/deny policy model; permissions are that idea applied to agent tools.
- **REPL** (Read-Eval-Print Loop) — an interactive program loop; a coding agent is closer to this than to a single function call.
- **PR** (Pull Request) — the review surface; the agent can open one, you still decide if it lands.
