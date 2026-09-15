# Voiceprint — technical build spec

How to build it end to end on Cloudflare, with Google sign-in, free tier, no payments.

Companion to `docs/voiceprint-spec.md` (what the product is and why). **That document owns product
decisions; this one owns implementation.** Where they disagree, the product spec wins and this file
is wrong.

**Status:** not built. Every file path below is a proposal.

---

## 1. What we are building

A web app where someone uploads writing they know is theirs, uploads a document an AI has edited,
and gets back a version that sounds like them again.

### Who it is for — broader than the first draft assumed

The product spec's examples were job applications. That was one person's problem, not the market.
The real shape is **any document where being the author is the point**:

| Document | Why AI editing hurts it |
|----------|-------------------------|
| Reassignment and staffing letters | A manager writes twelve, runs them through AI, and all twelve read identically. The recipient notices |
| Performance reviews | Generic praise is worse than no praise; specifics are the entire value |
| Recommendation letters | The reader is calibrating on *your* voice across the letters you have written |
| Applications and statements | Competing against hundreds of documents that had the same edit applied |
| Internal memos, grant sections, personal essays | Written by a named person to people who know them |

The common factor is not job-seeking. It is that **a named human is accountable for the words**, and
smoothing removes what made them accountable — the specifics, the rhythm, the willingness to say
something that could be argued with.

Nothing in the build is audience-specific. Do not hardcode application-shaped language into the UI.

### Scope for v1

- Free. No payments, no Stripe, no billing code.
- Two documents per user, enforced server-side.
- Google sign-in only.
- The deliverable is a downloadable document.

Explicitly out: payments, teams, saved voiceprints across sessions, Google Docs add-on, OCR,
mobile app, any non-Google identity provider.

---

## 2. Principles that drive the architecture

These are constraints, not aspirations. Each one rules something out.

1. **Documents are never stored.** No R2 bucket, no `text` column, no log line containing user
   prose. This is not a policy we promise — it is an absence of anywhere to put it. It rules out
   server-side session state and forces the client to resend context on every call.
2. **The measurement is free; only generation costs money.** Everything deterministic runs in the
   browser. The paywall-shaped boundary sits exactly at the Claude call, which is also the only
   place spend can run away.
3. **The server is stateless except for counters.** The Worker holds credits, caps and spend. It
   holds no document, no fingerprint, no draft.
4. **Degrade, do not fail.** If Claude is down or the daily cap is hit, analysis still works. The
   user loses rewriting, not the product.
5. **The Python script is the reference implementation.** `.claude/skills/sounds-like-me/scripts/voiceprint.py`
   already works. The TypeScript engine is a port that must produce identical numbers, proven by
   tests, not by eyeballing.

---

## 3. System overview

```
┌─ Browser ─────────────────────────────────────────────────┐
│  Preact SPA                                                │
│   ├─ mammoth / pdf.js      parse .docx .pdf .md .txt       │
│   ├─ voiceprint.ts         fingerprint, drift, paragraphs  │  ← all local
│   ├─ docx                  export                          │
│   └─ session state in memory + sessionStorage              │
└───────────────┬────────────────────────────────────────────┘
                │  fetch, session cookie
┌───────────────▼─ Cloudflare Worker ────────────────────────┐
│  /api/auth/google    verify Google ID token, issue cookie  │
│  /api/me             credits + caps                        │
│  /api/questions      → Claude (structured output)          │
│  /api/rewrite        → Claude (streamed passthrough)       │
│                                                             │
│  bindings: DB (D1) · RL (rate limit) · AE (analytics)      │
│  secrets:  ANTHROPIC_API_KEY · SESSION_SECRET ·            │
│            GOOGLE_CLIENT_ID                                 │
└───────────────┬────────────────────────────────────────────┘
                │
        ┌───────▼────────┐        ┌──────────────────┐
        │  AI Gateway    │───────▶│  Anthropic API   │
        │  logs, spend,  │        │  claude-sonnet-5 │
        │  retries       │        └──────────────────┘
        └────────────────┘
        ┌────────────────┐
        │  D1: users,    │   counters and outcomes only.
        │  documents,    │   no document text, ever.
        │  daily_spend   │
        └────────────────┘
```

One request path costs money: `/api/rewrite`. Everything else is free to serve.

---

## 4. Cloudflare services

### Used

| Service | For | Why this and not something else |
|---------|-----|--------------------------------|
| **Workers (static assets)** | Hosting + API in one deploy | One `wrangler deploy`, one origin, no CORS. Cloudflare's current recommended path for new projects; Pages Functions would also work and this team already knows it, but a new product does not need to inherit that split |
| **D1** | users, documents, daily_spend | SQLite, already used in this org for `theaicommit`. The data is three small tables of integers |
| **AI Gateway** | In front of Anthropic | Per-request logging, spend analytics, retries and rate limiting without writing any of it. Point the SDK's `baseURL` at it and you are done |
| **Rate Limiting binding** | `/api/rewrite`, `/api/auth` | Native, no Redis, no counter table |
| **Turnstile** | Sign-in | Stops scripted account creation. Free |
| **Analytics Engine** | Funnel events | Funnel without a third-party tracker, which would contradict §2.1 |
| **Secrets** | API keys | `wrangler secret put` |

### Deliberately not used

| Service | Why not |
|---------|---------|
| **R2** | Storing documents is the one thing we promise not to do. Not creating the bucket is the strongest form of that promise |
| **KV** | Sessions are signed cookies; JWKS caching uses the Cache API. Nothing else needs it |
| **Durable Objects** | Credit accounting is a D1 transaction at this volume. Revisit only if a concurrency bug proves otherwise |
| **Queues** | The user is watching. Every call is synchronous |
| **Workers AI** | Voice-matching quality is the product. Run it on Claude |

---

## 5. Authentication — Google sign-in

### Why Google Identity Services, not full OAuth

We need identity, not access to anyone's Gmail. That makes the **ID token flow** correct and the
authorization-code flow unnecessary: no redirect URIs, no refresh tokens, no token storage, no
callback route.

The browser renders Google's button, Google hands back a signed JWT, we verify it in the Worker and
issue our own session. Total server code: about 80 lines.

### Client

```html
<div id="g_id_onload"
     data-client_id="…apps.googleusercontent.com"
     data-callback="onGoogleCredential"
     data-auto_prompt="false"></div>
<div class="g_id_signin" data-type="standard"></div>
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

```ts
async function onGoogleCredential(res: { credential: string }) {
  const r = await fetch("/api/auth/google", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ credential: res.credential, turnstile: turnstileToken }),
  });
  if (r.ok) session.set(await r.json());
}
```

### Worker verification — do it properly

**Decoding the JWT is not verifying it.** A decoded-but-unverified token is attacker-supplied JSON.
Verify the signature against Google's published keys, then check every claim:

```ts
const JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs";

async function verifyGoogleIdToken(jwt: string, clientId: string): Promise<GoogleClaims> {
  const [rawHeader, rawPayload, rawSig] = jwt.split(".");
  if (!rawHeader || !rawPayload || !rawSig) throw new Error("malformed");

  const header = JSON.parse(b64urlToText(rawHeader));
  if (header.alg !== "RS256") throw new Error("unexpected alg");

  // Cache API, keyed on the JWKS URL. Google rotates keys; respect the response's
  // cache headers rather than pinning a key.
  const jwks = await cachedJson(JWKS_URL);
  const jwk = jwks.keys.find((k: any) => k.kid === header.kid);
  if (!jwk) throw new Error("unknown kid");

  const key = await crypto.subtle.importKey(
    "jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);

  const ok = await crypto.subtle.verify(
    "RSASSA-PKCS1-v1_5", key,
    b64urlToBytes(rawSig),
    new TextEncoder().encode(`${rawHeader}.${rawPayload}`));
  if (!ok) throw new Error("bad signature");

  const claims = JSON.parse(b64urlToText(rawPayload));
  const now = Math.floor(Date.now() / 1000);
  if (claims.aud !== clientId) throw new Error("wrong audience");
  if (claims.iss !== "https://accounts.google.com" &&
      claims.iss !== "accounts.google.com") throw new Error("wrong issuer");
  if (claims.exp <= now) throw new Error("expired");
  if (!claims.email_verified) throw new Error("unverified email");

  return claims; // sub, email, name, picture
}
```

All of this is WebCrypto, which Workers ship natively. No Node polyfills.

### Our session

An HMAC-signed JWT in a cookie. Stateless, so no session table and no lookup on every request.

```
Set-Cookie: vp_session=<jwt>; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=2592000
```

Payload: `{ sub, email, iat, exp }`, signed HS256 with `SESSION_SECRET` via WebCrypto. 30 days.
`SameSite=Lax` is correct here — there are no cross-site POSTs in this app.

Sign-out clears the cookie. There is no server-side revocation in v1; if that becomes necessary,
add a `sessions_revoked_after` timestamp on the user row and compare against `iat`.

---

## 6. Data model

```sql
-- db/schema.sql

CREATE TABLE users (
  id             TEXT PRIMARY KEY,           -- Google 'sub', never the email
  email          TEXT UNIQUE NOT NULL,
  created_at     INTEGER NOT NULL,
  last_seen_at   INTEGER NOT NULL,
  credits_total  INTEGER NOT NULL DEFAULT 2,
  credits_used   INTEGER NOT NULL DEFAULT 0,
  status         TEXT NOT NULL DEFAULT 'active'   -- active | blocked
);

-- One row per document a user starts rewriting. Note what is absent:
-- no title, no text, no paragraphs, no questions, no answers.
CREATE TABLE documents (
  id                 TEXT PRIMARY KEY,       -- client-generated UUID
  user_id            TEXT NOT NULL REFERENCES users(id),
  created_at         INTEGER NOT NULL,
  word_count         INTEGER,
  assistant          TEXT,                   -- claude|chatgpt|gemini|generic|unsure
  paragraphs_flagged INTEGER,
  rewrites_used      INTEGER NOT NULL DEFAULT 0,
  questions_used     INTEGER NOT NULL DEFAULT 0,
  voice_match_before INTEGER,
  voice_match_after  INTEGER,
  exported           INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_documents_user ON documents(user_id, created_at);

CREATE TABLE daily_spend (
  day            TEXT PRIMARY KEY,           -- YYYY-MM-DD, UTC
  rewrite_calls  INTEGER NOT NULL DEFAULT 0,
  question_calls INTEGER NOT NULL DEFAULT 0,
  input_tokens   INTEGER NOT NULL DEFAULT 0,
  cached_tokens  INTEGER NOT NULL DEFAULT 0,
  output_tokens  INTEGER NOT NULL DEFAULT 0,
  usd_estimate   REAL    NOT NULL DEFAULT 0
);
```

Two things worth noticing.

**`voice_match_before` and `voice_match_after` are the product metric**, stored for free as two
integers. Median improvement across documents tells you whether the thing works better than any
survey would.

**A "document" is a credit, not a call.** A credit is consumed the first time a rewrite is requested
for a new `document.id`. Every subsequent paragraph in that document is free, within the caps. A
user who spends a credit and then cannot fix paragraph four would rightly be furious.

---

## 7. API

Four endpoints. All JSON, all behind the session cookie except the first.

### `POST /api/auth/google`

```
→ { credential: string, turnstile: string }
← { email, creditsTotal, creditsUsed }   + Set-Cookie
```

Verify Turnstile, verify the Google token (§5), upsert the user, issue the session.

```sql
INSERT INTO users (id, email, created_at, last_seen_at)
VALUES (?1, ?2, ?3, ?3)
ON CONFLICT(id) DO UPDATE SET last_seen_at = ?3, email = ?2;
```

### `GET /api/me`

```
← { email, creditsTotal, creditsUsed, caps: {...}, rewritesAvailable: boolean }
```

`rewritesAvailable` is false when the daily spend ceiling is hit, so the client can show the
degraded state before the user writes anything.

### `POST /api/questions`

One call per document. Returns the interview questions.

```
→ {
    docId, assistant, wordCount,
    fingerprint: { sentLenMean, sentLenSd, contractionsPer1k, specificityPer100w, ... },
    exemplars:   [ "…600 words of their own writing…" ],
    flagged:     [ { index, text, reasons: string[], originalText?: string } ]
  }
← { questions: [ { paragraphIndex, question, missing: "number"|"name"|"date"|"outcome" } ] }
```

`originalText` is the matching paragraph from their pre-AI original when the client can align one.
It is what makes a question specific — *"your original said eleven months here"* — and it is the
single highest-value field in the payload.

Use **structured outputs** so the response parses without defensive code:

```ts
output_config: {
  format: {
    type: "json_schema",
    schema: {
      type: "object",
      additionalProperties: false,
      required: ["questions"],
      properties: {
        questions: {
          type: "array",
          items: {
            type: "object",
            additionalProperties: false,
            required: ["paragraphIndex", "question", "missing"],
            properties: {
              paragraphIndex: { type: "integer" },
              question:       { type: "string" },
              missing: { type: "string", enum: ["number","name","date","outcome","opinion"] },
            },
          },
        },
      },
    },
  },
}
```

### `POST /api/rewrite`

The only expensive endpoint. Streams.

```
→ { docId, paragraph, answers: string[], constraints: {...}, exemplars: [...], assistant }
← text/event-stream  (Anthropic SSE, passed through)
```

Order of operations matters:

1. Session → user. 401 if absent.
2. Rate limit (binding). 429 if exceeded.
3. Daily spend ceiling. 503 `{ reason: "daily_cap" }` if hit.
4. Credit check: if `docId` is new and `credits_used >= credits_total`, 402
   `{ reason: "no_credits" }`. If new and credits remain, insert the document row and increment
   `credits_used` **in one transaction**.
5. Per-document caps: `rewrites_used < 20`, else 429 `{ reason: "doc_cap" }`.
6. Call Claude, stream the body straight back.
7. After the stream closes, record usage (see §9).

The client sends `exemplars` and `constraints` on every call because the server stores nothing.
That is the cost of §2.1 and it is worth paying.

**The client must serialize the style block byte-identically across every call in a session.**
Sort keys, fix number formatting, no timestamps. A single varying byte moves the cache prefix and
the hit rate silently drops to zero. See §8.

---

## 8. Claude integration

### Client and model

```ts
import Anthropic from "@anthropic-ai/sdk";

const anthropic = new Anthropic({
  apiKey: env.ANTHROPIC_API_KEY,
  baseURL: `https://gateway.ai.cloudflare.com/v1/${env.CF_ACCOUNT_ID}/voiceprint/anthropic`,
});
```

| | Model | Effort | Why |
|---|-------|--------|-----|
| Rewrite | `claude-sonnet-5` | `low` | A constrained transform, not a reasoning problem. Low effort is faster and cheaper, and this is the latency the user feels |
| Questions | `claude-sonnet-5` | `medium` | Noticing *what kind* of specific is missing is the judgment call in the whole product |

`claude-opus-5` is the upgrade path if measurement shows Sonnet 5 matching voice worse. Decide that
from an A/B on real documents, not from the price sheet — at free-tier volumes the difference is
tens of dollars a month.

### Prompt shape — cache placement is the whole game

Render order is `tools` → `system` → `messages`. Stable content goes first, volatile content last.

```ts
const stream = anthropic.messages.stream({
  model: "claude-sonnet-5",
  max_tokens: 1024,
  thinking: { type: "adaptive" },
  output_config: { effort: "low" },

  // STABLE — identical for every paragraph in this document. Cached.
  system: [
    { type: "text", text: REWRITE_INSTRUCTIONS },              // frozen, in source
    { type: "text", text: renderExemplars(body.exemplars) },   // their own writing
    { type: "text", text: renderConstraints(body.constraints), // measured fingerprint
      cache_control: { type: "ephemeral" } },
  ],

  // VOLATILE — changes every call. After the breakpoint.
  messages: [{ role: "user", content: renderParagraphTask(body.paragraph, body.answers) }],
});
```

The cached prefix is roughly 2,700 tokens: instructions, ~600 words of their writing, and the
constraint list. Eight or nine calls share it.

Three rules that keep it working:

- **Sequential, never parallel.** A cache entry is only readable once the first response has begun
  streaming. Firing eight paragraph rewrites at once means eight full-price writes and zero reads —
  roughly double the cost. The user reviews paragraphs one at a time anyway, so sequential hides
  the latency.
- **5-minute TTL is right.** A user working through paragraphs keeps it warm. If they wander off
  and it expires, they pay one more write. Do not build keep-alive requests for a free tier.
- **Verify it.** Log `usage.cache_read_input_tokens`. If it is zero across a session, something in
  the style block is varying between calls and the cache is doing nothing.

### Constraints, generated from the measurement

The fingerprint becomes instructions. This is what makes the rewrite aim at *them* rather than at
good prose:

```
Target sentence length: mean 10.4 words, standard deviation 4.8.
Vary deliberately — include sentences under 8 words.
Contractions: use them, roughly 35 per 1000 words.
Em dashes: this author does not use them.
Do not use: multifaceted, delve, meticulous, eager to contribute.
Do not use a three-item list of abstract nouns.
Do not use "not only X but also Y" or "it's not X, it's Y".
Never state a fact not present in the author's answers below.
If a specific is missing, write the sentence shorter rather than inventing one.
```

That last pair of lines is the never-invent rule from the product spec, enforced at the prompt
level. It is also enforced structurally: the server never sends a fact the client did not send it.

### Pitfalls

- **No assistant prefill.** Prefilling the last assistant turn returns a 400 on current models. Use
  the system prompt or structured outputs to shape the response.
- **Stream through, do not buffer.** `return new Response(upstream.body, { headers })` costs a
  Worker almost nothing. Reassembling the SSE to re-emit it wastes CPU time and delays first token.
- **Check `stop_reason` before reading content.** `refusal` returns HTTP 200.
- **Parse tool/structured JSON with `JSON.parse`**, never string matching.

---

## 9. Credits, caps and the spend ceiling

### Caps

| Cap | Value | Why |
|-----|-------|-----|
| Documents per user | 2 | The free tier |
| Rewrite calls per document | 20 | 10 paragraphs × 2 re-rolls |
| Words per document | 2,500 | A 6,000-word document is 3× the cost of the estimate |
| Rate limit | 30 req/min/user | Scripted abuse |
| Daily spend | set in config | §9.2 |

The per-document cap matters more than the model choice. Without it, one user re-rolling every
paragraph twenty times costs what thirty normal users do.

### The daily ceiling, and degrading well

Before each Claude call, read today's `daily_spend`. Over budget → 503 with
`{ reason: "daily_cap" }`.

The client's response to that is the important part: **analysis keeps working.** Scores, drift
table, flagged paragraphs and interview questions are all local or already fetched. The page says
rewrites are back tomorrow and offers the questions as something to work on by hand. A capacity
message, not an error.

Set the ceiling deliberately low at launch. It is easier to raise it after a week of real traffic
than to explain a surprise bill.

### Recording spend

After the stream completes, the SDK exposes final usage. Estimate dollars in the Worker so
`daily_spend` is self-contained, and reconcile against AI Gateway's own analytics rather than
trusting either alone.

```ts
const final = await stream.finalMessage();
const u = final.usage;
const usd = (u.input_tokens * IN_RATE
           + (u.cache_read_input_tokens ?? 0) * IN_RATE * 0.1
           + (u.cache_creation_input_tokens ?? 0) * IN_RATE * 1.25
           + u.output_tokens * OUT_RATE) / 1_000_000;

ctx.waitUntil(recordSpend(env.DB, usd, u));
```

`ctx.waitUntil` keeps the accounting off the response path.

---

## 10. The client

**Preact + signals.** Small, and this UI has enough interacting state — four uploads, a
fingerprint, a ranked paragraph list, an answer set, per-paragraph accept/reject — that hand-rolled
DOM updates become the bug surface. Vanilla is defensible; a framework is less work.

```
src/
  main.tsx
  state.ts                 signals: docs, fingerprint, flagged, answers, rewrites
  parse/
    docx.ts                mammoth
    pdf.ts                 pdf.js, text layer only
    text.ts
  engine/
    voiceprint.ts          the port — §11
    profiles/
      chatgpt-2026-09.json
      claude-2026-09.json
      gemini-2026-09.json
      generic.json
  export/
    docx.ts
  ui/
    Upload.tsx  Scores.tsx  DriftTable.tsx  ParagraphList.tsx
    Interview.tsx  Rewrite.tsx  Export.tsx
```

Tell profiles are **static JSON assets, not code**. The quarterly refresh the product spec requires
is then a file swap, and a stale profile is visible in its filename.

Session state lives in memory plus `sessionStorage` for crash recovery. Nothing in `localStorage`,
nothing that outlives the tab — consistent with §2.1.

A scanned PDF with no text layer is rejected with a clear message. OCR is a later problem.

---

## 11. Porting the metrics engine

`voiceprint.py` is ~450 lines of regex and arithmetic and ports to TypeScript almost directly.
The risk is not that the port is hard; it is that it drifts by a few percent and nobody notices,
so the browser and the skill disagree about the same document.

**Keep the Python as the reference implementation and test against it.**

```
engine/
  voiceprint.ts
  __tests__/
    fixtures/            6-8 documents: human, AI-edited, mixed, short, long, bulleted
    golden/              JSON from `voiceprint.py --json` on each fixture
    parity.test.ts       asserts TS output == golden, every numeric field
```

Regenerate goldens only via the Python script, never by hand. A parity failure means the port is
wrong until proven otherwise.

Watch three things specifically:

- **Sentence splitting.** Python's `re.split` with lookbehind and the abbreviation guard must be
  reproduced exactly. JS regex lookbehind is supported in Workers and modern browsers.
- **Unicode.** Curly apostrophes, em dashes, non-breaking spaces. Normalize identically on both
  sides (`NFC`) before tokenizing.
- **Float formatting.** Round at the same places or parity tests fail on noise.

---

## 12. Security and privacy

| Concern | Handling |
|---------|----------|
| API key exposure | `ANTHROPIC_API_KEY` is a Worker secret. It never reaches the client and never appears in a response |
| Session theft | HttpOnly, Secure, SameSite=Lax, 30-day expiry |
| Forged identity | Full RS256 verification against Google's JWKS, plus `aud` / `iss` / `exp` / `email_verified` |
| Bot signups | Turnstile on `/api/auth/google` |
| Using us as a free rewriting API | Google account + 2 documents + rate limit + per-doc cap. The product spec's baseline gate also means a caller must supply 400 words of real writing first |
| Document leakage | No storage layer exists. Do not log request bodies — `console.log(body)` in a debugging session is the realistic way this promise gets broken |
| XSS | CSP allowing only self and `accounts.google.com`. Preact escapes by default; no `dangerouslySetInnerHTML` on user text |
| PII | Email and Google `sub`. Deletion endpoint removes both rows. Say so in the privacy page |

The privacy page should state plainly: *we store your email and counts of what you did. We do not
store your documents, and there is no system here that could.*

---

## 13. Observability

Analytics Engine, one event per meaningful step. No third-party tracker.

```ts
env.AE.writeDataPoint({
  blobs:   [step, assistant, capReason ?? ""],
  doubles: [wordCount, voiceMatchBefore, voiceMatchAfter],
  indexes: [userId],
});
```

Steps worth recording: `signin`, `upload_baseline`, `analyzed`, `questions_shown`,
`questions_answered`, `rewrite_started`, `rewrite_accepted`, `exported`, `cap_hit`.

The two numbers that decide whether the product works:

1. **`upload_baseline` ÷ `signin`.** Finding 400 words you definitely wrote is the highest-friction
   step in the product. If this is under ~40%, the funnel problem is here and nothing downstream
   matters.
2. **Median `voiceMatchAfter − voiceMatchBefore` among exported documents.** If that is under ~15
   points, the rewrite is not earning its cost.

AI Gateway covers latency, error rates, token spend and per-request logs without extra code.

---

## 14. Deploy

```
voiceprint/
  wrangler.jsonc
  src/worker/         index.ts, auth.ts, claude.ts, credits.ts, spend.ts
  src/client/         the Preact app
  db/schema.sql
  dist/               vite build output, served as static assets
```

```jsonc
{
  "name": "voiceprint",
  "main": "src/worker/index.ts",
  "compatibility_date": "2026-09-15",
  "assets": { "directory": "./dist", "not_found_handling": "single-page-application" },
  "d1_databases": [{ "binding": "DB", "database_name": "voiceprint", "database_id": "…" }],
  "analytics_engine_datasets": [{ "binding": "AE", "dataset": "voiceprint_events" }],
  "ratelimits": [{ "name": "RL", "namespace_id": "1001", "simple": { "limit": 30, "period": 60 } }],
  "vars": { "CF_ACCOUNT_ID": "…", "GOOGLE_CLIENT_ID": "…", "DAILY_USD_CAP": "10" }
}
```

```bash
wrangler d1 execute voiceprint --file=db/schema.sql
wrangler secret put ANTHROPIC_API_KEY
wrangler secret put SESSION_SECRET
wrangler secret put TURNSTILE_SECRET
npm run build && wrangler deploy
```

Two environments: `preview` (own D1, own gateway) and `production`. GitHub Actions deploys
production on push to `main`. `GOOGLE_CLIENT_ID` differs per environment and both origins must be
registered in the Google Cloud console.

---

## 15. What it costs to run

| | Cost |
|---|------|
| Workers paid plan | $5/month |
| D1 | Free tier covers it comfortably — three small tables, a handful of writes per user |
| Static assets, AI Gateway, Turnstile | Free |
| Analytics Engine | Included in the Workers plan |
| **Infrastructure** | **~$5/month** |
| Claude, free tier, 2 docs/user | ~$0.09/user on Sonnet 5 |

100 new users/day ≈ **$9/day**, before the funnel discount — realistically nearer $4, since only
about 40% of sign-ups get far enough to trigger a rewrite. The `DAILY_USD_CAP` is what stops a
deadline-week spike from surprising you.

---

## 16. Build order

| Phase | Days | Ships |
|-------|------|-------|
| **1** | 1–2 | Worker skeleton, D1 schema, Google sign-in end to end, `/api/me` |
| **2** | 3–5 | Engine port + parity tests. **Nothing below this is trustworthy until parity passes** |
| **3** | 6–7 | Upload, parse, analyze, scores, drift table, paragraph list — no Claude yet. Shippable and free to run |
| **4** | 8–9 | `/api/questions`, interview UI |
| **5** | 10–12 | `/api/rewrite`, streaming, credits, caps, spend ceiling, degraded mode |
| **6** | 13–14 | .docx export, what-was-cut list, before/after, privacy page |

Phase 3 is a real launch. An analyzer that costs nothing to serve and tells someone which
paragraphs stopped sounding like them is worth putting in front of users while phases 4–6 are
being built — and the traffic tells you whether to build them at all.

---

## 17. Open questions

1. **Does Sonnet 5 match voice as well as Opus 5?** Assumed yes. Settle it with 20 real documents
   before the free tier's model is locked in.
2. **Is 2 documents right?** A user with one document who never returns is a worse outcome than a
   slightly higher bill. Watch how many people use their second credit before tuning.
3. **What counts as "another sample you wrote"** for someone who mostly writes email? The product
   assumes people can find 600 words. Phase 3's funnel number answers this, and it is the biggest
   unvalidated assumption in the whole design.
4. **Do we need alignment between the original and the draft** to be smarter than token overlap?
   Only if the `originalText` field in `/api/questions` turns out to be frequently wrong.
5. **Deletion.** v1 deletes on request. Automatic deletion of inactive accounts after N months is
   easy to add and worth doing before there is much data to delete.
