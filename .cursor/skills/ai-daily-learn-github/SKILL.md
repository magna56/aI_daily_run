---
name: ai-daily-learn-github
description: >
  Runs a full AI Daily Learn session (five artifacts including visualize.html) and pushes it to
  GitHub main — but does NOT deploy the site. No Cloudflare Pages rebuild, no gh-pages push, no
  newsletter. Use when the user says "push to github but don't deploy", "commit today's session,
  skip the site", "publish to github only", or "ai-daily-learn-github". Use ai-daily-learn-publish
  instead when they want it live too.
---

# AI Daily Learn — GitHub Only (Cursor)

## Step A — generate (or reuse)

If the session is not on disk yet, run `.cursor/skills/ai-daily-learn` through
check-clean (all five files, including `visualize.html`).

If they asked to push a session that already exists, skip generation.

Note the exact folder name: `YYYY-MM-DD` or `YYYY-MM-DD-s2`.

## Step B — push to GitHub, stop there

Follow `.claude/skills/ai-daily-learn-github/SKILL.md` Step B.

Prefer this repo's script:

```bash
bash .claude/skills/ai-daily-learn-github/scripts/publish_github.sh YYYY-MM-DD
```

That commits the session + `journal.md` and pushes `main` on `magna56/aI_daily_run` — it is
`ai-daily-learn-publish`'s script with the `deploy.sh` call removed, so theaicommit.com, the
gh-pages mirror, and the newsletter are all left exactly as they were. Never open a PR. Never
force-push.

## Step C — report

```
Pushed to GitHub: https://github.com/magna56/aI_daily_run/commit/<short-sha>

Site not deployed — theaicommit.com and the mirror are unchanged, no newsletter sent.
Run 'make deploy' or ai-daily-learn-publish when you want this live.
```
