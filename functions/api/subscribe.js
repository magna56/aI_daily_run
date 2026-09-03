// POST /api/subscribe  { email }
// Collects an address into D1 and activates it immediately — single opt-in,
// no confirmation step. If Resend is configured the address gets a welcome
// email; if it isn't, the row is still stored active so a missing API key
// never silently drops a signup.

import { json, options, isEmail, newToken, nowIso, siteUrl, subscriberCounts } from "../_lib/http.js";
import { mailConfigured, sendEmail, welcomeEmail, ownerInbox, ownerSignupEmail } from "../_lib/mail.js";

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
    return json(request, { ok: true, message: "You're on the list." });
  }

  const email = body && typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
  if (!isEmail(email)) return json(request, { error: "invalid_email" }, 400);

  const existing = await env.DB.prepare(
    "SELECT email, status, confirm_token, unsub_token FROM subscribers WHERE email = ?"
  ).bind(email).first();

  const now = nowIso();

  if (existing && existing.status === "active") {
    return json(request, { ok: true, already: true, message: "You're already on the list." });
  }

  // confirm_token is kept only because the column is NOT NULL UNIQUE; nothing
  // reads it any more now that signup is single opt-in.
  const confirm = newToken();
  const unsub = (existing && existing.unsub_token) || newToken();

  if (existing) {
    await env.DB.prepare(
      "UPDATE subscribers SET status = 'active', confirm_token = ?, unsub_token = ?, confirmed_at = ?, unsubscribed_at = NULL WHERE email = ?"
    ).bind(confirm, unsub, now, email).run();
  } else {
    await env.DB.prepare(
      "INSERT INTO subscribers (email, status, confirm_token, unsub_token, created_at, confirmed_at) VALUES (?, 'active', ?, ?, ?, ?)"
    ).bind(email, confirm, unsub, now, now).run();
  }

  if (mailConfigured(env)) {
    const mail = welcomeEmail({ site: siteUrl(env), unsub });
    await sendEmail(env, { to: email, ...mail });
  }

  await notifyOwner(env, email, "active");
  return json(request, { ok: true, message: "You're on the list. We'll email when a new daily session ships." });
}

async function notifyOwner(env, email, status) {
  if (!mailConfigured(env)) return;
  const counts = await subscriberCounts(env.DB);
  const mail = ownerSignupEmail({ email, status, counts });
  await sendEmail(env, { to: ownerInbox(env), ...mail });
}
