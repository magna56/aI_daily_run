# Session contract — required every day

**This file governs both tracks.** A Frontier session (`frontier/YYYY-MM-DD/`) is written to
exactly the same contract as a daily lab session — same metadata keys, same required sections,
same `Implementing It` rules. There is no separate Frontier contract, deliberately: a second
standard is a second thing to maintain, drift and argue about. The only differences are where the
material is sourced, where the folder lives, and that a thin Frontier day is skipped rather than
filled. Frontier sessions do not get a `journal.md` block.

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

Never write today's article into `learn/`. That tree is the evergreen two-day track. A Frontier
session uses the identical layout under `frontier/YYYY-MM-DD/`.

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

Required `##` sections, in this order — **seven, five fixed and two named for the topic**:

| # | heading | fixed or topic-named |
| --- | --- | --- |
| 1 | `## Explain Like I'm 5` | fixed |
| 2 | `## The Problem` | fixed |
| 3 | `## How <the thing> Works` | **topic-named**, must start `How ` |
| 4 | `## For a Software Engineer` | fixed |
| 5 | `## What This Means for You` | fixed |
| 6 | `## Implementing It` | fixed |
| 7 | `## When <the thing> Is the Wrong Tool` | **topic-named**, must start `When ` |

Sections 3 and 7 carry the topic in the heading the way a reference article does — `## How the
Hook Matcher Decides`, `## When a Hook Is the Wrong Tool` — so the table of contents describes
*this* article rather than the template. `--check` matches them by pattern. Inside section 3, use
`###` sub-headings named for their subject (`### Byte Pair Encoding`), not for their function.

**Retired**, and warned on for sessions from 2026-08-26: `What It Is` and `Key Technical Details`
(merged into section 3, which now runs shallow to deep in one pass instead of explaining the
topic twice); `Why It Matters` (its significance argument belongs in `The Problem`, and the
momentum-reporting check moved with it); `How It Connects to What You Know` (its analogy was the
same move as `For a Software Engineer`, done twice — what survives is a one-line pointer into the
`learn/` track, in the body, not a heading); `Try It Yourself` (a pointer to a tab the reader can
already see); `Glossary`.

**Total prose budget: 1,300 words**, fenced code excluded, warned by `--check`. Every *other*
length rule here governs proportion — `Implementing It` is the longest section, ELI5 is 3-5
sentences — and none governed how big the document gets, so sessions drifted to ~1,700 words with
every individual rule green. `**Time to read**` was a number the author typed, checked by nothing.
When over budget, **cut, do not redistribute**: the explanatory sections carry the excess, and
`Implementing It` is the payload that survives the trim.

**Reading rhythm is part of the contract, not a style preference.** In the on-ramp sections
(`Explain Like I'm 5`, `The Problem`, the mechanism section), `--check` warns on any paragraph over
**110 words**, any sentence over **45 words**, and a `The Problem` written as a single block. These
were advisory for weeks and were ignored every day, because every other length rule is measured per
*section* while a reader actually quits inside a *paragraph*. The caps are loose on purpose: they
do not make prose good, they only catch the wall of text nobody finishes.

The companion rule, which no linter can check: **every detail must change a decision the reader
makes, enable an action they can take, or alter an outcome they care about.** Detail that only
describes the source system — its full component taxonomy, its internal names, its architecture the
reader will never touch — is cut no matter how central it was to the paper. Borrow the two or three
pieces the article actually uses and link the rest. A term defined once and never used again should
never have been defined.

**No Glossary section. Define every term at the moment it is first used**, in the sentence that
needs it, the way the reference publications do. A term that cannot be defined in a clause
without derailing the sentence is a term the article should not be using yet. This replaces a
305-word appendix that competed with the code for attention.

The old eleven-section order stands in the back catalog and is not warned on. It is not the
shape to copy: it explained the topic four times and named the object in the fifth section.

`What This Means for You` is three labelled parts: **When this matters**, **How it affects you**,
**What to do about it**. Required on Tier C too.

`Implementing It` is a hard requirement, and it is the one most easily faked. Four conditions,
all checked by `--check`:

1. At least one **fenced code block or literal payload in `topic.md` itself** — a link to
   `code_example.py` does not satisfy it. But the write-up carries the lines that *change*, not
   the program that contains them: any single block over **30 lines**, or a block that is a
   verbatim slab of `code_example.py`, warns. The article states the decisions; the code file is
   the runnable whole. Neither restates the other.
2. Two labelled parts: **The change** and **How you know it worked**. A reader who cannot tell
   whether the change took has been given a suggestion, not an implementation. (The third part,
   the counter-case, is now section 7 — a heading of its own, because it was the part readers
   most needed and the part most easily buried at the end of a long section.)
3. Code for **each role the change touches**, not only the role the source announcement
   addresses.
4. **It is the longest section in the document, measured on prose with fenced code excluded.**
   Measured across the first 22 sessions the shape was 97% explanatory prose and 3%
   implementation, with no code in the write-up at all. If some other section is longer, tighten
   that one — never pad this one, and never pad it with pasted code: code does not count toward
   the measurement, precisely so that dumping `code_example.py` here cannot buy compliance.

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
