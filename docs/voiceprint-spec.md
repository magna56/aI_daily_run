# Voiceprint — product spec (v0)

**One line:** you give it two things you unquestionably wrote, and it tells you which paragraphs of
your AI-edited draft no longer sound like you — and what the AI took out.

Working name. Alternatives: *Still You*, *Trueprint*, *Baseline*.

**Status:** spec only. Nothing built. Scoped to a ~2-week first version.

---

## 1. The problem, stated honestly

Someone writes a cover letter or a personal statement. They run it through an AI to tighten it. The
AI hands back something fluent, balanced, and slightly anonymous. They edit it further. Now they
cannot tell how much of their own voice survived, and they are about to send it to a committee that
reads 300 of these and has started flagging the ones that read like a language model.

The anxiety is real but the usual framing is wrong. The failure mode is almost never *"a detector
caught me."* Detectors are noisy and committees know it — they produce false positives at rates that
make them unusable as evidence, and they are notably worse on non-native English writers. What
actually sinks an application is softer and more damaging:

> **"This could have been written by any of the 300 people in this pile."**

AI editing strips specifics, flattens rhythm, removes the odd opinion, and deletes the failure
stories. What is left is *competent and interchangeable*. That is the thing to fix, and fixing it
happens to also fix the detector worry — because the cure is putting real, specific, personal
material back in, not laundering the prose.

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

**Model tells** — the pattern library, matched as spans so they can be highlighted.

12. Cliché lexicon (~200 phrases: *delve, tapestry, testament to, underscore, multifaceted, navigate the complexities, in today's landscape, robust framework*)
13. Paragraph-opening connectives (*Moreover / Furthermore / Additionally*) as a share of paragraphs
14. Tricolons — the three-item list, especially of abstract nouns (*rigor, curiosity, and collaboration*)
15. Antithesis scaffolds (*not only X but also Y*, *it isn't X, it's Y*, *while X, Y*)
16. Empty closers — final paragraphs that introduce no noun not already used above

**Concreteness** — the one that actually wins interviews.

17. Specificity density: proper nouns + numerals + dates + units + tool names per 100 words
18. Count of sentences containing **zero** concrete referents
19. Consequence markers — does any sentence describe something that went wrong, cost something, or was given up?

### Scoring

Three subscores, never one. A single number invites gaming and hides the useful detail.

| Score | Definition | Shown as |
|-------|------------|----------|
| **Voice match** | Weighted distance from the user's fingerprint (metrics 1–11) | 0–100 vs *your* baseline, not vs "human" |
| **Concreteness** | Metrics 17–19, absolute scale | Per-paragraph, with the empty sentences listed |
| **Tell density** | Metrics 12–16 per 1,000 words | Highlighted spans, dismissible |

---

## 4. The screen

Single page. Four paste boxes collapsing to one working view.

```
┌──────────────────────────────────────────────────────────────┐
│  Voice match  70/100      Concreteness  34/100    Tells  11  │
│  ▓▓▓▓▓▓▓░░░               ▓▓▓░░░░░░░               ↓ from 23 │
├───────────────────────────────┬──────────────────────────────┤
│                               │  WHAT THE AI CHANGED         │
│  Your draft, paragraph-       │                              │
│  shaded by voice distance:    │  Sentence variance  ↓ 41%    │
│                               │  Contractions       ↓ 100%   │
│  ░ para 1  close to you       │  Numbers/names      ↓ 62%    │
│  ▓ para 2  DRIFTED            │  Tricolons          ↑ 4 → 11 │
│  ░ para 3                     │  Avg para length    → uniform│
│  ▓ para 4  DRIFTED            │                              │
│  ░ para 5                     │  ── SELECTED: para 2 ──      │
│                               │  · "multifaceted" — not a    │
│  [click a paragraph]          │    word you have ever used   │
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

## 5. The rewrite, and why it asks questions

Per paragraph, on demand. The prompt is few-shot on **the user's own A and C samples**, with hard
constraints derived from their measured fingerprint ("target sentence-length SD ≥ 9; contractions
permitted; do not use the following 14 phrases").

**The rule that defines the product: it never invents a fact.** When a paragraph fails the
concreteness check, the tool does not write a plausible number. It asks:

> *This paragraph says "significantly improved the pipeline." Your original mentioned a duration
> here. What was the actual number, and what did you give up to get it?*

The user types the answer. The tool works it in. This is better output *and* it is the ethical
line — a tool that fabricates biographical detail for an application is a tool for committing fraud,
and this one structurally cannot.

---

## 6. Guardrails, built in rather than promised

| Rule | Mechanism |
|------|-----------|
| Cannot be used to ghostwrite | **No baseline samples → no rewrite.** The feature is dead without ≥800 words the user wrote. A person with nothing of their own to feed it gets an analyzer and nothing else. |
| Never fabricates | Rewrite returns a question, not a guess, when a specific is missing |
| No evasion claims | Never markets against a named detector, never reports or predicts a "pass rate", never optimizes against a detector's score |
| Baseline honesty | If the "your writing" samples themselves score high on tell density, warn: *your baseline looks AI-assisted; the fingerprint will be unreliable* |
| Privacy | Metrics run client-side. Only the rewrite call leaves the browser. No storage in v0, no training on user text, stated plainly |
| Disclosure, not concealment | Export includes an optional, honest AI-assistance disclosure line the user can paste into their application |

That last row matters more than it looks. The market is drifting toward *disclosed* AI assistance
being normal and acceptable. A product that helps you say "I drafted this, used an AI editor,
and verified it still reads as mine" is on the right side of that drift. One that helps you hide
is on a five-year clock.

---

## 7. Build

Deliberately boring. The differentiated part is the metric set and the diff, not the stack.

| Layer | Choice | Why |
|-------|--------|-----|
| App | Vite + TypeScript, single page, static | No backend for the part that does the work |
| Metrics | Hand-rolled TS: sentence splitter, tokenizer, frequency list, regex span matchers | ~600 lines. Runs in <50ms on 2,000 words. Client-side = privacy is real, not claimed |
| Rewrite | One serverless function (Vercel/CF Workers) proxying Claude, holding the key | Only network call |
| Model | `claude-sonnet-5` for rewrites | Style-matching from few-shot exemplars is the task it is good at |
| .docx in/out | `mammoth` to read, `docx` to write | Applicants live in Word |
| Hosting | Cloudflare Pages + one Function | Same shape as theaicommit.com — known quantity |
| Storage | None in v0 | Ship faster, privacy claim is trivially true |

### Timeline

| | Days | Ships |
|---|------|-------|
| **v0** | 1–5 | Paste 4 boxes → three scores, A→B drift table, paragraph heat map, tell highlighting. **No LLM at all.** This is already sellable and costs nothing to run. |
| **v0.5** | 6–9 | Per-paragraph rewrite, seeded on user samples, with the question-asking behavior |
| **v1** | 10–14 | .docx upload and export, provenance report, saved voiceprints (accounts) |
| v2 | later | Google Docs add-on — meet the writing where it happens |
| v3 | later | B2B house-voice: same engine, fingerprint is a brand's not a person's |

The v0 cut is the important one. A deterministic analyzer with zero inference cost, shipped in five
days, tells you whether anyone cares — before you pay for a single token.

---

## 8. Who pays

| Segment | Document | Urgency |
|---------|----------|---------|
| **Academic job seekers** | Research / teaching / diversity statements, cover letters | Very high, seasonal, high stakes |
| Grad + professional school applicants | SOPs, personal statements | Very high, seasonal |
| Career switchers | Cover letters at volume | Medium, bursty |
| Students | Coursework where AI editing is permitted but authorship is assessed | High |
| Later: comms teams | House voice across writers | Steady, B2B pricing |

**Pricing.** Job hunting is bursty, so subscriptions fit badly:

- **Free** — one document, analysis only, no rewrite. The scores are the hook.
- **$12 one-off** — "application pack": 5 documents, rewrites, .docx export, provenance report.
- **$19/mo** — repeat writers and consultants.

Lead with the one-off. Someone three days from a deadline will pay $12 and will not sign up for a
subscription.

**Wedge:** academic job market forums and subreddits in hiring season. The pitch is not "beat AI
detection" — it is *"your statement got smoothed into everyone else's; here's exactly what it lost."*
That framing is shareable in places where the evasion framing would get the post removed.

---

## 9. What could go wrong

| Risk | Response |
|------|----------|
| Users want a pass-rate guarantee | Refuse it, in writing, on the landing page. Promise voice fidelity and specificity. Anyone who leaves over this was going to churn and complain |
| Metric-chasing makes writing worse | Every suggestion is accept/reject per span. Never auto-apply. Add a readability floor |
| Their "own" samples are AI-written | Detect and warn (guardrail table above). Degrade to generic analysis |
| Fingerprints are unstable on short samples | Require 800+ words across ≥2 documents before showing a voice-match score. Show a confidence band |
| Detection anxiety fades as norms shift | The concreteness half of the product has nothing to do with AI. "Your writing is too generic to get an interview" survives the shift |
| Commodity — an LLM can approximate this in one prompt | True for the rewrite, false for the A→B diff and the longitudinal fingerprint. Defend on the measurement, not the generation |

---

## 10. Does it work

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

---

## Appendix — the manual version

Everything in v0 can be done by hand in about an hour. Useful as a sanity check on whether the
product is worth building, and useful immediately to anyone with a deadline this week.

1. **The only-me test.** Sentence by sentence: could another applicant in your field have written
   this exact sentence? If yes, it is doing nothing for you. Replace it with a fact only you have.
2. **Put the numbers back.** AI deletes specifics. Dates, headcounts, durations, tool names, the
   name of the thing that broke. "Improved the process" → "cut the nightly batch from 11 hours to
   40 minutes, mostly by deleting one join."
3. **Restore one failure.** AI drafts are relentlessly positive and consequence-free. One paragraph
   about something that did not work, and what you did next, reads as human more than any stylistic
   trick — and committees remember it.
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
