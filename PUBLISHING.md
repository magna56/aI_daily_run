# Publishing Reference

Quick reference for how a new session gets written and published — the daily
automated path and the manual commands, in one place.

## The short version

A new session gets written and published automatically every day at **11:00**.
You don't need to do anything. Everything below is for checking on it,
running it on demand, or fixing it when something goes wrong.

## Run it yourself, right now

```bash
# In Claude Code, inside this repo:
/ai-daily-learn-publish                        # next category in the rotation
/ai-daily-learn-publish "speculative decoding"  # a specific topic
```

This finds a topic, writes the four session files (`topic.md`,
`diagram.excalidraw`, `code_example.py`, `articles.md`), commits and pushes to
`main` on GitHub, then rebuilds and republishes the reader to **both** hosts.
Takes about 10 minutes (it does real research).

Already generated a session locally with plain `/ai-daily-learn` and just want
to publish it? Say so — "publish today's session," "publish yesterday's" — the
skill detects it's already on disk and skips straight to the push, no
regeneration.

## The daily schedule (LaunchAgent)

A macOS LaunchAgent runs the publish skill unattended every day.

```bash
cd ~/ai_learning
bash .claude/skills/ai-daily-learn-publish/scripts/install_schedule.sh --status
```

Current setup:

| | |
|---|---|
| Label | `com.mayuragnani.ai-daily-learn` |
| Fires at | **11:00** daily |
| Runner | `.claude/skills/ai-daily-learn-publish/scripts/run_daily.sh` |
| Logs | `~/ai_learning/.logs/run.log` (and `run.err.log`) |

```bash
# Run today's job right now, instead of waiting for 11:00
launchctl start com.mayuragnani.ai-daily-learn
tail -f ~/ai_learning/.logs/run.log

# Change the time
bash .claude/skills/ai-daily-learn-publish/scripts/install_schedule.sh --time 09:30

# Turn it off / back on
bash .claude/skills/ai-daily-learn-publish/scripts/install_schedule.sh --uninstall
bash .claude/skills/ai-daily-learn-publish/scripts/install_schedule.sh
```

A LaunchAgent (not `cron`) is used deliberately: it runs a missed job when the
Mac wakes up, where `cron` just silently skips it if the machine was asleep at
11:00.

## Where it publishes

| Host | URL | Role |
|---|---|---|
| Cloudflare Pages | **https://theaicommit.com** | Primary — real domain, GitHub sign-in/Publish-to-Gist, light/dark toggle |
| GitHub Pages | https://magna56.github.io/aI_daily_run/ | Mirror — free fallback if Cloudflare is ever down |
| Source | https://github.com/magna56/aI_daily_run | The repo itself — pushed straight to `main`, no PRs |

One `make deploy` (or the skill's own publish step) updates both — same build,
uploaded twice. GitHub Pages has no serverless functions, so the GitHub
sign-in feature in the Code tab only works on theaicommit.com.

## Manual commands

```bash
cd ~/ai_learning
make serve     # build + preview locally at http://127.0.0.1:8000
make check     # lint every session, write nothing
make deploy    # rebuild and republish to both hosts, right now
make clean     # drop the build cache
```

`make deploy` is what to run if a scheduled publish reported "site deploy
failed" — the session itself is already safely on `main` at that point; this
just retries the site rebuild.

## Credentials this depends on

Nothing here needs re-entering day to day — this is just where things live if
something ever needs rotating:

- **GitHub push**: SSH key / git credential helper, same as any normal `git
  push` on this machine.
- **Cloudflare Pages deploy**: an API token in macOS Keychain
  (`security find-generic-password -a wrangler -s cloudflare-api-token-theaicommit`),
  read by `deploy.sh` at publish time.
- **GitHub OAuth (sign-in / Publish-to-Gist feature)**: a Client ID (public,
  in `index.html`) and Client Secret, stored as Cloudflare Pages secrets —
  `wrangler pages secret put GITHUB_CLIENT_SECRET --project-name=theaicommit`
  — never in the repo.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `run.log` shows `FATAL: claude CLI not on PATH` | `claude`'s auth expired or isn't on the LaunchAgent's minimal PATH. Run `claude login` interactively, or check `install_schedule.sh --status`. |
| `[publish] WARN: site deploy failed` | Rerun `make deploy` — the session is already safely pushed, only the site rebuild needs a retry. |
| Push rejected / no network | Rerun `bash .claude/skills/ai-daily-learn-publish/scripts/publish.sh` later — never force-push. |
| Rebase conflict | The script aborts and stops rather than guessing — resolve by hand in `~/ai_learning`. |
| GitHub sign-in button 404s | You're on the `.github.io` mirror, not theaicommit.com — that feature only works on the primary host. |

## Where the actual logic lives

- `.claude/skills/ai-daily-learn/SKILL.md` — topic selection, research sources, the four-file format
- `.claude/skills/ai-daily-learn-publish/SKILL.md` — the publish variant, scheduling, error handling (the canonical spec — this file is a cheat-sheet, that one is the source of truth)
- `deploy.sh` — builds once, publishes to both hosts
- `Makefile` — the `make` targets above
