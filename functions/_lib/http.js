// Shared response helpers for Pages Functions. CORS is open only to this
// site's own hosts so the GitHub Pages mirror can POST signups at
// theaicommit.com (that mirror has no Functions of its own).

const ALLOWED = [
  "https://theaicommit.com",
  "https://theaicommit.pages.dev",
  "https://magna56.github.io",
  "http://127.0.0.1:8000",
  "http://localhost:8000",
];

export function siteUrl(env) {
  return (env && env.PUBLIC_URL) || "https://theaicommit.com";
}

export function corsHeaders(request) {
  const origin = (request && request.headers.get("Origin")) || "";
  const preview = /^https:\/\/[a-z0-9-]+\.theaicommit\.pages\.dev$/.test(origin);
  const ok = ALLOWED.includes(origin) || preview;
  return {
    "Access-Control-Allow-Origin": ok ? origin : "https://theaicommit.com",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Vary": "Origin",
  };
}

export function json(request, obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
      ...corsHeaders(request),
    },
  });
}

export function options(request) {
  return new Response(null, { status: 204, headers: corsHeaders(request) });
}

export function page(title, bodyHtml) {
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="theme-color" content="#111217" />
<title>${escapeHtml(title)} — The AI Commit</title>
<style>
  :root { --bg:#111217; --ink:#e7e2d8; --muted:#9a9488; --dim:#857f70; --accent:#a78bfa; --sans:"Source Sans 3",ui-sans-serif,system-ui,sans-serif; }
  html,body{margin:0;padding:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.7}
  .wrap{max-width:560px;margin:0 auto;padding:72px 24px}
  a{color:var(--accent);text-decoration:none}
  a:hover{text-decoration:underline}
  h1{font-size:26px;margin:0 0 12px}
  p{color:#cfcabf;font-size:15px}
  .k{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin:0 0 18px}
</style>
</head>
<body>
<div class="wrap">
  <p class="k">The AI Commit</p>
  <h1>${escapeHtml(title)}</h1>
  ${bodyHtml}
  <p><a href="https://theaicommit.com/">← Back to the lab</a></p>
</div>
</body>
</html>`;
  return new Response(html, {
    status: 200,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" },
  });
}

export function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function nowIso() {
  return new Date().toISOString();
}

export function isEmail(s) {
  if (typeof s !== "string") return false;
  const e = s.trim().toLowerCase();
  if (e.length < 5 || e.length > 254) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e);
}

export function newToken() {
  return crypto.randomUUID();
}

export async function subscriberCounts(db) {
  const rows = await db.prepare(
    "SELECT status, COUNT(*) AS n FROM subscribers GROUP BY status"
  ).all();
  const counts = { active: 0, pending: 0, unsubscribed: 0 };
  for (const r of (rows && rows.results) || []) {
    if (r.status in counts) counts[r.status] = Number(r.n) || 0;
  }
  counts.total = counts.active + counts.pending + counts.unsubscribed;
  return counts;
}
