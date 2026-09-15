// POST /api/newsletter
// Secret-protected send of one daily-session issue to every subscriber who
// has not unsubscribed — signup is single opt-in, so unconfirmed ("pending")
// rows left over from the old double opt-in flow are mailed too. deploy.sh
// calls this after a Cloudflare publish. The issues table is the idempotency
// key — republishing the same session does not mail again.

import { json, options, siteUrl } from "../_lib/http.js";
import { mailConfigured, sendEmail, issueEmail } from "../_lib/mail.js";

export async function onRequestOptions(context) {
  return options(context.request);
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const secret = env.NEWSLETTER_SECRET;
  const auth = request.headers.get("Authorization") || "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  if (!secret || token !== secret) {
    return json(request, { error: "unauthorized" }, 401);
  }
  if (!env.DB) return json(request, { error: "db_unavailable" }, 503);

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return json(request, { error: "invalid_request" }, 400);
  }

  const sessionId = body && typeof body.session_id === "string" ? body.session_id.trim() : "";
  const title = body && typeof body.title === "string" ? body.title.trim() : "";
  const hook = body && typeof body.hook === "string" ? body.hook.trim() : "";
  const url = body && typeof body.url === "string" ? body.url.trim() : "";
  if (!sessionId || !title || !url) {
    return json(request, { error: "missing_fields" }, 400);
  }

  const already = await env.DB.prepare(
    "SELECT session_id FROM issues WHERE session_id = ?"
  ).bind(sessionId).first();
  if (already) {
    return json(request, { ok: true, skipped: true, reason: "already_sent" });
  }

  const rows = await env.DB.prepare(
    "SELECT email, unsub_token FROM subscribers WHERE status <> 'unsubscribed'"
  ).all();
  const list = (rows && rows.results) || [];
  const site = siteUrl(env);

  let sent = 0;
  let failed = 0;
  if (mailConfigured(env)) {
    for (const row of list) {
      const mail = issueEmail({ site, title, hook, url, unsub: row.unsub_token, sessionId });
      const result = await sendEmail(env, { to: row.email, ...mail });
      if (result.ok) sent += 1;
      else failed += 1;
    }
  }

  await env.DB.prepare(
    "INSERT INTO issues (session_id, title, hook, url, sent_at, sent_count) VALUES (?, ?, ?, ?, ?, ?)"
  ).bind(sessionId, title, hook, url, new Date().toISOString(), sent).run();

  return json(request, {
    ok: true,
    sent,
    failed,
    subscribers: list.length,
    mailed: mailConfigured(env),
  });
}
