// POST /api/subscribe  { email }
// Collects an address into D1 and activates it immediately — single opt-in,
// no confirmation step. If Resend is configured the address gets a welcome
// email; if it isn't, the row is still stored active so a missing API key
// never silently drops a signup.
//
// The row IS the signup. Everything after the write — the welcome email, the
// owner notification and the count query it needs — is notification, and none
// of it is allowed to decide what the person sees. Until 2026-09-20 it could:
// the handler had no try/catch and awaited all four fallible steps before
// responding, so one Resend network blip after a committed write returned a
// 5xx, and the front end rendered "Couldn't subscribe just now" to somebody
// who was already subscribed. Retrying later hit the already-active branch and
// looked like the problem had healed itself. It had not; the first attempt had
// worked all along.

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

  try {
    const existing = await env.DB.prepare(
      "SELECT email, status, confirm_token, unsub_token FROM subscribers WHERE email = ?"
    ).bind(email).first();

    if (existing && existing.status === "active") {
      return json(request, { ok: true, already: true, message: "You're already on the list." });
    }

    const now = nowIso();
    // confirm_token is kept only because the column is NOT NULL UNIQUE; nothing
    // reads it any more now that signup is single opt-in.
    const confirm = newToken();
    const unsub = (existing && existing.unsub_token) || newToken();

    // One idempotent write, because the read above and the write below are not
    // atomic. Two submissions in flight at once — two tabs, a double tap that
    // beat the disabled button — both saw no row, both inserted, and the loser
    // hit the email primary key and threw. RETURNING gives back the token that
    // is actually stored, so the loser's welcome email cannot carry an
    // unsubscribe link that was never written.
    const stored = await env.DB.prepare(
      "INSERT INTO subscribers (email, status, confirm_token, unsub_token, created_at, confirmed_at) "
      + "VALUES (?, 'active', ?, ?, ?, ?) "
      + "ON CONFLICT(email) DO UPDATE SET status = 'active', confirmed_at = excluded.confirmed_at, "
      + "unsubscribed_at = NULL "
      + "RETURNING unsub_token"
    ).bind(email, confirm, unsub, now, now).first();

    const token = (stored && stored.unsub_token) || unsub;

    // The signup is done. Hand the mail to the runtime and answer now — a slow
    // or failing Resend must not hold the response, and must not fail it.
    const mailing = deliverSignupMail(env, email, token);
    if (typeof context.waitUntil === "function") context.waitUntil(mailing);

    return json(request, { ok: true, message: "You're on the list. We'll email when a new daily session ships." });
  } catch (err) {
    // A real failure to store the address. The person is genuinely not signed
    // up, so say so and give them the path that does not depend on this code.
    return json(request, {
      error: "signup_failed",
      message: "Couldn't save that just now. Email theaicommit@gmail.com and we'll add you.",
    }, 500);
  }
}

// Notification only. Swallows everything: by the time this runs the response
// has already gone out, so a throw here would be an unhandled rejection and
// nothing more.
async function deliverSignupMail(env, email, unsub) {
  if (!mailConfigured(env)) return;
  try {
    await sendEmail(env, { to: email, ...welcomeEmail({ site: siteUrl(env), unsub }) });
    const counts = await subscriberCounts(env.DB);
    await sendEmail(env, { to: ownerInbox(env), ...ownerSignupEmail({ email, status: "active", counts }) });
  } catch (e) {
    // Deliberately empty. The address is stored; mail is best effort.
  }
}
