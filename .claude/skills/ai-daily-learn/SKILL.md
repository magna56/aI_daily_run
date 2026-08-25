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

- **Model**: this session should run on Opus — the most capable model available, not whatever
  happens to be active. The unattended daily job pins this itself (`run_daily.sh` passes
  `--model opus`), so this only matters for a manually-invoked run: if you can tell the active
  model is something else (e.g. the user has been on Sonnet or Haiku earlier in the
  conversation), say so before generating and suggest `/model opus` — a skill invocation cannot
  force a live model switch mid-session, so this has to be a flag-and-ask, not a silent
  workaround.
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
   - `https://news.ycombinator.com/` — front page, for what practitioners are actually arguing
     about; also the best signal for which framing of a topic will land
   - `https://mlconcepts.viveksingh-heritage.workers.dev/` — **intermediate / basics, every
     day.** Interactive primers (LoRA, self-attention, embeddings, calibration, backprop,
     build-an-LLM, agents in prod). On-ramp or `articles.md` further reading — not the news
     lead. Skip it as today's source if a changelog/eng post in the due category has a
     Monday action, or if it would re-teach a `learn/` chapter.
   - **Papers, subject to the one-per-7 budget above**: `https://arxiv.org/list/cs.AI/recent`
     and `https://arxiv.org/list/cs.LG/recent`
   - Try **WebSearch** first; if blocked (VPCSC error), fall back to WebFetch on the URLs above.
     `openai.com` returns 403 to WebFetch; use the arXiv or HN mirror of the announcement.
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
**Time to read**: ~10 minutes

## Explain Like I'm 5
[3-5 sentences. ONE everyday analogy, zero jargon, no acronyms at all.]

## The Problem
[2-4 sentences. What was broken, wasteful, or unsolved before this — the actual pain that
made someone go build it. See the rules below.]

## For a Software Engineer
[3-5 short paragraphs or bullets. The bridge section — see the rules below.]

## What This Means for You
[The anchor section. When this is useful, how it affects your work, and what to actually
do about it — see the rules below. REQUIRED on every session, including Tier C.]

## What It Is
[2-3 paragraph technical explanation. Assume a strong software engineer, not an ML researcher.]

## Why It Matters
[Significance, what it enables, comparison to prior work]

## Key Technical Details
[Open with a short **Background first** paragraph, then the bullets — see the rules below.]

## Implementing It
[The code the reader has to write, in fenced blocks, for every role the change touches —
see the rules below. REQUIRED on every session.]

## How It Connects to What You Know
[Connect to something they already ship — caches, CI, code review, HTTP — then to earlier
sessions. If this daily piece assumes a chapter (tokens, the agent loop, RAG, the harness),
link the matching `learn/<slug>` page instead of re-teaching it.]

## Try It Yourself
[Pointer to code_example.py and what it demonstrates]

## Glossary
[Every acronym and domain term actually used above — see the rules below.]
```

**The title is the hook.** This is the whole article for everyone who only sees a link — on the
card grid, in Slack, on Hacker News. Write it for a curious software engineer scrolling past,
including someone who has only used Cursor and has never read a paper. If the title needs a
glossary, it failed.
- **Lead with the surprise, the cost, or the question the reader has already felt** — the
  thing that makes someone go "wait, really?" A concrete stake beats a method name every time.
- **Ban academic formatting.** No `Method Name: Formal Description via Mechanism`. That pattern
  is why sessions feel all over the place. Compare:
  - ✗ `Truncated Jump Sampling: Training-Free Diffusion Acceleration via Endpoint Decodability`
    → ✓ `Skip 40% of Diffusion Steps Without Retraining Anything`
  - ✗ `LUMI: Tokenizer-Agnostic LLM-Based Lossless Image Compression`
    → ✓ `An LLM Compresses Images Better Than PNG — And It's Absurdly Slow`
  - ✗ `Prefill-Pressure Adaptive Scheduling: Why max_num_batched_tokens Has No Right Value`
    → ✓ `The vLLM Setting Everyone Copies From Blog Posts Is Wrong For You`
  - ✗ `Deterministic Verification Gates for Tool-Using LLM Agents`
    → ✓ `Don't Let the Agent Call a Tool Until a Check It Can't Talk Past Says Yes`
- **Questions are welcome** when the question is one the reader has actually asked:
  "Why Does My Agent Cost $30 Some Days and $3 Others?" A question they have never wondered
  is just a worse statement.
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
(Problem, For a Software Engineer, What This Means for You) exist because the deep sections
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
- 2-4 sentences. This section motivates; `## What It Is` explains.

**`## For a Software Engineer`** — the load-bearing section. Explain the topic using **generic
engineering principles the reader already owns**, not AI ones.
- Anchor to something familiar and name it explicitly: "this is a quantization problem", "this
  is head-of-line blocking", "this is a cache invalidation problem", "this is padding waste in
  a tensor, but for pixels".
- State plainly what an engineer would *do differently* on Monday — a config to check, a cost
  to measure, an assumption to stop making. Practical application is the whole point.
- Give at least one number from the session that a non-specialist can feel (a cost multiple, a
  percentage wasted, a hard ceiling) and say why it is surprising.
- Never require a later section to be understood first. This must stand alone.

**`## What This Means for You`** — the anchor section, and the one that decides whether a deep
topic lands or bounces. The reader's real question is never "is this clever?", it is *"does this
touch my work, and what do I do about it?"* Answer that explicitly rather than leaving them to
infer it. Three short labelled parts, in this order:

- **When this matters** — the concrete situation where this shows up. Name the trigger, not the
  topic: "you're paying more than you expect for a long Claude Code session", "your RAG answers
  got worse after you raised top-k", "you're choosing between an A10G and an L4". If the reader
  can't recognise themselves in this line, the framing is wrong — rewrite it before continuing.
- **How it affects you** — the consequence in their terms. Money, latency, a bug class they'll
  hit, a decision they're about to get wrong, a belief they hold that's outdated.
- **What to do about it** — at least one thing they can actually do: a setting to change, a
  command to run, a number to go measure in their own logs, a check to add to CI, or an
  explicit "nothing yet, but here's the signal to watch for". Be specific enough to act on
  without re-reading the article.

Rules:
- **Required on every session, including Tier C.** A frontier paper still owes the reader this.
  If the honest answer is "this won't affect your work for a year", *say that* — a truthful
  "not yet, and here's what would change that" is far better than an invented use case.
- **At least one item must be a change, not an audit.** "Go check whether your client honours
  the TTL" only tells the reader to open a file; it does not tell them what to write once they
  are in it. An audit is a fine *first* step, but every audit item owes its second half — "and
  if the answer is bad, here is the fix" — pointing at `## Implementing It` rather than
  restating it.
- **Never invent applicability.** Overstating relevance is worse than admitting there is little;
  this section is the site's credibility, not its marketing.
- Write it in second person, plainly. This is the least academic section in the document.

**`## Why It Matters`** — significance in engineering terms, never in industry terms.
- Compare to prior work by what it *costs or enables* — bytes, latency, money, a class of bug
  that stops happening — not by how it was received.
- **No momentum reporting.** How fast the ecosystem adopted it, how large the release is next to
  past releases, and who publicly praised it are facts about a market, not about a system. A
  named person's quote earns its place only when it carries a technical claim the reader can go
  check; never as an endorsement.
- Criticism belongs here at full strength. If there is a real objection ("has this just
  rediscovered REST?"), state the strongest version of it and answer it with a mechanism.

**`## Key Technical Details`** — keep the depth, but stop dropping the reader into it cold. This
section is where the write-up historically loses people: it opens on config constants and
specialist names the reader has never met.
- Open with a **Background first** paragraph — 2-4 plain sentences naming the handful of
  primitives the bullets are about to assume, and what each one *is*. Do not restate the topic;
  give exactly the vocabulary the bullets need. Example: before any bullet mentions
  `patch_size` or `spatial_merge_size`, say in plain English that a vision encoder cuts an image
  into small squares, reads each one, and may merge neighbours to cut the count.
- **Order the bullets foundational → specialist**, never in the order you happened to research
  them. The first bullet must be understandable straight out of the background paragraph.
- **Lead each bullet with what it means, then give the constants.** "One visual token is a 28×28
  pixel block — that's `patch_size=14` with `spatial_merge_size=2`" reads; "`patch_size=14`,
  `spatial_merge_size=2`; 14×2=28" does not.
- A proper noun the reader has not met (NaViT, DeepStack, M-RoPE) needs a four-word gloss on the
  spot — "NaViT's patch-n-pack (packing many images into one sequence)" — even though it also
  appears in the glossary. Do not make them scroll to follow a sentence.
- Depth is not the problem and must not be reduced. The entry to it is the problem.

**`## Implementing It`** — the section that makes this site worth reading instead of the
changelog it came from. Every section above explains the change; this one shows the code that
lives with it. Required on every session.

- **Put real code or a real payload in a fenced block, in `topic.md` itself.** Pointing at
  `code_example.py` does not discharge this — most readers never open the Code tab, and nobody
  reading on a phone is going to run Python. The block belongs next to the sentence that
  motivates it.
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
- 3-6 short blocks and at least one fenced code block. If the honest answer is that nothing is
  implementable yet (a paper with no released code), implement the *mechanism* from the paper in
  a dozen lines instead — that is what "implementing Y from scratch" means here.

**`## Glossary`** — closes the document as reference, in the order terms first appear.
- Cover **every** acronym and domain term used anywhere above — no exceptions, including ones
  that feel obvious to you (VLM, token, prefill, KV cache, RLAIF, patch, DPI).
- Format: `- **Term** (expansion) — one or two plain sentences.`
- For any unit or quantity the session turns on, explain **what it buys you**, not just what it
  stands for. "DPI" is not "dots per inch"; it is "how much detail survives — 93 dpi means 6pt
  text is ~8 pixels tall, which is why small print gets misread."
- Define terms in terms of *other glossary entries or plain English only*, never in terms of
  jargon defined nowhere.

### Step 6: Write code_example.py

Write `~/ai_learning/YYYY-MM-DD/code_example.py` — a **runnable** pure Python script:

- Include a docstring explaining what it demonstrates and how to run it
- **No API keys needed** — use simulations, visualizations, pure implementations
- Keep under 150 lines — focused, not a tutorial dump
- Include print output so results are visible immediately
- For hardware/business topics: write analysis, visualization, or comparison code
- For algorithm topics: implement a minimal working version from scratch
- **Implement the mechanism; do not only price it.** For a protocol, API, config or algorithm
  change, the script must contain a working version of the thing — the client that builds and
  validates the request, the cache that honours the TTL, the retry loop, the scheduler — in a
  shape the reader can lift into their own code. Byte counts and cost curves are a *result* the
  implementation prints, never the whole script. A script that only measures a change tells the
  reader what to expect; one that implements it tells them what to write.
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

Prioritize: primary source, best technical explanation, practical tutorial, industry analysis.
When the session touches LoRA, attention, embeddings, calibration, backprop, or agents,
include one ML Concepts page from https://mlconcepts.viveksingh-heritage.workers.dev/
as the **intermediate / basics** slot.

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
- **Key insight**: [plain first sentence, then the detail — see below]
- **Code**: `YYYY-MM-DD/code_example.py` — [what it demonstrates]
- **Articles**: [count] articles collected
```

**`Key insight` is a hook, not a summary.** The reader renders it in a highlighted box at the top
of the Overview pane — *above* `Explain Like I'm 5` — so it is the first thing anyone sees, and a
dense one cancels out every on-ramp below it. The homepage card uses `**Hook**` from `topic.md`,
not this field — keep both plain. It has been drifting into 200-word jargon walls; that is the
single most daunting thing on the page.

- **Hard cap: 3 sentences, ~70 words.** Count them. Longer is a defect, not a thorough entry.
- **Plain language throughout** — not just the first sentence. No acronyms, no config identifiers
  (`min_pixels`, `patch_size`), no formulas, no arrow-chains of pipeline steps.
- **At most ONE number**, picked for how surprising it is rather than how precise.
- **Do not restate the write-up.** The full thesis, every constant, and all the supporting numbers
  already live a few hundred pixels below in `## Why It Matters` and `## Key Technical Details`.
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

Two content rules no linter can check, so check them by eye before you stop:

- `## Implementing It` gives code for **every role the change touches** — client *and* server,
  producer *and* consumer — not only the role the source announcement was written for. A section
  that is all server and one sentence of "clients should check X" has failed this.
- `## Why It Matters` carries no momentum reporting: no "largest release since", no "adoption was
  unusually fast", no advocate quoted approving of it. Those are the two ways a session reads as
  a press release rather than as something an engineer can use.

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
