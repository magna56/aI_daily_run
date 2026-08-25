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
→ What It Is → Why It Matters → Key Technical Details → Implementing It
→ How It Connects to What You Know → Try It Yourself → Glossary

`What This Means for You` is three labelled parts: **When this matters**, **How it affects you**,
**What to do about it**. Required on Tier C too.

`Implementing It` is a hard requirement, and it is the one most easily faked. Four conditions,
all checked by `--check`:

1. At least one **fenced code block or literal payload in `topic.md` itself** — a link to
   `code_example.py` does not satisfy it.
2. Three labelled parts: **The change**, **How you know it worked**, **When not to**. The last
   two are what separate an engineering document from a tutorial and are the two most often
   skipped. A reader who cannot tell whether the change took has been given a suggestion; a
   technique with no stated downside reads as marketing.
3. Code for **each role the change touches**, not only the role the source announcement
   addresses.
4. **It is the longest section in the document.** Measured across the first 22 sessions the shape
   was 97% explanatory prose and 3% implementation, with no code in the write-up at all. If some
   other section is longer, tighten that one — never pad this one.

The acceptance test behind all four: *could a competent engineer ship this change from the
article alone, without opening the source it was built from?* A session whose deepest content is
a description of what a release says has not met this contract, however long it is.

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
