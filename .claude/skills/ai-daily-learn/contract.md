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

Required `##` sections, in this order — **six from 2026-09-01, four fixed and two named for the
topic**:

| # | heading | fixed or topic-named |
| --- | --- | --- |
| 1 | `## Explain Like I'm 5` | fixed |
| 2 | `## The Problem` | fixed |
| 3 | `## How <the fix> Works` | **topic-named**, must start `How ` |
| 4 | `## What to Do About It` | fixed |
| 5 | `## Implementing It` | fixed |
| 6 | `## When <the thing> Is the Wrong Tool` | **topic-named**, must start `When ` |

**Two shapes, one contract.** Which spine an article uses depends on the reader's state, and it
is declared by a section rather than a metadata key, so the two can never drift apart:

| shape | the reader | spine |
| --- | --- | --- |
| **Fix** (default) | has a live problem and wants the answer now | `The Problem` **names the fix before it ends** |
| **Explainer** | is curious; there is no emergency | a `## By the End of This You Will` section sits at position 2, and `The Problem` may withhold the fix so the reveal is earned |

An Explainer buys its deferral with a promise: two to four bullets saying what the reader will
understand by the end. That promise is what keeps a reader oriented while the apparatus is built,
and it is the only thing that licenses withholding the answer. Without it, withhold nothing.

**Everything else is identical in both shapes** — the five artifacts, the engineer anchor, the
implementation payload, `What to Do About It`, the counter-case, every band and lint. This is one
contract with a documented variant, not a second standard. The reference article this borrows
from is a pure explainer with no code to ship and a product plug at the end; that half is
deliberately not copied, because the implementation payload is what makes this site a lab rather
than a blog.

**Sub-headings inside the mechanism section are the reader's question, in the reader's voice.**
Not `### Ratio versus count` but `### Why not just cap retries per call?`; not `### Budget
exhaustion` but `### Wait, what happens when the budget runs out?`. Say the doubt out loud at the
moment it forms, then answer it. `--check` warns when a mechanism section has two or more
sub-headings and none of them is a question — that is the difference between a lecture and
someone explaining something to you.

**Figures go in the flow, at the point of difficulty.** A line reading exactly `[[visualize]]`
splices the interactive artifact into the Overview prose there; `[[diagram]]` does the same for
the Excalidraw SVG. `--check` warns from 2026-09-01 when a session ships `visualize.html` and
never places the marker. When a session inlines the visualizer, the reader drops the now-duplicate
Visualize tab — the artifact is unchanged, only where it is met.

**The article is one argument, and every section advances it.** That is the whole reason this
shape replaced the seven-section one on 2026-09-01. The old shape had two sections that re-entered
the topic from a new angle instead of moving forward: `For a Software Engineer` was a *second*
analogy arriving after the mechanism (the first is `Explain Like I'm 5`), and `What This Means for
You` restated the problem in its "When this matters" part before reaching the action. Read end to
end, an article went problem → mechanism → analogy again → applicability again → and only fifth,
the fix. The reader is a working engineer spending scarce time; a document that re-enters its own
topic three times spends it badly.

The spine now reads: **problem → the fix, named → how it works → what to do → build it → when
not to.** The problem is stated once, in section 2, which must end by naming the fix.

**The engineer anchor survives as a sentence, not a heading**, and it opens section 3. It must
announce itself — begin it literally *"From a software engineering perspective, …"* — and then
name the thing the reader has already shipped ("this is a configuration precedence bug, and you
have shipped one"). `--check` enforces the opener. As a *heading* this move invited re-teaching
the topic before drawing the analogy, which is what made it a digression; as one signposted
sentence it is a bridge into the mechanism and still the site's most distinctive beat. What it
must not do is re-explain: it compares, in one or two sentences, and hands over.

`## What to Do About It` is **one beat, not three labelled parts.** Its old "When this matters"
and "How it affects you" belong in `The Problem`, which is where the reader meets the failure.
What stays here is the decision and the graduated actions — and **the first action must carry no
precondition**, so a reader outside the exact case still has something to do today.

**Retired**, and warned on for sessions from 2026-08-26: `What It Is` and `Key Technical Details`
(merged into section 3, which now runs shallow to deep in one pass instead of explaining the
topic twice); `For a Software Engineer` and `What This Means for You` (retired 2026-09-01 — see
the six-section table above); `Why It Matters` (its significance argument belongs in `The Problem`, and the
momentum-reporting check moved with it); `How It Connects to What You Know` (its analogy was the
same move as the engineer anchor, done twice — what survives is a one-line pointer into the
`learn/` track, in the body, not a heading); `Try It Yourself` (a pointer to a tab the reader can
already see); `Glossary`.

**Per-section word bands**, fenced code excluded, warned by `--check` from 2026-09-01:
`Explain Like I'm 5` 60-120 · `The Problem` 190-320 · mechanism section cap 370 (no floor) ·
`What to Do About It` 150-260 · `Implementing It` 300-460 · counter-case 150-250.
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

**No Glossary section. Define every term at the moment it is first used**, in the sentence that
needs it, the way the reference publications do. A term that cannot be defined in a clause
without derailing the sentence is a term the article should not be using yet. This replaces a
305-word appendix that competed with the code for attention.

The old eleven-section order stands in the back catalog and is not warned on. It is not the
shape to copy: it explained the topic four times and named the object in the fifth section.

`What to Do About It` is required on Tier C too. If the honest answer is "this will not affect
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
