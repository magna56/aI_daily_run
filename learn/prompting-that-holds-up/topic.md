# How to write prompts that hold up

**Category**: Coding Agents & Productivity
**Tags**: prompt-engineering, coding-agents
**Date**: 2026-08-23
**Level**: Start here
**For**: Using tools
**Hook**: Vague instructions make agents invent scope. A spec with examples is what holds up in production.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

If you tell a helper "make the room nicer," they might paint the walls, throw out a chair, and buy a plant you hate. If you say "move the blue chair to the window, do not touch the shelves, here is a photo of how it should look," they have a job. The helper is not being difficult. You gave them a wish, not a spec.

## The Problem

Production prompts die the same way production tickets die: "make it better," "handle the edge cases," "be careful with prod." The model fills the gaps with whatever continuation was likely in training — extra files, a new helper, a refactor you did not ask for. Then you spend the afternoon reverting. People blame the model. The prompt never named the output shape, the stop condition, or one example of done.

## For a Software Engineer

This is an interface, not poetry. A prompt that holds up looks like a function signature plus two tests: inputs, outputs, invariants, and a worked example. "Write a good commit message" is `f(??) -> ??`. "Write a commit message in this template, 50-char subject, no trailer, here are two good and one bad" is something you can grade.

The number worth feeling: one extra sentence of *negative* spec — "do not add a new file" — often saves more than a paragraph of vibe. Models are next-token machines (lesson 1). If "add a util" is a common continuation after "clean this up," they will add a util unless the prefix makes that token unlikely.

Monday morning: take the prompt you reuse this week. Add (1) the output contract, (2) one in-bounds example, (3) one out-of-bounds example, (4) what to do when information is missing. Run it twice. If the two runs invent different scope, the spec is still a wish.

## What This Means for You

**When this matters**: you paste the same fuzzy paragraph into Cursor or Claude every day, or a "simple" agent task keeps shipping extra files.

**How it affects you**: vague prompts fail by *invention*. You will not see a stack trace. You will see a polite diff that solved a different ticket.

**What to do about it**: write the prompt like a ticket you would give a new hire on their second day — acceptance checks included. Put standing rules in `CLAUDE.md` / Cursor rules, not in a paste you will drift. For agents, name the files they may touch.

## What It Is

A production prompt is a spec:

- **Job** — one sentence.
- **Inputs** — what they can read (paths, APIs, "only the open file").
- **Outputs** — format, file list, "diff only," "JSON with these keys."
- **Invariants** — do not, never, stop if.
- **Examples** — one happy path, one refusal / missing-info path.
- **Done** — how they know to stop.

Few-shot examples work because they are extra prefix that makes the desired continuation likely. They are not magic. Bad examples teach bad continuations. Three sharp examples beat twelve mushy ones.

Chain-of-thought is still tokens (lesson 1). Asking the model to "think step by step" can help on puzzles and hurt on "return this JSON." If a parser is downstream, constrain the output; do not hope.

## Why It Matters

Coding agents amplify a weak spec. A chat box invents text. An agent invents *edits*. The same fuzzy sentence is more expensive in the repo (lesson 4). Teams that treat prompts as source — versioned, reviewed, tested against a tiny fixture — stop having "it usually works" as the quality bar.

## Key Technical Details

**Background first.** The model only sees the prefix. A system prompt, a rules file, retrieved docs, and the user message are one concatenated string at the end of the day. Later tokens cannot "go back" and unread an earlier contradiction. If two instructions fight, the likely continuation is whoever won in training plus whoever appeared last.

- **Examples beat adjectives.** "Be concise" is weak. Two sample replies of the length you want are strong.
- **Name the escape hatch.** "If the file is missing, say so and stop" prevents a fictional file.
- **Put invariants near the output.** A buried "never commit" in paragraph one loses to "commit the fix" in the user message.
- **Test prompts like tests.** Three fixtures. Same prompt. Fail if scope drifts.

## How It Connects to What You Know

You would not ship an API with a comment that says "be reasonable." You ship a schema. Prompts that survive contact with an agent are schemas plus examples.

Previous: [How tokens and sampling work](#learn/tokens-and-sampling). Next: [Coding agents 101](#learn/coding-agents-101).

## Try It Yourself

`code_example.py` scores a tiny next-token table on a vague instruction vs the same job with a spec and a counterexample, so you can see the "invent a file" continuation lose probability when the prefix actually forbids it.

## Glossary

- **Prompt** — the prefix you send: system, rules, examples, user text.
- **Spec** — a prompt that names inputs, outputs, invariants, and done.
- **Few-shot** — examples in the prefix that show the output shape.
- **Invariant** — a rule that must hold even if the model has a "better idea."
- **Scope creep** — extra files, refactors, or features the ticket did not ask for.
