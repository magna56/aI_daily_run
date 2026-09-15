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

### Who it is for — anyone

This got narrowed twice while the spec was being written, first to job applicants, then to people
writing formal letters. Both were wrong. **Do not define the audience by document type at all.**

The audience is defined by a *moment*, not a profession or a genre:

> You wrote something. You ran it through an AI. It came back better organized and less like you,
> and that bothers you.

That happens to a salesperson rewriting outreach, a student tightening an essay, a manager writing
reassignment letters, someone drafting a wedding speech, a founder writing a changelog, somebody
complaining to their landlord. The stakes run from *a committee will judge me for this* down to
*I just don't like how it reads*, and the product works the same at both ends. Someone annoyed that
their own newsletter sounds like a press release is as real a user as an applicant.

Three consequences for the build, which is why this section exists rather than just being a
marketing note:

**Documents are often short.** A sales email is 150 words, not 1,000. Paragraph-level flagging
barely works on three paragraphs, so short documents need sentence-level flagging — see §11. The
cost model in §15 assumes ~1,000 words; short documents are cheaper, which is fine, but they are
also the common case and the UI must not look empty when only two spans are flagged.

**Register varies and must be preserved.** The tell lexicon and the rewrite constraints were drafted
against formal prose (*"eager to contribute"*). Casual writing has different tells — *Absolutely!*,
*Here's the thing:*, *game-changer*, sudden emoji, a bulleted list where a sentence was. The
constraints must never push a casual writer toward professional prose. Returning someone to
themselves means keeping their register, including *lol* and a sentence fragment.

**Some people are repeat users.** An applicant uses this twice, ever. A salesperson would use it
twenty times a week. Two free documents is right for the first and wrong for the second. v1 keeps
the cap at two for everyone; the repeat segment is the one that would plausibly pay later, so the
schema tracks documents per user (§6) rather than a single boolean.

Nothing in the build is audience-specific. Do not hardcode application-shaped, workplace-shaped, or
academic-shaped language into the UI — the word is "document", not "statement", "letter", or
"essay".

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

1. **Storage is tiered and consented, never all-or-nothing.** An earlier draft stored nothing at
   all, which made privacy structural but forced every returning user to re-upload 400 words of
   their own writing — the highest-friction step in the product. We now store, in four tiers with
   separate defaults and separate consent (§5a). The rule that survives: **nothing is stored that
   the user did not choose to store**, and the working document — usually the sensitive one — is
   off by default.
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
│   ├─ paste box (primary)   + mammoth / pdf.js for files    │
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
        ┌────────────────┐   ┌──────────────────────────┐
        │  D1: users,    │   │  R2: encrypted text       │
        │  voiceprints,  │──▶│   baselines/<user>/…      │
        │  documents,    │   │   docs/<user>/<doc>/…     │
        │  daily_spend   │   │   encrypted per user      │
        └────────────────┘   └──────────────────────────┘
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
| **R2** | Stored baselines and (opt-in) working documents | Blobs, cheap, write-once. Envelope-encrypted per user (§5a) so a leaked bucket is not readable prose |
| **Secrets** | API keys, the storage master key | `wrangler secret put` |

### Deliberately not used

| Service | Why not |
|---------|---------|
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

## 5a. Storage: four tiers, four decisions

Storing everything and storing nothing are both wrong. The value is concentrated in the baseline;
the risk is concentrated in the working document. Separate them.

| Tier | What | Default | Why |
|------|------|---------|-----|
| **1. Fingerprint** | ~40 numbers: sentence stats, contraction rate, punctuation profile, specificity | **On** | Not prose. Writing cannot be reconstructed from it. Lets a returning user analyze a new document instantly with no upload |
| **2. Baseline exemplars** | ~600–1,000 words the user chose as "things I wrote" | **On, revocable** | The funnel fix. Rewriting needs real sample text for style matching; numbers are not enough |
| **3. Working documents** | The original, the AI version, the draft, the rewrite | **On** | Resume after closing the tab, and a history the user can come back to. This is what people expect from an account, and v1 takes that default |
| **4. Corpus use** | Tier-3 documents used to build measured tell profiles | **Off, separate consent** | Real pre-AI/post-AI pairs are the ideal corpus for §4 of the product spec and near-impossible to get otherwise. Never bundle this with tier 3 |

Tiers 1–3 are on for v1. Tier 4 stays off and separately consented, and that is not caution — it is
a different thing being asked. **A user agreeing to store their document has not agreed to let it
train anything.** Two checkboxes, worded differently, never pre-ticked together.

Because tier 3 is now on by default, it has to be *disclosed*, not buried: one plain line at first
use ("we keep your documents in your account so you can come back to them — you can delete any of
them, any time") and a visible off switch. A default that a user would be annoyed to discover is a
default that needs saying out loud.

### Encryption

R2 encrypts at rest, which protects against a lost disk and not against a leaked credential. For
this document set that is not enough, so add envelope encryption:

```ts
// Per-user key, derived from a master secret held as a Worker secret.
// A dumped bucket is ciphertext; decrypting it needs the Worker's secret too.
async function userKey(masterSecret: string, userId: string): Promise<CryptoKey> {
  const base = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(masterSecret), "HKDF", false, ["deriveKey"]);
  return crypto.subtle.deriveKey(
    { name: "HKDF", hash: "SHA-256",
      salt: new TextEncoder().encode("voiceprint.v1"),
      info: new TextEncoder().encode(userId) },
    base, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
}
```

Store `iv || ciphertext`. Rotating the master secret means re-wrapping, so version the key
(`voiceprint.v1`) from day one rather than discovering you cannot rotate.

### Retention

| Object | Lifetime |
|--------|----------|
| Fingerprint | Until account deletion |
| Baseline exemplars | Until the user replaces or deletes them |
| Working documents | Until the user deletes them, or the account goes inactive (§17) |
| Corpus copies (tier 4) | Until consent is withdrawn |

**Indefinite, deliberately.** An earlier draft expired documents after 30 days. With tier 3 off that
was a sensible blast-radius limit; with it on by default it becomes a trap — a user who finds their
document gone from their own account has been surprised by a safety feature, which is the worst kind
of surprise. Keep them, make deletion obvious, and purge with inactive accounts instead.

The cost of that choice is a larger standing blast radius, which is why the encryption above is not
optional. If business users ever arrive, configurable retention becomes a requirement rather than a
nicety — note it now so it is not a surprise later.

### Deletion has to be real

- `DELETE /api/documents/:id` — R2 objects and the D1 row, immediately.
- `DELETE /api/voiceprint` — exemplars and fingerprint.
- `DELETE /api/me` — everything, including corpus copies, then the user row.

A deletion flag that leaves bytes in a bucket is not deletion. Test it by deleting and then
attempting a direct R2 `get`.

### What this costs

Text is tiny. 10,000 users at ~10KB of baseline each is 100MB, comfortably inside R2's free tier.
Storage is not a cost decision here; it is only a risk decision.

### The honest privacy statement

The old claim — *there is nowhere to put your document* — was structurally true and a genuine
differentiator. It is gone. Do not replace it with a vaguer version of itself. Say what is true:

> We keep your writing samples and your documents in your account, so you can come back to them and
> so you never have to upload your samples twice. Everything is encrypted with a key specific to
> your account. We don't use any of it to train or improve anything unless you separately say yes.
> You can delete any of it or all of it, and deletion means the bytes are gone.

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

-- Tier 1 + 2 (see 5a). One row per user. The fingerprint is numbers; the
-- exemplars live in R2 under exemplar_key, encrypted.
CREATE TABLE voiceprints (
  user_id        TEXT PRIMARY KEY REFERENCES users(id),
  updated_at     INTEGER NOT NULL,
  fingerprint    TEXT NOT NULL,          -- JSON, ~40 numbers
  word_count     INTEGER NOT NULL,
  sample_count   INTEGER NOT NULL,
  register       TEXT NOT NULL,          -- formal | casual, drives lexicon choice
  exemplar_key   TEXT                    -- R2 key; NULL if the user declined tier 2
);

-- One row per document a user starts rewriting. Text lives in R2 under
-- r2_prefix when stored = 1, which is the v1 default.
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
  exported           INTEGER NOT NULL DEFAULT 0,
  source             TEXT NOT NULL DEFAULT 'paste', -- paste | docx | pdf | md | txt
  title              TEXT,                           -- filename, or first words of pasted text
  stored             INTEGER NOT NULL DEFAULT 1,     -- tier 3, on in v1
  r2_prefix          TEXT,                           -- NULL only if the user turned storage off
  corpus_consent     INTEGER NOT NULL DEFAULT 0      -- tier 4, separately given
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

Three things worth noticing.

**The `voiceprints` table is what makes a second visit cheap.** A returning user lands with their
fingerprint already loaded and can analyze a new document with zero uploads. That is the single
biggest funnel improvement available, and it is one small table.

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

### `GET | PUT | DELETE /api/voiceprint`

```
GET    ← { fingerprint, wordCount, sampleCount, register, hasExemplars, updatedAt } | 404
PUT    → { samples: string[], fingerprint, register }   -- client computes the fingerprint
       ← { ok, wordCount, sampleCount }
DELETE ← { ok }
```

`PUT` encrypts the joined samples and writes them to `baselines/<userId>/current`, then upserts the
row. The client still computes the fingerprint — the engine only exists in the browser, and there is
no reason to port it twice.

Reject a `PUT` under 400 words with `{ reason: "baseline_too_short" }`. The gate belongs on the
server too, not only in the UI.

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

### `GET /api/documents` · `DELETE /api/documents/:id` · `DELETE /api/me`

History, per-document deletion, account deletion. `GET` returns metadata always and text only for
documents where `stored = 1`. The two `DELETE`s remove R2 objects before the D1 rows, so a failure
mid-way leaves an orphaned row rather than orphaned bytes.

### `POST /api/rewrite`

The only expensive endpoint. Streams.

```
→ { docId, paragraph, answers: string[], constraints: {...}, assistant,
    exemplars?: string[] }        -- omitted when the server has a stored baseline
← text/event-stream  (Anthropic SSE, passed through)
```

When `exemplars` is absent the Worker loads and decrypts the stored baseline. That is the common
path once a user has been here before, and it is strictly better than the client resending — see
§8.

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

If the request carries a stored `docId` with `stored = 1`, persist the accepted rewrite alongside
the original under `docs/<userId>/<docId>/` after the stream closes, via `ctx.waitUntil`.

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

**Stored baselines make the cache more reliable, not just more convenient.** When the client
resent exemplars on every call, a byte-identical prefix depended on the browser serializing the
style block the same way every time — sorted keys, fixed number formatting, no timestamps — and a
single stray byte silently dropped the hit rate to zero with no error anywhere. With the baseline
in R2, the **Worker** renders that block from one code path, so identical bytes are the default
rather than a discipline. Keep the client path working for first-time users, and make both paths
call the same `renderStyleBlock()` so they cannot drift.

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
Register: casual. Keep fragments, keep "lol", do not make this more professional.
```

The register line is not decoration. Without it the model drifts every document toward business
prose, which for a casual writer is the same failure the original AI edit made.

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
    paste.ts               the primary path - see below
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
    Input.tsx   Scores.tsx  DriftTable.tsx  ParagraphList.tsx
    Interview.tsx  Rewrite.tsx  Export.tsx
```

### Paste is the primary input, not a fallback

Someone who has just used ChatGPT has the text in their clipboard, not in a `.docx`. A student works
in Google Docs, a salesperson in their mail client, a founder in a web editor — none of them have a
file to give you. **Each of the four inputs is a textarea first, with "or upload a file" underneath.**
Getting this ordering backwards adds a download-then-upload round trip to the most common path in
the product.

Files still matter — Word documents are real — but they are the second path, not the first.

**Pasted text loses paragraph structure, and the splitter has to cope.** The Python engine splits on
blank lines, which pasted text often does not have. Normalize before analyzing:

```ts
export function splitParagraphs(raw: string): string[] {
  const t = raw.replace(/\r\n?/g, "\n").normalize("NFC").trim();

  // 1. Blank lines present — the normal case, and what the Python engine assumes.
  if (/\n[ \t]*\n/.test(t)) return t.split(/\n[ \t]*\n/).map(p => p.trim()).filter(Boolean);

  // 2. Single newlines only (a textarea, or a copy out of a web editor). Treat a line
  //    as its own paragraph when lines are substantial; otherwise it is wrapped prose
  //    and the newlines are noise, so rejoin them.
  const lines = t.split("\n").map(l => l.trim()).filter(Boolean);
  if (lines.length > 1) {
    const avg = lines.reduce((n, l) => n + l.split(/\s+/).length, 0) / lines.length;
    if (avg >= 15) return lines;
    return [lines.join(" ")];
  }

  // 3. One unbroken blob. Do not guess at paragraph boundaries — fall through to
  //    sentence mode (§11), which needs no paragraph structure at all.
  return [t];
}
```

Case 3 is why sentence mode earns its place twice over: it is the answer for short documents *and*
the answer for a 900-word paste with no line breaks, which is common and otherwise unanalyzable at
paragraph granularity.

Pasted text has no filename, so `documents.title` falls back to the first six words plus a date.

Tell profiles are **static JSON assets, not code**. The quarterly refresh the product spec requires
is then a file swap, and a stale profile is visible in its filename.

Each profile carries two lexicons, `formal` and `casual`, because the tells differ by register: a
smoothed cover letter says *eager to contribute*, a smoothed Slack post says *Absolutely!* and
*Here's the thing:*. Pick the lexicon from the author's own baseline (contraction rate and mean
sentence length separate the two cleanly), never from the document being fixed — the document has
already been pushed toward formal, which is the problem.

Session state lives in memory plus `sessionStorage` for crash recovery. Nothing in `localStorage`:
anything meant to outlive the tab belongs in the account (§5a), where the user can see and delete
it, not in browser storage they will never think to clear.

Storage consent is UI, not a settings page. Tier 2 is offered at the moment it pays off — *"save
these samples so you don't have to find them again?"* — right after the first successful analysis.
Tier 3 is offered only if the user does something that implies wanting it, such as closing a
half-finished document. Tier 4 is never offered inline; it lives in account settings, off.

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

### Short documents need sentence-level flagging

The Python script drops paragraphs under 12 words and ranks whole paragraphs. That is right for a
1,000-word statement and useless for a 150-word sales email, where the entire document is three
paragraphs and flagging one of them says almost nothing.

The TypeScript engine adds a second mode, chosen by length rather than by the user:

| Document | Mode | Unit |
|----------|------|------|
| ≥ 400 words | paragraph | Rank paragraphs, as today |
| < 400 words | sentence | Rank sentences; tells, specificity and length-band checks all work unchanged at sentence granularity |

The signals do not change — only what they are attached to. Variance-based checks (`sent_len_sd`
within a unit) are already suppressed on small samples and simply stay off in sentence mode.

Parity tests cover paragraph mode only, since it is what the Python script implements. Sentence
mode gets its own fixtures and is allowed to diverge; note that clearly in the test file so a
future reader does not "fix" it back into parity.

**The baseline still needs 400 words even when the document is 150.** That is not a bug — a
fingerprint from 150 words is noise. It does mean the friction is worst exactly where the document
is smallest, which is the funnel risk in §17.

---

## 12. Security and privacy

| Concern | Handling |
|---------|----------|
| API key exposure | `ANTHROPIC_API_KEY` is a Worker secret. It never reaches the client and never appears in a response |
| Session theft | HttpOnly, Secure, SameSite=Lax, 30-day expiry |
| Forged identity | Full RS256 verification against Google's JWKS, plus `aud` / `iss` / `exp` / `email_verified` |
| Bot signups | Turnstile on `/api/auth/google` |
| Using us as a free rewriting API | Google account + 2 documents + rate limit + per-doc cap. The product spec's baseline gate also means a caller must supply 400 words of real writing first |
| Stored document exposure | Envelope encryption per user (§5a): a dumped R2 bucket is ciphertext without the Worker's master secret. v1 keeps documents indefinitely, so encryption and working deletion carry the weight that a short retention window used to |
| Document leakage via logs | Never log request or response bodies. `console.log(body)` during a debugging session is the realistic way this leaks, and it now also lands in Workers logs that outlive the request |
| Cross-user access | Every R2 key is prefixed with the authenticated `userId` and built server-side from the session, never from a request field. No endpoint accepts a raw R2 key |
| Consent drift | Tier 3 and tier 4 are separate columns, separate checkboxes, never pre-ticked. Storing is not training |
| XSS | CSP allowing only self and `accounts.google.com`. Preact escapes by default; no `dangerouslySetInnerHTML` on user text |
| PII | Email and Google `sub`. Deletion endpoint removes both rows. Say so in the privacy page |

The privacy page uses the wording in §5a. The old claim — *there is nowhere to put your document* —
was structurally true and is no longer available; replacing it with a vaguer version of the same
sentence would be worse than the honest one.

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
  "r2_buckets": [{ "binding": "DOCS", "bucket_name": "voiceprint-docs" }],
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
wrangler secret put STORAGE_MASTER_KEY
wrangler r2 bucket create voiceprint-docs
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
| R2 | Free tier. 10,000 users at ~10KB of baseline is 100MB against a 10GB allowance |
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
| **3** | 6–7 | Paste and upload, parse, analyze, scores, drift table, paragraph/sentence list — no Claude yet. Shippable and free to run |
| **4** | 8–9 | `/api/questions`, interview UI |
| **5** | 10–12 | `/api/rewrite`, streaming, credits, caps, spend ceiling, degraded mode |
| **6** | 13–15 | Storage: R2 + envelope encryption, `/api/voiceprint`, saved-baseline path in `/api/rewrite`, history, deletion |
| **7** | 16–17 | .docx export, what-was-cut list, before/after, privacy page |

Storage moved ahead of export because it is no longer an add-on: with tiers 1–3 on by default, the
account *is* the product on a second visit. Until it ships, every returning user re-uploads their
baseline — the step the funnel is most likely to die on.

Phase 3 is a real launch. An analyzer that costs nothing to serve and tells someone which
paragraphs stopped sounding like them is worth putting in front of users while phases 4–6 are
being built — and the traffic tells you whether to build them at all.

---

## 17. Open questions

1. **Does Sonnet 5 match voice as well as Opus 5?** Assumed yes. Settle it with 20 real documents
   before the free tier's model is locked in.
2. **Is 2 documents right?** A user with one document who never returns is a worse outcome than a
   slightly higher bill. Watch how many people use their second credit before tuning.
3. **Where does a normal person find 400 words they wrote?** Still the biggest unvalidated
   assumption, and storage only halves it: it removes the problem on visit two and leaves it fully
   intact on visit one, which is where people quit. Sent email is the one source almost everybody
   has — "paste three emails you sent" is probably a better prompt than "upload a writing sample",
   and it costs nothing to test in Phase 3. If `upload_baseline ÷ signin` is bad, fix this before
   anything about rewriting.
4. **Do we need alignment between the original and the draft** to be smarter than token overlap?
   Only if the `originalText` field in `/api/questions` turns out to be frequently wrong.
5. **Does anyone turn tier 3 off?** v1 stores working documents by default. If a noticeable share
   of users switch it off, or ask where their documents went, the default is wrong and the earlier
   opt-in design was right. Instrument the toggle; it is one boolean and it answers a question that
   would otherwise be argued about.
6. **Is the credit model the wrong shape for repeat users?** Two documents fits someone with one
   application to fix. It does not fit a salesperson who would run this on outreach every day —
   and that person is the one who would plausibly pay. Do not build for them in v1, but watch
   whether anyone burns both credits within an hour; that is the signal.
7. **Automatic deletion of inactive accounts** after N months. Easy to add, and much easier to add
   before there is data to delete than after.
