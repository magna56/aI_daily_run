#!/usr/bin/env bash
#
# Publish an AI Daily Learn session to GitHub ONLY.
#
# Commits the session directory plus journal.md and pushes STRAIGHT TO main.
# No branch, no PR. Idempotent: a no-op when there is nothing new to commit.
#
# Deliberately does NOT call deploy.sh: theaicommit.com, the gh-pages mirror,
# and the newsletter are all untouched by this script. The commit lands on
# main and nothing else happens. Use .claude/skills/ai-daily-learn-publish's
# publish.sh instead (or run `make deploy` after this script) to also go live.
#
# Usage:
#   publish_github.sh                       # publish today's session (YYYY-MM-DD)
#   publish_github.sh 2026-08-18-s2         # publish a specific session directory
#   publish_github.sh frontier/2026-08-25   # publish a Frontier session
#
# Exit codes: 0 ok / nothing to do, 1 setup or push failure.

set -uo pipefail

ROOT="${AI_LEARNING_DIR:-$HOME/ai_learning}"
REMOTE_URL="${AI_LEARNING_REMOTE:-git@github.com:magna56/aI_daily_run.git}"
BRANCH="main"
SESSION="${1:-$(date +%F)}"
# A Frontier session lives at frontier/<date>. It publishes through the same path
# as a lab session; what differs is that the audience gate does not apply to it —
# the track is deliberately excluded from the reader-pyramid mix it exists to
# protect, so there is nothing for that gate to judge.
case "$SESSION" in
  frontier/*) IS_FRONTIER=1 ;;
  *)          IS_FRONTIER=0 ;;
esac

say()  { printf '[publish-github] %s\n' "$*"; }
die()  { printf '[publish-github] ERROR: %s\n' "$*" >&2; exit 1; }

[ -d "$ROOT" ] || die "$ROOT does not exist"
cd "$ROOT" || die "cannot cd to $ROOT"

# --- Ensure the working tree is a git repo pointed at the right remote --------
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  say "initialising git repo in $ROOT"
  git init -q -b "$BRANCH" || die "git init failed"
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  say "adding origin -> $REMOTE_URL"
  git remote add origin "$REMOTE_URL" || die "could not add origin"
fi

# --- Content gate -------------------------------------------------------------
# This script never deploys, so nothing here protects a live site or a
# newsletter send — but main is still the source of truth this repo's history
# is built from, and a session that silently missed contract.md should not
# land there uncaught any more than it should reach a live host. `--check`
# writes nothing, and only the contract-breaking warnings block: a
# code_example.py that exits non-zero is a rendered traceback by design, not
# a broken build. Sessions predating the contract are exempt inside build.js
# itself (date-gated), so republishing the back catalog never trips this.
content_gate() {
  [ "${ADL_SKIP_GATE:-0}" = "1" ] && { say "content gate skipped (ADL_SKIP_GATE=1)"; return 0; }
  [ -d "$SESSION" ] || return 0
  [ -f build.js ] || return 0
  command -v node >/dev/null 2>&1 || { say "WARN: node not found — content gate skipped"; return 0; }

  local blocking
  blocking=$(node build.js --check 2>&1 \
    | grep -F "$SESSION:" \
    | grep -E 'Implementing It|fenced code block|visualize\.html|no topic\.md' || true)

  if [ -n "$blocking" ]; then
    printf '[publish-github] ERROR: content gate — %s does not meet contract.md:\n' "$SESSION" >&2
    printf '%s\n' "$blocking" | sed 's/^/[publish-github]   /' >&2
    printf '[publish-github] Fix the session, then re-run. See .claude/skills/ai-daily-learn/contract.md\n' >&2
    exit 1
  fi

  # Did this session take a slot the audience mix said was already at cap?
  # Reported, never fatal — the daily cadence is the product, and one
  # session's mix is repaired by what gets picked tomorrow, not by holding
  # this one back from main.
  if [ "$IS_FRONTIER" = "1" ]; then
    say "audience gate not applicable to a Frontier session"
    say "content gate passed for $SESSION"
    return 0
  fi

  local mix_out mix_rc
  mix_out=$(node build.js --mix "$SESSION" 2>&1); mix_rc=$?
  printf '%s\n' "$mix_out" | sed 's/^/[publish-github] /'
  if [ "$mix_rc" = "3" ]; then
    say "WARN: audience gate — $SESSION ignores what was due; publishing anyway."
    say "WARN: correct it in tomorrow's pick — run 'node build.js --mix' to see what is owed."
  fi

  say "content gate passed for $SESSION"
}

content_gate

# --- Stage the session --------------------------------------------------------
# Staging and committing happen BEFORE the rebase: `git rebase` refuses to run
# against a dirty working tree, so syncing first would fail on every real run.
staged_any=0
if [ -d "$SESSION" ]; then
  git add -- "$SESSION" && staged_any=1
else
  say "WARN: session directory '$SESSION' not found — publishing journal only"
fi
[ -f journal.md ]  && git add -- journal.md
[ -f README.md ]   && git add -- README.md
[ -f .gitignore ]  && git add -- .gitignore

if git diff --cached --quiet; then
  say "nothing new to publish for $SESSION"
  exit 0
fi

n_files=$(git diff --cached --name-only | wc -l | tr -d ' ')

# --- Commit -------------------------------------------------------------------
# Pull the topic title out of topic.md for a meaningful subject line.
title=""
if [ -f "$SESSION/topic.md" ]; then
  title=$(sed -n 's/^# //p' "$SESSION/topic.md" | head -1)
fi
if [ "$IS_FRONTIER" = "1" ]; then
  subject="Frontier ${SESSION#frontier/}: ${title:-Frontier session}"
else
  subject="$SESSION: ${title:-AI daily learn session}"
fi

git commit -q -m "$subject" -m "Automated by the /ai-daily-learn-github skill. $n_files file(s).

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>" \
  || die "commit failed"

say "committed: $subject ($n_files files)"

# --- Sync with the remote, now that the tree is clean -------------------------
# The daily job is the only writer, but a push from another machine would
# otherwise turn into a non-fast-forward rejection.
if git ls-remote --exit-code origin "$BRANCH" >/dev/null 2>&1; then
  git fetch -q origin "$BRANCH" || say "WARN: fetch failed, continuing offline"
  if git rev-parse --verify -q "origin/$BRANCH" >/dev/null 2>&1 &&
     ! git merge-base --is-ancestor "origin/$BRANCH" HEAD 2>/dev/null; then
    say "origin/$BRANCH has moved — rebasing"
    if ! git rebase -q --autostash "origin/$BRANCH"; then
      git rebase --abort 2>/dev/null
      die "rebase onto origin/$BRANCH conflicted — resolve by hand in $ROOT"
    fi
  fi
fi

# --- Push directly to main ----------------------------------------------------
if ! git push -q origin "HEAD:$BRANCH" 2>&1 | grep -vE 'post-quantum|store now|openssh\.com/pq|^\*\*' ; then
  :
fi

if git ls-remote --exit-code origin "$BRANCH" >/dev/null 2>&1 &&
   [ "$(git rev-parse HEAD)" = "$(git ls-remote origin "$BRANCH" | cut -f1)" ]; then
  say "pushed to $BRANCH -> ${REMOTE_URL%.git}"
  say "site NOT deployed — theaicommit.com, the gh-pages mirror, and the newsletter are"
  say "unchanged. Run 'cd $ROOT && make deploy' or use ai-daily-learn-publish to go live."
  exit 0
fi

die "push did not land on $BRANCH — local HEAD and origin/$BRANCH differ"
