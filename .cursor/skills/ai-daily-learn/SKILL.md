---
name: ai-daily-learn
description: >
  Daily 30-minute AI learning session for this repo. Picks one focused topic, then
  writes all five reader artifacts — topic.md, visualize.html, diagram.excalidraw,
  code_example.py, articles.md — plus a journal.md entry. Use when the user says
  "daily learn", "ai-daily-learn", "learn AI today", "what's new in AI",
  "AI learning session", "daily AI update", "teach me something about AI", or
  wants tomorrow's article in the current theaicommit.com format. Optional topic:
  /ai-daily-learn "vision transformers". Local only — do not publish unless asked.
---

# AI Daily Learn (Cursor)

Same daily session as Claude's `/ai-daily-learn`. This file is the Cursor runner.
The format spec lives next to it so the two tools cannot drift.

## Read these first (mandatory)

1. [SKILL.md](../../../.claude/skills/ai-daily-learn/SKILL.md) — topic pick, write-up, journal
2. [selection.md](../../../.claude/skills/ai-daily-learn/selection.md) — audience, sources, how to pick
3. [visualize.md](../../../.claude/skills/ai-daily-learn/visualize.md) — Visualize pane (required)
4. [contract.md](../../../.claude/skills/ai-daily-learn/contract.md) — five files + check

Then execute that workflow, Steps 1–12, in this workspace (`/Users/mayuragnani/ai_learning`
or `$HOME/ai_learning`).

## Cursor notes

- Use **WebSearch** then **WebFetch**. Do not skip sources. Every scan must
  include https://mlconcepts.viveksingh-heritage.workers.dev/ as the
  **intermediate / basics** feed (LoRA, attention, embeddings, calibration,
  agents). On-ramp or `articles.md` only — not the news lead. Full rules:
  [selection.md](../../../.claude/skills/ai-daily-learn/selection.md).
- Prefer the most capable model. If you are clearly on a small/fast one, say so before writing.
- Diagram generator:

  `python3 .claude/skills/ai-daily-learn/scripts/generate_excalidraw.py --help`

- **visualize.html is required.** Open the newest existing `visualize.html` and match that
  interaction quality. A session with only a write-up is not done.
- After the five files and the journal append:

  `node build.js --check`

  Fix every warning on today's id. Preview with `make serve` (or `make serve NORUN=1`)
  at `http://127.0.0.1:8000/#YYYY-MM-DD`. Click Overview → Visualize → Diagram → Code → Articles.
- Do not commit, push, or run `deploy.sh` unless the user said publish.
  Publishing is `.cursor/skills/ai-daily-learn-publish`.

## Done when

The folder has all five artifacts, `journal.md` has today's block, check is clean for
today's id, and the Visualize tab shows a working interactive model of the claim.
