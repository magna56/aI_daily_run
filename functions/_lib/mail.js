// Outbound mail via Resend. Cloudflare has no built-in marketing mail, so
// this is the one paid/external dependency. Every caller treats a missing
// RESEND_API_KEY as "mail is not configured" and still stores the signup.

export function mailConfigured(env) {
  return !!(env && env.RESEND_API_KEY);
}

export function fromAddress(env) {
  return (env && env.NEWSLETTER_FROM) || "The AI Commit <newsletter@theaicommit.com>";
}

export async function sendEmail(env, { to, subject, html, text }) {
  if (!mailConfigured(env)) {
    return { ok: false, skipped: true, error: "mail_not_configured" };
  }
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + env.RESEND_API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: fromAddress(env),
      to: [to],
      subject,
      html,
      text: text || "",
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    return { ok: false, error: data.message || data.name || "send_failed", status: res.status };
  }
  return { ok: true, id: data.id };
}

export function confirmEmail({ site, token }) {
  const url = site + "/api/confirm?t=" + encodeURIComponent(token);
  return {
    subject: "Confirm your subscription — The AI Commit",
    text:
      "Confirm your subscription to The AI Commit (one email when a new daily session ships):\n\n" +
      url +
      "\n\nIf you didn't sign up, ignore this.",
    html:
      wrap(
        "<p>One click confirms you're on the list. You'll get one email when a new daily session ships — not a digest, not a promo sequence.</p>" +
        '<p><a href="' + url + '" style="color:#a78bfa">Confirm subscription →</a></p>' +
        "<p style=\"color:#857f70;font-size:13px\">If you didn't sign up, ignore this.</p>"
      ),
  };
}

export function welcomeEmail({ site, unsub }) {
  const url = site + "/api/unsubscribe?t=" + encodeURIComponent(unsub);
  return {
    subject: "You're in — The AI Commit",
    text:
      "You're subscribed. One email when a new daily session ships.\n\nUnsubscribe anytime: " + url,
    html: wrap(
      "<p>You're on the list. When the next daily lab session publishes, you'll get one email with the title and a link — that's it.</p>" +
      '<p><a href="' + site + '" style="color:#a78bfa">Read the latest session →</a></p>' +
      '<p style="color:#857f70;font-size:13px"><a href="' + url + '" style="color:#857f70">Unsubscribe</a></p>'
    ),
  };
}

export function issueEmail({ site, title, hook, url, unsub }) {
  const unsubUrl = site + "/api/unsubscribe?t=" + encodeURIComponent(unsub);
  const blurb = hook ? "<p>" + escapeHtml(hook) + "</p>" : "";
  return {
    subject: title + " — The AI Commit",
    text:
      title +
      "\n\n" +
      (hook ? hook + "\n\n" : "") +
      url +
      "\n\nUnsubscribe: " +
      unsubUrl,
    html: wrap(
      "<h1 style=\"font-size:22px;margin:0 0 12px;color:#e7e2d8\">" + escapeHtml(title) + "</h1>" +
      blurb +
      '<p><a href="' + escapeHtml(url) + '" style="color:#a78bfa">Read the session →</a></p>' +
      '<p style="color:#857f70;font-size:13px"><a href="' + unsubUrl + '" style="color:#857f70">Unsubscribe</a></p>'
    ),
  };
}

function wrap(inner) {
  return (
    '<!doctype html><html><body style="margin:0;padding:24px;background:#111217;color:#e7e2d8;font-family:Georgia,serif;line-height:1.6">' +
    '<div style="max-width:560px;margin:0 auto">' +
    '<p style="font-family:ui-monospace,monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#a78bfa;margin:0 0 20px">The AI Commit</p>' +
    inner +
    "</div></body></html>"
  );
}

function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
