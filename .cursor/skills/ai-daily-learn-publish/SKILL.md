---
name: ai-daily-learn-publish
description: >
  Runs a full AI Daily Learn session (five artifacts including visualize.html) and
  publishes it live: commit and push straight to main, then deploy.sh to
  theaicommit.com and the gh-pages mirror. Use when the user says "daily learn and
  publish", "publish today's session", "ai-daily-learn-publish", "learn and push",
  or wants the new article live. Use ai-daily-learn when they want it local only.
---

# AI Daily Learn — Publish (Cursor)

## Step A — generate (or reuse)

If the session is not on disk yet, run `.cursor/skills/ai-daily-learn` through
check-clean (all five files, including `visualize.html`).

If they asked to publish a session that already exists, skip generation.

Note the exact folder name: `YYYY-MM-DD` or `YYYY-MM-DD-s2`.

## Step B — publish

Follow `.claude/skills/ai-daily-learn-publish/SKILL.md` Step B.

Prefer this repo's script:

```bash
bash .claude/skills/ai-daily-learn-publish/scripts/publish.sh YYYY-MM-DD
```

That commits the session + `journal.md`, pushes `main` on
`magna56/aI_daily_run`, and runs `./deploy.sh` (Cloudflare Pages primary,
gh-pages mirror). Never open a PR. Never force-push.

## Step C — report

```
Read it: https://theaicommit.com/#YYYY-MM-DD
Mirror:  https://magna56.github.io/aI_daily_run/#YYYY-MM-DD
```
