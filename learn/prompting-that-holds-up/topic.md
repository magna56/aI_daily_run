# How to Write Prompts That Hold Up

**Category**: Coding Agents & Productivity
**Tags**: prompt-engineering, coding-agents
**Date**: 2026-08-23
**Level**: Start here
**For**: Using tools
**Hook**: Vague instructions make agents invent scope. A spec with examples is what holds up in production.
**Kind**: Learn
**Time to read**: ~14 minutes

> **You'll be able to:** write a prompt the way you write a spec — background, task, requirements, constraints — and name which of a dozen techniques fixes a specific failure instead of reaching for all of them at once.

## Explain Like I'm 5

If you tell a helper "make the room nicer," they might paint the walls, throw out a chair, and buy a plant you hate. If you say "move the blue chair to the window, do not touch the shelves, here is a photo of how it should look," they have a job. The helper is not being difficult. You gave them a wish, not a spec.

## For a Software Engineer

**This is not a new skill. It is spec-writing wearing a costume.** Every technique below maps onto something you already do in a good ticket, a good PR description, or a good design doc — you already have the instinct, you are just not pointing it at the model.

| What a good ticket has | The prompt technique |
|---|---|
| Functional requirements — "the function shall take X, return Y" | Be specific about inputs and outputs |
| Acceptance criteria / test cases | Show examples (few-shot) |
| Non-functional requirements — "max 100ms latency" | Constrain the output |
| Design before implement | Chain of thought |
| Background, context, constraints | Role and context setting |
| Requirements gathering | Meta-prompting — let the model ask first |

**The test that actually works:** if your prompt would be a bad ticket, it will be a bad prompt. Enough context to act without asking, precise enough that "done" is unambiguous, scoped so one sitting finishes it — point that instinct at the model and most of "prompt engineering" collapses into things you already know.

**What to do differently on Monday:** the model only ever sees a prefix — system prompt, rules file, retrieved docs, your message, all concatenated into one string. It cannot go back and unread an earlier contradiction, and if two instructions fight, the one that appeared last usually wins. Put invariants (*never commit*, *do not touch other files*) close to the actual request, not buried in paragraph one of a rules file the model read ten thousand tokens ago.

## The Spec-Prompt Template

Four sections, in order, for anything more than a one-line ask:

```
Background:   who you are, tech stack, constraints
Task:         what you want, inputs, expected outputs
Requirements: edge cases, must-haves, must-nots
Constraints:  dependencies, style, scope limits
```

A worked example:

```
We're building a reconciliation service in Python 3.11. It runs on Kubernetes,
processes ~50K records/day, and writes to Postgres. We use SQLAlchemy and pytest.

Write a function that detects duplicate records. Two records are duplicates if
they share the same key, quantity, and timestamp within 1 second.

- Input: list[Record]   Output: list[tuple[Record, Record]] of duplicate pairs
- Must handle 50K records without OOM (batch if needed)
- Edge cases: empty list, single record, all duplicates

No new dependencies. Match the existing style in src/reconciliation/. Write pytest tests.
```

This is the difference between a wish and a job. "Make it better, follow best practices" has no output contract, so the model fills the gap with whatever continuation was likely in training — an extra file, a helper you did not ask for, a refactor you will spend the afternoon reverting. The example below scores exactly that gap.

## The Techniques, Grouped by What They Fix

Not fourteen unrelated tricks — four failure modes, each with one or two techniques that address it.

**The model invents scope** (extra files, unrequested refactors):
- **Be specific.** "Write a function to process data" is `f(??) -> ??`. Name the language, the input and output types, the constraint.
- **Constrain the output.** State what *not* to do: "only stdlib," "do not modify files outside `/src`," "diff only." One sentence of negative spec often saves more than a paragraph of positive description, because it makes the unwanted continuation less likely rather than merely undesired.
- **Name the escape hatch.** "If the file is missing, say so and stop" prevents a fabricated one.

**The model needs to reason, not just answer:**
- **Chain of thought.** For genuinely hard problems, ask it to reason before concluding: *"walk through each loop, identify nested iterations, then give your conclusion"* beats *"is this O(n) or O(n²)?"* asked cold. This costs tokens (lesson 2) and can *hurt* on tasks with one right shape — do not ask a JSON-only response to "think step by step" first.
- **Self-reflection.** A second pass — "now review what you wrote for off-by-ones and missed error handling" — catches what the generation pass didn't, because it is reading with different intent.

**The model needs to know what you know:**
- **Role and context.** It has no idea who you are or what your codebase looks like unless told. A CLAUDE.md or system prompt is *permanent* context — set once, resent every turn.
- **Few-shot examples.** Show, don't describe: two worked input→output pairs lock in a pattern faster than a paragraph of description. But bad examples teach bad continuations, and a shared incidental pattern (both examples happen to be lowercase) gets copied too — three sharp examples beat twelve mushy ones.
- **Reference grounding.** Paste the actual source. A model can only fabricate what it doesn't have; give it the real docs and it cites them instead.

**The request is genuinely ambiguous:**
- **Meta-prompting.** Before implementing, ask it to ask you: *"ask me the 3-5 questions you need answered before you start."* Use this when you are not sure what the constraints should be yourself.
- **Prompt chaining.** Split a pipeline into steps that each feed the next — extract, then classify, then generate — rather than one prompt trying to do all three. Each link is cheaper and easier to check.

## Three Workflows Worth Keeping as Templates

**Debugging** — paste the error and stack trace, paste the failing section, add *"here is what I've already tried,"* then ask for the top 3 causes ranked by likelihood.

**Code review** — *"Review this code for: 1) correctness — bugs, edge cases, off-by-ones, 2) performance, 3) security. For each issue: file:line, severity, fix."* A fixed rubric, reused, beats a fresh "does this look OK?" every time.

**Architecture** — state the problem and constraints, ask for the top 3 approaches with trade-offs, pick one, then *"design the interfaces, don't implement yet."* Separating the design pass from the implementation pass is the same discipline as a design doc before code.

## Quick Reference

| Term | Plain English |
|---|---|
| Prompt | The prefix you send: system, rules, examples, your message. Functionally a spec. |
| Few-shot | Showing 1–2 worked examples instead of only describing the output. |
| Chain of thought | Asking the model to reason before it answers. Costs tokens; not always a win. |
| Constraint | A stated *must-not*. Prevents rambling and scope creep more reliably than a *should*. |
| Meta-prompting | Asking the model what it needs to know before it starts. |
| Prompt chaining | Splitting one hard prompt into a pipeline of smaller, checkable ones. |
| Reference grounding | Pasting the real source so the model cites instead of fabricates. |
| Prefilling | Starting the model's own response (e.g. with `{`) to lock in a format. |
| Context engineering | Managing what occupies the context window, not just the wording. |
| Scope creep | Extra files, refactors, or features the request never asked for. |

## Do It Today

**Step 1 — see the gap, 2 minutes.** Run the example:

```bash
python3 learn/prompting-that-holds-up/code_example.py
```

It sends the same fake coding agent a vague wish and a spec with examples, against a fixed rubric. **You know it worked** when the vague wish scores **2/10** and touches `README.md` and `src/utils.py` it was never asked to touch, while the spec scores **10/10**, changes only `src/net.py`, and keeps the exact signature `def retry(fn, attempts=3, deadline=None):`. The underlying "model" did not change between runs — only the prefix did.

**Step 2 — rewrite a prompt you actually reuse.** Take the paragraph you paste into an agent most days and restructure it as Background / Task / Requirements / Constraints. Add one in-bounds example and one explicit *do not*.

**Step 3 — run it twice.** If the two runs invent different scope, the spec is still a wish. Tighten the Requirements section until they agree.

## Gotchas

- **A well-structured prompt is not a correct one.** The template catches missing constraints and missing examples, not whether your requirements are *right*. A precise spec for the wrong task still gets you the wrong task, faster.
- **Over-constraining backfires.** Fifteen constraints and no room for a clarifying question can produce a technically-compliant, useless answer. That is what meta-prompting is for.
- **Don't spec a one-line ask.** "Rename this variable to `userId`" needs zero template. The structure earns its cost on anything you would otherwise have to correct twice.
- **Chain-of-thought is still tokens.** It helps on puzzles and can hurt on "return this exact JSON" — if a parser is downstream, constrain the output; do not hope reasoning gets you there.
- **Permanent context is not free.** Everything in CLAUDE.md or a system prompt is resent and repaid for on every turn. Past a couple hundred lines it starts costing more than it saves.

## How It Connects to What You Know

You already write specs, tickets and PR descriptions that other engineers execute without a follow-up question. Prompting is the same discipline, aimed at a collaborator who cannot infer anything you did not say and starts fresh most conversations. The four-part template mirrors any well-run engineering process: state the constraints (Background), state the deliverable (Task), state what "done" means (Requirements), state the guardrails (Constraints). Nothing here needs new intuition — it needs the intuition you already trust, pointed at a new kind of teammate.

Next: [How Coding Agents Work](#learn/coding-agents-101) — the same spec discipline, now with the model taking actions instead of only producing text.
