---
name: ai-daily-learn-feedback
description: >
  Turn feedback on a published AI Daily Learn session into a durable change to the spec that
  generates every future session. The user critiques one document — a section that dragged, a
  title that oversold, a diagram that explained nothing, a Monday action that was not actionable —
  and this skill decides whether that note is a standing rule, edits the right spec file so the
  generator obeys it from now on, and logs what changed. Use when: "feedback", "/feedback",
  "this article was too X", "the ELI5 didn't land", "don't write it like this again",
  "fix this for future articles", "update the skill with this". Accepts the note inline:
  /ai-daily-learn-feedback "the glossary repeated the body text". Fixing today's article is
  optional and secondary — the point is that the same note never has to be given twice.
---

# AI Daily Learn — Feedback

**The deliverable is a spec change, not a fixed article.** Anyone can patch one document. This
skill exists so the next twenty documents do not need the same patch. If you finish having only
edited a session folder, you have not run this skill.

## Step 0: The invocation argument IS the feedback

**Whatever the user typed next to the skill name is the note. Use it verbatim as the input to
Steps 3-5 — do not ask them to repeat it, and do not substitute your own opinion of the article.**

```
/ai-daily-learn-feedback the glossary just repeated the body text
/ai-daily-learn-feedback 2026-08-21 the diagram was three boxes of prose
```

- The argument may **lead with a session id** (`2026-08-21`, `2026-08-03-s2`). If it does, that is
  the target and the rest is the note. If it does not, the target is resolved in Step 1.
- The argument may carry **several distinct notes** in one line ("too long, and the title oversold
  it"). Split them and triage each separately in Step 3 — do not collapse them into one edit.
- **If there is no argument**, look back at the user's recent messages for the critique they are
  referring to and quote it back for confirmation. If there is no such message, ask what the
  feedback is. Never run this skill on an article with no stated note and invent one.
- Preserve the user's own wording in the log (Step 8). Their phrasing is the record of what was
  actually asked for; your paraphrase is not.

## Step 1: Identify the target

If Step 0's argument named a session id, use it. Otherwise default to the newest daily session
folder (`ls -d 20*/ | sort | tail -1`), and say which one you picked so a wrong guess is visible.
If the feedback is about the site rather than a document — layout, buttons, colours, the reader
shell — jump to the routing table in Step 4; it is still in scope, it just lands in `index.html`
instead of a spec file.

## Step 2: Read the document AND the spec that produced it

Never write a rule without reading the rule that is already there. Read the target's `topic.md`
(plus whichever of the five files the note is about), then the spec section that governs it. The
spec is four files:

```
.claude/skills/ai-daily-learn/SKILL.md       # the workflow, Steps 1-12, and every content rule
.claude/skills/ai-daily-learn/selection.md   # audience, category tiers, sources, the 5 gates
.claude/skills/ai-daily-learn/visualize.md   # the Visualize pane contract
.claude/skills/ai-daily-learn/contract.md    # required files, metadata keys, section order
```

`.cursor/skills/ai-daily-learn/SKILL.md` is a **thin runner that links to those four files**, not a
copy. Editing the canonical files updates Cursor automatically. Only touch the Cursor twin when the
change is about how the runner is invoked, never for a content rule.

## Step 3: Triage every point separately

A single message usually carries several notes of different kinds. Classify each one before
editing anything. Three outcomes:

| Verdict | Test | Action |
| --- | --- | --- |
| **Standing rule** | Would this apply to a future session on a completely different topic? | Edit the spec (Step 4-5) |
| **One-off** | Is this true only of this article's subject or this day's source? | Offer to fix the document; do **not** touch the spec |
| **Compliance gap** | Does the spec **already** say this, and the session broke it? | Do not add a duplicate sentence — **strengthen** the existing rule |

The compliance case is the one most often got wrong. If the spec already says "no method-name
titles" and a method-name title shipped anyway, adding a second sentence saying the same thing
makes the spec longer and no more obeyed. Instead promote it: move it into `contract.md` as a hard
requirement, add it to a checklist the workflow already runs, or give it a concrete ✗/✓ example
pair so it is unmissable.

Also reject, out loud, feedback that cannot become a rule. "Make it more interesting" is not
actionable; "open with the cost before the mechanism" is. Ask for the concrete version rather than
inventing one.

## Step 4: Route to the file that already owns the concern

| Feedback is about | Edit |
| --- | --- |
| Title, hook, tone, a `##` section's content rules, glossary, journal `Key insight` | `SKILL.md` (Step 5's template and the per-section rules under it) |
| Which topic got picked, category weighting, sources, paper budget, repeat detection | `selection.md` |
| The interactive visualizer — what it must model, controls, contract | `visualize.md` |
| A file becoming required, a metadata key, section order, anything `--check` should catch | `contract.md` |
| `code_example.py` — length, style, what it must print, dependency line | `SKILL.md` Step 6 |
| Diagram panels, what the Excalidraw must show | `SKILL.md` Step 7 + the docstring in `scripts/generate_excalidraw.py` |
| `articles.md` — count, source mix, summary style | `SKILL.md` Step 9 |
| A new **tag**, category, Level or For value | `build.js` (`TAGS` / `CATEGORIES` / `LEVELS` / `JOBS`) **first**, then the spec — see Step 6 |
| How the article *renders* — reader layout, buttons, colours, tabs, SEO markup | `index.html` (this is a site change, not a spec change) |

Put the rule **in the section that already owns that concern**. Never append a "Feedback" or
"Recent notes" section at the bottom of a spec file — a rule the generator has to hunt for is a
rule it will miss.

## Step 5: Write a rule, not a transcript

Match the surrounding voice. These spec files are imperative, explain *why*, and use concrete
contrast pairs. A good edit looks like the text around it, not like a quoted complaint.

- **State the instruction, then the reason.** The existing rules all justify themselves ("this is
  why sessions feel all over the place"), which is what makes them stick under pressure.
- **Give a ✗/✓ pair** when the rule is about phrasing. The title rules in `SKILL.md` are the model.
- **Prefer tightening an existing sentence** over adding a new one. The spec is already long; every
  added sentence competes for attention with the ones that matter.
- **Quantify if the feedback was quantitative.** "Too long" becomes a cap with a number, the way
  `Key insight` has a hard 3-sentence / ~70-word cap.
- **Never weaken an existing rule to accommodate one note** without saying so explicitly in the
  report — that is a spec regression and the user should get to veto it.

## Step 6: Vocabulary changes touch the validator first

If the note requires a tag, category, `Level` or `For` value that does not exist, add it to the
matching array in `build.js` **before** referencing it in the spec. `build.js` is the validation
source of truth; a spec that names a tag the linter rejects fails silently on every future run.
Then run `node build.js --check` and confirm no session started warning.

## Step 7: Fixing the current document is optional

Ask before editing the target session. Backfilling one article is cosmetic; the published record
is a dated log, and the user has previously said old sessions can stay as they are. If they do want
it fixed, edit the session file, then `node build.js --check` and confirm today's id is clean.

Do **not** publish or deploy from this skill. If a document changed and the user wants it live,
point them at `/ai-daily-learn-publish` or `make deploy`.

## Step 8: Log what changed

Append to `.claude/skills/ai-daily-learn-feedback/feedback-log.md`:

```markdown
## YYYY-MM-DD — <target session id>
- **Note**: <the feedback, in the user's own words, trimmed>
- **Verdict**: standing rule | one-off | compliance gap
- **Changed**: <file> — <the rule, in one line>
- **Not changed**: <anything deliberately rejected, and why>
```

The log matters because spec edits compound. Without it, a later note can quietly reverse an
earlier one and nobody notices the spec now contradicts itself.

## Step 9: Report

State plainly:

1. Each note, and its verdict — including any you declined to turn into a rule, **and why**.
2. The exact file and section changed, with the rule as it now reads.
3. Whether the current document was edited, and whether anything needs publishing.
4. Anything you could not act on because the feedback was not specific enough to become a rule.

Never claim a rule will fix something it cannot. If the note is really about model judgment rather
than a missing instruction, say so — some things do not have a spec fix.

## Error Handling

- **Feedback is vague** → ask for the concrete version; do not invent a rule to look responsive.
- **Feedback contradicts an existing rule** → surface the conflict, quote both, and let the user
  decide which wins. Do not silently overwrite.
- **Feedback is about the site, not the article** → route it to `index.html` and say so; it is
  still valid feedback, just not a spec change.
- **Feedback applies to a Learn-track page** (`learn/<slug>/`) → those are the evergreen two-day
  track, not daily sessions; edit that page directly, and only change the spec if the note is about
  the daily format too.

## Scope

Local only. This skill edits spec files, optionally a session folder, and the feedback log. It does
not commit, push, or deploy — publishing stays in `/ai-daily-learn-publish` and `make deploy`.
