# Voiceprint — product spec (v0)

**One line:** you upload what you wrote, it works out what the AI took out, and it hands you back a
document that sounds like you.

**The deliverable is a finished document.** Scores, heat maps and drift tables are how it gets
there and how the user trusts it, but a session that ends in analysis has failed. Everything below
is in service of a file the user can send.

Working name. Alternatives: *Still You*, *Trueprint*, *Baseline*.

**Status:** spec only. Nothing built. Scoped to a ~2-week first version.

---

## 1. The problem, stated honestly

Someone writes something — a letter, an essay, an outreach email, a speech. They run it through an
AI to tighten it. The AI hands back something fluent, balanced, and slightly anonymous. They edit it
further. Now they cannot tell how much of their own voice survived.

Two versions of the same moment, at opposite ends of the stakes:

> A manager writes twelve reassignment letters, runs them through an AI, and gets twelve letters
> that read identically. The people receiving them will notice.
>
> Someone rewrites their own newsletter and it comes back sounding like a press release. Nobody is
> judging them. They just hate it.

Both are this product's user. Where the stakes are high, a second worry gets attached: *will the
reader think I used AI?* That worry is real but usually misdirected. Detectors are noisy enough
that the people using them know it — false-positive rates make them unusable as evidence, and they
misfire hardest on non-native English writers. The damage is softer:

> **"This could have been written by anyone."**

AI editing strips specifics, flattens rhythm, removes the odd opinion, and deletes the stories about
things going wrong. What is left is *competent and interchangeable*. That is the thing to fix, and
fixing it happens to also settle the detector worry — because the cure is putting real, specific,
personal material back in, not laundering the prose.

So the product is **not** an AI humanizer. It is a **voice-fidelity and authorship-provenance tool.**
That distinction is the whole design, the whole guardrail, and the whole marketing position.

---

## 2. The insight the product is built on

The user's own instinct was right and is better than the obvious version. They proposed feeding in
three documents: the original, the AI version, and another sample of their writing. That gives you
something no "humanize this text" tool has:

| Input | What it buys you |
|-------|------------------|
| **A. Your pre-AI original** | Your voice under the exact same task and pressure |
| **B. The AI-edited version** | The diff A→B *is a measurement of what AI removed from you* |
| **C. An unrelated sample you wrote** | Validates the fingerprint — proves A wasn't a one-off |
| **D. Your current working draft** | The thing being scored |
| **E. Which assistant edited it** | Selects the tell profile — see §4. Claude / ChatGPT / Gemini |

Everyone else scores a single document against a generic notion of "human." Voiceprint scores a
document against **this particular person**, using a diff that shows exactly which properties changed
when the model touched it. That is a harder thing to copy and a much more useful output.

The headline number is not "87% human." It is:

> **"You've recovered 70% of your voice. Six paragraphs still read as not-yours. Here they are."**

---

## 3. What it measures

All of this is deterministic, computable in the browser, no model required. Two documents, two
profiles, one distance.

**Rhythm** — the strongest and most overlooked signal.

1. Mean sentence length
2. Sentence-length standard deviation (*burstiness* — humans put a 4-word sentence next to a 40-word one; models do not)
3. Share of sentences under 8 words
4. Share of sentences over 30 words
5. Paragraph length mean and SD

**Lexical habits** — fingerprint-grade, hard to fake, unconscious.

6. Contraction rate per 1,000 words
7. Punctuation profile: comma / semicolon / colon / em-dash / parenthesis rate
8. Rare-word rate (tokens outside a top-5,000 frequency list)
9. First-person density (`I` / `we` / `my`)
10. Hedge rate (`may`, `could`, `generally`, `often`, `arguably`)
11. Passive-voice share

**Model tells** — the pattern library, matched as spans so they can be highlighted. The lexicon and
weights here are **selected by which assistant the user names** (§4), not one generic list.

12. Cliché lexicon (*delve, tapestry, testament to, underscore, multifaceted, navigate the complexities, in today's landscape, robust framework*)
13. Paragraph-opening connectives (*Moreover / Furthermore / Additionally*) as a share of paragraphs
14. Tricolons — the three-item list, especially of abstract nouns (*rigor, curiosity, and collaboration*)
15. Antithesis scaffolds (*not only X but also Y*, *it isn't X, it's Y*, *while X, Y*)
16. Empty closers — final paragraphs that introduce no noun not already used above

**Concreteness** — the one that most makes a document yours rather than anyone's.

17. Specificity density: proper nouns + numerals + dates + units + tool names per 100 words
18. Count of sentences containing **zero** concrete referents
19. Consequence markers — does any sentence describe something that went wrong, cost something, or was given up?

### Scoring

Three subscores, never one. A single number invites gaming and hides the useful detail.

| Score | Definition | Shown as |
|-------|------------|----------|
| **Voice match** | Weighted distance from the user's fingerprint (metrics 1–11) | 0–100 vs *your* baseline, not vs "human" |
| **Concreteness** | Metrics 17–19, absolute scale | Per-unit, with the empty sentences listed |
| **Tell density** | Metrics 12–16 per 1,000 words | Highlighted spans, dismissible |

---

## 4. Which assistant edited it

A required input, multi-select because people chain tools: **Claude / ChatGPT / Gemini / Other /
Not sure.** It is not cosmetic — it selects the tell profile and re-weights the drift comparison.

**Why it earns its place.**

1. **Precision.** One generic 200-phrase list flags phrases the model in question never produces,
   and every false highlight costs trust. A per-model lexicon is 60–90 entries and nearly all of
   them land on the document in front of the user.
2. **Different assistants break different things.** The drift signature is not uniform — one
   flattens sentence variance hardest, another strips contractions and injects headings and bullets
   into flowing prose, another over-produces triads and *not-only-but-also* frames. Weighting the
   distance metric by the known signature finds the drifted paragraphs faster and explains them
   better.
3. **The rewrite knows what to undo.** *"Reverse the specific transformations this assistant
   applies"* is a far tighter instruction than *"make it sound human."*

### Profiles are measured, not authored

This is the part to get right. Hand-writing a list of "ChatGPT words" from memory produces a folk
wisdom artifact that is wrong within two model releases. Each profile is a versioned, dated data
file derived from a corpus run:

```json
{
  "id": "chatgpt",
  "measured": "2026-09",
  "corpus": { "docs": 240, "task": "tighten-this-statement" },
  "lexicon": [ { "span": "delve into", "lift": 14.2 }, { "span": "multifaceted", "lift": 9.1 } ],
  "structural": { "tricolon_lift": 2.6, "heading_injection": 0.41, "antithesis_lift": 3.3 },
  "drift_signature": { "sentence_sd": -0.38, "contractions": -0.71, "specificity": -0.55 }
}
```

`lift` is how much more often a span appears in that assistant's edits than in the human baseline
corpus. Only spans above a lift threshold make the list, so the lexicon is *derived* rather than
guessed.

**Building the corpus is the product's own core measurement, aggregated.** Take 200–300
human-written statements, run each through one fixed edit prompt on each assistant, and record the
A→B delta distribution — the identical code path §2 already describes, just averaged. No user
documents are needed, which keeps the privacy promise in §7 intact.

### Auto-detect, and the consistency check

Score the AI-edited version against all three profiles and report the best match with a confidence
band. Two uses:

- It backs the **"Not sure"** option, which will be a large share of users.
- It is a **consistency check.** If the user says ChatGPT and the text matches Gemini, they likely
  chained tools or pasted from somewhere they have forgotten. The tool should say so rather than
  silently scoring against the wrong profile.

### Profiles rot

Assistants change every few months and a stale profile is worse than no profile, because it is
confidently wrong. Rules:

- Every profile carries its `measured` date and is surfaced in the UI.
- A profile older than six months shows a staleness warning and falls back to the generic lexicon
  for any span below a confidence bar.
- Refresh quarterly. It is a scripted corpus run — roughly half a day, mostly waiting.

### The one thing not to build

**No leaderboard of which assistant is hardest to detect.** The per-model breakdown invites it, and
it would be the most shareable page on the site, which is exactly why it is a trap: it converts a
voice-fidelity tool into an evasion tool and forfeits the entire position in §7.

Ranking assistants on *how much of an author's voice they strip* is a legitimate quality question
and a good piece of content. Ranking them on how well they hide is not. The line is firm enough to
write into the repo's README so it survives a growth-hungry quarter.

---

## 5. The screen

Single page. Four upload slots and one assistant picker, collapsing to one working view, ending in a
download.

**Uploads, entirely in the browser.** Drag-and-drop or file picker for each of the four inputs,
with paste as a fallback for people working from a web editor. `.docx`, `.txt`, `.md` and `.pdf`
(text-layer only) are parsed client-side — `mammoth` for Word, `pdf.js` for PDF — so the files never
leave the machine. No upload endpoint exists in v0, which makes the privacy claim structural rather
than a policy: there is nowhere for a document to be stored even by accident. The only network call
in the whole product is the per-paragraph rewrite.

A scanned PDF with no text layer is rejected with a clear message rather than sent to OCR. That is
a v2 problem.

```
┌──────────────────────────────────────────────────────────────┐
│  Voice match  70/100      Concreteness  34/100    Tells  11  │
│  ▓▓▓▓▓▓▓░░░               ▓▓▓░░░░░░░               ↓ from 23 │
├───────────────────────────────┬──────────────────────────────┤
│                               │  WHAT CHATGPT CHANGED  [▾]   │
│  Your draft, paragraph-       │  profile measured 2026-09    │
│  shaded by voice distance:    │                              │
│                               │  Sentence variance  ↓ 41%    │
│  ░ para 1  close to you       │  Contractions       ↓ 100%   │
│  ▓ para 2  DRIFTED            │  Numbers/names      ↓ 62%    │
│  ░ para 3                     │  Tricolons          ↑ 4 → 11 │
│  ▓ para 4  DRIFTED            │  Avg para length    → uniform│
│  ░ para 5                     │                              │
│                               │  Heavier than a typical      │
│  [click a paragraph]          │  ChatGPT edit on specifics,  │
│                               │  lighter on structure.       │
│                               │                              │
│                               │  ── SELECTED: para 2 ──      │
│                               │  · "multifaceted" — not a    │
│                               │    word you have ever used,  │
│                               │    and 9× more likely in a   │
│                               │    ChatGPT edit than a human │
│                               │    one                       │
│                               │  · 3 sentences, all 19–22    │
│                               │    words. You normally run   │
│                               │    6–34.                     │
│                               │  · No numbers, no names.     │
│                               │    Your original said        │
│                               │    "eleven months" here.     │
│                               │                              │
│                               │  [ Rewrite in my voice ]     │
└───────────────────────────────┴──────────────────────────────┘
```

The right panel is the product. "Your original said *eleven months* here" is the line that makes
someone pay.

---

## 6. The rewrite, and why it asks questions

Per paragraph, on demand. The prompt is few-shot on **the user's own A and C samples**, with hard
constraints derived from their measured fingerprint ("target sentence-length SD ≥ 9; contractions
permitted; do not use the following 14 phrases").

**The rule that defines the product: it never invents a fact.** When a paragraph fails the
concreteness check, the tool does not write a plausible number. It asks:

> *This paragraph says "significantly improved the pipeline." Your original mentioned a duration
> here. What was the actual number, and what did you give up to get it?*

The user types the answer. The tool works it in. This is better output *and* it is the ethical
line — a tool that invents biographical detail on someone's behalf is a tool for lying in their
name, and this one structurally cannot.

**Unanswered questions cut the sentence, they do not fill it.** A user who skips a question gets a
shorter document, not an invented one, and the export names what was removed so nothing vanishes
silently.

### Ending in a document

The rewrite loop is not the end of the session. When the user accepts the last paragraph, the page
hands them:

1. **The rewritten document** — `.docx` or `.md`, same format they uploaded, generated client-side.
2. **What was cut**, one line each, for anything dropped because a question went unanswered.
3. **Before and after** — voice match, measures outside range, tells, sentences without specifics.
   Three lines. This is the receipt, not the product.
4. Optionally, a **disclosure line** they can adapt if they want to state that they used an AI editor.

Rewriting toward the score past roughly 85 is fitting to a proxy. The page should stop encouraging
edits at that point rather than gamifying the number.

---

## 7. Guardrails, built in rather than promised

| Rule | Mechanism |
|------|-----------|
| Cannot be used to ghostwrite | **No baseline samples → no rewrite.** The feature is dead without ≥800 words the user wrote. A person with nothing of their own to feed it gets an analyzer and nothing else. |
| Never fabricates | Rewrite returns a question, not a guess, when a specific is missing |
| No evasion claims | Never markets against a named detector, never reports or predicts a "pass rate", never optimizes against a detector's score |
| No assistant leaderboard | Per-model profiles (§4) are never aggregated into a ranking of which assistant hides best. Voice-stripping comparisons are fine; evasion comparisons are not |
| Baseline honesty | If the "your writing" samples themselves score high on tell density, warn: *your baseline looks AI-assisted; the fingerprint will be unreliable* |
| Privacy | Metrics run client-side. Only the rewrite call leaves the browser. No storage in v0, no training on user text, stated plainly |
| Disclosure, not concealment | Export includes an optional, honest AI-assistance disclosure line the user can paste in wherever it is relevant |

That last row matters more than it looks. The market is drifting toward *disclosed* AI assistance
being normal and acceptable. A product that helps you say "I drafted this, used an AI editor,
and verified it still reads as mine" is on the right side of that drift. One that helps you hide
is on a five-year clock.

---

## 8. Build

Deliberately boring. The differentiated part is the metric set and the diff, not the stack.

| Layer | Choice | Why |
|-------|--------|-----|
| App | Vite + TypeScript, single page, static | No backend for the part that does the work |
| Metrics | Hand-rolled TS: sentence splitter, tokenizer, frequency list, regex span matchers | ~600 lines. Runs in <50ms on 2,000 words. Client-side = privacy is real, not claimed |
| Tell profiles | Three versioned JSON files (`profiles/{claude,chatgpt,gemini}-YYYY-MM.json`) shipped as static assets, plus a generic fallback | Data, not code — a quarterly refresh is a file swap, not a release |
| Profile builder | Offline Node script: corpus → one fixed edit prompt per assistant → lift table | Reuses the same metric module as the app. Run quarterly, never in production |
| Rewrite | One serverless function (Vercel/CF Workers) proxying Claude, holding the key | Only network call |
| Model | `claude-sonnet-5` for rewrites | Style-matching from few-shot exemplars is the task it is good at |
| Uploads | `mammoth` (.docx), `pdf.js` (.pdf text layer), plain read for .md/.txt — all client-side | No upload endpoint means no document store to leak |
| Export | `docx` npm package, generated in the browser | Most people's documents live in Word |
| Hosting | Cloudflare Pages + one Function | Same shape as theaicommit.com — known quantity |
| Storage | None in v0 | Ship faster, privacy claim is trivially true |

### Timeline

| | Days | Ships |
|---|------|-------|
| **v0** | 1–5 | Upload 4 files, pick the assistant → three scores, A→B drift table, paragraph heat map, tell highlighting. Ships with hand-seeded profiles for the three assistants. **No LLM at all.** This is already sellable and costs nothing to run. |
| **v0.5** | 6–9 | Per-paragraph rewrite, seeded on user samples and the source assistant's drift signature, with the question-asking behavior |
| **v1** | 10–14 | Profile builder run for real (replaces the hand-seeded lists), assistant auto-detect and the "Not sure" path, .docx export, provenance report, saved voiceprints (accounts) |
| v2 | later | Google Docs add-on — meet the writing where it happens; OCR for scanned PDFs |
| v3 | later | B2B house-voice: same engine, fingerprint is a brand's not a person's |

The v0 cut is the important one. A deterministic analyzer with zero inference cost, shipped in five
days, tells you whether anyone cares — before you pay for a single token.

One honest wrinkle: v0's profiles are hand-seeded, which is exactly the folk-wisdom artifact §4 warns
against. That is an acceptable trade for five days, on two conditions — the UI labels them
*provisional*, and the v1 corpus run is scheduled before v0 ships, not after someone complains.

---

## 9. Who pays

> **Audience correction — read this before the table.** The segments below are examples, not the
> market, and this spec narrowed the audience twice before getting it right: first to job
> applicants, then to people writing formal letters. **The audience is anyone.** It is defined by a
> moment, not a profession or a document type: *you wrote something, you ran it through an AI, it
> came back less like you, and that bothers you.* Salespeople rewriting outreach, students
> tightening essays, a manager writing reassignment letters, someone drafting a wedding speech or
> complaining to their landlord. The stakes run from *a committee will judge me* down to *I just
> don't like how it reads*, and the product works the same at both ends.
>
> This is not only a marketing note — it changes the build. Short documents need sentence-level
> rather than paragraph-level flagging; casual register must be preserved rather than smoothed into
> business prose; and some users are repeat users, which the two-document free tier does not fit.
> `docs/voiceprint-build-spec.md` §1 carries the consequences.

| Segment | Document | Shape of use |
|---------|----------|--------------|
| **Anyone who noticed** | Whatever they just ran through an AI | The default. Do not design past it |
| Salespeople, recruiters, founders | Outreach, proposals, posts, changelogs | **Repeat** - daily or weekly, short documents |
| Students | Essays, applications, coursework where editing is allowed but authorship is assessed | Bursty, term-shaped |
| Managers | Reassignment letters, reviews, recommendations | Batches - twelve letters that must not read identically |
| Applicants | Statements, cover letters | One-off, high stakes, seasonal |
| Later: comms teams | House voice across writers | Steady, B2B pricing |

The repeat row is the commercially interesting one and the one a two-document free tier fits worst -
somebody rewriting outreach every day exhausts it before lunch. Do not build for them in v1; do
notice if they show up.

**Pricing.** Job hunting is bursty, so subscriptions fit badly:

- **Free** — one document, analysis only, no rewrite. The scores are the hook.
- **$12 one-off** — "document pack": 5 documents, rewrites, .docx export, provenance report.
- **$19/mo** — repeat writers and consultants.

Lead with the one-off. Someone three days from a deadline will pay $12 and will not sign up for a
subscription.

**Wedge: the analysis is the ad.** Anyone can run it on their own text in thirty seconds, for free,
and the output is inherently shareable — *"ChatGPT deleted 62% of the numbers and every contraction
from my writing, here's the diff."* That screenshot travels in writing, sales, student and general
AI communities alike, and it needs no audience segmentation because everyone who has pasted
something into an AI recognizes it.

The pitch is never "beat AI detection." It is *"here is exactly what the AI took out of your
writing."* The evasion framing would get the same post removed from most of those communities; this
one gets upvoted in all of them.

---

## 10. What could go wrong

| Risk | Response |
|------|----------|
| Users want a pass-rate guarantee | Refuse it, in writing, on the landing page. Promise voice fidelity and specificity. Anyone who leaves over this was going to churn and complain |
| Metric-chasing makes writing worse | Every suggestion is accept/reject per span. Never auto-apply. Add a readability floor |
| Their "own" samples are AI-written | Detect and warn (guardrail table above). Degrade to generic analysis |
| Fingerprints are unstable on short samples | Require 800+ words across ≥2 documents before showing a voice-match score. Show a confidence band |
| Per-model profiles go stale on the next release | Dated profiles, staleness warning past six months, quarterly refresh as a scripted corpus run. The generic lexicon is always the floor, so a stale profile degrades rather than breaks |
| User names the wrong assistant, or chained two | Auto-detect scores against all three and flags the mismatch instead of silently using the wrong profile. Assistant picker is multi-select |
| "Which one should I use so it looks least AI?" | The question the per-model view invites. Answer it as a voice-stripping question, never an evasion one, and never ship the ranking as a page |
| Detection anxiety fades as norms shift | The concreteness half of the product has nothing to do with AI. "Your writing is too generic to get an interview" survives the shift |
| Commodity — an LLM can approximate this in one prompt | True for the rewrite, false for the A→B diff and the longitudinal fingerprint. Defend on the measurement, not the generation |

---

## 11. Does it work

| Metric | Target |
|--------|--------|
| Activation | % who paste a real baseline sample (not just the draft) — this is the whole funnel |
| Engagement | Paragraphs edited per session ≥ 4 |
| Value proof | Concreteness score delta, first open → export |
| Retention | % returning with a *second* document within 30 days |
| Revenue | Free → one-off conversion on the second document |

Validation before building v0.5: run 20 statements through the v0 analyzer by hand and check
whether the paragraphs it flags are the paragraphs a real reader finds hollow. If flagged ≠ hollow,
the metric weights are wrong and no amount of LLM rewriting will save it.

Validation for the profiles specifically: hold out 30 edits per assistant from the corpus run and
check that auto-detect picks the right one. Below roughly 70% the profiles are not capturing
anything real, and the per-model view should be pulled rather than shipped as decoration.

---

## Appendix — the manual version

Everything in v0 can be done by hand in about an hour. Useful as a sanity check on whether the
product is worth building, and useful immediately to anyone with a deadline this week.

1. **The only-me test.** Sentence by sentence: could anyone else have written this exact sentence?
   If yes, it is doing nothing for you. Replace it with something only you would say or only you
   would know.
2. **Put the numbers back.** AI deletes specifics. Dates, headcounts, durations, tool names, the
   name of the thing that broke. "Improved the process" → "cut the nightly batch from 11 hours to
   40 minutes, mostly by deleting one join."
3. **Restore one failure.** AI drafts are relentlessly positive and consequence-free. A line about
   something that did not work, and what you did next, reads as human more than any stylistic
   trick — and it is what readers remember.
4. **Read it aloud.** Anything you would never say out loud, rewrite. This catches most of it.
5. **Break the rhythm.** Find three paragraphs where every sentence is 18–25 words. Add a short one.
   Four words is fine.
6. **Kill the triads and the seesaws.** Delete one item from every three-item list. Rewrite every
   *"not only X but also Y"* and *"it isn't X, it's Y."*
7. **Cut one adjective per noun phrase.** Nearly always an improvement.
8. **Take one position.** A mild, defensible opinion someone could disagree with. Models do not do
   this; it is the clearest signal of a person.
9. **Retype the first and last paragraph from scratch**, without looking at the draft. Those get
   read most and are where borrowed cadence is most visible.
10. **Compare against your own old writing.** Open something you wrote two years ago. Do you use
    contractions? Em dashes? Long sentences? Match yourself, not an idea of good prose.
11. **Provenance hygiene.** Type your edits rather than pasting one block; keep the version history;
    do not hand over a file whose metadata shows three minutes of editing time.
12. **One human read.** Someone who knows you, asked exactly one question: *does this sound like me?*

---

## Appendix B — the prototype that already exists

`/sounds-like-me` (`.claude/skills/sounds-like-me/`) is this product as a Claude Code skill: same
four inputs, same assistant picker, same interview, same deliverable. It exists to find out what
the product should be before any of it is built in a browser.

- `scripts/voiceprint.py` is the v0 metric engine — pure Python, no dependencies, no network. The
  browser version is a port of it, not a rewrite.
- The skill's Step 3 interview is where the product's real behavior lives, and it is the part
  hardest to get right from a spec. Questions that reliably produce good answers should be logged
  and folded back in here.
- The skill enforces the 400-word baseline gate and the never-invent-a-fact rule the same way the
  product is meant to.

Run it on real documents before building v0. Anything it gets wrong is cheaper to learn there.
