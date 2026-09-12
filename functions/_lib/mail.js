// Outbound mail via Resend. Templates are table-based and light-on-cream so
// they survive Gmail (the old dark slab looked empty and got inverted).

export function mailConfigured(env) {
  return !!(env && env.RESEND_API_KEY);
}

export function fromAddress(env) {
  return (env && env.NEWSLETTER_FROM) || "The AI Commit <newsletter@theaicommit.com>";
}

export function ownerInbox(env) {
  return (env && env.NEWSLETTER_NOTIFY) || "theaicommit@gmail.com";
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
    html: wrap({
      site,
      preheader: "One click and you're on the list.",
      eyebrow: "Almost in",
      inner:
        heading("Confirm your subscription") +
        lede("You'll get one email when a new daily session ships — the title, the insight, a link. Not a digest.") +
        cta(url, "Confirm subscription") +
        '<p style="margin:18px 0 0;font-size:13px;color:#857f70">If you didn\'t sign up, ignore this.</p>',
    }),
  };
}

export function welcomeEmail({ site, unsub }) {
  const url = site + "/api/unsubscribe?t=" + encodeURIComponent(unsub);
  return {
    subject: "You're in — The AI Commit",
    text:
      "You're subscribed. One email when a new daily session ships.\n\nUnsubscribe anytime: " + url,
    html: wrap({
      site,
      unsub: url,
      preheader: "You're on the list. Next issue lands when the next daily session ships.",
      eyebrow: "Welcome",
      inner:
        heading("You're on the list") +
        lede("When the next daily lab session publishes, you'll get one email with the title, the insight, and a link. That's the whole product.") +
        cta(site, "Read today's session"),
    }),
  };
}

export function ownerSignupEmail({ email, status, counts }) {
  const n = counts || { active: 0, pending: 0, unsubscribed: 0, total: 0 };
  const line =
    status === "pending"
      ? email + " signed up and still needs to confirm."
      : email + " is on the list.";
  const tally =
    "Active: " + n.active +
    "  ·  pending: " + n.pending +
    "  ·  unsubscribed: " + n.unsubscribed +
    "  ·  total: " + n.total;
  return {
    subject: "Newsletter signup (" + n.active + " active) — " + email,
    text: line + "\n\n" + tally,
    html: wrap({
      site: "https://theaicommit.com",
      preheader: line,
      eyebrow: "New signup",
      inner:
        heading(email) +
        lede(line) +
        '<p style="margin:0;font-size:14px;color:#857f70">' + escapeHtml(tally) + "</p>",
    }),
  };
}

export function issueEmail({ site, title, hook, url, unsub, sessionId }) {
  const unsubUrl = site + "/api/unsubscribe?t=" + encodeURIComponent(unsub);
  const dateLine = formatSessionDate(sessionId);
  return {
    subject: title + " — The AI Commit",
    text:
      title +
      "\n\n" +
      (hook ? hook + "\n\n" : "") +
      url +
      "\n\nUnsubscribe: " +
      unsubUrl,
    html: wrap({
      site,
      unsub: unsubUrl,
      preheader: hook || title,
      eyebrow: dateLine ? "Daily lab  ·  " + dateLine : "Daily lab",
      inner:
        heading(title) +
        (hook ? lede(hook) : "") +
        cta(url, "Read the session") +
        '<p style="margin:16px 0 0;font-size:13px;color:#857f70">A 30-minute lab: the mechanism, a diagram, and code that runs in the browser.</p>',
    }),
  };
}

function wrap({ site, inner, eyebrow, preheader, unsub }) {
  const preview = preheader
    ? '<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;opacity:0;color:transparent">' +
      escapeHtml(preheader) +
      "</div>"
    : "";
  const brand = site || "https://theaicommit.com";
  const foot =
    '<p style="margin:20px 0 0;font-family:Georgia,\'Times New Roman\',serif;font-size:12px;line-height:1.65;color:#857f70">' +
    'The AI Commit &nbsp;·&nbsp; one email when a new daily session ships<br />' +
    '<a href="' + escapeHtml(brand) + '" style="color:#7c5cd9;text-decoration:none">theaicommit.com</a>' +
    (unsub
      ? ' &nbsp;·&nbsp; <a href="' + escapeHtml(unsub) + '" style="color:#857f70;text-decoration:underline">Unsubscribe</a>'
      : "") +
    "</p>";

  return (
    "<!doctype html><html><head>" +
    '<meta charset="utf-8" />' +
    '<meta name="viewport" content="width=device-width,initial-scale=1" />' +
    '<meta name="color-scheme" content="light" />' +
    '<meta name="supported-color-schemes" content="light" />' +
    "</head>" +
    '<body style="margin:0;padding:0;background:#f3efe6;">' +
    preview +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f3efe6">' +
    '<tr><td align="center" style="padding:32px 16px 48px">' +
    '<table role="presentation" width="560" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;width:100%;background:#fffcf7;border:1px solid #e6e0d4;border-radius:14px">' +
    '<tr><td style="height:5px;background:#7c5cd9;border-radius:14px 14px 0 0;font-size:0;line-height:0">&nbsp;</td></tr>' +
    '<tr><td style="padding:28px 36px 8px">' +
    '<p style="margin:0;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#7c5cd9">The AI Commit</p>' +
    (eyebrow
      ? '<p style="margin:8px 0 0;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#857f70">' +
        escapeHtml(eyebrow) +
        "</p>"
      : "") +
    "</td></tr>" +
    '<tr><td style="padding:12px 36px 8px;font-family:Georgia,\'Times New Roman\',serif;color:#1c1914">' +
    inner +
    "</td></tr>" +
    '<tr><td style="padding:8px 36px 32px;border-top:1px solid #efe9dc">' +
    foot +
    "</td></tr>" +
    "</table></td></tr></table></body></html>"
  );
}

function heading(text) {
  return (
    '<h1 style="margin:0 0 14px;font-family:Georgia,\'Times New Roman\',serif;font-size:28px;line-height:1.25;font-weight:700;letter-spacing:-0.02em;color:#1c1914">' +
    escapeHtml(text) +
    "</h1>"
  );
}

function lede(text) {
  return (
    '<p style="margin:0 0 8px;font-family:Georgia,\'Times New Roman\',serif;font-size:17px;line-height:1.6;color:#3d382f">' +
    escapeHtml(text) +
    "</p>"
  );
}

function cta(href, label) {
  return (
    '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:26px 0 4px">' +
    "<tr><td style=\"border-radius:8px;background:#7c5cd9\">" +
    '<a href="' +
    escapeHtml(href) +
    '" style="display:inline-block;padding:13px 22px;font-family:Georgia,\'Times New Roman\',serif;font-size:16px;font-weight:700;color:#ffffff;text-decoration:none">' +
    escapeHtml(label) +
    "</a></td></tr></table>"
  );
}

function formatSessionDate(id) {
  if (!id) return "";
  const m = String(id).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return "";
  const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  return months[Number(m[2]) - 1] + " " + Number(m[3]) + ", " + m[1];
}

function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
