# Specs and Examples Beat Vague Prompts

**Category**: Coding Agents & Productivity
**Tags**: prompt-engineering, coding-agents
**Date**: 2026-08-23
**Level**: Start here
**For**: Using tools
**Hook**: Vague instructions make agents invent scope. A spec with examples is what holds up in production.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5
If you tell a new helper "make the kitchen nicer," they might repaint the walls, throw out a mug they don't like, and reorganize the drawers. If you show them a photo of the shelf you want, a list of what must stay, and one example of a drawer that is already "done," they copy the pattern. Same helper. Different instructions. The first version sounds friendly. The second version is the one you can live with after they leave.

## The Problem
A prompt that works once in a chat box falls apart when you put it in a loop. "Improve this function," "be careful," and "follow best practices" do not tell a coding agent which files are in scope, what "done" looks like, or what it must not touch. In a single chat you can course-correct. In production — a nightly agent, a PR bot, a skill that runs without you — there is no adult in the room. The model will still pick a next token. If the prefix did not constrain the task, the tokens will invent a task.

## For a Software Engineer
This is an API-without-types problem. A prompt is an untyped function call: no schema, no compiler, no `Exact<T>`. The model will *always* return something that looks like a completion. Specificity is how you add types. Examples are how you add tests. Negative examples ("do not rename the public function") are how you add regressions.

The number worth feeling: a one-line wish and a twenty-line spec often cost a similar number of output tokens for a small edit — the spec spends tokens on the *input*, where they buy constraint, instead of on a long, wandering *output*. Teams that "save tokens" by shortening the prompt frequently pay them back in retries, reverted diffs, and review time. A failed agent turn is the expensive one.

Monday-morning action: rewrite one prompt you reuse (a Cursor rule, a Claude skill, a code-review command) as if it were a ticket: goal, in-scope paths, out-of-scope paths, one good example, one bad example, and a checkable done condition. If you cannot write the done condition, the agent cannot know it either.

## What This Means for You
**When this matters**: you are writing a prompt that will run more than once — a coding-agent instruction, a review bot, a data-extraction call, anything without you watching every token.

**How it affects you**: vague prompts fail by *expansion*. The agent refactors a neighbor file, "improves" naming, upgrades a dependency, or invents a helper. That looks helpful in a demo and reads as a hostile PR on Monday. Specific prompts fail smaller: they miss an edge case you did not list. You can add the edge case. You cannot easily subtract a creative rewrite of `utils.py`.

**What to do about it**: put the contract in the prefix. Name files. Show the exact output shape (a diff hunk, a JSON schema, a commit message template). Give one input→output example that you would merge. Give one counter-example you would reject. Add a verifier the model cannot talk past — tests, a linter, a schema check — because a prompt is not a test suite.

## What It Is
Prompting that holds up is specification, not incantation. You are writing the minimum document a competent teammate would need to do the task without Slack. For a language model that only ever continues the prefix (see the first Learn chapter), that document *is* the program.

The techniques that keep showing up in provider docs are boring on purpose:

- **Be specific.** Say what to change, where, and what "correct" means. "Add a 30s timeout to `fetchUser` in `src/api.ts` and leave the signature alone" beats "make the API more robust."
- **Show examples.** One worked example (few-shot) does more than a paragraph of adjectives. Two examples that differ in the dimension you care about (a success and a refusal, a small diff and a "do nothing") do more than five similar ones.
- **State the non-goals.** Agents optimize for looking helpful. "Do not edit files under `vendor/`," "do not add dependencies," "if the test already passes, make no diff" are load-bearing.

In a chat you can do this conversationally. In an agent, the first message has to carry it, because the agent will start reading and writing files before you see a draft.

## Why It Matters
Coding agents multiply prompt quality. A vague instruction in ChatGPT wastes one reply. A vague instruction in Claude Code or Cursor wastes a tree of tool calls: searches, edits, test runs, and a PR that is expensive to unwind. The failure mode is not "the model is bad at code." It is "the prefix did not say what success is, so the model optimized for something else" — usually completeness, cleverness, or matching a training-data style of "thorough engineer."

Production agents add three extra ways to break.

First, **context conflicts**. A `CLAUDE.md` that says "always add tests" plus a user prompt that says "tiny hotfix, no tests" will be resolved however the model feels that day. Make the precedence explicit.

Second, **unbounded tools**. "Fix the flaky test" with a shell is an invitation to rerun the suite until the flake hides, or to pin a sleep. Constrain the tool: which command, how many retries, what to do on failure.

Third, **no verifier**. If the only check is "the model said it worked," you have an honor system. Hold the output to `pytest`, `tsc`, a JSON schema, or a screenshot diff. The prompt describes intent; the verifier enforces it.

## Key Technical Details

**Background first.** A *prompt* is the token prefix you send: system instructions, user text, examples, and any files you attach. *Few-shot prompting* means putting input/output examples in that prefix so the next-token distribution shifts toward the same pattern. A *coding agent* is a model plus tools (read file, edit file, run command) in a loop. *Production* here means the prompt runs without a human steering every step. A *verifier* is a check the model cannot talk its way around — a test runner, a typechecker, a schema validator.

- **Specificity is scope control.** Name paths, symbols, and invariants. "Change only `retry()` in `src/net.ts`. Do not touch callers. Public signature stays `(fn, opts) => Promise`." That is a patch ticket. "Improve retries" is a month of work.
- **Examples beat adjectives.** "Be concise" is weak because the model has seen every length of "concise." A 12-line example reply, or a 6-line diff, is a sample from the distribution you want. Prefer real repo snippets over toy `foo/bar` examples; the tokenizer and the model both latch onto surface form.
- **Negative examples close the failure mode you have already seen.** If the agent keeps rewriting comments, show a rejected diff that is "comment-only" and say reject. If it keeps adding `try/catch` soup, show that. This is the same instinct as a regression test.
- **Structured output is a prompt plus a parser.** Ask for JSON, a unified diff, or a specific markdown shape, then *parse* it. If parse fails, retry or abort — do not "flexibly" accept prose. Providers now have native schema / tool-call formats; use them when the output is data.
- **What breaks in agent loops is state, not poetry.** The prompt is re-sent (or summarized) every turn. A rule buried in turn 1 can be compressed away. Put standing rules in `CLAUDE.md` or a Cursor rule file, keep the turn prompt to *this* task, and repeat the hard constraints ("no new dependencies") near the end of the user message, where they are less likely to be dropped.
- **Helpfulness is the default objective.** Preference training (first chapter) rewards replies that look useful. An agent will therefore take extra steps unless you make extra steps look like failure. "If you cannot find `MAX_RETRIES`, stop and say so" is a first-class instruction.
- **Evals are how you know a prompt held up.** Save ten real tasks, the spec you used, and a check (tests pass / diff only listed files / JSON parses). Change the prompt, rerun. A prompt you have never eval'd is a guess that happened to work on the example you remember.

## How It Connects to What You Know
You would not file a Jira ticket that says "make it better" and then be surprised at the PR. You would not ship an HTTP API without a schema and then blame the client for sending the wrong JSON. Prompts are the same contract, written in English because the runtime has no typechecker. Examples are fixtures. Verifiers are CI.

This page is a chapter in the Learn track. The first two chapters explained the machine (next-token, then tokens and sampling). This one is how you steer that machine with text. The daily lab is the case-study feed — later dated posts about a new agent harness, a prompt-injection paper, or a team that eval'd their review bot are applications of this chapter, not a different idea.

## Try It Yourself
`code_example.py` is a tiny fake agent: it "edits" a Python function under a vague instruction and under a spec-with-examples. A rubric scores scope creep, missing constraints, and whether tests would still pass. The vague wish scores 2/10 (busy diff, extra files, no deadline). The spec scores 10/10.

## Glossary
- **Prompt** — the token prefix sent to the model: instructions, user text, examples, and attached files.
- **Prompt engineering** — writing and iterating that prefix so the next-token distribution matches a spec; not a bag of magic phrases.
- **Few-shot** — including one or more input/output examples in the prompt so the model continues the pattern.
- **Negative example** — an output you would reject, shown so the model can avoid that pattern.
- **System prompt** — standing instructions that sit above the user message (product voice, tool rules, safety).
- **Coding agent** — a model in a loop with tools to read, edit, and run code, rather than a single chat reply.
- **Scope creep** — the agent changing files or behavior you did not ask for, usually in the name of being helpful.
- **Verifier** — an automatic check (tests, types, schema) that decides whether the output is acceptable.
- **Eval** — a saved set of tasks plus a scoring rule, used to compare prompts without relying on memory.
- **CLAUDE.md** — a project briefing file that Claude Code reads at the start of a session; covered in the next chapter.
- **API** (Application Programming Interface) — here, the idea that a prompt is an untyped call: no compiler, so the spec has to live in the text.
- **JSON** — a structured text format; ask for it, then parse it, instead of accepting free prose.
- **PR** (Pull Request) — the review surface a coding agent often produces; vague prompts show up as hostile diffs here.
- **CI** (Continuous Integration) — where verifiers (tests, types, schema) should run, because a prompt is not a test suite.
