---
name: ai-daily-learn
description: >
  Daily 30-minute AI learning session for senior engineers. Searches latest AI news/research,
  picks a focused topic, and produces three artifacts: an Excalidraw visual diagram, a runnable
  pure-Python code example, and curated articles with summaries. Saves everything locally to
  ~/ai_learning/YYYY-MM-DD/ and nowhere else — nothing is pushed anywhere. Use the sibling skill
  ai-daily-learn-publish to also publish the session to GitHub. Tracks covered topics to avoid
  repetition. Use when: "daily learn", "ai-daily-learn",
  "learn AI today", "what's new in AI", "AI learning session", "daily AI update", "teach me
  something about AI". Accepts optional topic argument: /ai-daily-learn "vision transformers".
argument-hint: "[optional-topic]"
verified: llm
---

# AI Daily Learn — 30-Minute Session

Senior AI researcher and educator running a focused 30-minute learning session for a
software engineer who already deeply understands LLM fundamentals, prompt engineering, agent
architectures (ReAct, Reflexion, ReWOO), Claude internals, and reasoning models. Skip basics.
Go straight to what is NEW, interesting, and practically useful.

**CRITICAL: Keep everything practical and software-engineering relevant.** Every topic must
connect to something a working engineer can build, deploy, optimize, or integrate. No pure
theory without application. Code examples should demonstrate real patterns, not toy demos.
Topics like "how to use X in production" or "implementing Y from scratch" beat "understanding
the math behind Z".

## Session Parameters

- **Time budget**: 30 minutes of reading/coding material
- **Output directory**: `~/ai_learning/YYYY-MM-DD/` (today's date)
- **Artifacts**: 4 files per session (topic.md, diagram.excalidraw, code_example.py, articles.md)
- **Journal**: `~/ai_learning/journal.md` tracks all sessions
- **Code**: Pure Python only — no API keys, no external services. Self-contained demos.
- **Excalidraw**: Open at excalidraw.com (drag & drop)
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

If the user provided a topic argument, use that. Otherwise:

1. Determine which **category** is due next:
   - If any category in the list below has **never** appeared in `journal.md`, take that one.
     A newly added category should not wait out a full cycle before its first session.
   - Otherwise cycle in order from the last covered category.
2. Use **WebFetch** to scan live sources for the most interesting recent development in that category:
   - `https://news.ycombinator.com/` — scan front page for AI-related stories
   - `https://arxiv.org/list/cs.AI/recent` — latest AI papers
   - `https://arxiv.org/list/cs.LG/recent` — latest ML papers
   - `https://simonwillison.net/` — AI engineering blog (practical, tools-focused)
   - `https://www.latent.space/` — AI engineering podcast/blog
   - `https://huggingface.co/blog` — new models, tools, techniques
   - `https://www.deeplearning.ai/the-batch/` — Andrew Ng's weekly roundup; strong for
     research-to-practice framing and catching developments the harness-focused sources miss
   - `https://openai.com/blog`, `https://www.anthropic.com/research`, or `https://x.ai/blog` —
     model provider updates
   - For **Coding Agents & Productivity** specifically, these are the load-bearing ones:
     - `https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md` — the canonical
       Claude Code changelog (the docs.claude.com release-notes URL 301s here)
     - `https://www.anthropic.com/engineering` — Claude Code internals, harness design,
       agent patterns, written by the people who build it
     - `https://simonwillison.net/` — the best running commentary on coding-agent tooling
     - `https://cursor.com/changelog` and the Gemini CLI / Codex release notes — for
       cross-tool comparison rather than single-vendor news
   - Try **WebSearch** first; if blocked (VPCSC error), fall back to WebFetch on the URLs above.
     `openai.com` returns 403 to WebFetch; use the arXiv or HN mirror of the announcement.
3. Pick ONE focused topic that fits 30 minutes — specific, not broad
4. Use **WebFetch** on the chosen article/paper URL to get full technical details

**Category Rotation** (11 categories, cycle in order — always with practical SWE angle):
1. New Models & APIs — new model releases, how to use them, API differences, migration guides
2. AI Hardware for Engineers — GPU programming, inference optimization, hardware-aware coding
3. Agent Frameworks & Tools — new dev tools, orchestration libraries, MCP servers, SDKs
4. Coding Agents & Productivity — getting more out of the agent tools you already drive every
   day: Claude Code / Cursor / Codex / Gemini CLI configuration, hooks, skills, subagents, MCP
   setup, context and cost management, worktrees, loops, permission modes; what shipped this
   week in their changelogs and whether it changes your workflow. Cross-tool comparison is
   welcome — the reader uses more than one.
5. AI in Production — deployment patterns, serving infra, cost optimization, monitoring, MLOps
6. Applied Research — papers with working code, reproducible results, practical implications
7. AI Safety & Testing — guardrails, eval frameworks, red-teaming tools, responsible AI patterns
8. Multimodal Engineering — vision/audio/video pipelines, building multimodal apps
9. Open Source Tools — new open models to run locally, tools, datasets, community libraries
10. AI Engineering Practices — architecture patterns, scaling, team workflows, code review for AI
11. Hands-on Techniques — fine-tuning, RAG pipelines, evaluation harnesses, prompt optimization

**#3 vs #4** — #3 is about *building* agent systems (you are the author of the harness);
#4 is about *operating* the ones you already use (you are the user of someone else's harness).
"How MCP sampling works so I can implement it" is #3. "Three hooks worth adding to
settings.json today" is #4. When a topic could be either, prefer the one whose reader is doing
something different tomorrow morning.

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
# [Topic Title]

**Category**: [which of the 11 categories — exactly as written in the rotation list]
**Date**: YYYY-MM-DD
**Time to read**: ~10 minutes

## Explain Like I'm 5
[3-5 sentences. ONE everyday analogy, zero jargon, no acronyms at all.]

## For a Software Engineer
[3-5 short paragraphs or bullets. The bridge section — see the rules below.]

## What It Is
[2-3 paragraph technical explanation for a senior engineer]

## Why It Matters
[Significance, what it enables, comparison to prior work]

## Key Technical Details
[Open with a short **Background first** paragraph, then the bullets — see the rules below.]

## How It Connects to What You Know
[Connect to existing knowledge: transformers, agents, Claude internals, etc.]

## Try It Yourself
[Pointer to code_example.py and what it demonstrates]

## Glossary
[Every acronym and domain term actually used above — see the rules below.]
```

**The reader.** A working software engineer who is *learning* AI and intends to apply it
practically. Assume fluency in general software engineering — caching, padding, schedulers,
quantization, compilers, batching, indexes, back-pressure. Do **not** assume fluency in AI
internals, and do not assume they can decode an acronym from context. The three framing
sections exist because the deep sections alone lose this reader.

**`## Explain Like I'm 5`** — leads the document deliberately, because a reader who bounces off
paragraph one never reaches the good part.
- One concrete, everyday analogy carried all the way through. Do not mix metaphors.
- Zero jargon and zero acronyms. If a term is unavoidable, you picked the wrong analogy.
- 3-5 sentences. Land the *shape* of the problem, not the mechanism.
- It must still be **true** — a simplification, never a fiction you walk back later.

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

### Step 8: Write articles.md

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
`deeplearning.ai/the-batch` is a good candidate for the industry-analysis slot when it has
covered the topic — it tends to connect a development to the broader research trend rather
than just reporting the release.

### Step 9: Update the Journal

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
dense one cancels out every on-ramp below it. It is also the card blurb in the index. It has been
drifting into 200-word jargon walls; that is the single most daunting thing on the page.

- **Hard cap: 3 sentences, ~70 words.** Count them. Longer is a defect, not a thorough entry.
- **Plain language throughout** — not just the first sentence. No acronyms, no config identifiers
  (`min_pixels`, `patch_size`), no formulas, no arrow-chains of pipeline steps.
- **At most ONE number**, picked for how surprising it is rather than how precise.
- **Do not restate the write-up.** The full thesis, every constant, and all the supporting numbers
  already live a few hundred pixels below in `## Why It Matters` and `## Key Technical Details`.
  Duplicating them here buys nothing and costs the reader the on-ramp.
- Test: could someone who has never opened the session read this and want to? If it instead reads
  like the conclusion of a paper they haven't read, cut it down.

### Step 10: Present the Summary

`~/ai_learning/` contains a reader that renders these four files as one page —
diagram pre-rendered to SVG, code shown beside its captured output. Point the user
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
    Overview → Diagram → Code (with output) → Articles, ~30 min end to end

Files created:
  ~/ai_learning/YYYY-MM-DD/topic.md           — the write-up (~10 min)
  ~/ai_learning/YYYY-MM-DD/diagram.excalidraw — rendered in the reader; drop into excalidraw.com to edit
  ~/ai_learning/YYYY-MM-DD/code_example.py    — Run: python3 ~/ai_learning/YYYY-MM-DD/code_example.py (~15 min)
  ~/ai_learning/YYYY-MM-DD/articles.md        — pick one to deep-dive (~5 min)

Saved locally only. To publish this session, run: /ai-daily-learn-publish
```

Keep the three `What you'll learn` bullets readable by someone who has not read the write-up
yet: expand an acronym on first use, and lead each bullet with the finding rather than the
mechanism. The summary is an invitation to read, not a compressed version of the deep sections.

## Error Handling

- WebSearch returns nothing → broaden search terms, fall back to known interesting topic
- Code example needs API → write a pure Python simulation instead
- Excalidraw script fails → generate JSON inline (see Step 7 fallback)
- Journal corrupted → recreate with header, note the reset

## Scope

This skill is local-only by design. Do not commit, push, or open a PR from here, even if the
user's repo happens to be a git working tree. Publishing lives in `/ai-daily-learn-publish`.
