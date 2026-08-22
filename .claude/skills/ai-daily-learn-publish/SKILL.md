---
name: ai-daily-learn-publish
description: >
  Runs a full AI Daily Learn session AND publishes it to GitHub. Identical to ai-daily-learn —
  same topic selection, same four artifacts in ~/ai_learning/YYYY-MM-DD/ — but afterwards commits
  the session and pushes it straight to main on magna56/aI_daily_run (no branch, no PR). This
  is what the automated 11:00 daily job runs. Use when: "daily learn and publish", "publish today's
  session", "ai-daily-learn-publish", "learn and push", "daily AI session to github", or when the
  user wants the session to land in the repo. Use plain /ai-daily-learn instead when they want it
  saved locally only. Accepts optional topic argument: /ai-daily-learn-publish "vision transformers".
argument-hint: "[optional-topic]"
verified: llm
---

# AI Daily Learn — Publish Variant

This skill is **the `ai-daily-learn` skill plus a publish step**. It deliberately does not restate
the session workflow, so the two skills can never drift apart.

## Step A: Run the full session

Execute the entire `ai-daily-learn` workflow, Steps 1 through 10, exactly as written:

```
Skill(skill="tp-mcp-config:ai-daily-learn", args="<the topic argument, if the user gave one>")
```

If the Skill tool is unavailable, read
`~/.claude/plugins/tp-mcp-config/skills/ai-daily-learn/SKILL.md`
(or `~/tp_claude/plugins/tp-mcp-config/skills/ai-daily-learn/SKILL.md`) and follow it directly.

Note the exact session directory name it produced — `YYYY-MM-DD`, or `YYYY-MM-DD-s2` for a second
session on the same day. Step B needs it.

## Step B: Publish to GitHub

Push the session straight to `main` on
`git@github.com:magna56/aI_daily_run.git`.
**Never open a PR** — this is a personal notes repo and the daily job is its only writer.

```bash
PUB=""
for CAND in \
  ./.claude/skills/ai-daily-learn-publish/scripts/publish.sh \
  "${AI_LEARNING_DIR:-$HOME/ai_learning}/.claude/skills/ai-daily-learn-publish/scripts/publish.sh" \
  ~/.claude/plugins/tp-mcp-config/skills/ai-daily-learn-publish/scripts/publish.sh \
  ~/tp_claude/plugins/tp-mcp-config/skills/ai-daily-learn-publish/scripts/publish.sh \
  ~/.claude/skills/ai-daily-learn-publish/scripts/publish.sh ; do
  [ -f "$CAND" ] && { PUB="$CAND"; break; }
done
[ -n "$PUB" ] || echo "publish.sh not found — see Manual fallback below"

bash "$PUB" YYYY-MM-DD    # the exact session dir name from Step A
```

The script is self-healing and idempotent: it initialises the repo and remote if missing, commits
the session directory plus `journal.md`, rebases if the remote moved, pushes to `main`, and then
rebuilds and republishes the reader site to the `gh-pages` branch. Re-running it with nothing new
is a safe no-op that still refreshes the site — which is how you recover from a deploy that failed
the first time. `.venv/`, `.claude/`, `.logs/`, `site/`, and `.DS_Store` are gitignored and never
pushed to `main`.

The site step is deliberately non-fatal: if it warns `site deploy failed`, the session is already
safely on `main` and only the reader is stale — run `cd ~/ai_learning && make deploy` to retry.

### Manual fallback

If the script is missing entirely:

```bash
cd ~/ai_learning
git add YYYY-MM-DD journal.md
git commit -m "YYYY-MM-DD: <topic title>"
git push origin HEAD:main
```

## Step C: Report

Use the same summary block as `ai-daily-learn` Step 10, but replace its "Read it" block and
closing line with the published deep link — that URL opens the rendered session directly and is
the thing worth sharing:

```
Read it: https://magna56.github.io/aI_daily_run/#YYYY-MM-DD
Source:  https://github.com/magna56/aI_daily_run
```

Pages can take a minute to serve a fresh push. If `publish.sh` warned that the site deploy failed,
say so and give the retry command rather than the link.

## Publish-Only Mode

If the user asks to publish a session that already exists — "publish yesterday's", "push the
2026-08-18 session" — **skip Step A entirely** and run Step B against that directory. Do not
regenerate a session that is already on disk.

## Error Handling

- Push rejected / no network / VPN down → say so in the Step C summary and tell the user to
  re-run `bash "$PUB" YYYY-MM-DD` later. **Never** force-push, and never open a PR instead.
- Rebase conflict in `~/ai_learning` → the script aborts the rebase and stops; resolve by hand.
- Session generation failed in Step A → do not publish a partial session. Report the failure.
- Everything else → see `ai-daily-learn`'s own Error Handling section.

## Scheduling

This skill runs unattended at 11:00 every day via a macOS LaunchAgent
(`com.<user>.ai-daily-learn`) that invokes `scripts/run_daily.sh`. Logs land in
`~/ai_learning/.logs/` (gitignored).

Manage it with `scripts/install_schedule.sh` — never hand-edit the plist, since the script
regenerates it:

```bash
bash scripts/install_schedule.sh              # install / reinstall at 11:00
bash scripts/install_schedule.sh --time 09:30 # different time
bash scripts/install_schedule.sh --status     # is it registered? when does it fire?
bash scripts/install_schedule.sh --uninstall  # remove it
```

Once installed:

```bash
launchctl start com.$(id -un).ai-daily-learn  # run it right now
tail -f ~/ai_learning/.logs/run.log           # watch a run
```

The plist is **generated, not committed**: it must carry this machine's real `$HOME` and this
checkout's real script path, and a static file would hardcode one developer's username. The
generated `PATH` includes `$HOME/.local/bin` plus the usual Homebrew/system locations, since
launchd's own environment is minimal and won't otherwise resolve `claude` or anything it shells
out to.

A LaunchAgent is used rather than `crontab` because launchd runs a missed job when the laptop
wakes; cron silently skips it if the machine was asleep at 11:00.

### If a scheduled run fails

Check `~/ai_learning/.logs/run.log`. There's no portable way to verify `claude`'s auth ahead of
time, so an expired login surfaces as a failure from the `claude -p` call itself rather than a
fast preflight — fix it by running `claude login` interactively (or setting
`ANTHROPIC_API_KEY`). A failed run never publishes a partial session; the local files stay put
and the next run picks them up.
