#!/usr/bin/env bash
# Publish the AI Daily Learn reader (static SPA) to two hosts:
#   1. the gh-pages branch, which GitHub Pages serves
#   2. Cloudflare Pages, which serves theaicommit.com
#
# What gets published: index.html, 404.html, _redirects (Cloudflare's native
# SPA-fallback file — GitHub Pages ignores it, harmlessly), site/data/ (the
# session manifest and payloads generated from the YYYY-MM-DD/ folders by
# build.js) and site/assets/ (each session's .excalidraw source plus any
# figures). Pages Functions (OAuth + newsletter) live in functions/ and only
# run on Cloudflare; the GitHub Pages mirror has no server.
#
# Both targets build from the SAME local site/ folder, built once up front —
# never from a fresh build.js run on the host's own servers. That matters:
# Cloudflare's own build servers are not guaranteed to have python3, which
# lib/runner.js needs to execute every code_example.py and capture its
# output. Building locally first and uploading the finished folder sidesteps
# that risk entirely.
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

echo "==> gh-pages done. Pages will serve the update shortly:"
echo "    https://magna56.github.io/aI_daily_run/"

# --- Cloudflare Pages -----------------------------------------------------
# Set SKIP_CLOUDFLARE=1 to publish the GitHub Pages mirror only (for previews).
# Non-fatal by design: gh-pages above is already safely published by this
# point, and a Cloudflare hiccup (expired token, network blip, npx cold-start
# failure) must not read as "the whole deploy failed" — same philosophy as
# the site-refresh step in publish.sh being non-fatal to the git push.
if [ "${SKIP_CLOUDFLARE:-}" = "1" ]; then
  echo "==> Skipping Cloudflare Pages (SKIP_CLOUDFLARE=1)"
  exit 0
fi
CF_ACCOUNT_ID="573958e0e782dd175caf762d7e255da8"   # not a secret — an account identifier, visible in any dashboard URL
CF_PROJECT="theaicommit"

CF_TOKEN="$(security find-generic-password -a "wrangler" -s "cloudflare-api-token-theaicommit" -w 2>/dev/null || true)"
if [ -z "$CF_TOKEN" ]; then
  echo "==> WARN: no Cloudflare API token in Keychain (account=wrangler, service=cloudflare-api-token-theaicommit) — skipping Cloudflare Pages"
elif ! command -v npx >/dev/null 2>&1; then
  echo "==> WARN: npx not found — skipping Cloudflare Pages"
else
  echo "==> Publishing $COUNT session(s) to Cloudflare Pages ($CF_PROJECT)"
  if CLOUDFLARE_API_TOKEN="$CF_TOKEN" CLOUDFLARE_ACCOUNT_ID="$CF_ACCOUNT_ID" \
      npx --yes wrangler pages deploy site --project-name="$CF_PROJECT" --commit-dirty=true >/dev/null 2>&1; then
    echo "==> Cloudflare Pages done:"
    echo "    https://theaicommit.com  (https://$CF_PROJECT.pages.dev)"

    # Mail the newest *daily* session once. D1's issues table is the lock —
    # republishing the same session does not send again. Non-fatal: a send
    # miss must not look like the deploy failed.
    NL_SECRET="$(security find-generic-password -a "wrangler" -s "newsletter-secret-theaicommit" -w 2>/dev/null || true)"
    if [ -z "$NL_SECRET" ]; then
      echo "==> note: no newsletter secret in Keychain (account=wrangler, service=newsletter-secret-theaicommit) — skip send"
    else
      NL_PAYLOAD="$(node -e '
        global.window = {};
        require("./site/data/index.js");
        const daily = (window.SESSIONS || [])
          .filter((s) => s.kind !== "learn")
          .sort((a, b) => String(b.id).localeCompare(String(a.id)))[0];
        if (!daily) process.exit(0);
        process.stdout.write(JSON.stringify({
          session_id: daily.id,
          title: daily.title,
          hook: daily.hook || daily.insight || "",
          url: "https://theaicommit.com/#" + daily.id,
        }));
      ' || true)"
      if [ -n "${NL_PAYLOAD:-}" ]; then
        echo "==> Sending newsletter for newest daily session"
        if NL_RES="$(curl -sS -X POST "https://theaicommit.com/api/newsletter" \
            -H "Authorization: Bearer ${NL_SECRET}" \
            -H "Content-Type: application/json" \
            -d "${NL_PAYLOAD}")"; then
          echo "    ${NL_RES}"
        else
          echo "==> WARN: newsletter send failed (list is unchanged; retry later)"
        fi
      fi
    fi
  else
    echo "==> WARN: Cloudflare Pages deploy failed — gh-pages is still up to date; retry with 'make deploy' later"
  fi
fi
