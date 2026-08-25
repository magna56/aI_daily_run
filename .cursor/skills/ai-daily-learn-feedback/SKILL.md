---
name: ai-daily-learn-feedback
description: >
  Turn feedback on a published AI Daily Learn session into a durable change to the spec that
  generates future sessions. Use when the user critiques an article — a section that dragged, a
  title that oversold, a diagram that explained nothing — and wants the generator fixed rather
  than just this one document. Triggers: "feedback", "this article was too X", "don't write it
  like this again", "fix this for future articles", "update the skill with this".
  Local only — does not commit, push, or deploy.
---

# AI Daily Learn Feedback (Cursor)

Same workflow as Claude's `/ai-daily-learn-feedback`. This file is the Cursor runner; the spec
lives next to it so the two tools cannot drift.

## Read this first (mandatory)

[SKILL.md](../../../.claude/skills/ai-daily-learn-feedback/SKILL.md) — the full workflow,
Steps 1–9: identify the target, read the governing rule before writing one, triage each note as a
standing rule / one-off / compliance gap, route it to the file that already owns the concern, write
it as a rule rather than a transcript, and log it.

Then execute that workflow in this workspace (`/Users/mayuragnani/ai_learning`).

## The two things not to get wrong

**1. The text typed next to the skill name is the feedback.** Use it verbatim as the note — do not
ask for it again, and do not substitute your own read of the article. It may lead with a session id
(`2026-08-21 the diagram was three boxes of prose`), and it may contain several distinct notes that
must each be triaged separately. With no argument, quote back the critique from the user's recent
messages to confirm; never invent one.

**2. The deliverable is a spec change, not a fixed article.** Editing only the session folder means
the same note has to be given again next week.

The spec files this edits are the same four the daily skill reads:

```
.claude/skills/ai-daily-learn/SKILL.md
.claude/skills/ai-daily-learn/selection.md
.claude/skills/ai-daily-learn/visualize.md
.claude/skills/ai-daily-learn/contract.md
```

Those are canonical for both tools, so editing them here updates Claude too — there is no separate
Cursor copy of the content rules to keep in sync.
