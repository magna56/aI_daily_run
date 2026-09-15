---
name: sounds-like-me
description: >
  Take a document that an AI has edited and hand back a version that sounds like the person who
  wrote the original. The user supplies what they wrote before the AI touched it, at least one
  other sample of their own writing, the AI-edited version, the draft they are working on now,
  and which assistant they used (Claude / ChatGPT / Gemini). The skill measures their voice,
  measures what the AI changed, interviews them for the specifics the AI deleted, and rewrites
  the document paragraph by paragraph back into their voice. The deliverable is a finished
  document, not a report. Use when: "sounds like me", "does this sound like AI", "make this
  sound human", "make this sound like me", "I used ChatGPT on my cover letter", "worried the
  committee will think I used AI", "de-AI this", "restore my voice", "personal statement
  sounds generic". Accepts a folder or file list inline:
  /sounds-like-me ~/applications/cambridge
argument-hint: "[folder or files]"
---

# Sounds Like Me

**The deliverable is a document, not a diagnosis.** A score, a highlighted list of tells, and a
tidy summary of what the AI did are all inputs to this skill's real job, which is handing the user
back a file they can send. If you finish having produced analysis and no rewritten document, you
have not run this skill.

**The second rule, which the first one keeps trying to break: you do not know anything about this
person's life.** The AI that edited their document deleted specifics and replaced them with
plausible filler. Your job is to put the *real* specifics back, and the only place those exist is
in the user's head. You ask. You never fill the gap yourself. A skill that invents "eleven months"
because the sentence needs a number is a skill for committing application fraud.

---

## What this is not

Say this once, early, if the user's framing needs it — then get on with the work.

This is not a detector-evasion tool and it should not be sold to the user as one. AI detectors are
unreliable enough that committees cannot use them as evidence, and they misfire hardest on
non-native English writers. The thing that actually sinks an application is quieter: the document
reads like every other document in the pile, because AI editing strips out the specifics, the
rhythm, the opinions, and the failures that made it theirs.

So the work is restoring what was removed. That happens to be the only honest fix, and it is also
the one that improves the document.

If the user asks which assistant is hardest to detect, answer the useful question instead — which
one strips the most voice — and say plainly that you are not going to help optimize against a
detector.

---

## Step 0: Collect the inputs

Five things. Four are documents, one is a question.

| | Input | Required | Why |
|---|-------|----------|-----|
| **A** | The original, before any AI touched it | **Yes** | Their voice on this exact task |
| **B** | The AI-edited version | Strongly preferred | A→B is a direct measurement of what was taken out |
| **C** | Another thing they wrote, any topic | **Yes** | Proves A was not a one-off. Old email, blog post, thesis chapter |
| **D** | The draft they are working on now | **Yes** | The thing being rewritten. May be the same as B |
| **E** | Which assistant edited it | Yes | `claude`, `chatgpt`, `gemini`, or `generic` if unsure |

Accept a folder, a list of paths, or pasted text saved to the scratchpad. `.docx` gets converted
first (`textutil -convert txt` on macOS, or `pandoc`); if neither is available, ask them to paste.

**The hard gate: A and C together must be at least 400 words, and 800 is where the measurement
starts being trustworthy.** Below 400 the script refuses and so do you. This is not a technicality
to work around — without their own writing there is no voice to restore, and rewriting anyway
would just be ghostwriting with extra steps. If they cannot produce 400 words they wrote, say so
and offer the Step 3 interview on its own, which is useful without any measurement at all.

If B is missing, the skill still works; you lose the A→B change table but keep everything else.

---

## Step 1: Measure

```bash
python3 .claude/skills/sounds-like-me/scripts/voiceprint.py \
    --baseline original.md other_sample.md \
    --ai ai_version.md \
    --draft current_draft.md \
    --assistant chatgpt
```

Add `--json` when you want to read the numbers back programmatically, `--top 12` for more flagged
paragraphs. It is pure Python, no dependencies, no network.

**Run it before you form an opinion.** You are good at noticing that prose sounds like AI and bad
at noticing *which* properties changed and by how much. The script exists so the rewrite is aimed
at measured drift rather than at your impression of it. Your judgement is for the rewriting, where
it is actually needed.

Read the output as three things:

- **The fingerprint** — their sentence length and variance, contraction rate, specificity density.
  This is the target you are rewriting *toward*.
- **The change table** — what the AI did. Long words up 700%, contractions gone, paragraph length
  made uniform.
- **The flagged paragraphs** — ranked worst first, each with the specific reasons it was flagged.

Believe the flags less than the fingerprint. A tell hit means *look at this sentence*, not
*this sentence is guilty*; the phrase lists are hand-seeded and provisional, and the script says so.

---

## Step 2: Show the user what was taken from them

Short. A table of the five biggest changes and a count of flagged paragraphs. This step exists
because it is the moment the user realizes the problem is not "it sounds robotic" but "my numbers
are gone", and that realization is what makes Step 3 work.

Do not paste the full script output. Do not explain every metric.

---

## Step 3: The interview — the step that makes this worth running

For each flagged paragraph, find what the AI deleted and **ask for it**. The original (A) is your
best source of questions: when a sentence in D is vague and the matching sentence in A had a
number, a name, or a story, that is the exact thing to ask about.

Ask in one batch, numbered, six to ten questions. Not one at a time — they are doing this at
11pm the night before a deadline.

Good questions are answerable in a sentence:

> 1. Para 2 says "significant performance improvements." Your original said the batch took eleven
>    hours. What did it come down to, and how long did finding it take you?
> 2. Para 3 says you value "rigor, curiosity, and collaboration." Can you name one time
>    collaboration actually changed what you built? Who, and what changed?
> 3. Para 4 says you are "eager to contribute to your team." Which part of their work do you
>    actually want to work on, and what would you do in the first month?
> 4. Is there something in this application that went wrong and that you would be willing to
>    mention? The draft has no failures in it at all, which reads as evasive.

**If the user does not answer a question, the vague sentence gets cut, not filled.** A shorter
honest document beats a longer invented one. Say that out loud when you cut something.

Never propose a specific for them to confirm — "was it around eleven hours?" is a leading question
that ends with a number you supplied appearing in their application. Ask open.

---

## Step 4: Rewrite

Paragraph by paragraph, toward the fingerprint from Step 1, using their answers from Step 3.

**Return them to themselves. Do not improve them.** This is the instruction most easily broken.
If their baseline runs 10-word sentences, write 10-word sentences, even though 18 would read more
professionally. If they start sentences with "And", so do you. If they use a semicolon once a page
and no em dashes, match that. A rewrite that is objectively better prose but measurably less like
them is a failed rewrite — it is the same failure the original AI edit made, in a nicer direction.

Concretely, per paragraph:

| Do | Don't |
|----|-------|
| Match their sentence-length mean **and variance** — put a four-word sentence next to a long one | Make every sentence the target average |
| Restore their contraction rate | Formalize because it is an application |
| Use the words they use in A and C | Use a synonym you prefer |
| Put their Step 3 answers in as plain fact | Dress the answers up |
| Cut a sentence that says nothing | Rewrite an empty sentence into a prettier empty sentence |
| Keep one mild opinion or one failure per page | Smooth out anything that could be argued with |
| Leave their quirks, including ones a style guide would flag | "Fix" a habit that is part of the fingerprint |

Hard bans in the output, regardless of what the baseline does: the tricolon of abstract nouns
(*rigor, curiosity, and collaboration*), *not only X but also Y*, *it's not X, it's Y*, and any
phrase on the tell list unless the user themselves used it in A or C. If it is in their baseline,
it is theirs — keep it.

Leave the first and last paragraphs for last and write them from scratch against their answers
rather than editing the AI's version. Those get read most, and borrowed cadence is most visible
there.

---

## Step 5: Verify, and be willing to report failure

Save the rewrite and run the script again with the new file as `--draft`.

```bash
python3 .claude/skills/sounds-like-me/scripts/voiceprint.py \
    --baseline original.md other_sample.md --draft rewritten.md --assistant chatgpt
```

Report the before and after honestly:

```
voice match      46 -> 81
measures outside your range    7 of 13 -> 2 of 13
tells            7 -> 0
sentences with no specifics    9 of 10 -> 3 of 11
```

If the score barely moved, say so and say why rather than shipping it quietly. Usually it is one
of three things: the user did not answer the interview questions, so the paragraphs are still
empty; the baseline was too short to aim at; or you rewrote toward good prose instead of toward
them. The third is the most common and the easiest to fix — reread their baseline and try again.

Do not chase the score past about 85. Past that you are fitting to the metric, and the metric is a
proxy. Two measures outside range on a document full of their own specifics is a finished document.

---

## Step 6: Deliver

Three things, in this order:

1. **The rewritten document**, complete, as a file they can send. Same format they gave you. This
   is the deliverable — lead with it, do not bury it under commentary.
2. **What you cut and why**, if you cut anything for lack of an answer. One line each. They need
   to know what is missing before they send it.
3. **The before/after numbers** from Step 5. Three lines, not a report.

Then stop. Do not offer to keep polishing.

If the user wants to disclose AI assistance, offer a plain sentence they can adapt — *"I drafted
this myself, used an AI tool to edit, and revised the result"* — rather than drafting a
justification. Disclosure is increasingly normal and is a better position than concealment.

---

## Never

- **Never invent a biographical fact.** Not a number, not a date, not a job title, not a
  collaborator's name, not a reason. Ask, or cut.
- **Never rewrite without a baseline.** Under 400 words of their own writing, the script refuses
  and so do you.
- **Never optimize against a named detector**, report a predicted pass rate, or tell the user a
  document will "pass". You are measuring distance from *their* voice, which is a different
  question and the only one you can answer.
- **Never present the tell lists as authoritative.** They are hand-seeded, dated, and will be wrong
  about some phrase. `docs/voiceprint-spec.md` §4 owns the plan to replace them with measured ones.
- **Never touch git.** This skill reads and writes documents in the user's working folder. It does
  not commit, branch, or push.

---

## Where this is going

This skill is the working prototype of the product specced in `docs/voiceprint-spec.md` — the
browser tool that takes uploads and hands back a rewritten document. `scripts/voiceprint.py` is the
v0 metric engine, and the interview in Step 3 is the behavior that keeps the product from being a
fabrication machine.

Two things learned here should flow back into that spec rather than living only in this file: any
phrase that turns out to be a false positive, and any interview question that reliably produces a
good answer. The second list is more valuable than the first.
