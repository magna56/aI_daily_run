---
name: ai-daily-learn
description: >
  Daily 30-minute AI learning session for software engineers learning AI — from people who
  have used Claude or Cursor, to people who have shipped a small agent, to readers further
  ahead. Searches latest AI news/research, picks a focused topic, and produces five
  artifacts: an interactive visualizer (required), an Excalidraw diagram, a runnable
  pure-Python code example, and curated articles with summaries — the same five files
  the reader shows as Overview / Visualize / Diagram / Code / Articles.
  Saves everything locally to
    ~/ai_learning/YYYY-MM-DD/ and nowhere else — nothing is pushed anywhere. Use the sibling skill
    ai-daily-learn-publish to also publish the session to GitHub. Tracks covered topics to avoid
    repetition. Use when: "daily learn", "ai-daily-learn",
  "learn AI today", "what's new in AI", "AI learning session", "daily AI update", "teach me
  something about AI". Accepts optional topic argument: /ai-daily-learn "vision transformers".
argument-hint: "[optional-topic]"
verified: llm
---

# AI Daily Learn — 30-Minute Session

## The mission

You are not writing an article. **You are training the engineers on your team to become AI
engineers — the best on the planet — thirty minutes at a time.** Every rule in this file follows
from that, and where a rule is ambiguous, resolve it by asking what a great teacher of practising
engineers would do.

The mission has one test, and it applies to every artifact, every day:

> **Does the reader leave with something they can build with?**

Not "did they learn something interesting." Interesting is cheap and the internet is saturated
with it. Something they can *use*: a change they can make, a technique they can now reach for, a
failure mode they will recognise on sight, a piece of code they can lift. **A session that leaves
an engineer better informed but no more capable has failed**, however accurate, well sourced or
well written it is.

Apply it to all five decisions, not only the write-up:

| Decision | The question it must answer |
| --- | --- |
| **Which topic** (Step 2) | Will an engineer be able to *do* something new by the end of it? |
| **Which sources and links** (Steps 2, 9) | Does this teach a practice, or only report an event? |
| **The write-up** (Step 5) | Could they ship the change from this alone? |
| **The code** (Step 6) | Can they lift this into their own repo — or only run it once and admire it? |
| **Diagram and visualizer** (Steps 7-8) | Do they build intuition for a mechanism the reader will implement? |

Accuracy, good sourcing and a hot topic are table stakes. **Capability is the product.**

---

Educator running a focused 30-minute session for software engineers who are learning AI.
The same page has to work for three entry points — do not pick one and abandon the others:

- **Tool users** have used Claude, Cursor, or ChatGPT on real work. They have not trained a
  model and may not know what a KV cache or a tool schema is. They need the analogy and the
  Monday-morning action first.
- **Builders** have written a skill, an MCP server, or a small agent loop. They need the
  mechanism and the failure mode.
- **Further ahead** already live in evals, serving, or papers. They still want the last third
  to be deep — numbers, ablations, the source. They do not need you to skip the first third.

**Never "skip basics."** Open with the problem in product language. Define every term before
you use it. Then go as deep as the topic deserves. Depth lives in the second half of the
write-up, not in the title or the first paragraph.

**Depth means implementation detail, not more description.** A longer, better-sourced account
of what a release says is still a summary. The reader is depth-satisfied when they could go
write the thing: the actual payload, the handler, the config key, the retry, the cache. If a
session's deepest section could be retitled "what the announcement announced", it is not deep,
however many numbers it quotes.

**CRITICAL: Keep everything practical and software-engineering relevant.** Every topic must
connect to something a working engineer can build, deploy, optimize, or integrate. No pure
theory without application. Code examples should demonstrate real patterns, not toy demos.
Topics like "how to use X in production" or "implementing Y from scratch" beat "understanding
the math behind Z".

**Write for the engineer who has to implement it, never for the ecosystem that shipped it.**
This is not a newsletter about how important a release is. Momentum reporting — "the largest
revision since launch", "adoption was unusually fast", "the SDKs shipped within days", a vendor
advocate quoted approving of it — is advertising copy wearing technical vocabulary, and it is
the fastest way to read as a press release to an audience that is professionally suspicious of
one. Every such sentence is a sentence not spent on what the reader has to type. Mention
adoption only where it decides something ("the Rust SDK is still beta, so a Rust client stays
on the legacy path"), and then say what it decides.

## Session Parameters

- **Model**: this session runs on Opus — the most capable model available, not whatever happens
  to be active. It is pinned in three places so no path can miss it: the unattended daily job
  passes `--model opus` (`run_daily.sh`), and both publishing skills carry `model: opus` in their
  frontmatter, which covers the nested run of this skill in their Step A.
  **The only uncovered path is a direct, manual `/ai-daily-learn` on a smaller model.** If you can
  tell that is the case, say so and stop — ask the user to run `/model opus` and re-invoke, rather
  than generating the session and noting the model in the summary afterwards. That is what
  happened on 2026-08-27: the session was generated on Sonnet, flagged only at the end, and the
  user rejected the article. A flag the reader sees after the work is done costs a whole session.
- **Time budget**: 30 minutes of reading/coding material
- **Output directory**: `~/ai_learning/YYYY-MM-DD/` (today's date)
- **Do not write today's session into `learn/`.** That tree is the evergreen
  two-day track (`#learn`). Daily sessions cite those chapters instead of
  re-teaching the whole on-ramp. Never pick a Learn slug as "today's article."
- **Artifacts**: all 5 files, every session — `topic.md`, `visualize.html` (required,
  not a nice-to-have), `diagram.excalidraw`, `code_example.py`, `articles.md`. Read
  [contract.md](contract.md) before writing. A folder that is only a write-up is not done.
- **Visualizer**: read [visualize.md](visualize.md) and match the newest existing
  `visualize.html` in this repo. The Visualize tab is empty without this file.
- **Journal**: `~/ai_learning/journal.md` tracks all sessions
- **Code**: Pure Python only — no API keys, no external services. Self-contained demos.
- **Excalidraw**: Open at excalidraw.com (drag & drop)
- **Cursor twin**: `.cursor/skills/ai-daily-learn/SKILL.md` runs this same spec from Cursor.
  Edit this file (and visualize.md / contract.md) when the format changes.
- **Feedback loop**: this spec is meant to change. When a session comes back with a note — a
  section that dragged, a title that oversold, a diagram that explained nothing —
  `/ai-daily-learn-feedback` decides whether it is a standing rule and edits the right file here,
  so the same note is never given twice. Do not hand-patch these rules ad hoc; route notes through
  that skill so every change lands in the section that owns it and gets logged.
- **Scope**: local only. This skill writes to disk and stops — it does not commit, push, or
  publish anything. To publish as well, use `/ai-daily-learn-publish`, which runs this exact
  workflow and then pushes the session to GitHub.

## Two tracks, one contract

This skill produces sessions for two tracks. **Everything about how an article is written is
identical on both** — the mission, the ELI5-first ladder, all five artifacts, `## Implementing It`
as the longest section, the glossary, the acceptance test. Only three things differ, and none of
them is a content rule:

| | **Daily lab** (default) | **Frontier** (`--frontier`) |
| --- | --- | --- |
| Sources | Changelogs, docs, engineering blogs, production write-ups | Frontier lab research and papers — see [selection.md](selection.md) |
| Output | `~/ai_learning/YYYY-MM-DD/` | `~/ai_learning/frontier/YYYY-MM-DD/` |
| Cadence | **Never a blank day** | **Skip a thin day** — publish nothing rather than something padded |

Run the Frontier track when the user asks for it by name ("frontier session", "do the frontier
one", `/ai-daily-learn-publish --frontier`). Otherwise run the daily lab.

**On the Frontier track, three steps change and no others:** Step 2 draws from the Frontier source
list and may conclude *nothing today*; Step 4 writes to `frontier/YYYY-MM-DD/`; Step 10 is skipped
(Frontier does not appear in `journal.md`, and never counts toward `--mix`). Steps 5-9 and 11-12
run exactly as written.

**If nothing clears the bar, stop and say so.** That is a successful run, not a failure. Name what
you looked at and why none of it was worth an article. Do not lower the bar to fill the slot — the
one failure that would kill this track is a reader learning the tab wastes their time.

**Never skip the ELI5 because the audience is advanced.** This instinct returns every time you
write for Frontier. Refuse it every time; the reasoning is in [selection.md](selection.md).

## Workflow

### Step 1: Check the Journal

Read `~/ai_learning/journal.md`. If it does not exist, create it:

```markdown
# AI Learning Journal

> Daily 30-minute learning sessions on AI developments.
> Started: YYYY-MM-DD

---
```

Note which categories and topics have been covered.

### Step 2: Select Today's Topic

Read [selection.md](selection.md) before picking. Shortlist **three** candidates, score them
on the audience gates (Monday action, mechanism, 30 minutes, primary source, not a repeat),
and name the two losers in the final summary. Do not grab the first interesting link.

**If the user is in the room and wants a say in what gets written, this is the wrong skill for
Step 2.** `/ai-daily-learn-pick` researches the same sources, puts three worked proposals in front
of them, settles the article *and its content* in conversation, and only then runs Steps 3-12 from
here against the agreed brief. Autonomous selection below is correct for the unattended daily job,
where there is nobody to ask.

If the user provided a topic argument, use that. Otherwise:

0. **Ask what is due. Do not estimate it.**

   ```bash
   cd ~/ai_learning && node build.js --mix
   ```

   It prints the trailing-10 tier mix, the `For` mix, what is **DUE NEXT** and what to
   **AVOID**, straight from every `topic.md`. Writes nothing, runs no code examples, takes a
   second. Pick inside what it says is due, and say in the summary which constraint it gave you.

   Do not count journal entries by hand instead. That is what was being done, and the frontier
   tier drifted to **double its cap** — 32% against a 20% target — while every individual day's
   pick looked defensible. A rule nobody can evaluate on the day is not a rule.

1. Determine which **category** is due — **by tier weight, not flat rotation** (see Category
   Tiers below), inside whatever `--mix` reported:
   - **Tier A ≈ 50%** of sessions (about 3-4 of every 7)
   - **Tier B ≈ 30%** (about 2 of every 7)
   - **Tier C ≈ 20%** (about 1-2 of every 7)
   - Inside the chosen tier, prefer the category least recently covered.
   - If any category has **never** appeared in `journal.md`, it jumps the queue *within its
     own tier* — a new category shouldn't wait out a full cycle, but it also shouldn't break
     the tier weighting to get in.
   - **A `For` layer named as due outranks the category rotation.** `For` is the field that
     tracks the reader; category is a proxy and the proxy leaks. See the reader pyramid at the
     top of [selection.md](selection.md).

   Flat one-at-a-time rotation across all 11 categories is what this replaces, and why: equal
   weighting guaranteed the single most relevant category (Coding Agents & Productivity) got
   1/11 of the coverage. Over the first 20 sessions it appeared **once**, tied for last, while
   GPU quantization and diffusion sampling each got double. The tiers exist to stop that
   arithmetic, not to rank the topics by worth.
2. Use **WebFetch** to scan live sources for the most interesting recent development in that
   category. **Default to non-paper sources.** Changelogs, engineering blogs, docs, release
   notes and real production write-ups should drive most sessions; arXiv is the exception, not
   the default feed:

   > **Paper budget: at most ONE arXiv-led session per 7.** Check `journal.md` before
   > choosing — if a paper drove any session in the last 7, pick a non-paper source this time
   > even if an interesting paper is sitting right there. A paper can still be *cited* as
   > supporting evidence any day; this cap is about what the session is *built on*.

   - `https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md` — canonical Claude Code
     changelog; the single highest-yield source for Tier A
   - `https://www.anthropic.com/engineering` — harness design, agent patterns, written by the
     people who build it
   - `https://simonwillison.net/` — AI engineering blog (practical, tools-focused)
   - `https://www.latent.space/` — AI engineering podcast/blog
   - `https://huggingface.co/blog` — new models, tools, techniques
   - `https://www.deeplearning.ai/the-batch/` — Andrew Ng's weekly roundup; strong for
     research-to-practice framing and catching developments the harness-focused sources miss
   - `https://openai.com/blog`, `https://www.anthropic.com/research`, or `https://x.ai/blog` —
     model provider updates
   - `https://ai.meta.com/blog/` — Meta AI: Llama releases, PyTorch/infra work, and unusually
     detailed production engineering write-ups
   - `https://blog.google/technology/ai/` and `https://developers.googleblog.com/` — Google AI:
     Gemini releases and API changes; the developers blog is the more practical of the two
   - `https://cursor.com/changelog` and the Gemini CLI / Codex release notes — for cross-tool
     comparison rather than single-vendor news
   - `https://news.ycombinator.com/` — **noticing only, never cited.** The front page tells you
     what practitioners are arguing about and which framing will land; then follow the link out
     and build on what it points at.
   - **Papers, subject to the one-per-7 budget above**: `https://arxiv.org/list/cs.AI/recent`
     and `https://arxiv.org/list/cs.LG/recent`
   - Try **WebSearch** first; if blocked (VPCSC error), fall back to WebFetch on the URLs above.
     `openai.com` returns 403 to WebFetch; route around it via the platform changelog or the
     cookbook — and if you reach the announcement through an HN or arXiv mirror, cite the thing
     itself, not the mirror.

   **Every source you build on or cite must pass the admission test** in
   [selection.md](selection.md): you can name the institution or person accountable for the page,
   *and* a senior engineer would accept it as a citation in a design doc. Named practitioners on
   personal domains pass; unvetted personal sites do not, however good the explainer is. Cite the
   published, versioned spec rather than the working repo behind it. This applies to `articles.md`
   just as hard as to the primary source — those links are published.
3. Pick ONE focused topic that fits 30 minutes — specific, not broad
4. Use **WebFetch** on the chosen article/paper URL to get full technical details

**Category Tiers** (11 categories in 3 weighted tiers — always with practical SWE angle).
The tier is about *how far the topic sits from the reader's Monday morning*, not how
sophisticated it is. A Tier A topic can be every bit as deep — it just starts from a problem
the reader already has.

**Tier A — Ship it this week (~50% of sessions).** The reader changes how they work tomorrow.
1. Coding Agents & Productivity — getting more out of the agent tools you already drive every
   day: Claude Code / Cursor / Codex / Gemini CLI configuration, hooks, skills, subagents, MCP
   setup, context and cost management, worktrees, loops, permission modes; what shipped this
   week in their changelogs and whether it changes your workflow. Cross-tool comparison is
   welcome — the reader uses more than one.
2. Building Agents & MCP — *authoring* agent systems rather than operating them: tool schema
   design, MCP servers, orchestration libraries, SDKs, agent architecture.
3. AI Engineering Practices — reviewing, testing and trusting agent-written code; migrations
   at scale; architecture patterns; team workflows for AI-heavy codebases.
4. Evals & Reliability — "does my AI feature actually work?" App-level eval harnesses,
   regression catching, guardrails you ship, output validation. This is the *practitioner*
   half of testing — the research half lives in Tier C.

**Tier B — Understand the machine (~30%).** Not actionable this morning, but it changes a
decision the reader makes this month.
5. New Models & APIs — new model releases, how to use them, API differences, migration guides,
   pricing and routing calls.
6. AI in Production — deployment patterns, serving infra, cost optimization, monitoring, MLOps,
   RAG at scale.
7. Hands-on Techniques — fine-tuning, RAG pipelines, prompt and context engineering.

**Tier C — Frontier (~20%).** The credibility layer: proof this site reads primary sources
rather than press releases. Keep it — but capped, and it still owes the reader a
"What This Means for You" section like everything else.
8. Applied Research — papers with working code, reproducible results, practical implications.
9. AI Hardware for Engineers — **how to actually use the hardware you have or rent**: picking
   an instance type, quantization you can run today, inference-speed wins, memory limits,
   what a given GPU can and can't hold, local-vs-hosted tradeoffs. *Not* novel silicon
   research — a reader should finish able to make a better hardware or serving decision, not
   just having admired someone's chip design.
10. Multimodal Engineering — vision/audio/video pipeline internals, building multimodal apps.
11. AI Safety & Alignment — alignment research, red-teaming findings, model behaviour studies.
    (Shipping guardrails and eval harnesses belong in #4, Tier A.)

**#1 vs #2** — #2 is about *building* agent systems (you are the author of the harness);
#1 is about *operating* the ones you already use (you are the user of someone else's harness).
"How MCP sampling works so I can implement it" is #2. "Three hooks worth adding to
settings.json today" is #1. When a topic could be either, prefer the one whose reader is doing
something different tomorrow morning.

Open Source Tools is gone as a category — it was never a topic, it was a property of one. File
an open-source tool under whatever it actually teaches (the `llm` CLI plugin architecture was a
Tier A tooling piece, not a "look, a tool" piece).

**Accuracy rule for #4** — this category is the one most likely to invent a flag, a config key
or a model ID that does not exist, and a wrong `settings.json` snippet is worse than no session.
Verify every command, flag and file path against the changelog or docs you fetched, and load the
`claude-api` skill before stating any model ID, price or context limit. If you cannot verify a
detail, leave it out rather than guessing.

### Step 3: Deep Research

Use **WebFetch** on the source article/paper to extract full technical content. Then fetch
1-2 more related URLs (blog posts, docs, HN discussion threads) for additional perspective.
Try **WebSearch** for targeted queries too — if it works, great; if VPCSC-blocked, rely on
WebFetch from known sources. Gather enough detail to write a substantive technical summary.

### Step 4: Create Output Directory

```bash
mkdir -p ~/ai_learning/YYYY-MM-DD
```

If today's directory already exists with a completed session (this is a second session on the
same day), use a `-s2` / `-s3` suffix instead: `~/ai_learning/YYYY-MM-DD-s2`. Remember the exact
directory name — later steps refer to it.

### Step 5: Write topic.md

Write `~/ai_learning/YYYY-MM-DD/topic.md`:

```markdown
# [Topic Title — a hook, not a method name]

**Category**: [which of the 11 categories — exactly as written in the rotation list]
**Tags**: [2-4 tags from the Tag Vocabulary below, comma-separated, lowercase]
**Date**: YYYY-MM-DD
**Level**: [Start here | Building | Deeper]
**For**: [Using tools | Building agents | Shipping AI | How models work]
**Hook**: [one plain sentence for the homepage card — no acronyms]
**Engineer's view**: [the thing they have already shipped, named. Renders as the FIRST box on the page, above the ELI5. Max 55 words.]
**TLDR**: [two lines, plain language, at most one number. Renders directly under it.]
**Time to read**: ~10 minutes

## Explain Like I'm 5
[3-5 sentences. ONE everyday analogy, zero jargon, no acronyms at all.]

## The Problem
[3-6 sentences. What breaks today, concretely, and what it costs — the significance argument
lives here now. Open on the specific failure, never on a definition. See the rules below.]

## The Fix: [what to do]
[TOPIC-NAMED, and it must ANNOUNCE the solution rather than presume it — "## The Fix: Borrow a
Mature Project's Test Suite", not "## How a Borrowed Test Suite Works". Use "## The Answer: …" for
an explainer whose payoff is understanding. Then the mechanism, shallow to deep in ONE pass. Prefer ###
sub-headings phrased as the reader's own question at that moment (### Why not just split on
spaces?). Define every term in the sentence that first
needs it; there is no Glossary.]

## What This Means for You
[Three labelled parts — When this matters / How it affects you / What to do about it. The FIRST
action must carry no precondition. REQUIRED on every session, including Tier C.]

## Implementing It
[REQUIRED, and the section with the most prose in the document. Two labelled parts: **The
change** (the lines that change, in fenced blocks, for every role the change touches) and
**How you know it worked** (the verification signal — a number, a log line, an assertion).
See the rules below.]

## When [the thing] Is the Wrong Tool
[TOPIC-NAMED, must start with "When". The honest counter-case: when the old way is still right,
what this costs in complexity, latency, money or operational surface, and what you checked if
the answer is genuinely "nothing". Close on the two or three questions a reader should ask
before adopting it.]

```

**An Explainer variant** may add `## By the End of This You Will` right after the ELI5 — two to
four bullets promising what the reader will understand — when the reader is curious rather than
stuck. That promise is what licenses withholding the answer until later. Everything else, every
artifact and the whole implementation payload, is identical.

**Sub-headings in the mechanism section are the reader's interruption, in their voice.** This is
the single biggest flow win available and it is nearly free. At the moment a reader starts to
doubt, say the doubt out loud as the heading, then answer it.
- ✗ `### Ratio versus count` · `### Budget exhaustion` · `### The chain that just inverted`
- ✓ `### Why not just cap retries per call?` · `### Wait, what happens when the budget runs out?`
`--check` warns when a mechanism section has two or more sub-headings and none is a question.

**The middle sections keep their headings.** A six-section variant that merged `For a Software
Engineer` into the mechanism and collapsed `What This Means for You` was tried on 2026-08-31 and
reverted the same day: it took the middle from three sections and 710 words to two and 524, and
the middle is the part that reads well, because it alternates modes — mechanism, then the
translation into something already shipped, then what to do. The lesson kept is the inverse:
**readability comes from more small units with figures, never from merging sections.**

**Three older sections are gone, and one line replaces them.** If this daily piece assumes
a chapter (tokens, the agent loop, RAG, the harness), put a single sentence in `The Problem` or
the mechanism section linking the matching `learn/<slug>` page — *"New to this? Start at AI
basics → [Context and the harness](#learn/context-and-harness)."* That is what survived of `How
It Connects to What You Know`; its analogy half was always the engineer anchor's job, done
twice. `Try It Yourself` pointed at a tab the reader can already see. `Glossary` is replaced by
defining terms where they are used.

**The acceptance test — apply it to the whole document, not just one section.**

> Could a competent engineer who has never met this topic ship the change from your article
> alone — open the editor, write it, and know whether it worked — without opening the source
> you built it from?

If the honest answer is no, you have written a summary with a code block in it, however long and
however well sourced. This is the bar the whole write-up is measured against; every section below
either serves it or is cut.

You are not filing a report on a development. **You are the senior engineer writing the internal
doc that upskills your team on something they are about to have to use.** That register is the
whole difference: an internal doc names the file, gives the real config key, says what broke last
time, and admits where the approach is wrong. It never pads, because the audience is people whose
time you will have to face on Monday.

### What to borrow from ByteByteGo — and what stays ours

ByteByteGo's AI writing is the reference for *how to explain*, not a template to copy. Take these
four things:

1. **Open on the specific failure, not on a definition.** *"The main problem with standard RAG
   isn't the retrieval or the generation. It's that nothing sits in the middle deciding whether
   the retrieval was actually good enough."* That sentence names the gap before naming the
   technique, and everything after it has somewhere to land. `## The Problem` should read like
   this, and never like a paragraph that begins "Agentic RAG is an approach in which…".
2. **Scaffold through concrete scenarios before the solution.** Walk the reader through the
   ambiguous query, the evidence scattered across three documents, the confident wrong answer —
   then show what changes. A mechanism explained against a failure the reader recognises is
   remembered; the same mechanism explained abstractly is not.
3. **Vary the paragraph rhythm.** Four or five sentences to develop an idea, then a one-sentence
   paragraph to land it. *"This works fine for simple questions with obvious answers."* Our
   sessions drift toward uniform dense blocks, which is what makes them tiring rather than long.
   **This is now enforced, because it was ignored for weeks as advice.** In the on-ramp sections
   (`Explain Like I'm 5`, `The Problem`, the mechanism section) `--check` warns on any paragraph
   over **110 words** or any sentence over **45 words**, and on a `The Problem` written as a single
   block. The caps are deliberately loose — they do not make prose good, they only catch the wall
   of text nobody finishes. A reader gives up *inside* a paragraph, never between two.
4. **Let the diagram carry a step of the argument.** Theirs are load-bearing: the pipeline, then
   the same pipeline as a control loop. Ours (`diagram.excalidraw`, `visualize.html`) should be
   the thing that makes a step click, never a picture of the sentence above it.

**What we do not borrow, because it is the reason this site exists:** ByteByteGo's AI pieces
carry no code and end at understanding. We end at implementation. `## Implementing It` stays the
spine, `code_example.py` stays runnable, every session still keeps its **How you know it worked**
and **When not to**, and the reader is still expected to leave able to build something. Their
closing move — three questions to ask before adopting this — is worth stealing *into* `When not
to`, not instead of it.

The rule in one line: **borrow their clarity, keep our payload.** If a session comes out readable
and elegant and the reader cannot ship anything from it, we have copied the wrong half.

**`## Implementing It` must be the longest section in the document** — measured on **prose,
with fenced code excluded from every section's count**. This is a structural rule with a number
behind it: measured across the first 22 sessions the shape was **97% explanatory prose, 3%
implementation, and zero fenced code blocks in the write-up** — an explainer with an appendix
bolted on. A single required section cannot outweigh nine explanatory ones. Everything else gets
tightened until the implementation is the spine, not the epilogue.

Code is excluded from that measurement on purpose, because the cheapest way to pass the rule
would otherwise be to paste `code_example.py` into the write-up — and **the article is not the
implementation.** The two artifacts have different jobs and must not restate each other:

| | owns | looks like |
| --- | --- | --- |
| `topic.md` → `Implementing It` | the **decisions** — what changes, in which file, for which role, the real config key and function name, how to tell it worked, when not to | the lines that *change*: a config block, a changed handler signature, a payload, a before/after pair |
| `code_example.py` | the **complete runnable artifact** — the whole mechanism end to end, liftable into the reader's own repo | a program that runs and prints something that proves the claim |

So the write-up shows enough code to make each decision concrete and unambiguous, and stops
there. A fenced block long enough to be a program has crossed the line — **cap any single block
in `Implementing It` at 30 lines**, and if a block is a verbatim slab of `code_example.py`, one
of the two is redundant. Both are `--check` warnings. The reader should finish the article
knowing exactly what to type, and open the Code tab to get the finished thing, not to get the
same thing again.

**Every section has a word band — a floor and a cap, fenced code excluded**, both warned by
`--check`. There is no document-wide total any more, and the reason it went is worth knowing
before you are tempted to reinvent it. A single 1,300-word cap ran from 2026-08-27 and worked
exactly as instructed: the spec said the explanatory sections absorb the cut and `Implementing It`
is protected, so four consecutive articles paid the whole trim out of `The Problem` (−48%) and
`What This Means for You` (−37%) while the implementation gave up 23%. The result was dense,
specific articles with nothing left explaining why a reader outside the exact case should care.

| Section | floor | cap |
| --- | --- | --- |
| `Explain Like I'm 5` | 60 | 120 |
| `The Problem` | 190 | 320 |
| `The Fix: <what to do>` | — | 370 |
| `What This Means for You` | 200 | 300 |
| `Implementing It` | 300 | 460 |
| `When <the thing> Is the Wrong Tool` | 150 | 250 |

**A floor is a real rule, not a suggestion.** Under a total, the sections that make an article
*apply to someone* were always the cheapest to cut; a floor is what stops that, so treat a
below-floor warning as the same class of defect as a missing section. **Cut inside the section
that is over** — the mechanism section is the one with a cap and no floor, because that is where
a spec dump lands and a simple topic is allowed to explain itself briefly.

**No space filler.** Every section must carry something no other section has. These are the
patterns that produce padding, and each one is a cut, not a rewrite:
- The same point restated in `The Problem`, the mechanism section and `What This Means for You`.
  Pick the one that owns it. The seven-section order exists to make this hard: the old eleven
  explained the topic four times, so restating was the path of least resistance.
- `The Problem` explaining *that* it matters rather than what it costs or enables.
- A definition given twice — once inline where the term is used and again a screen later. Inline
  is the one that survives.
- Background the reader does not need to make the change — history, org politics, who shipped it
  first, how many stars the repo has.
- Any sentence you could delete without changing what the reader does. Delete it.

**The title says what the reader will understand.** This is the whole article for everyone who
only sees a link — on the card grid, in Slack, on Hacker News. Write it for a curious software
engineer scrolling past, including someone who has only used Cursor and has never read a paper.
If the title needs a glossary, it failed.

**Before you accept a title, read it as that engineer — not as its author.** You already know
what the article is about, so every title you draft sounds clear to you; the only useful test is
whether it lands on someone who does not have that context yet. Stop and ask, out loud if it
helps: *what does this title actually tell me I would be able to do? Is that specific enough that
I would click it over the four other tabs open right now?* If the honest answer is "not really,"
the title is not done, no matter how many of the rules below it technically follows.

The tell that a title needs this pass is a **placeholder word standing in for the real one** —
usually because the real noun or verb felt too plain to be a "title word," when plain is exactly
what makes it land:
- Vague nouns: *"something," "a thing," "a way," "an approach"* — always name the concrete noun
  the article actually delivers instead. `How an AI Code Review Becomes Something CI Can Gate On`
  → `How to Turn AI Code Review Comments Into a CI Gate` reads better for one reason: "a CI Gate"
  replaced "Something," and a CI gate is the literal thing `Implementing It` teaches the reader
  to build.
- Weak or passive verbs: *"becomes," "involves," "relates to," "is about"* — find the verb an
  engineer would actually use in a standup. "Turn X into Y" beats "X becomes Y" because turning
  something into something is an action the reader pictures doing, and becoming is a thing that
  merely happens.
- A title that is accurate but generic enough to fit five other articles — if you could paste it
  onto a completely different session's `topic.md` and it would still basically work, it is
  describing the category, not this piece.

**Default to the explanatory form.** The house style is ByteByteGo's: name the thing and say
plainly what the reader is about to understand about it. It reads as a reference someone would
come back to rather than a post that was timely once, it survives being read six months later,
and it is the same promise the article actually keeps. Four shapes cover nearly everything:

| shape | use it when | examples |
| --- | --- | --- |
| `How X Works` / `How X Does Y` | a mechanism is the subject — the most common case | `How Large Language Models Learn` · `How Agentic RAG Works` · `How a Coding-Agent Hook Decides to Fire` |
| `A vs B` (`: what it decides`) | the session is a real comparison | `Ollama vs vLLM vs SGLang` · `Waymo vs Tesla: Two Ways to Build Self-Driving Cars` |
| `Name: plain-English gloss` | the thing has a name worth teaching | `GraphRAG: How AI Answers Questions Hidden Across Many Documents` |
| `A Guide to X` / `Why X Matters` | a survey or a stance, used sparingly | `A Guide to LLM Evals` |

Note the third shape against the banned one below: the colon is allowed when the tail is **plain
English about what it does for the reader**, and banned when the tail is a formal restatement of
the method. `GraphRAG: How AI Answers Questions Hidden Across Many Documents` teaches; `LUMI:
Tokenizer-Agnostic LLM-Based Lossless Image Compression` announces.

- **A surprise in the title is optional, not the goal.** *This demotes an earlier rule that said
  to lead with the surprise or the cost.* It produced titles that were sharp on the day and
  unreadable as an index — `Nobody Re-Tests Their RAG Chunk Size — One Grid Search Cut It 88%`
  works once, in a feed. Keep the number and the surprise; put them in `**Hook**`, in the first
  paragraph, and in `Key insight`, where they have room to be true. If a surprise fits the
  explanatory form without straining, keep it there too: `How a Coding-Agent Hook Decides to Fire
  (And Why It Still Isn't a Gate)` is both.
- **Ban academic formatting.** No `Method Name: Formal Description via Mechanism`. That pattern
  is why sessions feel all over the place. Compare — and note the ✓ column now prefers the
  explanatory form:
  - ✗ `Truncated Jump Sampling: Training-Free Diffusion Acceleration via Endpoint Decodability`
    → ✓ `How Diffusion Models Skip Steps Without Retraining`
  - ✗ `LUMI: Tokenizer-Agnostic LLM-Based Lossless Image Compression`
    → ✓ `How an LLM Compresses Images Better Than PNG`
  - ✗ `Prefill-Pressure Adaptive Scheduling: Why max_num_batched_tokens Has No Right Value`
    → ✓ `How vLLM Decides How Many Requests to Batch`
  - ✗ `Deterministic Verification Gates for Tool-Using LLM Agents`
    → ✓ `How to Gate an Agent's Tool Calls Behind a Check It Can't Talk Past`
- **Questions are welcome** when the question is one the reader has actually asked:
  "Why Does My Agent Cost $30 Some Days and $3 Others?" A question they have never wondered
  is just a worse statement. Prefer the `How` form when both work — the question form dates
  faster.
- **No glyph only one product's users can read.** A title may quote code, but only code whose
  meaning survives a reader who has never opened that product. `Bash(rm *)`, `min_pixels`,
  `--max-num-seqs` and `PreToolUse` are in-house vocabulary: to the Cursor-only engineer scrolling
  past, they are noise where the surprise should be. Say what the thing *does* and let the glyph
  appear in paragraph one.
  - ✗ `Bash(rm *) Even Catches echo $(rm -rf /). It's Still Not a Gate.`
    → ✓ `How a Coding-Agent Hook Decides to Fire (And Why It Still Isn't a Gate)`
  A good test: if the `Hook` line would work better as the title for someone who has only used
  Cursor, the title lost and the hook won — use the hook.
- **One clause, one subject.** This is the most common structural defect and it reads as
  "confusing" without the reader being able to say why. A title with two clauses joined by a
  purpose conjunction — *"How to X **so that** Y can't Z"* — usually gives each half a **different
  subject**, and the reader has to build the bridge between them unaided. That unbuilt bridge is
  the disconnected feeling. The reference publications almost never do this: *"Why is Kafka so
  fast?"*, *"How does ChatGPT work?"*, *"How to Choose a Message Queue?"* are all one clause with
  one subject.
  - ✗ `How to Test an AI Agent So a Broken Layer Can't Hide` — subject of the first half is *you*,
    of the second half is *a broken layer*; "layer" is the source paper's word, undefined to a
    reader scrolling past; and "hide" is given no object, when the thing it hides *from* (the
    passing score) is the entire idea.
    → ✓ `How to Catch the Broken Step Your Agent's Tests Miss`
  Two tests before accepting a title: **do both halves share a subject or an object?** and **does
  the second half introduce a noun the reader has not met?** If a purpose clause feels necessary,
  the real subject of the article usually has not been named yet — name it, and the title collapses
  to one clause by itself.
- **Friendly, plain, curious.** Contractions are fine. Speak like a smart colleague who found
  something interesting, not like an abstract.
- **Never oversell.** A hook the article doesn't pay off is the fastest way to lose this
  audience — they are professionally suspicious of hype. Surprising *and true*.
- Keep it under ~70 characters where you can; a name the reader can repeat beats a name that
  covers every nuance. `**Hook**` on the card and the write-up carry the precision.

**`**Level**` and `**For**`** — required. Pick exactly one of each from the lists in the
template.

**Aim for 3 `Start here` / 6 `Building` / 1 `Deeper` per ten sessions**, and treat `Deeper` as
the rationed one. The measured mix was 2 / 4 / 4 — `Deeper` tied for the most common level on a
site whose widest reader has never trained a model. `Deeper` is a budget, not a compliment to
the topic; spend it when the mechanism genuinely cannot be shown any other way.

Level is runway, not prestige:
- **Start here** — a tool user can finish the first third and act on it
- **Building** — assumes they have shipped a skill, tool, or small agent
- **Deeper** — the machine under the tools; still opens with an analogy
**For** is the job: Using tools · Building agents · Shipping AI · How models work.

**`**Hook**`** — one sentence, no acronyms, no paper names. This is the homepage card blurb.
If someone who has used Cursor for a week cannot repeat it, rewrite it.

**`**Tags**`** — the cross-cutting facet. A session has exactly one **category** (what it is
*about*, and what decides the rotation) and 2-4 **tags** (what it *touches*). Tags are what let a
reader who arrived for one article find the other four that share a concern with it, so pick them
for what someone would plausibly filter by, not to describe the article exhaustively.

- **Pick only from this vocabulary**, lowercase, comma-separated. The reader validates against it
  and `build.js --check` warns on anything else:
  - *technique* — `rag`, `fine-tuning`, `quantization`, `caching`, `context-engineering`,
    `prompt-engineering`, `reranking`, `distillation`
  - *concern* — `cost`, `latency`, `reliability`, `security`, `benchmarks`, `observability`
  - *surface* — `agents`, `mcp`, `coding-agents`, `multimodal`, `embeddings`,
    `inference-serving`, `training`, `transformers`
  - *use-case / provenance* — `from-scratch`, `paper`, `production`, `interview`
- **Never invent a tag inline.** If a session genuinely needs a facet that does not exist, add it
  to the `TAGS` array in `build.js` *first*, then use it — otherwise the lint and this skill
  disagree and the tag silently fails validation. A vocabulary that drifts into
  `fine-tuning`/`finetuning`/`Fine Tuning` stops working as a filter, which is the whole point.
- **Don't restate the category as a tag.** An "Evals & Reliability" session tagged `reliability`
  adds nothing; tag it for what it *also* touches (`benchmarks`, `coding-agents`, `production`).
- Use `paper` when the session is built on a paper — it pairs with the paper budget in Step 2 and
  makes the Tier C share visible at a glance.

**The reader.** A working software engineer who is *learning* AI and intends to apply it
practically. Assume fluency in general software engineering — caching, padding, schedulers,
quantization, compilers, batching, indexes, back-pressure. Do **not** assume fluency in AI
internals, and do not assume they can decode an acronym from context. The framing sections
(the Engineer's view box, Problem, What This Means for You) exist because the deep sections
alone lose this reader.

**`## Explain Like I'm 5`** — leads the document deliberately, because a reader who bounces off
paragraph one never reaches the good part.
- One concrete, everyday analogy carried all the way through. Do not mix metaphors.
- Zero jargon and zero acronyms. If a term is unavoidable, you picked the wrong analogy.
- 3-5 sentences. Land the *shape* of the problem, not the mechanism.
- It must still be **true** — a simplification, never a fiction you walk back later.

**`## The Problem`** — names the actual pain before the reader is shown the fix for it. A
solution without its problem reads as cleverness for its own sake; this is what keeps a deep
topic from feeling like showing off.
- Name what was broken, wasteful, slow, expensive, or simply unsolved — concretely, with a
  number if the source has one ("teams were losing 40% of their context window to padding").
  Who had this problem, and what were they doing about it before (usually: something manual,
  wasteful, or nothing).
- This is the pain the paper/release exists to fix — not a restatement of the ELI5 analogy.
  If you can't state the problem in plain terms, you don't understand the topic well enough
  to write the rest of the session yet — go back to Step 3.
- **Open on the specific failure, not on a definition.** *"The main problem with standard RAG
  isn't the retrieval or the generation. It's that nothing sits in the middle deciding whether
  the retrieval was actually good enough."* That sentence names the gap before naming the
  technique, so everything after it has somewhere to land. Never *"X is an approach in which…"*.
- **Significance lives here now**, in engineering terms and never industry ones. Compare to
  prior work by what it *costs or enables* — bytes, latency, money, a class of bug that stops
  happening — not by how it was received.
- **No momentum reporting.** How fast the ecosystem adopted it, how large the release is next to
  past releases, and who publicly praised it are facts about a market, not about a system. A
  named person's quote earns its place only when it carries a technical claim the reader can go
  check; never as an endorsement.
- **Never cite another vendor's changelog as proof the topic matters.** That someone else shipped
  a comparable feature says the category is popular, which the reader already assumed by clicking.
  It says nothing about the mechanism, and it is the exact sentence that makes a session read like
  a launch post.
  - ✗ `Hooks are becoming the standard way teams put policy around agents. Cursor shipped custom
    modes in August; 2.1.243 alone added modelPicker and managed-settings visibility. The
    governance surface is growing fast.`
  - ✓ `Fail-open is the correct default for a workflow hook — one that failed closed on an
    unparseable command would wedge the agent constantly. The mistake is the reader's: the syntax
    is borrowed from the permission system, the file is the same file, and the mental model comes
    along for free.`
  `build.js --check` warns when this section contains a version string, a rival product name, or
  adoption language, so this one is caught rather than trusted.
- **Name the fix before the section ends. Never hand off on a tease.** The reader has just been
  given three or four paragraphs of what is broken; if the section closes without saying what the
  answer *is*, they carry the whole problem into the next section unresolved, and the article
  reads as long no matter how few words it has. This was diagnosed on 2026-08-31 from an article
  whose `The Problem` was 119 words — the shortest in its run — and which the site's owner still
  reported as too long, because it ended on "What worked was upstream of all of it" and then spent
  another ninety words on benchmark setup before naming anything. Length was not the defect;
  **latency to the answer** was.
  - ✗ *"What worked was upstream of all of it."* — a direction, not a thing. Nothing is named.
  - ✓ *"The fix: stop grading the agent once, and grade each step separately."* (2026-08-27)
  - ✓ *"What worked was the step before any of that: deciding what gets written down at all."*
  One plain sentence naming the mechanism is enough — the section that follows explains it. If the
  fix genuinely cannot be stated before the mechanism is built up, say so in a clause and open the
  mechanism section with it instead; what is not allowed is the reader reaching a `###`
  sub-heading still not knowing what the article proposes.
- Criticism belongs here at full strength. If there is a real objection ("has this just
  rediscovered REST?"), state the strongest version of it and answer it with a mechanism.
- 3-6 sentences. This section motivates; section 3 explains.
- **Never one block.** This is the section where a reader decides whether to stay, and a 180-word
  monolith at position two loses them before the article has made its case. Develop the failure,
  then land it in a short paragraph of its own — two or three sentences, then one. `--check` warns
  on a single-block `The Problem` and on any paragraph over 110 words.

**`## The Fix: <what to do>`** — the solution, named in the heading, then the mechanism behind it.
`## The Fix: Pin the First Four Tokens`, `## The Fix: Borrow a Mature Project's Test Suite`. This
is `What It Is` and `Key Technical Details` merged into one pass, because as two sections they
explained the same thing twice at two depths — and it is now titled for the answer rather than for
the mechanism, so a reader scanning the headings meets the fix instead of a description of one.

- **One ladder, climbed once: what it is → how it works → the detail an implementer needs.** The
  old shape re-entered the topic four separate times; this one enters it once and keeps going.
  Depth is not reduced — only the re-introductions are.
- **Use `###` sub-headings named for their subject**, the way a reference article does: `###
  Byte Pair Encoding`, `### The Fail-Open Path`. Never `### Details` or `### Background`. A
  reader scanning the sub-headings should learn what this mechanism is made of.
- **Open on the concrete instance, not the abstraction.** Show `"Hello world!"` breaking into
  tokens, then say what a token is. The example first, the definition second.
- **Every detail must earn its place against the reader, not against the source.** The test, and
  it is the sharpest one in this file: *does this detail change a decision the reader makes,
  enable an action they can take, or alter an outcome they care about?* If not, cut it — however
  accurate it is, however prominent it was in the source. This is the rule that separates depth
  from a spec dump, and a spec dump is the single most common way a session that opens well goes
  boring by the middle.
- **Never transcribe the source system's taxonomy.** A paper or release describes *its own*
  architecture exhaustively; the article borrows only the parts it actually uses. Enumerating
  eight components of a system the reader will never touch is maximally specific and minimally
  useful — it reads as diligence and lands as tedium.
  - ✗ "The paper decomposes the agent into eight named layers: **ontology** (turning words into a
    canonical product ID), **intent** (a signal vector), **routing** (which handler is invoked),
    **decomposition** (splitting into sub-goals), **escalation** (when to involve a human),
    **safety** (price and allergen checks), **memory** (prior session context), and a cross-cutting
    **envelope/defense** band."
  - ✓ "The paper splits its agent into eight layers; three matter here. **Escalation** decides when
    an order needs a human — and it is the one that broke. **Ontology** resolves a product ID, and
    everything downstream depends on it. The other six are in the paper."
  The ✓ version is shorter, names the same source, and every noun in it does work later in the
  article. If a term never appears again after you define it, it should never have been defined.
- **Define every term in the sentence that first needs it.** There is no Glossary any more, so a
  proper noun the reader has not met (NaViT, DeepStack, M-RoPE) gets a four-word gloss on the
  spot — "NaViT's patch-n-pack (packing many images into one sequence)". A term that cannot be
  glossed in a clause without derailing the sentence is a term this article should not be using.
- **Lead each point with what it means, then give the constants.** "One visual token is a 28×28
  pixel block — that's `patch_size=14` with `spatial_merge_size=2`" reads; "`patch_size=14`,
  `spatial_merge_size=2`; 14×2=28" does not.
- **Order foundational → specialist**, never in the order you happened to research it.
- **Scaffold through the failure before the fix.** Walk the ambiguous query, the evidence split
  across three documents, the confidently wrong answer — then show what the mechanism changes. A
  mechanism explained against a failure the reader recognises is remembered; the same mechanism
  explained abstractly is not.
- Depth is not the problem and never gets reduced. The entry to it was the problem.

**Section 3's heading is the solution, stated.** Reading only the headings must give
problem → fix → how it works → what to do. The old `How <the thing> Works` form was reported as
unclear twice, on different articles, because it explains a mechanism to a reader who has not been
told the mechanism is the answer. `--check` enforces the `The Fix:` / `The Answer:` form.

**State the fix in `The Problem`; do not narrate it.** The sentence that introduces the solution is
an instruction, not a report of who found it.
- ✗ *"He took the test suites of well-known packages and had the AI rewrite them against his API."*
- ✓ *"**Borrow your oracle: take the test suite of a mature project, have the agent port those
  tests onto your API, and treat every failure as a question.** Dumpleton did this with packages
  that lean on `unittest.mock`."*
Attribution follows the claim; it never replaces it.

**`**Engineer's view**`** — the first thing on the page, and the site's most distinctive move: no
comparable publication translates AI topics into engineering the reader has already done. It was a
section at position four until 2026-09-02, which was late for it.
- **Name the thing they have shipped, explicitly.** "This is a configuration precedence bug." "This
  is head-of-line blocking." "This is loop interchange." "This is a cache key that does not include
  everything the result depends on."
- **One analogy, 55 words, and stop.** It is the hook, not the essay. The consequence belongs in
  `What This Means for You`, and the number worth holding onto goes there too.
- **`## For a Software Engineer` is retired** — the box replaces it. Do not write both.

**`**TLDR**`** — two lines under the box, plain language, at most one number. It inherits the old
`Key insight` rules: three sentences at most, no acronyms or config identifiers, and sentence two
continues sentence one rather than starting the evidence.

**`## What This Means for You`** — three labelled parts, **When this matters** / **How it affects
you** / **What to do about it**, because the labels are what make it scannable.

- **Graduated actions, and the first one must carry no precondition.** This is the rule that
  fixes the narrowness measured on 2026-08-31, where every recent article opened on a compound
  condition ("you maintain an MCP server *and* have a tool that exceeds your proxy timeout") and
  left everyone else with nothing. Give the thing anyone can do today first — a five-line config
  file, a `grep`, one question to ask the model — then the deeper move for the reader already in
  the specific case.
  - ✗ *"Add the poll branch to your client before you add tasks to your server."*
  - ✓ *"At the end of a session, ask the model for the five things worth remembering and append
    only those to your notes file. That is consolidation, done by hand, and it is most of the win.
    When you are ready to automate it, …"*
- **At least one item must be a change, not an audit.** "Go check whether your client honours the
  TTL" tells the reader to open a file, not what to write once they are in it. An audit is a fine
  *first* step, but it owes its second half — "and if the answer is bad, here is the fix" —
  pointing at `## Implementing It` rather than restating it.
- **Required on every session, including Tier C.** If the honest answer is "this will not affect
  your work for a year", say that and name the signal to watch for. **Never invent applicability**;
  overstating relevance is worse than admitting there is little, and this section is the site's
  credibility rather than its marketing.
- Write it in second person, plainly. This is the least academic section in the document.

**`## Implementing It`** — the section that makes this site worth reading instead of the
changelog it came from. Every section above explains the change; this one shows the code that
lives with it. Required on every session.

- **Put real code or a real payload in a fenced block, in `topic.md` itself.** Pointing at
  `code_example.py` does not discharge this — most readers never open the Code tab, and nobody
  reading on a phone is going to run Python. The block belongs next to the sentence that
  motivates it.
- **Show the lines that change, not the program that contains them.** This is the other half of
  the rule above and the one that gets overshot: the article is judged on whether an engineer
  can act, not on whether the article compiles. Give the config block, the changed signature,
  the payload, the before/after — and let `code_example.py` carry the runnable whole.
  - ✗ a 60-line script in the write-up that the Code tab then repeats verbatim
    → ✓ the eight lines the reader edits, then "the full matcher, with a corpus to test your own
    rules against, is in `code_example.py`"
  - A single fenced block over 30 lines, or one that is a verbatim slab of `code_example.py`,
    warns in `--check`.
- **Prefer a before/after pair** whenever something changed: the request as you sent it last
  month and as you must send it now; the handler as it was and as it must be. A diff is the
  fastest way an engineer confirms they understood.
- **Cover every role the change touches, not only the one the announcement was written for.**
  Almost every change moves work between two parties — client and server, producer and consumer,
  caller and callee, training and serving — and a release note is written by one of them, about
  their own half. Name both sides and give each its own code:
  - ✗ "servers no longer need a session store, and clients should honour the cache header"
    → ✓ **Server:** the handler that returns `405` on `GET` and rejects a header/body mismatch
    with `-32020`. **Client:** the TTL cache keyed on `cacheScope`, the `InputRequiredResult`
    retry loop, the version probe and its fallback.
  - If one side genuinely has nothing to do, say so in a sentence. Silence reads as an omission,
    because it usually is one.
- **Name the file and the function, not the intention.** "Add a check" is not implementable;
  "in your client's `list_tools()`, key the cache on `(server_url, cacheScope)` and store
  `fetched_at + ttlMs`" is.
- **Say what breaks if they get it wrong**, with the signature they would actually see — the
  error string, the log line, the metric that moves. A rule with a visible failure mode gets
  followed; one without gets skipped.
- Use the real API, field and config names throughout. Never write pseudocode for something that
  has an actual name in the source.
- If the honest answer is that nothing is implementable yet (a paper with no released code),
  implement the *mechanism* from the paper in a dozen lines instead — that is what "implementing
  Y from scratch" means here.

**Two labelled parts, in this order.** The counter-case used to be the third and is now section
7, a heading of its own — it was the part readers most needed and the part most easily buried at
the end of a long section:

- **The change** — the code itself, in fenced blocks, for every role the change touches. This is
  the bulk of the section. Real API, field and config names throughout; name the file and the
  function, not the intention.
- **How you know it worked** — the verification signal, concretely. The number that should move
  and in which direction, the log line that should appear or stop appearing, the assertion to add,
  the command to run and what its output looks like when correct. *"Log how often your client
  calls `tools/list` in one session; it should be close to 1, not close to your tool-call count"*
  is a verification. "Make sure caching is working" is not. **An engineer who cannot tell whether
  the change took has not been given an implementation** — they have been given a suggestion.

Length follows from the structural rule above: this section has the most **prose** in the
document. If it does not, tighten the explanatory sections rather than padding this one — padding
here fails the same anti-filler test as padding anywhere else, and padding it with pasted code
fails on top of that, because code is not counted and the article is not the implementation.

**`## When <the thing> Is the Wrong Tool`** — the counter-case, closing the document, and the
second heading named for the topic: `## When a Hook Is the Wrong Tool`, `## When Not to Fine-Tune`.
- **The honest counter-case and what the change costs.** When is the old way still right; what
  does this add in complexity, latency, money or operational surface; which constraint makes it
  a bad idea. A technique with no stated downside reads as marketing, and the audience is
  professionally suspicious of it. If it genuinely has no downside, say what you checked.
- **Close on the two or three questions a reader should ask before adopting it.** This is the
  move the reference publications end on, and it is the right last thing in the reader's head:
  not "wasn't that interesting" but "here is how I decide".
- It is a section, not an appendix. It earns a heading because it is the part readers most need
  and the part that was most easily buried at the end of `Implementing It`.

**No Glossary.** Terms are defined where they are used — see the mechanism-section rules above.
A 305-word appendix competing with the code for attention was the thing this replaces; the
discipline it enforced (every acronym and domain term gets explained, including the ones that
feel obvious — token, prefill, KV cache, patch, DPI) is unchanged, it just happens inline. For
any unit the session turns on, still say **what it buys you**, not what it stands for: DPI is
not "dots per inch", it is "how much detail survives — 93 dpi means 6pt text is ~8 pixels tall,
which is why small print gets misread."

### Step 6: Write code_example.py

Write `~/ai_learning/YYYY-MM-DD/code_example.py`. **The test is not whether it runs — it is
whether an engineer can lift it into their own repo.** A script they execute once, watch print
something interesting, and close has taught them nothing they can use on Monday.

**This file completes the article; it does not repeat it.** `Implementing It` gave the reader the
decisions and the lines that change — this is where the whole mechanism actually exists, running,
with the knobs at the top for them to point at their own inputs. If someone could read the article
and then find nothing new in the Code tab, this file has not done its job; if they could skip the
article because this file contains it all, the article has not done its.

- **Write the thing, not a demonstration of the thing.** The client that builds and validates the
  request, the cache that honours the TTL, the retry loop, the scheduler, the chunker — in the
  shape it would take in real code, with the names it would really have. Byte counts and cost
  curves are a *result* the implementation prints, never the whole script. A script that only
  measures a change tells the reader what to expect; one that implements it tells them what to
  write.
- **Structure it so one piece is liftable.** A reader should be able to copy one function or class
  out and have it work. Put the reusable core at the top as a named function or small class, and
  the demonstration — the scenario, the loop over inputs, the printing — below it in `main()`.
  The same logic as a 120-line top-to-bottom script is a demo; with a `def build_request(...)` at
  the top it is a snippet they will paste into their own code today.
- **Comment the decisions, not the syntax.** `# check the TTL before the cache read, not after —
  a stale hit is worse than a miss here` transfers judgement. `# loop over items` is noise. This
  is most of what separates code that runs from code that teaches.
- **The output must prove the article's claim, not restate it.** Print the numbers the write-up
  quotes, labelled, so the reader watches the claim get verified instead of taking it on trust.
  If the article says 34 KB against 383 KB, both appear in the output.
- **Put the interesting parameter at the top, named, with a comment saying what changes when they
  change it.** Learning happens when a reader edits one number and watches the conclusion move —
  make that edit obvious and one line long.
- **No API keys**, stdlib first — this runs in a browser sandbox. Include a docstring saying what
  it implements and how to run it.
- **Under 150 lines**, and `build.js --check` warns above it. If it does not fit, the topic was
  too broad; cut the demo furthest from the one mechanism, do not raise the limit. The combined
  "and now all of it together" finale at the bottom is almost always the cut.
- For a topic with genuinely nothing to implement (hardware economics, a market shift), implement
  the *model* — the cost function, the comparison — as something they can re-run against their own
  numbers. "Analysis code" still has to be code they can point at their own situation.
- **Library dependencies**: if the script needs numpy, matplotlib, or other packages, add a **`# REQUIRES: numpy==1.24.3, matplotlib==3.7.1`** line in the first few comments (exact versions, comma-separated). The reader uses this to auto-install libraries when running the code in the browser. Prefer stdlib whenever possible; use external packages only when essential.

### Step 7: Generate diagram.excalidraw

Run the generator script:

```bash
# Resolve the generator wherever this skill is installed from. The plugin copy is
# authoritative; the others cover a personal install or a direct repo checkout.
GEN=""
for CAND in \
  ./.claude/skills/ai-daily-learn/scripts/generate_excalidraw.py \
  "${AI_LEARNING_DIR:-$HOME/ai_learning}/.claude/skills/ai-daily-learn/scripts/generate_excalidraw.py" \
  ~/.claude/plugins/tp-mcp-config/skills/ai-daily-learn/scripts/generate_excalidraw.py \
  ~/tp_claude/plugins/tp-mcp-config/skills/ai-daily-learn/scripts/generate_excalidraw.py \
  ~/.claude/skills/ai-daily-learn/scripts/generate_excalidraw.py ; do
  [ -f "$CAND" ] && { GEN="$CAND"; break; }
done
[ -n "$GEN" ] || { echo "generate_excalidraw.py not found; use the Step 7 JSON fallback"; }

python3 "$GEN" \
  --title "Topic Title" \
  --subtitle "Brief subtitle" \
  --concepts '["Concept 1|Description 1", "Concept 2|Description 2", ...]' \
  --flow '["Step A", "Step B", "Step C"]' \
  --visuals '[{"type": "stack", ...}, {"type": "rows", ...}]' \
  --category "Category Name" \
  --output ~/ai_learning/YYYY-MM-DD/diagram.excalidraw
```

Provide 4-8 concepts as `"Name|Description"` pairs. Provide 3-6 flow steps if applicable.

**`--visuals` is the part that makes the diagram worth opening, so always provide 2-3 panels.**
`--concepts` is a terse grid and `--flow` is a pipeline strip; neither shows a *mechanism*. A
visual panel does, by making the shape of the thing carry the argument — a quantity compounding
across steps is drawn as a growing stack, a change that cascades is drawn as coloured segments
where the damage spreads, a counterintuitive ranking is drawn as bars you can compare by length.
Run the generator with `--help`, or read its module docstring, for the three panel types and
their exact JSON.

Pick the panels from *what the article argues*, and pull the numbers from the ones
`code_example.py` actually prints, so the diagram and the code agree.

**Never render a paragraph of prose into the diagram.** A wall of sentences inside a rectangle
is not a diagram — if a point cannot be drawn, it belongs in `topic.md`, which already explains
the article at length. The reader should understand the mechanism from the shapes before
reading a single label.

If the script fails, generate the Excalidraw JSON directly using this element format:
- Rectangle: `{"id":"r1","type":"rectangle","x":100,"y":100,"width":300,"height":80,"strokeColor":"#1e1e1e","backgroundColor":"#a5d8ff","fillStyle":"solid","strokeWidth":2,"roughness":0,"opacity":100,"roundness":{"type":3},...}`
- Text: `{"id":"t1","type":"text","x":110,"y":120,"text":"Content","fontSize":20,"fontFamily":5,"textAlign":"center","containerId":"r1",...}`
- Arrow: `{"id":"a1","type":"arrow","points":[[0,0],[100,0]],"startBinding":{"elementId":"r1"},"endBinding":{"elementId":"r2"},"endArrowhead":"arrow",...}`
- Wrapper: `{"type":"excalidraw","version":2,"source":"https://excalidraw.com","elements":[...],"appState":{"viewBackgroundColor":"#ffffff"},"files":{}}`

### Step 8: Generate visualize.html (required)

**Do not skip this step.** A session without `visualize.html` has no Visualize tab.

Read [visualize.md](visualize.md) and open the newest existing `visualize.html` in this repo
before writing. Then write `~/ai_learning/YYYY-MM-DD/visualize.html`: a custom interactive
model of the article's central mechanism. This is not a decorated summary and not a copy of
the Excalidraw diagram. The reader should be able to change one or two meaningful inputs and
watch the article's claim emerge. Pull constants and headline results from `topic.md` and
`code_example.py`; never invent data merely to make the interaction dramatic.

Use the interaction shape that fits the mechanism:
- **Pipeline/budget** — sliders or toggles change flow, token use, latency, cost, or failure rate.
- **Matrix/representation** — heatmaps, quantization grids, bit counts, or compression state.
- **Decision/eval** — policy toggles change accepted/rejected actions, score, or confound.
- **Search/serving** — sweep a threshold or load and show the winner/inversion/frontier.
- **Agent/tool system** — enable components and trace discovery, dispatch, validation, or trust.

Hard artifact contract:
- Complete standalone HTML/CSS/vanilla JavaScript; no React/JSX, package install, CDN, API key,
  fetch/XHR/WebSocket, external font, external image, or other network dependency.
- Include `<!doctype html>`, `<title>`, viewport metadata, and one root with
  `data-visualizer="<session-id>"`.
- Include this restrictive CSP:
  `default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'`.
- Match the reader's dark visual language, but make the interaction topic-specific. Include a
  clear mechanism, live numerical readout, concise state explanation, meaningful controls, and
  Reset. Use deterministic seeded data where simulation is needed.
- Controls must be labelled and keyboard-accessible; layout must work on a phone; honor
  `prefers-reduced-motion`; cap timers/loops and clean them up.
- Report height initially and whenever layout changes:

```javascript
function reportHeight() {
  parent.postMessage({
    type: "adl-visualize-height",
    height: document.documentElement.scrollHeight
  }, "*");
}
addEventListener("load", reportHeight);
new ResizeObserver(reportHeight).observe(document.documentElement);
```

Run a JavaScript syntax check before considering the artifact complete. The reader loads it only
when the Visualize pane opens, inside `sandbox="allow-scripts"` without same-origin, popups, forms,
or storage access.

### Step 9: Write articles.md

Write `~/ai_learning/YYYY-MM-DD/articles.md` with 3-5 curated articles from WebSearch:

```markdown
# Further Reading: [Topic Title]

## Articles

### 1. [Article Title](URL)
**Source**: [publication] | **Date**: [date] | **Read time**: ~X min
> [2-3 sentence summary]

### 2. ...

## Papers (if applicable)

### [Paper Title](arxiv URL)
**Authors**: [names] | **Published**: [date]
> [2-3 sentence summary]
```

**Curation is teaching.** You are handing your engineers the three or four things worth their
next hour out of the hundred published this week — every link earns its place by what it makes
the reader *able to do*. A link that is merely *about* the topic is filler with a URL on it.

- **Write each summary as what they will be able to do**, not what the piece covers.
  - ✗ "A deep dive into the caching semantics of the new spec."
  - ✓ "Walks through building a TTL cache against a real server, including the invalidation case
    most clients get wrong. Read this before you write your own."
- **Say who it is for and when to read it.** "Read first if you maintain a server." "Skip unless
  you are debugging this today." "The reference to keep open while you implement." A reading
  order is worth more to an engineer than a fifth link.
- **At least one link must be something they can open in an editor** — a repo, a reference
  implementation, a cookbook page, a spec with worked examples. A list of five essays teaches
  reading, not building.
- **Prefer the vetted source. Rank by teaching value only between sources of equal standing.**
  Admission (can you name who is accountable?) is the floor; standing is still a tiebreaker above
  it. Given a choice, take the first-party doc, the spec revision, the lab's engineering post or a
  named practitioner with a public track record over a post by an engineer nobody can place —
  **avoid that flow wherever an alternative exists.** An unknown author earns a slot only when the
  post carries its own strong evidence: a reproducible benchmark, a public repo, production
  numbers, a method you could re-run. A precise-sounding post with no evidence behind it is the
  weakest link on the page, not a scrappy find, and "it explained it well" is not evidence.
- **Never pad to five.** Three excellent links beat five where the last two were symmetry.

Slots to fill, in priority order: primary source · the best mechanical explanation · one
genuinely hands-on thing · one wider-context piece.

**Every link must pass the admission test** — see [selection.md](selection.md). No exceptions for
the basics slot: when a session assumes a concept (attention, embeddings, LoRA, calibration, the
agent loop), the on-ramp is this site's own `learn/` track, linked inline in `topic.md` as
`#learn/<slug>`, then a Tier 1 conceptual doc or a Tier 3 named practitioner. There is no
third-party explainer site you are obliged to include, and there never was a good reason to fill
that slot with one.

Good candidates when they've covered the topic:
- `deeplearning.ai/the-batch` — the industry-analysis slot; connects a development to the
  broader research trend rather than just reporting the release.
- `ai.meta.com/blog` — Meta AI; strong for the practical-tutorial and primary-source slots on
  Llama, PyTorch and serving-infrastructure topics, and their production write-ups tend to
  carry real numbers rather than announcements.
- `blog.google/technology/ai` and `developers.googleblog.com` — Google AI; the primary source
  for anything Gemini, and the developers blog is usually the one with runnable detail.

Same spirit as the source rule in Step 2: **favour engineering write-ups, docs and changelogs
over papers** here too. The `## Papers` block is optional — use it when a paper genuinely is the
primary source, not to make the list look rigorous.

### Step 10: Update the Journal

Append to `~/ai_learning/journal.md`:

```markdown
## YYYY-MM-DD — [Topic Title]
- **Category**: [category name]
- **Key insight**: [three plain sentences: the surprise, its consequence, the takeaway — see below]
- **Code**: `YYYY-MM-DD/code_example.py` — [what it demonstrates]
- **Articles**: [count] articles collected
```

**`Key insight` is a hook, not a summary.** The reader renders it in a highlighted box at the top
of the Overview pane — *above* `Explain Like I'm 5` — so it is the first thing anyone sees, and a
dense one cancels out every on-ramp below it. The homepage card uses `**Hook**` from `topic.md`,
not this field — keep both plain. It has been drifting into 200-word jargon walls; that is the
single most daunting thing on the page.

**Each of the three sentences has a job, and the second one is where these go wrong.** This was
diagnosed on 2026-08-31, when the owner reported getting lost at the second line across six
consecutive entries. All six were inside the size caps; the defect was that sentence two had
become the *evidence* sentence — the place the article's proof, quantities and vocabulary landed.
Evidence cannot go there. This box renders above `Explain Like I'm 5`, so at sentence two the
reader has met none of the article's terms, and a sentence that argues instead of continuing is
the moment they stop.

| sentence | its job |
| --- | --- |
| 1 | **The surprise**, in words a stranger can read: what happened, or what turned out not to be true |
| 2 | **The consequence** — the same subject, carried one step further. Not the proof, not the numbers, not the mechanism |
| 3 | **The takeaway**: what it means, in one line |

Sentence two must **continue sentence one's subject and introduce no noun that needs explaining**.
If it names something the reader has not met, it belongs in the write-up.

- ✗ *"Three of five retrieval signals scored worse than not having them, and tuning the weights
  with reinforcement learning changed the result by exactly nothing."* — four quantities and two
  unexplained terms, arriving before the reader has been told what a retrieval signal is. This is
  the mechanism section, misfiled.
- ✓ *"The tool protocol now has a proper answer: the server returns a numbered ticket, and your
  client polls it."* — same subject as sentence one, no new vocabulary, no numbers, and the reader
  can picture it.

- **Hard cap: 3 sentences, ~70 words** (`--check` warns above 80). Count them. Longer is a defect,
  not a thorough entry. Note that size was never what broke these — every failing entry was inside
  the cap, which is why the sentence-job rule above exists alongside it.
- **Plain language throughout** — not just the first sentence. No acronyms, no config identifiers
  (`min_pixels`, `patch_size`), no formulas, no arrow-chains of pipeline steps. `--check` warns on
  a backticked or snake_case or camelCase token appearing here at all.
- **At most ONE number**, picked for how surprising it is rather than how precise, and warned by
  `--check`. Stacked quantities are the single most reliable way to make sentence two unreadable:
  five of the six entries that prompted this rule broke it, one of them with five numbers.
- **Do not restate the write-up.** The full thesis, every constant, and all the supporting numbers
  already live a few hundred pixels below in `## The Problem` and the mechanism section.
  Duplicating them here buys nothing and costs the reader the on-ramp.
- Test: could someone who has never opened the session read this and want to? If it instead reads
  like the conclusion of a paper they haven't read, cut it down.

### Step 11: Validate today's folder

From the repo root:

```bash
node build.js --check
```

Fix every warning that names today's id — missing `visualize.html`, missing viewport /
`data-visualizer` / `adl-visualize-height`, external `fetch`/`<script src>`, invalid JS,
unknown Category / Level / For / tag, no Hook, unrenderable diagram, **no
`## Implementing It` section**, **no fenced code block in `topic.md`**. Do not present the
summary until today's id is clean.

The linter also now catches what used to be honour-system: the seven-section order (missing,
mis-ordered, or retired sections, and a mechanism/counter-case heading that does not name the
topic), `code_example.py` over 150 lines, a visualizer missing its CSP / session-id marker /
`ResizeObserver` height / Reset button, and `## The Problem` slipping into momentum reporting.

**Readability is now measured too**, because it was ignored for weeks as advice. `--check` warns
on any paragraph over **110 words** or sentence over **45 words** in the on-ramp sections
(`Explain Like I'm 5`, `The Problem`, the mechanism section), on a `The Problem` written as a
single block, and on any section falling outside its **word band** (fenced code excluded).

When a band warning fires, fix it **in the section named**. A section over its cap is cut where it
stands; a section under its floor is owed words back, not trimmed further. Do not move words
between sections to satisfy a band — that is the move the old document-wide total rewarded, and it
is what drained the two sections that tell a reader why the article applies to them. And update
`**Time to read**` to match what you actually shipped: it is a number you type, so it is only true
if you keep it true.

Three content rules no linter can check, so check them by eye before you stop:

- `## Implementing It` gives code for **every role the change touches** — client *and* server,
  producer *and* consumer — not only the role the source announcement was written for. A section
  that is all server and one sentence of "clients should check X" has failed this.
- The title reads to someone who has only used Cursor. No product-specific glyph doing the work
  of the surprise; if the `Hook` line is the better title for that reader, swap them. **And it is
  one clause with one subject** — if it has two halves joined by "so that", check they share a
  subject and that the second half introduces no noun the reader has not met.
- **Every detail serves the reader, not the source.** Scan the mechanism section for anything that
  only describes the source system — its full component taxonomy, its internal names, architecture
  the reader will never touch. If a term is defined once and never used again, cut it. This is the
  rule that keeps a session that opens well from going boring by the middle.

### Step 12: Present the Summary

`~/ai_learning/` contains a reader that renders these five files as one page —
interactive visualizer sandboxed and lazy-loaded, diagram pre-rendered to SVG, and code shown
beside its captured output. Point the user
at that, not at the raw files, since the `.excalidraw` is unreadable on its own.

```
Today's AI Learning Session (YYYY-MM-DD)
=========================================
Topic: [Title]
Category: [Category] (session #N in this category)

In one line: [the ELI5 takeaway, plain language, no acronyms]

What you'll learn:
- [Key point 1]
- [Key point 2]
- [Key point 3]

Read it:
  cd ~/ai_learning && make serve      then open http://127.0.0.1:8000/#YYYY-MM-DD
    Overview → Visualize → Diagram → Code (with output) → Articles, ~30 min end to end

Files created:
  ~/ai_learning/YYYY-MM-DD/topic.md           — the write-up (~10 min)
  ~/ai_learning/YYYY-MM-DD/visualize.html     — interactive mechanism; standalone and sandboxed
  ~/ai_learning/YYYY-MM-DD/diagram.excalidraw — rendered in the reader; drop into excalidraw.com to edit
  ~/ai_learning/YYYY-MM-DD/code_example.py    — Run: python3 ~/ai_learning/YYYY-MM-DD/code_example.py (~15 min)
  ~/ai_learning/YYYY-MM-DD/articles.md        — pick one to deep-dive (~5 min)

Saved locally only. To publish this session, run: /ai-daily-learn-publish
  (Cursor: use the ai-daily-learn-publish skill)
```

Keep the three `What you'll learn` bullets readable by someone who has not read the write-up
yet: expand an acronym on first use, and lead each bullet with the finding rather than the
mechanism. The summary is an invitation to read, not a compressed version of the deep sections.

## Error Handling

- WebSearch returns nothing → broaden search terms, fall back to known interesting topic
- Code example needs API → write a pure Python simulation instead
- Visualizer cannot model the full system → model the smallest mechanism that proves the key claim
- Excalidraw script fails → generate JSON inline (see Step 7 fallback)
- Journal corrupted → recreate with header, note the reset

## Scope

This skill is local-only by design. Do not commit, push, or open a PR from here, even if the
user's repo happens to be a git working tree. Publishing lives in `/ai-daily-learn-publish`.
