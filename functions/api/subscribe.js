// POST /api/subscribe  { email }
// Collects an address into D1. If Resend is configured, the row stays
// pending until they hit /api/confirm; otherwise they go active immediately
// so a missing API key never silently drops a signup.

import { json, options, isEmail, newToken, nowIso, siteUrl } from "../_lib/http.js";
import { mailConfigured, sendEmail, confirmEmail } from "../_lib/mail.js";

export async function onRequestOptions(context) {
  return options(context.request);
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.DB) return json(request, { error: "db_unavailable" }, 503);

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return json(request, { error: "invalid_request" }, 400);
  }

  // Honeypot: bots fill hidden fields. Pretend success.
  if (body && (body.website || body.company)) {
    return json(request, { ok: true, message: "Check your email to confirm." });
  }

  const email = body && typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
  if (!isEmail(email)) return json(request, { error: "invalid_email" }, 400);

  const existing = await env.DB.prepare(
    "SELECT email, status, confirm_token, unsub_token FROM subscribers WHERE email = ?"
  ).bind(email).first();

  const confirm = newToken();
  const unsub = newToken();
  const now = nowIso();
  const needConfirm = mailConfigured(env);
  const status = needConfirm ? "pending" : "active";

  if (existing && existing.status === "active") {
    return json(request, { ok: true, already: true, message: "You're already on the list." });
  }

  if (existing) {
    await env.DB.prepare(
      "UPDATE subscribers SET status = ?, confirm_token = ?, unsub_token = ?, confirmed_at = ?, unsubscribed_at = NULL WHERE email = ?"
    ).bind(status, confirm, unsub, needConfirm ? null : now, email).run();
  } else {
    await env.DB.prepare(
      "INSERT INTO subscribers (email, status, confirm_token, unsub_token, created_at, confirmed_at) VALUES (?, ?, ?, ?, ?, ?)"
    ).bind(email, status, confirm, unsub, now, needConfirm ? null : now).run();
  }

  if (needConfirm) {
    const mail = confirmEmail({ site: siteUrl(env), token: confirm });
    const sent = await sendEmail(env, { to: email, ...mail });
    if (!sent.ok && !sent.skipped) {
      return json(request, { error: "mail_failed" }, 502);
    }
    return json(request, { ok: true, message: "Check your email to confirm." });
  }

  return json(request, { ok: true, message: "You're on the list. We'll email when a new daily session ships." });
}
