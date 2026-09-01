---
name: ai-daily-learn-pick
description: >
  Research today's candidates, present three worked article proposals, decide with the
  user, then write the session. Use when they say "pick an article", "give me three
  options", "what should I write today", "let me choose the topic", "ai-daily-learn-pick".
  Use ai-daily-learn instead when they want it chosen and written unattended.
---

# AI Daily Learn — Pick (Cursor)

The full spec is `.claude/skills/ai-daily-learn-pick/SKILL.md`. Read it before running.
The short version:

## Step 1-3 — research and work up three candidates

`node build.js --mix` for what is due, then fetch 8-12 live sources across at least three
categories. Narrow to **three genuinely different** candidates — not three angles on one
release, at most one arXiv-led, all clearing the source gates in
`.claude/skills/ai-daily-learn/selection.md`. Fetch the primary source for all three and
write each up in the proposal template in the main spec: source, slot, claim, mechanism,
what the reader can *do* afterwards, the code `Implementing It` would show, the weakness.

## Step 4 — present and stop

End the turn. Do not pick for the user; recommend in one line at most. Do not start
writing anything until they choose.

## Step 5-6 — shape it, then lock the brief

Settle the title, the angle, what `Implementing It` covers, what is cut, and the
visualizer's one idea. Write it to `~/ai_learning/.briefs/YYYY-MM-DD.md` and get a yes.

## Step 7-8 — write, report, do not publish

Run `.cursor/skills/ai-daily-learn` for the full five-artifact session, skipping its topic
selection — the brief decides title, angle and scope; the contract still binds everything
else. Report the two losers and why. Publishing is a separate explicit step
(`.cursor/skills/ai-daily-learn-publish`).
