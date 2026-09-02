# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal daily AI-learning log plus the static site ("the reader") that renders it. Each
`YYYY-MM-DD/` folder is one 30-minute session — the source of truth, never generated from the
site — containing up to five peer files:

```
topic.md            # H1 title, **Key**: value metadata block, then ## sections
visualize.html       # standalone interactive model, lazy-loaded in a restricted iframe
diagram.excalidraw   # Excalidraw scene JSON
code_example.py       # runnable, pure Python, no API keys
articles.md          # 3-5 curated sources with summaries
```

A `-s2` suffix (`2026-08-03-s2`) means a second session that day. `learn/<slug>/` is the
evergreen two-day track (same five files, `**Kind**: Learn`) — curriculum, not today's news.
`frontier/YYYY-MM-DD/` is the **Frontier** track: frontier-lab research and papers, written to the
*same* contract as a daily session (same five files, same required sections) and differing only in
sourcing, placement and cadence. It never enters the card grid, never appears in `journal.md`, and
never counts toward `node build.js --mix` — the track exists so frontier material stops competing
for the daily slot. Compiled with `kind: "frontier"` and a `frontier-` id prefix so a lab and a
Frontier piece can share a date; it still gets its own page, OG card, sitemap and RSS entries plus
a crawlable `/frontier/` landing page. A thin Frontier day is skipped; a thin lab day is not.
`journal.md` is the running index of *daily* sessions: `## <id> — <Title>` blocks with
`- **Key**: value` bullets, most importantly `Key insight`, which the reader uses as the
card blurb. Learn cards use `Hook` instead.

`build.js` compiles the session folders into `site/data/` (a small manifest plus one JSON payload
per session); `index.html` is the reader SPA that loads that data. `site/` is build output, never
committed — `deploy.sh` publishes it to Cloudflare Pages (theaicommit.com, the primary host) and
force-pushes it to the `gh-pages` branch (GitHub Pages, kept as a mirror).

**Short video.** `video.js` turns a daily session into a ~30–45s 9:16 explainer
(slides, optional Playwright capture of `visualize.html`, OpenAI TTS, burned-in
captions). Scratch output is `videos/<id>/` (gitignored). Committable copies live
in `media/videos/`. Run via `/ai-daily-learn-video` (Claude) or the Cursor skill
of the same name; first-draft lock is `tts-1-hd` / `alloy`, with `## For a Software
Engineer` as one extra beat — see `.claude/skills/ai-daily-learn-video/SKILL.md`.
Voiceover uses `OPENAI_API_KEY` or macOS Keychain `openai-api-key-theaicommit`.

## Commands

```bash
make serve           # build + preview at http://127.0.0.1:8000
make build            # regenerate site/data/ only
make check             # lint every session, write nothing (use in review/CI)
make mix              # what to publish next — trailing-10 audience mix, due/avoid
make deploy           # build and publish to Cloudflare Pages + gh-pages (runs deploy.sh)
make clean             # drop site/ and the run cache
make video             # newest session → 9:16 short (ffmpeg; optional OPENAI_API_KEY)
make video ID=YYYY-MM-DD MEDIA=1   # named session + copy to media/videos/
make video-setup       # one-time Playwright install for visualize.html capture

make serve NORUN=1    # skip executing code_example.py files (~45s faster, no output pane)
node build.js --check  # same as `make check`
node build.js --mix    # same as `make mix`
node build.js --no-run # same as NORUN=1
```

There is no test suite and no linter beyond `make check`, which validates every session folder
(missing `# Title`, unknown category, unrenderable diagram, etc.) and fails the build on hard
errors while treating missing optional files (no diagram, no articles) as warnings.

A first build runs every `code_example.py`; results are cached by source hash in
`.build-cache.json`, so later builds re-run only sessions whose code changed. A crashing example
is not a build failure — the reader shows its traceback and the command to reproduce it locally.

## Architecture

**`build.js`** is the whole pipeline, dependency-free (no npm install needed — plain Node). Key
internals worth knowing before touching it:
- `parseTopic` / `parseJournal` / `parseArticles` are hand-rolled markdown parsers tuned to the
  exact conventions above (e.g. articles.md bylines wrap mid-line and must be rejoined before
  splitting on `|`). Changing a session's markdown shape means updating the matching parser.
- `compile(id, ...)` builds two things per session: the full `payload` (written to
  `site/data/<id>.json`, fetched on demand) and a lightweight `card` (folded into
  `site/data/index.js` for the grid). This split keeps the grid fast as sessions accumulate.
  Daily folders match `SESSION_RE`; `learn/<slug>/` is compiled in `LEARN_TRACK` order
  with `kind: "learn"` and exported as `window.LEARN_TRACK` for `#learn`.
- `REPO_BLOB` (env `ADL_REPO_BLOB`) controls where each session's "Files" link points — override
  it if this checkout's origin differs from the GitHub default baked into the script.
- `visualize.html` is copied to `site/assets/<id>/` rather than embedded in the session payload.
  The reader creates its iframe only when Visualize opens and uses `sandbox="allow-scripts"`
  without same-origin/popups/forms. Keep each artifact self-contained (inline CSS/JS/data, no
  external requests) and preserve its `adl-visualize-height` postMessage contract.

**`lib/runner.js`** executes each `code_example.py` in a throwaway temp cwd (never dirties the
repo), with a 60s timeout, `MPLBACKEND=Agg`, and prefers `.venv/bin/python3` over system Python.
Results are cached by source hash across builds; a run's own images (e.g. a saved PNG) are copied
into `site/assets/<id>/` and cache-invalidated if those copies go missing.

**`lib/excalidraw-svg.js`** renders `.excalidraw` scene JSON to a standalone, byte-deterministic
SVG string at build time — no browser, no Excalidraw runtime dependency. It only understands the
element shapes the generator script (`.claude/skills/ai-daily-learn/scripts/generate_excalidraw.py`)
actually emits (rectangle/text/arrow, roughness 0); anything else is skipped rather than
approximated, and the build warns when that happens.

**`deploy.sh`** builds `site/` once, then publishes that *same* built folder to two hosts — it
never rebuilds per-target, which matters because `lib/runner.js` needs `python3` to execute every
`code_example.py`, and that is only guaranteed to exist on this machine, not on a remote build
server:
- **Cloudflare Pages** (theaicommit.com, primary): `npx wrangler pages deploy site
  --project-name=theaicommit`, authenticated via a `CLOUDFLARE_API_TOKEN` read from macOS Keychain
  (`security find-generic-password -a wrangler -s cloudflare-api-token-theaicommit`). Non-fatal on
  failure — a Cloudflare hiccup must not undo the gh-pages publish that already succeeded above it.
  After a successful publish, `deploy.sh` POSTs the newest *daily* session to
  `/api/newsletter` (secret from Keychain `newsletter-secret-theaicommit`) so
  subscribers get one email; D1's `issues` table is the idempotency lock.
- **GitHub Pages** (mirror): initializes a *throwaway* git repo in a temp dir, commits, and
  force-pushes that single commit to the `gh-pages` branch of whatever `origin` remote is
  configured — it does not touch this repo's own git history or branches. It has no
  Functions; the homepage form posts signups to theaicommit.com.

`site/_redirects` (`/api/*` kept as-is, then `/* /index.html 200`, written by `make site`)
is Cloudflare Pages' native SPA-fallback. GitHub Pages ignores this file; it uses
`404.html`'s own redirect-with-hash-preserved script instead.

**D1 + newsletter.** `wrangler.jsonc` binds D1 database `theaicommit`
(`fa0d5d4b-8907-420f-956f-8fbbd8a854f2`) as `DB`. Schema is `db/schema.sql`
(`subscribers`, `issues`). Pages Functions: `POST /api/subscribe`, `GET /api/confirm`,
`GET /api/unsubscribe`, `POST /api/newsletter` and `GET /api/stats` (Bearer
`NEWSLETTER_SECRET`). A signup also emails `NEWSLETTER_NOTIFY` (default
`theaicommit@gmail.com`) with the address and running counts. Mail goes
through Resend (`RESEND_API_KEY`, optional `NEWSLETTER_FROM` / `PUBLIC_URL`). Without
the Resend key, signups are still stored and marked active so an unset secret never
drops an address. Same D1 is the place for later signup-adjacent features (comments,
accounts) — add tables in `db/schema.sql`, don't stand up a second store.

## Session content conventions

Session content is generated by the `/ai-daily-learn` and
`/ai-daily-learn-publish` skills under `.claude/skills/`, whose SKILL.md files are the canonical
spec — read those before hand-writing or editing session content, rather than inferring the
format solely from `build.js`'s parser.

The shape those skills enforce, worth knowing before touching a session: a session is written to
leave the reader **able to build something**, and it reads as one argument rather than parallel
takes on a topic. `topic.md` runs seven sections — ELI5 → `The Problem` (which must name the fix
before it ends) → `The Fix: <what to do>` → `For a Software Engineer` → `What This Means for You`
→ **`## Implementing It`** → `When <it> Is the Wrong Tool`. A six-section merge of the middle was
tried and reverted on 2026-08-31; do not re-attempt it. An article whose reader is curious rather
than stuck may add `## By the End of This You Will` at position 2 and earn a later reveal. Every
section has a word band with a floor as well as a cap, and `## Implementing It`
must be the longest section, must carry real fenced code in the write-up (not a pointer to
`code_example.py`), must cover every role a change touches, and must include its **How you know
it worked** and **When not to** parts. `code_example.py` is judged on whether an engineer can
lift it into their own repo, not on whether it runs. Topic choice is governed by a reader pyramid
keyed on the `For` field — `make mix` prints what is due and what is at cap — and
`.claude/skills/ai-daily-learn/selection.md` holds the per-category source lists and the source
quality gates. `.claude/skills/ai-daily-learn-feedback/feedback-log.md` records why each of these
rules exists; read it before reversing one. `/ai-daily-learn` writes locally only; `/ai-daily-learn-publish`
additionally commits and pushes straight to `main` on the GitHub remote (no branches, no PRs —
this is a personal notes repo). Both skills, by design, never touch this repo's own git state
except through those two explicit publish paths.

When adding a session by hand: `topic.md` must start with `# Title` followed by `**Key**: value`
metadata lines (`Category` must be one of the 11 categories in `build.js`'s `CATEGORY_TIERS`
map, from which `CATEGORIES` is derived so tier membership cannot drift from the list — that map
is the validation source of truth; `Date` drives the grid;
`Level` is `Start here` / `Building` / `Deeper`; `For` is `Using tools` / `Building agents` /
`Shipping AI` / `How models work`; `Hook` is the one-line card blurb). A session dated on or
after 2026-08-25 must also carry `## Implementing It` with the properties above; `make check`
warns on all of it and the back catalog is exempt by date. A session missing a diagram or
articles file simply shows fewer tabs in the reader.
The unfiltered homepage is Latest first — daily sessions only, newest on top.
The header splits **Daily lab** (the default homepage) from **AI basics**.
Basics pages do not appear in the lab grid; they live on `#learn` as a
numbered lesson list (Day 1 foundations, Day 2 agents and the machine).
