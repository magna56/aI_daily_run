#!/usr/bin/env bash
# Allow verified search crawlers (Googlebot, etc.) through Cloudflare without
# JS challenges. Requires a token with Zone.Zone Settings:Edit (and ideally
# Zone.Firewall Services:Edit for custom rules).
#
# Usage:
#   export CLOUDFLARE_API_TOKEN=...
#   export CLOUDFLARE_ZONE_ID=c5dbbddffb2f1b349cbed664b3491916   # optional
#   ./scripts/seo-cloudflare-bots.sh
set -euo pipefail

TOKEN="${CLOUDFLARE_API_TOKEN:?set CLOUDFLARE_API_TOKEN}"
ZONE_ID="${CLOUDFLARE_ZONE_ID:-c5dbbddffb2f1b349cbed664b3491916}"
API="https://api.cloudflare.com/client/v4"

auth=(-H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json")

echo "==> Zone ${ZONE_ID}"

# 1) Security level → medium (not "I'm Under Attack")
echo "==> security_level → medium"
curl -sS -X PATCH "${API}/zones/${ZONE_ID}/settings/security_level" \
  "${auth[@]}" --data '{"value":"medium"}' | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("success"), d.get("errors") or d.get("result",{}).get("value"))'

# 2) Browser Integrity Check — leave on; verified bots usually pass. Report current.
echo "==> browser_check (read)"
curl -sS "${API}/zones/${ZONE_ID}/settings/browser_check" \
  "${auth[@]}" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("success"), d.get("errors") or d.get("result",{}).get("value"))'

# 3) Bot Fight Mode off when the endpoint exists (Free plan Super Bot Fight)
echo "==> bot_management / bot_fight_mode"
for path in bot_management "settings/bot_fight_mode"; do
  code=$(curl -sS -o /tmp/cf-bot.json -w "%{http_code}" "${API}/zones/${ZONE_ID}/${path}" "${auth[@]}")
  echo "  GET ${path} → ${code}"
  python3 -c 'import json; d=json.load(open("/tmp/cf-bot.json")); print(" ", d.get("errors") or d.get("result"))' 2>/dev/null || true
done

# Try disable bot fight mode via settings (Free)
curl -sS -X PATCH "${API}/zones/${ZONE_ID}/settings/bot_fight_mode" \
  "${auth[@]}" --data '{"value":"off"}' | python3 -c 'import sys,json; d=json.load(sys.stdin); print("bot_fight_mode off:", d.get("success"), d.get("errors") or d.get("result",{}).get("value"))' || true

# 4) Custom WAF rule: skip challenge for verified bots (needs Firewall Edit)
echo "==> custom skip rule for verified bots (if permitted)"
ENTRY=$(curl -sS "${API}/zones/${ZONE_ID}/rulesets/phases/http_request_firewall_custom/entrypoint" "${auth[@]}" || true)
echo "$ENTRY" | python3 -c 'import sys,json
try:
  d=json.load(sys.stdin)
except Exception as e:
  print("no entrypoint", e); raise SystemExit(0)
print("success", d.get("success"), "errors", d.get("errors"))
' || true

# 5) Quick probe: does Googlebot UA still get challenged from this host?
echo "==> probe Googlebot UA on /sitemap.xml"
curl -sS -A 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)' \
  -o /tmp/sm-probe.html -w "HTTP %{http_code} cf-mitigated=%{header_json}\n" \
  "https://theaicommit.com/sitemap.xml" 2>/dev/null | head -5 || \
curl -sS -A 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)' \
  -D - -o /tmp/sm-probe.html "https://theaicommit.com/sitemap.xml" | head -15
if grep -q 'Just a moment' /tmp/sm-probe.html 2>/dev/null; then
  echo "WARN: still serving challenge page to Googlebot UA from this network."
  echo "      In dashboard: Security → Bots → turn Bot Fight Mode OFF"
  echo "      and Security → Settings → Security Level = Medium (not I'm Under Attack)."
else
  echo "OK: sitemap response does not look like a challenge page."
fi

echo "==> done"
