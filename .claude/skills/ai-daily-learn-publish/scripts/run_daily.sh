#!/usr/bin/env bash
#
# Unattended daily driver for the /ai-daily-learn-publish skill.
# Invoked at 11:00 by the generated LaunchAgent (see install_schedule.sh —
# label com.<you>.ai-daily-learn).
#
# Runs the skill headlessly with `claude -p`, then makes sure the session got
# published even if the model's own publish step was skipped or failed.
#
# Manual run:  bash run_daily.sh          (today)
#              bash run_daily.sh "topic"  (forced topic)

set -uo pipefail

ROOT="${AI_LEARNING_DIR:-$HOME/ai_learning}"
LOGDIR="$ROOT/.logs"
SESSION="$(date +%F)"
TOPIC="${1:-}"

mkdir -p "$LOGDIR"

log() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

# launchd hands us a minimal PATH; put the usual tool locations back so
# `claude` (and anything it shells out to) resolves the same as in a normal
# interactive terminal.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

CLAUDE="$(command -v claude || true)"
[ -n "$CLAUDE" ] || { log "FATAL: claude CLI not on PATH"; exit 1; }

# No portable way to verify auth ahead of time here — if this machine's login
# (interactive `claude login`, or ANTHROPIC_API_KEY) has expired or is unset,
# the `claude -p` call below fails fast on its own and rc is logged below.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log "=== ai-daily-learn-publish starting (session $SESSION) ==="

# Already done today? Bail out rather than producing a duplicate.
if [ -f "$ROOT/$SESSION/topic.md" ] && [ -z "$TOPIC" ]; then
  log "session $SESSION already exists — skipping generation, ensuring it is published"
  bash "$SCRIPT_DIR/publish.sh" "$SESSION"
  log "=== done (already existed) ==="
  exit 0
fi

PROMPT="/ai-daily-learn-publish"
[ -n "$TOPIC" ] && PROMPT="/ai-daily-learn-publish \"$TOPIC\""

# Scoped allowlist rather than --dangerously-skip-permissions: the job needs to
# read the web, write into ~/ai_learning, and shell out to the two helper scripts.
# --model opus: session generation should always run on the most capable model,
# regardless of whatever a prior interactive session last had active — that
# state doesn't carry over to an unattended launchd run anyway, so this is the
# one place that setting can be pinned reliably.
"$CLAUDE" -p "$PROMPT" \
  --model opus \
  --allowed-tools WebSearch WebFetch Read Write Edit Bash Glob Grep Skill \
  --permission-mode acceptEdits
rc=$?

log "claude exited rc=$rc"

# Safety net: publish regardless of what the model did, so a skipped or failed
# Step 10 never leaves a session stranded on local disk.
if [ -d "$ROOT/$SESSION" ]; then
  bash "$SCRIPT_DIR/publish.sh" "$SESSION"
else
  log "WARN: no session directory $ROOT/$SESSION was produced"
fi

log "=== ai-daily-learn-publish finished (rc=$rc) ==="
exit "$rc"
