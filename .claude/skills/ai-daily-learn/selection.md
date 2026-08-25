# Topic selection — audience, sources, how to pick

## The reader pyramid

The audience is a pyramid, widest at the top, and the `**For**` field on each session is which
layer it serves. This is the number that actually tracks the reader; category is a proxy for it
and the proxy leaks.

| Layer | `**For**` | How many readers | Target per 10 |
| --- | --- | --- | --- |
| Uses AI on real work — productivity, code writing, driving Claude Code / Cursor | `Using tools` | **Most of them.** 90% of professional developers use a coding agent weekly, 68% daily | **3** |
| Authors things — skills, MCP servers, a small agent | `Building agents` | Many | 3 |
| Ships it — production, evals, reviewing agent-written code | `Shipping AI` | Many | 3 |
| Model internals — inference, training, post-training verification | `How models work` | **Fewest** | **1** |

The pyramid is not aspirational. Measured over the first 22 sessions the site published **9%**
for `Using tools` and **32%** for `How models work` — as much for the narrowest layer as for the
second-widest — while every single day's pick looked defensible on the day. That is the failure
mode this file exists to prevent: not a bad choice, an unwatched average.

The layers below the top are not "advanced readers"; they are *fewer* readers. A session that
serves only the bottom layer is a session most of the audience has no reason to open.

## How a winner is chosen (do this in order)

### 0. Ask what is due — do not estimate it

```bash
cd ~/ai_learning && node build.js --mix
```

This reads every `topic.md` and prints the trailing-10 mix, what is **DUE NEXT**, and what to
**AVOID**. It writes nothing, runs no code examples, and takes a second. Run it before you look
at a single source, and pick inside what it says is due — counting journal entries by hand is
how the tier weighting drifted to double its cap without anyone noticing.

If `--mix` names a `For` layer as due, that constraint outranks the category rotation: pick a
category that can serve that layer. `Using tools` due means Coding Agents & Productivity is the
obvious answer, not a fallback.

### 1. Category inside what is due

Pick from the **under-weight** tier (A 50% / B 30% / C 20%). Inside that tier, least-recent
category wins. A category that has never appeared jumps the queue *inside its tier only*.

If `--mix` puts Tier C at its cap, **do not pick Tier C today** even if a famous paper dropped.
Cite it later; do not build the session on it. The same applies to `How models work` at its cap —
a Tier B category written entirely for model internals breaches the pyramid just as surely as a
Tier C one, which is why `For` is checked separately from tier.

### 2. Scan sources for that category only

Fetch 4–6 items from the lists below. Prefer changelogs, engineering blogs, docs, and
production write-ups. **Paper budget: at most one arXiv-led session in the last 7.**

### 3. Shortlist three, then pick one

Write down three candidates (title, URL, category, one-line claim). Score each 0 or 1:

| Gate | Pass if |
| --- | --- |
| **Monday action** | Reader 1 can change a setting, measure a number, or stop a bad habit after the first third |
| **Mechanism** | Reader 2 learns *why*, not just a product announcement |
| **Leaves them capable** | Name the thing an engineer can *do* after reading that they could not do before. If the honest answer is "understand X better", it fails — being better informed is not being more capable |
| **Implementable** | You can already name the code that changes — the payload, the handler, the config key — for *every* role the change touches, not only the one the announcement is addressed to |
| **Fits 30 min** | One claim, not a survey |
| **Primary source** | A changelog, doc, eng blog, or paper you can fetch — not a recap of a recap |
| **Not a repeat** | Journal does not already have this claim |

Pick the highest score. On a tie, prefer the one whose reader does something different
tomorrow morning. **#1 (operating tools) beats #2 (authoring harnesses)** when both fit.

In the session summary, name the two losers and why they lost. If you cannot, you did not
compare — you grabbed the first interesting link.

### Hard rejects (even if the category is due)

- Method-name title you cannot rewrite as a surprise, a cost, or a question the reader has asked
- No honest "What to do about it" that is not "wait a year"
- Invented applicability (overstating relevance is worse than skipping)
- Nothing to implement: the honest write-up would be a description of an announcement, with no
  code the reader could write on either side of it
- Second paper-led session inside the last 7
- A Learn-track slug (`tokens`, `the agent loop`, `RAG` as a recap) dressed up as news

## Sources — keyed to the category

The category is chosen first (Step 0-1), so this list is keyed to the **category**, not to a
reader. That ordering is deliberate and it is a fix, not a formatting choice: when the only
concrete high-yield feeds in this file were two coding-agent changelogs and one generic
"everything else" bucket, six of the eleven categories had no list of their own — and arXiv was
the path of least resistance, always fresh, always fetchable, always interesting. The frontier
tier drifted to double its cap. A category with no sources listed is a category that will lose
to a category that has them.

**Primary** is what the session is built on. **Secondary** is the second perspective and the
`articles.md` further reading. Never open arXiv first unless the paper budget is open *and* the
category is Tier C.

### Every day, whatever is due

- https://news.ycombinator.com/ — framing, and what practitioners are actually arguing about
- https://simonwillison.net/ — the single best filter for "does this matter to an engineer"
- https://www.latent.space/ — AI engineering practice, interviews, what shipped and why
- https://www.deeplearning.ai/the-batch/ — Andrew Ng's weekly. Its real value is the
  research-to-practice bridge: it catches developments the harness-focused feeds miss and frames
  them for people who build rather than train. Strongest as the **industry-analysis slot in
  `articles.md`** and as a way to notice a topic; weakest as the primary source, because it
  summarises. When it points at something good, go fetch what it points at.
- https://www.deeplearning.ai/short-courses/ and `/courses/` — on-ramp only, same rule as ML
  Concepts: `articles.md` further reading when a session assumes a concept, never the news lead.
- https://mlconcepts.viveksingh-heritage.workers.dev/ — ML Concepts: interactive primers (LoRA,
  self-attention, embeddings, calibration, backprop, agents in prod). **On-ramp only, never the
  news lead.** Use it when Level is `Start here`, or as `articles.md` further reading. Do not
  re-teach a `learn/` chapter as "today's article."

---

## Tier A — ship it this week (50% of sessions)

### Coding Agents & Productivity  ·  `For: Using tools`  ·  target 3 per 10

The widest reader tier and the deepest bench — 90% of professional developers drive one of these
daily. Changelogs are the highest-yield feed on the whole list because they are dated, specific,
and describe something the reader already has installed.

- **Primary** — https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
- **Primary** — https://docs.claude.com/en/docs/claude-code/overview (hooks, skills, subagents,
  settings; pair a changelog line with the doc that explains it)
- **Primary** — https://cursor.com/changelog
- **Primary** — https://www.anthropic.com/engineering — harness design, context, agent patterns
- **Primary** — https://github.com/openai/codex/releases and
  https://github.com/google-gemini/gemini-cli/releases — cross-tool comparison
- Secondary — https://github.blog/changelog/ (Copilot), https://aider.chat/HISTORY.html
- Secondary — https://newsletter.pragmaticengineer.com/ — adoption and workflow reporting

### Building Agents & MCP  ·  `For: Building agents`  ·  target 3 per 10

- **Primary** — https://modelcontextprotocol.io/specification/latest — the spec is the primary
  source; read the revision's own changelog before any commentary on it
- **Primary** — https://github.com/modelcontextprotocol/servers — reference servers and SDK
  releases; the code is the spec's ground truth
- **Primary** — https://www.anthropic.com/engineering — agent architecture, tool design
- **Primary** — https://docs.claude.com/en/docs/claude-code/overview — Agent SDK, tool schemas
- Secondary — https://blog.langchain.com/ and https://www.llamaindex.ai/blog — orchestration,
  **only when the post carries a measured result**, never a product launch
- Secondary — https://blog.cloudflare.com/tag/agents/ — remote MCP, deployment shape

### AI Engineering Practices  ·  `For: Shipping AI`  ·  target 2-3 per 10

The biggest measured pain in the audience: developers now spend **11.4 hrs/week reviewing
AI-written code vs 9.8 writing new code**, and while 84% use these tools only 29% trust the
output. Reviewing, testing and trusting agent-written code is the richest under-served seam on
this whole list.

- **Primary** — https://www.anthropic.com/engineering — review workflows, verification
- **Primary** — https://github.blog/changelog/ — code review, CI and agent surfaces
- **Primary** — https://dora.dev/research/ — the measured research on delivery practice
- Secondary — https://survey.stackoverflow.co/ and https://www.thoughtworks.com/radar — what
  teams actually report doing, useful for the "you are not alone" framing
- Secondary — https://newsletter.pragmaticengineer.com/, https://simonwillison.net/

### Evals & Reliability  ·  `For: Shipping AI`  ·  target 1-2 per 10

- **Primary** — https://hamel.dev/ — the best practical writing on LLM evals anywhere
- **Primary** — https://www.anthropic.com/engineering — eval design, guardrails
- **Primary** — https://www.braintrust.dev/blog and https://blog.langchain.com/ — harness
  tooling, again only with a measured result
- Secondary — https://eugeneyan.com/writing/ — applied ML evaluation and RAG measurement
- Secondary — https://www.swebench.com/, https://lmsys.org/blog/, https://artificialanalysis.ai/
  — benchmark methodology and where leaderboards mislead

---

## Tier B — understand the machine (30%)

### New Models & APIs  ·  `For: Using tools` / `Shipping AI`  ·  target 1-2 per 10

- **Primary** — https://docs.claude.com/en/release-notes/api and
  https://platform.openai.com/docs/changelog — dated API changes beat launch posts
- **Primary** — https://developers.googleblog.com/ — the practical Google feed
- **Primary** — https://ai.meta.com/blog/ — Llama, PyTorch, real production numbers
- Secondary — https://huggingface.co/blog, https://artificialanalysis.ai/ (measured comparison
  rather than vendor claims), https://cookbook.openai.com/ and
  https://github.com/openai/openai-cookbook
- Secondary, other labs — https://mistral.ai/news, https://qwenlm.github.io/blog/,
  https://api-docs.deepseek.com/news/, https://cohere.com/blog, https://www.together.ai/blog,
  https://allenai.org/blog. **Build on the technical report or model card, never the launch
  post.** An open-weights release with a real report is a session; the announcement of it is the
  press release this site exists not to be.

**Fetchability, checked:** every `openai.com` surface — `/news/`, `/index/`, `/research/` — 403s
to WebFetch, not just the blog. Route around it via the platform changelog, the cookbook (site or
GitHub repo), or HN. `x.ai/news` 403s the same way.

### AI in Production  ·  `For: Shipping AI`  ·  target 1-2 per 10

- **Primary** — https://blog.vllm.ai/ — serving internals with numbers
- **Primary** — https://modal.com/blog and https://www.baseten.co/blog/ — inference economics
- **Primary** — https://lmsys.org/blog/ — SGLang, throughput, scheduling
- **Primary** — https://engineering.fb.com/ (and `/category/ai-research/`) — Meta's *engineering*
  blog, distinct from `ai.meta.com/blog`: serving infra, storage, scale, with real numbers. One
  of the few places a production write-up says what actually broke.
- Secondary — https://blog.cloudflare.com/tag/agents/, https://developer.nvidia.com/blog/,
  https://www.databricks.com/blog/category/engineering

### Hands-on Techniques  ·  `For: Shipping AI` / `Building agents`  ·  target 1-2 per 10

- **Primary** — https://huggingface.co/blog — the densest how-to feed on the list
- **Primary** — https://docs.unsloth.ai/ — fine-tuning that runs on one GPU
- **Primary** — https://qdrant.tech/blog/, https://www.pinecone.io/blog/ — retrieval with
  measured results
- Secondary — https://jina.ai/news/ — embeddings, reranking
- Secondary — https://eugeneyan.com/writing/ — RAG patterns and their failure modes

---

## Tier C — frontier (20%, and only 1 per 10 for `How models work`)

Capped, not banned. A Tier C session still owes a Monday action; if the honest answer is "watch
for this", it loses to any Tier A candidate. Check the paper budget before opening arXiv.

- https://www.anthropic.com/research, https://huggingface.co/papers (the daily filter — use it
  instead of raw arXiv listings)
- https://deepmind.google/discover/blog/ and https://ai.meta.com/research/ — frontier work that
  usually ships with enough detail to reimplement a piece of it, which is what earns a Tier C slot
- https://arxiv.org/list/cs.AI/recent and https://arxiv.org/list/cs.LG/recent
- https://magazine.sebastianraschka.com/ and https://lilianweng.github.io/ — papers already
  translated into engineering terms, which is usually the better source than the paper itself
- **AI Hardware** — https://semianalysis.com/, https://chipsandcheese.com/,
  https://developer.nvidia.com/blog/
- **Multimodal** — https://huggingface.co/blog, https://blog.roboflow.com/
- **AI Safety & Alignment** — https://www.anthropic.com/research; hardest category to give a
  Monday action, so hold it until Tier C is genuinely under weight

---

### Source quality gates

Before building a session on a source, all four must hold. Any failure sends you back to the
category list, not forward into writing.

1. **Dated and primary.** A changelog entry, a spec revision, a docs page, an engineering post
   with numbers. Not a recap, not a roundup, not another blog's summary of it.
2. **Something changed.** "Here is what X is" is a `learn/` chapter. "Here is what changed and
   what it costs you" is a session.
3. **Implementable from what it says.** If the source does not contain enough for you to write
   `## Implementing It` with real code for every role the change touches, it is not enough
   source — find the docs or the reference implementation that fills the gap, or pick again.
4. **Verified, not remembered.** Fetch it. Quote its own numbers. Never write a session from
   recollection of a release; the whole value of a dated log is that its facts are checkable.

## Worked example (last five sessions)

These already shipped. Use them as a calibration, not a schedule.

| Session | Why it would win or lose this rubric |
| --- | --- |
| Context Is a Budget (08-22) | **Win.** Reader 1 changes caching tomorrow. Primary: changelog + docs. |
| RAG chunk size (08-23) | **Win.** Reader 2 measures a pipeline they will ship. Action: grid-search chunk size. |
| Bigger VM / evals (08-23-s2) | **Win for reader 2.** Action: publish memory limits on the eval. Reader 1 still gets the "leaderboard gaps can be infra" warning. |
| Pixels Are Not Tokens (08-21) | **Borderline.** True and useful for vision cost, but Reader 1 has no Monday action unless they ship images. Prefer when Tier C is under weight. |
| Every Model Cheats (08-20) | **Lose today if Tier C is already heavy.** Strong paper, weak Monday action ("don't trust an anti-cheat prompt"). Hold for a week when A/B are due. |
