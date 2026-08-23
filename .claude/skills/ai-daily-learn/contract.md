# Session contract — required every day

A daily session is incomplete until all five files exist **and** `journal.md` is updated.
`build.js --check` only *warns* on a missing visualizer or diagram so old folders still
build. **New sessions may not ship that way.** Do not stop after `topic.md`.

## Folder

```
YYYY-MM-DD/                 # or YYYY-MM-DD-s2 if today already has a session
  topic.md                  # required
  visualize.html            # required — Visualize tab; see visualize.md
  diagram.excalidraw        # required — Diagram tab
  code_example.py           # required — Code tab
  articles.md               # required — Articles tab
```

Never write today's article into `learn/`. That tree is the evergreen two-day track.

## topic.md metadata (exact keys, exact allowed values)

```
# <hook title, not a method name>

**Category**: <one of the 11 names in build.js CATEGORIES>
**Tags**: <2-4 from build.js TAGS, lowercase, comma-separated>
**Date**: YYYY-MM-DD
**Level**: Start here | Building | Deeper
**For**: Using tools | Building agents | Shipping AI | How models work
**Hook**: <one plain sentence, no acronyms — homepage card>
**Time to read**: ~10 minutes
```

Required `##` sections, in this order:

Explain Like I'm 5 → The Problem → For a Software Engineer → What This Means for You
→ What It Is → Why It Matters → Key Technical Details → How It Connects to What You Know
→ Try It Yourself → Glossary

`What This Means for You` is three labelled parts: **When this matters**, **How it affects you**,
**What to do about it**. Required on Tier C too.

## journal.md

Append one `## YYYY-MM-DD — <Title>` block. **Key insight**: 3 sentences / ~70 words, at most
one number, no acronyms. The homepage card uses `Hook`, not this field.

## After writing

From the repo root:

```bash
node build.js --check
```

Fix every warning that names today's id (missing file, bad Category/Level/For/Hook/tag,
visualize contract, unrenderable diagram, crashing JS). Then tell the user:

```
cd ~/ai_learning && make serve
# open http://127.0.0.1:8000/#YYYY-MM-DD
# Overview → Visualize → Diagram → Code → Articles
```

Do not commit, push, or deploy unless they asked to publish.
