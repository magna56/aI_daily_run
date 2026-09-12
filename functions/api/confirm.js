// GET /api/confirm?t=<token>
// Legacy double opt-in endpoint. Signup is single opt-in now, so nothing
// sends these links any more — it stays so confirm links already in people's
// inboxes still land somewhere sensible.

import { page, siteUrl } from "../_lib/http.js";
import { mailConfigured, sendEmail, welcomeEmail } from "../_lib/mail.js";

export async function onRequestGet(context) {
  const { request, env } = context;
  const token = new URL(request.url).searchParams.get("t") || "";
  if (!token || !env.DB) {
    return page("Link didn't work", "<p>That confirm link is missing or expired. Sign up again from the homepage.</p>");
  }

  const row = await env.DB.prepare(
    "SELECT email, status, unsub_token FROM subscribers WHERE confirm_token = ?"
  ).bind(token).first();

  if (!row) {
    return page("Link didn't work", "<p>That confirm link is missing or expired. Sign up again from the homepage.</p>");
  }

  if (row.status !== "active") {
    await env.DB.prepare(
      "UPDATE subscribers SET status = 'active', confirmed_at = ? WHERE email = ?"
    ).bind(new Date().toISOString(), row.email).run();
    if (mailConfigured(env)) {
      const mail = welcomeEmail({ site: siteUrl(env), unsub: row.unsub_token });
      await sendEmail(env, { to: row.email, ...mail });
    }
  }

  return page(
    "You're subscribed",
    "<p>You'll get one email when a new daily session ships. Unsubscribe anytime from the link in that email.</p>"
  );
}
