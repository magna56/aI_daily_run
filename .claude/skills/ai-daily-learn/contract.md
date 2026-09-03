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
  code_example.py           # required — Code tab; stdlib, no agent frameworks
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
| 3 | `## The Fix: <what to do>` | **topic-named**, must announce the solution |
| 4 | `## What This Means for You` | fixed |
| 5 | `## Implementing It` | fixed |
| 6 | `## When <the thing> Is the Wrong Tool` | **topic-named**, must start `When ` |
| 7 | `## Glossary` | fixed, last |

**The Overview opens with the engineering translation, not the article.** Two metadata fields
render as boxes above `Explain Like I'm 5`:

```
**Engineer's view**: <name the thing they have already shipped, explain the mapping in one plain
sentence, then say what it costs them. Max 55 words. It must explain, not allude.>
**TLDR**: <two lines, plain language, at most one number.>
```

`Engineer's view` is the site's most distinctive move — no comparable publication translates AI
topics into engineering the reader has already done — and until 2026-09-02 it was a section at
position four, which is late for the most distinctive thing an article does. It is now the first
thing anybody reads. `--check` enforces both fields and applies the old `Key insight` checks
(sentences, words, one number, no identifiers) to `TLDR`.

**`## For a Software Engineer` is retired**, because the box replaces it and keeping both is the
duplication the anti-filler rule forbids. Note carefully that a *superficially identical* change
was reverted on 2026-08-31: that one **buried** the analogy as an unlabelled sentence inside the
mechanism section and the middle of the article thinned. This one **promotes** it above everything
else. Removing the section is only correct while the box exists; if the box ever goes, the section
comes back.

**Section 3 announces the solution; it does not presume it.** It was `## How <the thing> Works`
until 2026-09-01, and that form failed twice on different articles: scanned as a list the headings
went `The Problem` → `How a Borrowed Test Suite Works` → `For a Software Engineer`, and nothing in
that sequence tells the reader an answer has arrived. *How X Works* explains a mechanism to
somebody who has not yet been told the mechanism is the point. Name it for the answer instead —
`## The Fix: Borrow a Mature Project's Test Suite`, `## The Fix: Pin the First Four Tokens` — so
that reading only the headings gives problem → fix → how it works → what to do. An Explainer-shape
piece whose payoff is understanding rather than a change may use `## The Answer: …`. `--check`
enforces this from 2026-09-01.

**`The Problem` is told from the reader's side, and this is the site's USP.** Open on a bug the
engineer has already shipped and debugged in a system unrelated to AI, then show the topic as that
same bug at a different scale. The source paper's vocabulary waits for `The Fix`. An `Engineer's
view` box at the top does not discharge this: the perspective is how the problem gets explained,
not a label attached to the page.

**Write plain American English.** American spelling (`behavior`, `honor`, `artifact`, `normalize`,
`analyze`, `distill`, `$` not `£`), and sentences that carry one idea each. `--check` warns on any
British spelling in the write-up or the `Engineer's view` / `TLDR` / `Hook` lines, and on a **mean
sentence above 18 words** across the whole article, from 2026-09-03.

**And state the fix, do not narrate it.** The sentence in `The Problem` that introduces the
solution is an instruction, not a report of who discovered it. A description of what one engineer
happened to do does not read as something the reader should go and do, even when the words are
otherwise identical.
- ✗ *"He took the test suites of well-known packages and had the AI rewrite them against his API."*
- ✓ *"**Borrow your oracle: take the test suite of a mature project, have the agent port those
  tests onto your API, and treat every failure as a question.** Dumpleton did this with packages
  that lean on `unittest.mock`."*

**The middle sections keep their own headings, and this has been tested.** On 2026-08-31 a
six-section variant merged `For a Software Engineer` into the mechanism as a single sentence and
collapsed `What This Means for You` to one beat. Measured on the article it was applied to, the
middle went from three sections and 710 words to two and 524 — and it was reverted the same day,
because the middle is the part that reads well. It reads well because it *alternates modes*:
mechanism, then the translation into something the reader has already shipped, then what to do.
Three ways of thinking, three headings, each scannable.

The lesson kept from that experiment is the opposite of what it did: **an explanation is made
readable by more small units, each answering one question and each backed by a figure — never by
merging sections.** If the mechanism section is a wall, split it and put a figure in each part.
Do not propose merging the middle again.

**The software-engineering framing appears twice, at two weights.** The named analogy goes in the
`Engineer's view` box at the very top — "this is loop interchange", "this is a cache key missing an
input" — and a light clause inside `The Problem` echoes its shape without spending it again.

An **Explainer** variant may add `## By the End of This You Will` at position 2, promising in two
to four bullets what the reader will understand; that promise is what licenses withholding the
answer until later. Everything else is identical.

**`## Glossary` returned on 2026-09-02, in a different form.** It is a **lookup**, not an appendix:
the first appearance of each term in the article body renders as a link to its entry, so a reader
who gets stuck can jump there and back. Entries are `- **Term** — definition`, and the term must
be written exactly as the prose uses it — `--check` warns when a term never appears in the body,
because nothing then links to it and no reader will ever arrive at the entry.

**Five or six entries is the norm**, definitions capped at 20 words. Gloss the terms a reader could
stall on, not every noun. Going past six is allowed when the article genuinely needs it; that
warning is advisory and is deliberately not in the publish gate.

**This does not replace defining terms inline.** A term is still explained in the sentence that
first needs it, and the glossary entry is a terse pointer back to that. The version retired earlier
was an unlinked wall of definitions that repeated the prose at length — the caps and the
define-inline rule together are what stop it growing back into one.

**Retired**, and warned on for sessions from 2026-08-26: `What It Is` and `Key Technical Details`
(merged into section 3, which now runs shallow to deep in one pass instead of explaining the
topic twice); `Why It Matters` (its significance argument belongs in `The Problem`, and the
momentum-reporting check moved with it); `How It Connects to What You Know` (its analogy was the
same move as `For a Software Engineer`, done twice — what survives is a one-line pointer into the
`learn/` track, in the body, not a heading); `Try It Yourself` (a pointer to a tab the reader can
already see); `Glossary`.

**Per-section word bands**, fenced code excluded, warned by `--check`:
`Explain Like I'm 5` 60-120 · `The Problem` 190-320 · mechanism section cap 370 (no floor) ·
`What This Means for You` 200-300 · `Implementing It` 300-460 · counter-case 150-250.
`Engineer's view` caps at 55 words.
`Implementing It` keeps its longest-section rule on top of its band.

These replace a single 1,300-word document total that ran 2026-08-27 to 2026-08-31. The total was
the right diagnosis and the wrong instrument: paired with "cut, do not redistribute — the
explanatory sections carry the excess", it could only be paid out of whichever sections had the
weakest rule protecting them, and it was. Across the four articles written under it, `The Problem`
fell 48% and `What This Means for You` fell 37% while `Implementing It` gave up 23%. **A floor is
therefore as load-bearing as a cap here**, and a below-floor section is a defect, not a tidy
article.

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

**Define every term at the moment it is first used**, in the sentence that needs it, the way the
reference publications do. A term that cannot be defined in a clause without derailing the
sentence is a term the article should not be using yet. This rule survived the Glossary's
retirement and still binds now that the section is back: the glossary is a pointer a stuck reader
can jump to, never the place a term is first explained. The 305-word appendix that competed with
the code for attention was an *unlinked* wall of re-explanations, which the entry caps and this
rule together prevent.

The old eleven-section order stands in the back catalog and is not warned on. It is not the
shape to copy: it explained the topic four times and named the object in the fifth section.

`What This Means for You` is required on Tier C too. If the honest answer is "this will not affect
your work for a year", say that and name the signal to watch for — never invent applicability.

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
visualize contract, unrenderable diagram, crashing JS, **paragraph/sentence caps, single-block
`The Problem`, any section outside its word band**). Then tell the user:

```
cd ~/ai_learning && make serve
# open http://127.0.0.1:8000/#YYYY-MM-DD
# Overview → Visualize → Diagram → Code → Articles
```

Do not commit, push, or deploy unless they asked to publish.
