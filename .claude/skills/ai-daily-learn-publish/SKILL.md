---
name: ai-daily-learn-publish
description: >
  Runs a full AI Daily Learn session AND publishes it live. Identical to ai-daily-learn — same
  topic selection, same five artifacts in ~/ai_learning/YYYY-MM-DD/ — but afterwards commits the
  session and pushes it straight to main on magna56/aI_daily_run (no branch, no PR), then rebuilds
  and republishes the reader to theaicommit.com (Cloudflare Pages, primary) and
  magna56.github.io/aI_daily_run (GitHub Pages, mirror). This is what the automated 11:00 daily
  job runs. Use when: "daily learn and publish", "publish today's session", "ai-daily-learn-publish",
  "learn and push", "daily AI session to github", "find and publish a new article", or when the
  user wants the session live. Use plain /ai-daily-learn instead when they want it saved locally
  only. Accepts optional topic argument: /ai-daily-learn-publish "vision transformers".
argument-hint: "[optional-topic]"
verified: llm
---

# AI Daily Learn — Publish Variant

This skill is **the `ai-daily-learn` skill plus a publish step**. It deliberately does not restate
the session workflow, so the two skills can never drift apart.

## Step A: Run the full session

Execute the entire `ai-daily-learn` workflow, Steps 1 through 12, exactly as written:

```
Skill(skill="tp-mcp-config:ai-daily-learn", args="<the topic argument, if the user gave one>")
```

If the Skill tool is unavailable, read this checkout first:

```
./.claude/skills/ai-daily-learn/SKILL.md
./.claude/skills/ai-daily-learn/selection.md
./.claude/skills/ai-daily-learn/visualize.md
./.claude/skills/ai-daily-learn/contract.md
```

Fall back to `~/.claude/plugins/tp-mcp-config/skills/ai-daily-learn/SKILL.md` or
`~/tp_claude/plugins/tp-mcp-config/skills/ai-daily-learn/SKILL.md` only if those
are missing.

Note the exact session directory name it produced — `YYYY-MM-DD`, or `YYYY-MM-DD-s2` for a second
session on the same day. Steps A½ and B need it.

## Step A½: Gate the session before it goes live

Publishing is the irreversible half of this skill, and the 11:00 job runs it unattended with
nobody reading the output — so a session that quietly missed a content rule reaches the live site
and the newsletter before anyone sees it. Re-run the lint here rather than trusting that Step A
finished clean:

```bash
cd ~/ai_learning && node build.js --check 2>&1 | grep "YYYY-MM-DD"
```

**A content-contract warning naming today's id blocks the publish.** Fix the session and re-run;
never fix it by loosening the spec. The blocking ones:

- `no "## Implementing It" section` — the write-up never shows the code the reader has to write.
- `no fenced code block` — the section exists but defers to `code_example.py`, which most readers
  never open and nobody reading on a phone will run.
- anything about `visualize.html` — a session without a working visualizer has no Visualize tab.

Other warnings are advisory and do not block: a `code_example.py` that exits non-zero is a
*rendered traceback* by design, not a broken build.

Then confirm by eye the two things no linter can see (`ai-daily-learn` Step 11 has the same pair):
`## Implementing It` gives code for **every role the change touches**, and `## Why It Matters`
carries no momentum reporting. `publish.sh` enforces the machine-checkable half of this gate
itself, so the unattended run is protected even when nobody reads its log.

## Step B: Publish (push to GitHub, deploy to both hosts)

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
calls `./deploy.sh` — which builds the reader once locally and publishes that same build to
**both** hosts: Cloudflare Pages (`theaicommit.com`, primary) and the `gh-pages` branch (GitHub
Pages, mirror). Re-running it with nothing new is a safe no-op that still refreshes both hosts —
which is how you recover from a deploy that failed the first time. `.venv/`, `.claude/`, `.logs/`,
`site/`, `.wrangler/`, and `.DS_Store` are gitignored and never pushed to `main`.

The site step is deliberately non-fatal: if it warns `site deploy failed`, the session is already
safely on `main` and only the reader is stale — run `cd ~/ai_learning && make deploy` to retry.
Within `deploy.sh` itself, a Cloudflare-specific hiccup (expired token, network blip) is separately
non-fatal and never blocks the `gh-pages` push that runs before it — but a `publish.sh` caller
only ever sees one coarse "site deploy failed" either way, not which host specifically failed.

### Manual fallback

If the script is missing entirely:

```bash
cd ~/ai_learning
git add YYYY-MM-DD journal.md
git commit -m "YYYY-MM-DD: <topic title>"
git push origin HEAD:main
```

## Step C: Report

Use the same summary block as `ai-daily-learn` Step 12, but replace its "Read it" block and
closing line with the published deep link — that URL opens the rendered session directly and is
the thing worth sharing:

```
Read it: https://theaicommit.com/#YYYY-MM-DD
Mirror:  https://magna56.github.io/aI_daily_run/#YYYY-MM-DD
Source:  https://github.com/magna56/aI_daily_run
```

theaicommit.com is the primary link to share — it's the one with the real domain, the GitHub
sign-in/Publish-to-Repo feature (GitHub Pages has no serverless functions, so that button 404s on
the mirror), and the light/dark toggle. The GitHub Pages mirror exists as a free fallback if
Cloudflare is ever down.

Pages can take a minute to serve a fresh push. If `publish.sh` warned that the site deploy failed,
say so and give the retry command rather than the link.

## Publish-Only Mode

If the user asks to publish a session that already exists — "publish yesterday's", "push the
2026-08-18 session" — **skip Step A entirely** and run Step B against that directory. Do not
regenerate a session that is already on disk. Step A½ still applies and `publish.sh` still runs
its own gate, but sessions predating the content contract are exempt by date in `build.js`, so
republishing the back catalog never trips it.

## Error Handling

- Push rejected / no network / VPN down → say so in the Step C summary and tell the user to
  re-run `bash "$PUB" YYYY-MM-DD` later. **Never** force-push, and never open a PR instead.
- Rebase conflict in `~/ai_learning` → the script aborts the rebase and stops; resolve by hand.
- Session generation failed in Step A → do not publish a partial session. Report the failure.
- `publish.sh` aborted with `content gate` → the session does not meet `contract.md`. Fix the
  session (usually: write the `## Implementing It` section, with real code in `topic.md`) and
  re-run. `ADL_SKIP_GATE=1` exists for a deliberate override and should stay unused by the
  scheduled job — publishing past this gate is how the site drifts back into announcement recaps.
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
