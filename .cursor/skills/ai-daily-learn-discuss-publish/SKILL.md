---
name: ai-daily-learn-discuss-publish
description: >
  Decide the article together, then publish it — /ai-daily-learn-pick followed by the
  publish step, in one command. Use when they say "discuss and publish", "let me pick
  then publish it", "choose together and put it live", "ai-daily-learn-discuss-publish".
  Use ai-daily-learn-pick when nothing should go live, and ai-daily-learn-publish when
  they do not want to be asked at all.
---

# AI Daily Learn — Discuss, then publish (Cursor)

The full spec is `.claude/skills/ai-daily-learn-discuss-publish/SKILL.md`. Read it before
running. It composes two other skills and restates neither, so read those too:
`.claude/skills/ai-daily-learn-pick/SKILL.md` and
`.claude/skills/ai-daily-learn-publish/SKILL.md`.

The short version:

## Step 1 — the whole pick workflow

Run `.cursor/skills/ai-daily-learn-pick`, Steps 1-7: what is due, research wide, three
candidates that genuinely differ, **present and stop**, shape the content in the
conversation, lock the brief, write the session against it. Knowing that a publish
follows is not a reason to soften Step 4's hard stop.

## Step 2 — gate it

`ai-daily-learn-publish` Step A½ against the session directory, unchanged: `node build.js
--check`, then `node build.js --mix YYYY-MM-DD`. One change only — on a mix breach, do not
silently regenerate. The user chose this topic knowing what was due, so name the cost and
let him decide.

## Step 3 — publish

`ai-daily-learn-publish` Steps B and C: `publish.sh`, the live discoverability checks, then
`node build.js --mix` for what is due next. **This is the one place `ai-daily-learn-pick`
Step 8 is overridden** — agreeing the brief is the authorization, so do not ask twice. Say
out loud that a daily-lab publish mails real subscribers, and that a Frontier publish does
not.

## Step 4 — report

The publish summary with the live link, plus pick's two extra lines: what we passed on and
why, and where the article could not follow the brief. Then DUE NEXT.

`--frontier` runs the Frontier track, where publishing nothing is a successful run. A lab
day must never end empty — if the discussion stalls, say so and offer
`.cursor/skills/ai-daily-learn-publish` to fill the slot unattended.
