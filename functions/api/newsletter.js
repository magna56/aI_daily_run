// POST /api/newsletter
// Secret-protected send of one daily-session issue to every subscriber who
// has not unsubscribed — signup is single opt-in, so unconfirmed ("pending")
// rows left over from the old double opt-in flow are mailed too. deploy.sh
// calls this after a Cloudflare publish. The issues table is the idempotency
// key — republishing the same session does not mail again.

import { json, options, siteUrl, isEmail } from "../_lib/http.js";
import { mailConfigured, sendEmail, issueEmail, sleep } from "../_lib/mail.js";

// 125ms between sends is 8 per second, under Resend's limit of 10 with room
// for the clock skew between here and their limiter.
const MIN_SEND_INTERVAL_MS = 125;

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

  // Deliver one issue to one address. The issues table makes a normal send
  // idempotent, which is right for the broadcast and wrong for recovery: when
  // the 2026-09-20 send dropped an address to a Resend 429 there was no way to
  // reach that person at all, because a re-run answers "already_sent". This
  // branch deliberately neither reads nor writes that table.
  //
  // It will only mail an address that is already a subscriber. That is what
  // keeps a secret-protected send hook from being a general-purpose relay, and
  // it is also the only way to get a valid unsubscribe token into the email.
  const only = body && typeof body.to === "string" ? body.to.trim().toLowerCase() : "";
  if (only) {
    if (!isEmail(only)) return json(request, { error: "invalid_email" }, 400);
    const row = await env.DB.prepare(
      "SELECT email, status, unsub_token FROM subscribers WHERE email = ?"
    ).bind(only).first();
    if (!row) return json(request, { error: "not_a_subscriber", email: only }, 404);
    if (row.status === "unsubscribed") {
      return json(request, { error: "unsubscribed", email: only }, 409);
    }
    if (!mailConfigured(env)) return json(request, { error: "mail_not_configured" }, 503);
    const one = issueEmail({ site: siteUrl(env), title, hook, url, unsub: row.unsub_token, sessionId });
    const out = await sendEmail(env, { to: row.email, ...one });
    return json(request, out.ok
      ? { ok: true, resent: 1, session_id: sessionId, attempts: out.attempts || 1 }
      : { ok: false, error: out.error || "send_failed", status: out.status || null }, out.ok ? 200 : 502);
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
  let retried = 0;
  // sendEmail already returns why a send failed; this loop used to discard it,
  // which left a "failed: 2" in the publish log with no way to act on it. The
  // address is redacted because this response is echoed into deploy output that
  // gets pasted into issues and chats.
  const failures = [];
  if (mailConfigured(env)) {
    let previous = 0;
    for (const row of list) {
      // Stay under Resend's 10-per-second account limit. sendEmail retries a
      // 429 on top of this, but pacing is what stops us generating them: on
      // 2026-09-20 an unpaced loop of 12 tripped the limiter on the last one.
      // Past a few hundred subscribers this serial walk gets slow enough to
      // matter, and the answer then is Resend's batch endpoint, not a bigger
      // delay.
      const wait = MIN_SEND_INTERVAL_MS - (Date.now() - previous);
      if (previous && wait > 0) await sleep(wait);
      previous = Date.now();

      const mail = issueEmail({ site, title, hook, url, unsub: row.unsub_token, sessionId });
      const result = await sendEmail(env, { to: row.email, ...mail });
      if (result.attempts > 1) retried += 1;
      if (result.ok) {
        sent += 1;
      } else {
        failed += 1;
        failures.push({
          email: redactEmail(row.email),
          error: result.error || "send_failed",
          status: result.status || null,
          attempts: result.attempts || 1,
        });
      }
    }
  }

  await env.DB.prepare(
    "INSERT INTO issues (session_id, title, hook, url, sent_at, sent_count) VALUES (?, ?, ?, ?, ?, ?)"
  ).bind(sessionId, title, hook, url, new Date().toISOString(), sent).run();

  return json(request, {
    ok: true,
    sent,
    failed,
    // surfaced so a run that only just stayed inside the rate limit is visible
    // in the publish log before it becomes a dropped address
    ...(retried ? { retried } : {}),
    // only present when something went wrong, so a clean send stays one line
    ...(failures.length ? { failures } : {}),
    subscribers: list.length,
    mailed: mailConfigured(env),
  });
}

// b***@example.com — enough to identify the row, safe to paste in a log.
function redactEmail(email) {
  const at = String(email || "").indexOf("@");
  if (at < 1) return "***";
  return email[0] + "***" + email.slice(at);
}
