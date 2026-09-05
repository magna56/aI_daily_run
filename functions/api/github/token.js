// Cloudflare Pages Function — the one piece of this that must run server-side,
// because exchanging an OAuth code for an access token requires the app's
// client secret, which can never be shipped to the browser.
//
// Deliberately stateless: no session, no cookie, no database. Takes a code,
// returns a token, and forgets both immediately. The frontend is the one that
// holds onto the resulting token (in localStorage), same as everything else
// this site stores client-side.
export async function onRequestPost(context) {
  const { request, env } = context;

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return json({ error: "invalid_request" }, 400);
  }

  const code = body && body.code;
  if (!code || typeof code !== "string") {
    return json({ error: "missing_code" }, 400);
  }

  const upstream = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,
      code: code,
    }),
  });

  const data = await upstream.json();
  if (data.error) {
    return json({ error: data.error, error_description: data.error_description }, 400);
  }

  return json({ access_token: data.access_token, scope: data.scope }, 200);
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}
