# Topic selection — audience, sources, how to pick

Two readers, same page:

1. **Software engineer learning AI** — uses Cursor / Claude / ChatGPT on real work. Has not
   trained a model. Needs a Monday-morning action and an analogy first.
2. **On the path to AI engineer** — shipping a small agent, a RAG path, or an eval. Needs the
   mechanism and the failure mode, still not a paper club.

A topic that only works for reader 2 and abandons reader 1 is the wrong pick. Depth is allowed;
starting in the middle of a paper is not.

## How a winner is chosen (do this in order)

### 1. Category first, not "whatever is hot"

Read the last ~10 `journal.md` entries. Count tiers. Pick a category from the **under-weight**
tier (A 50% / B 30% / C 20%). Inside that tier, least-recent category wins. A category that
has never appeared jumps the queue *inside its tier only*.

If Tier C is already at or above 20% of the last 10, **do not pick Tier C today** even if a
famous paper dropped. Cite it later; do not build the session on it.

### 2. Scan sources for that category only

Fetch 4–6 items from the lists below. Prefer changelogs, engineering blogs, docs, and
production write-ups. **Paper budget: at most one arXiv-led session in the last 7.**

### 3. Shortlist three, then pick one

Write down three candidates (title, URL, category, one-line claim). Score each 0 or 1:

| Gate | Pass if |
| --- | --- |
| **Monday action** | Reader 1 can change a setting, measure a number, or stop a bad habit after the first third |
| **Mechanism** | Reader 2 learns *why*, not just a product announcement |
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
- Second paper-led session inside the last 7
- A Learn-track slug (`tokens`, `the agent loop`, `RAG` as a recap) dressed up as news

## Sources

Scan the **category's list**, then HN for framing. Do not start on arXiv unless the paper
budget is open and the category is Tier C.

### Every day (framing + what practitioners are arguing)

- https://news.ycombinator.com/
- https://simonwillison.net/
- https://www.latent.space/
- https://www.deeplearning.ai/the-batch/

### Reader 1 — using tools (Tier A: Coding Agents)

- https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
- https://cursor.com/changelog
- Codex / Gemini CLI release notes (WebSearch the current URL)
- https://www.anthropic.com/engineering

### Reader 2 — becoming an AI engineer (Tier A/B: agents, evals, production, techniques)

- https://www.anthropic.com/engineering — harnesses, evals, context
- https://huggingface.co/blog — models, serving, fine-tune how-tos
- https://ai.meta.com/blog/ — Llama, PyTorch, production numbers
- https://developers.googleblog.com/ — Gemini / API, the practical Google feed
- https://blog.google/technology/ai/ — Gemini announcements (use developers blog for how-to)
- https://openai.com/blog — model/API (WebFetch often 403; use HN or the cookbook mirror)
- Platform cookbooks / docs when the topic is "how do I call this": OpenAI Cookbook,
  Anthropic docs, Gemini API docs
- https://blog.langchain.com/ and LlamaIndex engineering posts — RAG / agent orchestration
  *when the post has a measured result*, not a product launch

### Frontier only (Tier C, capped)

- https://www.anthropic.com/research
- https://arxiv.org/list/cs.AI/recent and https://arxiv.org/list/cs.LG/recent
- Provider research blogs (x.ai, Meta, Google) when the paper has working code or a number
  an engineer can reuse

`openai.com` often returns 403 to WebFetch — use the arXiv or HN mirror.

## Worked example (last five sessions)

These already shipped. Use them as a calibration, not a schedule.

| Session | Why it would win or lose this rubric |
| --- | --- |
| Context Is a Budget (08-22) | **Win.** Reader 1 changes caching tomorrow. Primary: changelog + docs. |
| RAG chunk size (08-23) | **Win.** Reader 2 measures a pipeline they will ship. Action: grid-search chunk size. |
| Bigger VM / evals (08-23-s2) | **Win for reader 2.** Action: publish memory limits on the eval. Reader 1 still gets the "leaderboard gaps can be infra" warning. |
| Pixels Are Not Tokens (08-21) | **Borderline.** True and useful for vision cost, but Reader 1 has no Monday action unless they ship images. Prefer when Tier C is under weight. |
| Every Model Cheats (08-20) | **Lose today if Tier C is already heavy.** Strong paper, weak Monday action ("don't trust an anti-cheat prompt"). Hold for a week when A/B are due. |
