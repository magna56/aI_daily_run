import { page } from "../_lib/http.js";

export async function onRequestGet(context) {
  const { request, env } = context;
  const token = new URL(request.url).searchParams.get("t") || "";
  if (!token || !env.DB) {
    return page("Link didn't work", "<p>That unsubscribe link is missing or expired. Email theaicommit@gmail.com and we'll take you off the list.</p>");
  }

  const row = await env.DB.prepare(
    "SELECT email FROM subscribers WHERE unsub_token = ?"
  ).bind(token).first();

  if (!row) {
    return page("Already off the list", "<p>We couldn't find that subscription. You're not getting emails from us.</p>");
  }

  await env.DB.prepare(
    "UPDATE subscribers SET status = 'unsubscribed', unsubscribed_at = ? WHERE email = ?"
  ).bind(new Date().toISOString(), row.email).run();

  return page(
    "Unsubscribed",
    "<p>You're off the list. You can sign up again from the homepage any time.</p>"
  );
}
