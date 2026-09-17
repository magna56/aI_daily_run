#!/usr/bin/env bash
# Google Search Console helpers for theaicommit.com.
#
# You still create the property in Search Console once (browser). This script
# finishes verification + sitemap submit when you pass the token Google shows.
#
# DNS verification (preferred):
#   1. Search Console → Add property → Domain → theaicommit.com
#   2. Copy the TXT value (google-site-verification=...)
#   3. CLOUDFLARE_API_TOKEN must have Zone.DNS:Edit
#      GOOGLE_SITE_VERIFICATION='google-site-verification=.....' \
#      ./scripts/seo-gsc.sh dns
#
# HTML file verification:
#   1. Search Console → URL prefix → https://theaicommit.com
#   2. HTML file method → download name like google123.html
#      GOOGLE_HTML_VERIFICATION_FILE=google123.html \
#      GOOGLE_HTML_VERIFICATION_CONTENTS='google-site-verification: google123.html' \
#      ./scripts/seo-gsc.sh html
#   3. Commit, deploy, then click Verify in Search Console
#
# Sitemap (after verified):
#   ./scripts/seo-gsc.sh sitemap
set -euo pipefail

TOKEN="${CLOUDFLARE_API_TOKEN:-}"
ZONE_ID="${CLOUDFLARE_ZONE_ID:-c5dbbddffb2f1b349cbed664b3491916}"
API="https://api.cloudflare.com/client/v4"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CMD="${1:-help}"

auth=(-H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json")

case "$CMD" in
  dns)
    : "${TOKEN:?CLOUDFLARE_API_TOKEN required}"
    : "${GOOGLE_SITE_VERIFICATION:?set GOOGLE_SITE_VERIFICATION to the full TXT record value}"
    echo "==> Adding DNS TXT for Google site verification"
    curl -sS -X POST "${API}/zones/${ZONE_ID}/dns_records" \
      "${auth[@]}" \
      --data "$(python3 - <<PY
import json, os
print(json.dumps({
  "type": "TXT",
  "name": "theaicommit.com",
  "content": os.environ["GOOGLE_SITE_VERIFICATION"],
  "ttl": 3600,
}))
PY
)" | python3 -c 'import sys,json; d=json.load(sys.stdin); print("success", d.get("success")); print(d.get("errors") or d.get("result",{}).get("id"))'
    echo "Now click Verify in Search Console, then run: $0 sitemap"
    ;;
  html)
    : "${GOOGLE_HTML_VERIFICATION_FILE:?}"
    : "${GOOGLE_HTML_VERIFICATION_CONTENTS:?}"
    dest="${ROOT}/${GOOGLE_HTML_VERIFICATION_FILE}"
    # Google's HTML verification file is a tiny text file at the site root.
    printf '%s\n' "${GOOGLE_HTML_VERIFICATION_CONTENTS}" > "${dest}"
    # Ensure make site copies it
    if ! grep -q 'google.*\.html' "${ROOT}/Makefile"; then
      echo "NOTE: add ${GOOGLE_HTML_VERIFICATION_FILE} to the Makefile site: copy list before deploy."
    fi
    echo "Wrote ${dest}"
    echo "Commit + deploy, then Verify in Search Console, then: $0 sitemap"
    ;;
  sitemap)
    echo "==> Requesting Google to fetch sitemap (best-effort ping)"
    curl -sS -o /dev/null -w "ping HTTP %{http_code}\n" \
      "https://www.google.com/ping?sitemap=https%3A%2F%2Ftheaicommit.com%2Fsitemap.xml" || true
    echo "In Search Console → Sitemaps → add: https://theaicommit.com/sitemap.xml"
    echo "Also check Coverage / Pages for the old-slug 404s once redirects are live."
    ;;
  help|*)
    sed -n '2,24p' "$0"
    ;;
esac
