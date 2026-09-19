// GET /api/stats  Authorization: Bearer NEWSLETTER_SECRET
// Running newsletter counts. Not public — same secret as the send hook.

import { json, subscriberCounts } from "../_lib/http.js";

export async function onRequestGet(context) {
  const { request, env } = context;
  const secret = env.NEWSLETTER_SECRET;
  const auth = request.headers.get("Authorization") || "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  if (!secret || token !== secret) {
    return json(request, { error: "unauthorized" }, 401);
  }
  if (!env.DB) return json(request, { error: "db_unavailable" }, 503);
  return json(request, { ok: true, ...(await subscriberCounts(env.DB)) });
}
