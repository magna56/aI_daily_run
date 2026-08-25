#!/usr/bin/env bash
#
# Publish an AI Daily Learn session to GitHub.
#
# Commits the session directory plus journal.md and pushes STRAIGHT TO main.
# No branch, no PR. Idempotent: a no-op when there is nothing new to commit.
#
# Usage:
#   publish.sh                 # publish today's session (YYYY-MM-DD)
#   publish.sh 2026-08-18-s2   # publish a specific session directory
#
# Exit codes: 0 ok / nothing to do, 1 setup or push failure.

set -uo pipefail

ROOT="${AI_LEARNING_DIR:-$HOME/ai_learning}"
REMOTE_URL="${AI_LEARNING_REMOTE:-git@github.com:magna56/aI_daily_run.git}"
BRANCH="main"
SESSION="${1:-$(date +%F)}"

say()  { printf '[publish] %s\n' "$*"; }
die()  { printf '[publish] ERROR: %s\n' "$*" >&2; exit 1; }

PAGES_URL="https://theaicommit.com"

# Rebuild and republish the reader site (gh-pages) after the source lands on
# main. Deliberately non-fatal: the session itself is already safely pushed, and
# a missing node or a Pages hiccup must not read as "the session was lost".
deploy_site() {
  if [ ! -x ./deploy.sh ]; then
    say "no deploy.sh in $ROOT — skipping site refresh"
    return 0
  fi
  if ! command -v node >/dev/null 2>&1; then
    say "WARN: node not found — site not refreshed; run 'make deploy' in $ROOT later"
    return 0
  fi
  say "refreshing the reader site"
  if ./deploy.sh >/dev/null 2>&1; then
    say "site updated -> $PAGES_URL/#$SESSION"
  else
    say "WARN: site deploy failed — run 'make deploy' in $ROOT to retry"
  fi
}

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
# The unattended 11:00 run has nobody reading its log, so a session that missed a
# content rule would reach the live site and the newsletter unnoticed. `--check`
# writes nothing, and only the contract-breaking warnings block: a code_example.py
# that exits non-zero is a rendered traceback by design, not a broken build.
# Sessions predating the contract are exempt inside build.js itself (date-gated),
# so republishing the back catalog never trips this.
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
    printf '[publish] ERROR: content gate — %s does not meet contract.md:\n' "$SESSION" >&2
    printf '%s\n' "$blocking" | sed 's/^/[publish]   /' >&2
    printf '[publish] Fix the session, then re-run. See .claude/skills/ai-daily-learn/contract.md\n' >&2
    exit 1
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
  # Still refresh the site: this is the path a re-run takes after a deploy that
  # failed on the first attempt, and rebuilding is idempotent.
  deploy_site
  exit 0
fi

n_files=$(git diff --cached --name-only | wc -l | tr -d ' ')

# --- Commit -------------------------------------------------------------------
# Pull the topic title out of topic.md for a meaningful subject line.
title=""
if [ -f "$SESSION/topic.md" ]; then
  title=$(sed -n 's/^# //p' "$SESSION/topic.md" | head -1)
fi
subject="$SESSION: ${title:-AI daily learn session}"

git commit -q -m "$subject" -m "Automated by the /ai-daily-learn skill. $n_files file(s).

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
  deploy_site
  exit 0
fi

die "push did not land on $BRANCH — local HEAD and origin/$BRANCH differ"
