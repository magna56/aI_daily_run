#!/usr/bin/env bash
# Publish the AI Daily Learn reader (static SPA) to the gh-pages branch, which
# GitHub Pages serves.
#
# What gets published: index.html, 404.html, site/data/ (the session manifest
# and payloads generated from the YYYY-MM-DD/ folders by build.js) and
# site/assets/ (each session's .excalidraw source plus any figures).
# Everything is client-side — no server.
#
# Usage:  ./deploy.sh
set -euo pipefail
cd "$(dirname "$0")"

command -v node >/dev/null 2>&1 || { echo "error: node is required to build the site"; exit 1; }

echo "==> Building site/ from the session folders"
make site

REMOTE="$(git config --get remote.origin.url || true)"
if [ -z "$REMOTE" ]; then
  echo "error: no 'origin' remote configured — add one before deploying:"
  echo "  git remote add origin git@github.com:magna56/aI_daily_run.git"
  exit 1
fi

COUNT="$(node -e 'global.window={};require("./site/data/index.js");console.log(window.SESSIONS.length)')"
echo "==> Publishing $COUNT session(s) to gh-pages on $REMOTE"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cp -R site/. "$TMP"/

git -C "$TMP" init -q
git -C "$TMP" checkout -q -b gh-pages
git -C "$TMP" add -A
git -C "$TMP" -c user.name="ai-daily-learn" -c user.email="ai-daily-learn@users.noreply.github.com" \
  commit -qm "deploy: AI Daily Learn — $COUNT session(s) ($(date -u +%FT%TZ))"
git -C "$TMP" push -qf "$REMOTE" gh-pages

echo "==> Done. Pages will serve the update shortly:"
echo "    https://magna56.github.io/aI_daily_run/"
