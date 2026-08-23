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
`journal.md` is the running index of *daily* sessions: `## <id> — <Title>` blocks with
`- **Key**: value` bullets, most importantly `Key insight`, which the reader uses as the
card blurb. Learn cards use `Hook` instead.

`build.js` compiles the session folders into `site/data/` (a small manifest plus one JSON payload
per session); `index.html` is the reader SPA that loads that data. `site/` is build output, never
committed — `deploy.sh` publishes it to Cloudflare Pages (theaicommit.com, the primary host) and
force-pushes it to the `gh-pages` branch (GitHub Pages, kept as a mirror).

## Commands

```bash
make serve           # build + preview at http://127.0.0.1:8000
make build            # regenerate site/data/ only
make check             # lint every session, write nothing (use in review/CI)
make deploy           # build and publish to Cloudflare Pages + gh-pages (runs deploy.sh)
make clean             # drop site/ and the run cache

make serve NORUN=1    # skip executing code_example.py files (~45s faster, no output pane)
node build.js --check  # same as `make check`
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
- **GitHub Pages** (mirror): initializes a *throwaway* git repo in a temp dir, commits, and
  force-pushes that single commit to the `gh-pages` branch of whatever `origin` remote is
  configured — it does not touch this repo's own git history or branches.

`site/_redirects` (`/* /index.html 200`, written by `make site`) is Cloudflare Pages' native
SPA-fallback mechanism, needed because the reader is a single-page app using hash routing
(`#2026-08-22/code`) — without it, a fresh load of a path Cloudflare doesn't recognize 404s.
GitHub Pages ignores this file; it uses `404.html`'s own redirect-with-hash-preserved script
instead, for the same purpose.

## Session content conventions

Session content (topic.md structure, ELI5 → engineer-bridge → "What This Means for You" →
technical depth, the tier-weighted category selection, the `Key insight` hard cap) is generated
by the `/ai-daily-learn` and
`/ai-daily-learn-publish` skills under `.claude/skills/`, whose SKILL.md files are the canonical
spec — read those before hand-writing or editing session content, rather than inferring the
format solely from `build.js`'s parser. `/ai-daily-learn` writes locally only; `/ai-daily-learn-publish`
additionally commits and pushes straight to `main` on the GitHub remote (no branches, no PRs —
this is a personal notes repo). Both skills, by design, never touch this repo's own git state
except through those two explicit publish paths.

When adding a session by hand: `topic.md` must start with `# Title` followed by `**Key**: value`
metadata lines (`Category` must be one of the 11 categories in `build.js`'s `CATEGORIES` list,
which is ordered by tier — A/B/C — and is the validation source of truth; `Date` drives the grid;
`Level` is `Start here` / `Building` / `Deeper`; `For` is `Using tools` / `Building agents` /
`Shipping AI` / `How models work`; `Hook` is the one-line card blurb). Everything else is
optional — a session missing a diagram or articles file simply shows fewer tabs in the reader.
The unfiltered homepage is Latest first — daily sessions only, newest on top.
The header splits **Daily lab** from **Two-day tutorial**. Tutorial pages do
not appear in the lab grid; they live on `#learn` as a numbered lesson list
(Day 1 foundations, Day 2 agents and the machine).
