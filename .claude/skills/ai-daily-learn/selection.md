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

### 0a. Check for a campaign slate before you pick anything

```bash
cd ~/ai_learning && grep -n "| $(date +%F) |" .claude/skills/ai-daily-learn/campaign.md 2>/dev/null
```

A hit means today's topic is already decided and **Steps 0b through 3 below are skipped** — read
[campaign.md](campaign.md) in full for the row's category, level, `For`, primary source, and the
claim the day is testing, then go straight to Step 3 of `SKILL.md` (deep research) against that
source. No hit, or no file, means there is no campaign running and selection proceeds normally.

Three things a campaign does **not** do, and they are the whole reason it is safe to have one:

- It does not waive a single content rule. `node build.js --check` and the word bands apply
  unchanged, and a campaign day that cannot clear them gets rewritten rather than published past
  the gate.
- It does not waive the audience gate. Still run `node build.js --mix <id>` in Step A½. A slate is
  written to sit inside the bands, so an exit 3 on a campaign day means the article drifted from
  its row, not that the gate is wrong.
- It does not outlive its dates. Past the last row, this check simply stops matching and
  autonomous selection resumes with no edit required.

**A campaign row is a topic, not an article.** It names what to write about and what claim to
test; it does not excuse you from the acceptance test. If the only honest argument for a row is
who might read it, drop that row and take the autonomous pick for the date instead.

### 0b. Ask what is due — do not estimate it

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

**Count citations, not only what the session is built on.** Added 2026-09-26, because the budget
can read as satisfied while the track drifts. A reader does not know which source was the spine;
they see the further-reading list. One paper-led session in ten is within budget, and four of ten
citing arXiv still reads as a papers site. `articles.md` on the daily lab caps at one arXiv link,
and `--check` enforces it.

**And a Tier C candidate whose honest primary source is a paper belongs on Frontier.** This is the
tension the two tracks create and it has to be resolved deliberately: the audience bands pull Tier
C *into* the lab to keep the mix honest, while the Frontier track pulls papers *out* of it. Resolve
it toward sourcing rather than toward tier — keep the Tier C slot in the lab and fill it from
vendor architecture posts, hardware write-ups and engineering blogs, and send the paper to
Frontier. A Tier C lab session built on arXiv is the shape that makes the whole site look like a
paper feed.

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
| **Not a repeat** | Journal does not already have this claim — **and you ran the two checks below** |

**The repeat gate is the one that gets skipped, so run it rather than recall it.** It is the only
gate you cannot judge from the candidate alone, which is exactly why it goes unchecked on a day
when the source is fresh and interesting. Two commands, before you write anything:

```bash
cd ~/ai_learning
grep -ril "<the topic's key noun>" --include=topic.md 20*/ frontier/ | sort | tail -5
grep -rl "<the primary source's URL>" --include=articles.md 20*/ frontier/
```

**Both commands above search for NOUNS. Neither catches a repeat of the argument.** Added
2026-09-25, after two in one week. On 2026-09-23 the planned topic was "what a reasoning model
costs per task, not per token" — which is 2026-09-20's thesis verbatim, whose section three is
titled *Make the Task the Unit*. On 2026-09-25 the planned topic was small/frontier routing, which
2026-08-03 had already shipped as a confidence-gated cascade, with calibration named as the moat —
and 2026-09-21 had then spent a whole article on calibrating confidence. Different subjects, same
article. So run a third check, on the shape rather than the words:

```bash
cd ~/ai_learning
for d in $(ls -d 20*/ | sort | tail -6); do echo "--- $d"; grep -E '^## |^\*\*(Hook|TLDR)' $d/topic.md; done
```

Read the last five or six **section skeletons**, not the journal titles. The repetition a reader
notices is the argument: *"several vendors converged on one thing and the rules underneath still
differ"* is one article, and writing it twice in a fortnight reads as a formula even when the two
subjects are unrelated. If a candidate echoes a recent piece, either reshape it to a genuinely
different mechanism or say plainly in the summary why the difference is real.

**A hit on a dated source disqualifies the candidate. A hit on an evergreen doc does not.** Several
sessions legitimately cite the same reference pages — the Claude Code changelog and the hooks doc
each appear in three — because a stable doc supports many different topics. A dated post or a
specific release announcement supports one event, so a second session citing it is covering that
event twice.

- ✗ 2026-09-15 was built on the Datasette security releases and shipped four days after 2026-09-11,
  *"How an AI Audit Found Three Names for One Protected Table"*, which was built on the same
  releases. Two of five sources were identical, both of them the dated primaries. Same bug class,
  same three mechanisms, same two-human protocol, same `STRICT` flip in `code_example.py`. The
  audience mix was consulted and the journal was not, and the mix cannot see a repeat.

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

**Cadence is the second axis, and it is the one that was missing.** Primary tells you what may be
built on; it does not tell you whether the source has anything new today. Measured on 2026-09-15,
`vllm.ai/blog` published five posts in four days while `ai.meta.com/blog` had nothing dated for
seven weeks — both were Primary, and they are not interchangeable on a Tuesday. Three roles:

| role | cadence | use it as |
| --- | --- | --- |
| **spine** | several times a week | what you can actually build on today |
| **reference** | monthly or slower | excellent when the topic matches; never the default |
| **noticing** | daily digests, aggregators | find the primary, then cite the primary |

Entries below are tagged where it matters. **When a category's spine has nothing today, take
another category that is also due — do not fall through to arXiv and a link blog.** That fall-through
is exactly how 2026-09-11 and 2026-09-15 ended up on the same project four days apart.

### Every day, whatever is due

- https://news.ycombinator.com/ — **noticing only, never cited.** Framing, and what practitioners
  are actually arguing about. Follow the link out and cite what it points at.
- https://simonwillison.net/ — the single best filter for "does this matter to an engineer"
- https://www.latent.space/ — AI engineering practice, interviews, what shipped and why
- https://blog.pragmaticengineer.com/ (archive) and https://newsletter.pragmaticengineer.com/
  — `[spine]` Gergely Orosz, weekly. **Original reporting on what engineering organizations
  actually do**, which almost nothing else on this list carries: named companies, real numbers,
  and practices rather than releases. Recent examples are Uber and Stripe cutting inference cost
  by routing to open models, AI-assisted migrations, and Cursor usage statistics. Two cautions.
  It is partly paywalled, so check the free portion carries the detail before building on it.
  And it reports on other people's systems, so when the company has published its own write-up,
  that is the primary and this is the route to it.
- https://www.deeplearning.ai/the-batch/ — `[noticing]` Andrew Ng's weekly, and a **curated
  roundup rather than original reporting**, so it is a route to a primary and never a
  citation. Its real value is the
  research-to-practice bridge: it catches developments the harness-focused feeds miss and frames
  them for people who build rather than train. Strongest as the **industry-analysis slot in
  `articles.md`** and as a way to notice a topic; weakest as the primary source, because it
  summarises. When it points at something good, go fetch what it points at.
- https://www.deeplearning.ai/short-courses/ and `/courses/` — on-ramp only: `articles.md`
  further reading when a session assumes a concept, never the news lead.

**The basics on-ramp slot.** When a session assumes a concept the reader may not have
(attention, embeddings, LoRA, calibration, the agent loop), the on-ramp is **this site's own
`learn/` track first** — link it inline as `#learn/<slug>`, which is what the reader already
expects and the only on-ramp held to our own standard. After that, a Tier 1 conceptual doc or a
Tier 3 named practitioner. Do not reach for a third-party explainer site to fill this slot; most
of them fail the admission test below, and none of them are better than the chapter we wrote.
Do not re-teach a `learn/` chapter as "today's article" either — link it and move on.

---

## Tier A — ship it this week (50% of sessions)

### Coding Agents & Productivity  ·  `For: Using tools`  ·  target 3 per 10

The widest reader tier and the deepest bench — 90% of professional developers drive one of these
daily. Changelogs are the highest-yield feed on the whole list because they are dated, specific,
and describe something the reader already has installed.

- **Primary** — https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
- **Primary** — https://docs.claude.com/en/docs/claude-code/overview (hooks, skills, subagents,
  settings; pair a changelog line with the doc that explains it)
- **Primary** `[spine]` — https://code.visualstudio.com/updates — monthly, and roughly
  three-quarters of each release note is now AI: agent automations, voice mode, the Agents window
  in 1.137 (9 September 2026). The highest-reach surface on this whole list for the widest reader
  tier, and it was missing until 2026-09-15.
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
- **Primary** — https://developers.googleblog.com/ and
  https://ai.google.dev/gemini-api/docs/changelog — the practical Google feed, plus the dated
  Gemini API changelog, which is the one to build on for the same reason as above
- **Primary** `[reference]` — https://ai.meta.com/blog/ — Llama, PyTorch, real production
  numbers, but roughly one post a fortnight and nothing dated for seven weeks as of
  2026-09-15. Check it, do not plan around it.
- Secondary — https://huggingface.co/blog, https://artificialanalysis.ai/ (measured comparison
  rather than vendor claims), https://cookbook.openai.com/ and
  https://github.com/openai/openai-cookbook
- Secondary, other labs — https://mistral.ai/news, https://qwenlm.github.io/blog/,
  https://api-docs.deepseek.com/news/, https://cohere.com/blog, https://www.together.ai/blog,
  https://allenai.org/blog, and for xAI https://docs.x.ai/ plus
  https://huggingface.co/xai-org for model cards and weights. **Build on the technical report or model card, never the launch
  post.** An open-weights release with a real report is a session; the announcement of it is the
  press release this site exists not to be.

**Fetchability, checked and re-confirmed 2026-09-15:** every `openai.com` surface — `/news/`,
`/index/`, `/research/` — 403s to WebFetch, and so does `x.ai/news`. This is not a nuisance, it is
a gate: rule 4 says *verified, not remembered*, so a source you cannot fetch cannot be built on at
all. Route to the fetchable first-party surfaces instead — `platform.openai.com/docs/changelog`,
`cookbook.openai.com`, `developers.openai.com`, `docs.x.ai`, `huggingface.co/xai-org`. Those are
the **better** citation anyway, for a reason already in this file: build on the changelog, the docs
or the model card, never the launch post. Use HN only to notice that something shipped; following
it here and citing it was a rejection two sessions already shipped with.

### AI in Production  ·  `For: Shipping AI`  ·  target 1-2 per 10

- **Primary** `[spine]` — https://vllm.ai/blog — serving internals with numbers, several posts
  a week (KV-cache offloading, agentic serving, per-accelerator optimization). The most
  under-used source on this list: prescribed since the beginning and cited zero times, which the
  old `blog.vllm.ai` address — now a 301 — probably explains.
- **Primary** — https://modal.com/blog and https://www.baseten.co/blog/ — inference economics
- **Primary** — https://lmsys.org/blog/ — SGLang, throughput, scheduling
- **Primary** — https://engineering.fb.com/ (and `/category/ai-research/`) — Meta's *engineering*
  blog, distinct from `ai.meta.com/blog`: serving infra, storage, scale, with real numbers. One
  of the few places a production write-up says what actually broke.
- Secondary — https://blog.cloudflare.com/tag/agents/, https://developer.nvidia.com/blog/,
  https://www.databricks.com/blog/category/engineering
- Secondary — https://newsletter.pragmaticengineer.com/ — who is actually cutting inference
  cost and how, named and with numbers. Strongest for the routing and open-model-substitution
  decisions this category keeps circling; weakest on serving internals, which vLLM owns.

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

---

## Judging a source — both tracks

**Everything in this section applies to the daily lab and to Frontier equally.** It used to live
inside the Frontier section, which is why a daily-lab run had no reason to read it: on 2026-09-15 a
daily session shipped past the subject test and the repeat gate, and both of them were sitting one
heading below a banner saying "Frontier track". Placement is a rule's first line of defense.

### The admission test — is this source citable at all?

The four gates below judge whether a source is *good enough to build on*. This one comes first and
judges whether it belongs on the site at all. Both halves must hold:

1. **You can name the institution or the person accountable for the page.**
2. **A senior engineer would accept it as a citation in a design doc.**

That admits a named practitioner on a personal domain — Simon Willison, Hamel Husain, Eugene Yan,
Lilian Weng, Sebastian Raschka all publish on their own sites and all pass, because the author is
publicly identifiable and has standing in the thing they are writing about. It rejects a personal
site with no verifiable author standing no matter how useful the explainer is. The bar is
accountability, not domain shape. Pedagogical usefulness does not buy admission.

This matters because `articles.md` is published. A weak citation is a public statement about the
site's judgement, not an internal shortcut.

Three specific rejections that keep recurring:

- **The published spec, never the working repo.** When a standard has a dated, versioned surface —
  `modelcontextprotocol.io/specification/<revision>`, an API reference, a release note — that is
  the citation. ✗ `github.com/modelcontextprotocol/ext-tasks/blob/main/specification/...` as the
  article's authority. ✓ the published revision, with the repo cited separately *only* for a schema
  or code file and labelled as such ("the TypeScript schema, to paste into your client").
- **Aggregators are for noticing, never for citing.** Hacker News, Reddit, X, `huggingface.co/papers`
  and Papers with Code tell you something happened. Fetch what they point at and cite that. A link
  to the aggregator in `articles.md` means you never opened the original.
- **A practitioner's blog is an aggregator wearing a byline, and it is also a newsletter for their
  own projects.** This is the subtlest sourcing trap on the list, because the blog passes admission
  honestly — the author is named, has standing, and writes original work — so nothing stops it
  being used as the daily discovery feed. Measured on 2026-09-15, `simonwillison.net` was cited in
  **14 sessions, the third most-cited domain on the whole site**, behind only `arxiv.org` (33) and
  `github.com` (21), and it is one person's blog. He also maintains Datasette and LLM. So a feed
  used for discovery quietly supplies the *subject* as well, and on 2026-09-11 and 2026-09-15 it
  supplied the same project four days apart. Use the blog to notice, then go to the project's own
  docs — and when the item is about the author's own software, treat the project as the thing to
  run the repeat check against.
- **Vendor launch and press posts** are not primary sources for what changed. Build on the
  changelog, the docs page, the technical report or the model card.
- **An unknown author needs evidence, and is a last resort.** Passing admission is not the same as
  being a good choice. Prefer the first-party doc, the spec revision, the lab engineering post or a
  named practitioner with a public track record; reach for a post by an engineer nobody can place
  only when nothing better covers the point *and* the post carries its own strong evidence — a
  reproducible benchmark, a public repo, production numbers, a method you could re-run. "It
  explains it well" is not evidence.

### The subject test — is the AI the subject, or just how you found it?

**The AI must be the thing the article is about, not the provenance of the finding.** This is the
one property of a session that nothing else checks, because the whole site is an AI log and the
spec assumed it. It does not hold automatically, and the way it fails is specific: you find a
source where somebody used AI to discover something, and then you write about the something.

The shape to watch for is a source of the form *"we pointed a model at X and found Y."* That
source contains two candidate articles. One is about Y, and it is usually the more interesting and
more implementable of the two — which is exactly why it wins by default. It is also not an AI
article. The other is about doing the pointing: how to task the model, what it is good and bad at,
how you verify what it returns, what it costs to triage. That is the AI article, and it is the
harder one to write, so it needs protecting.

**Run the deletion test before you commit to the topic.** Strike every AI word from your planned
article — model, agent, prompt, inference, the vendor names. If what remains is still a complete,
coherent article that teaches the same lesson, the AI was scenery and the session is about
something else.

- ✗ 2026-09-15 shipped on a source where three coding agents found authorization bugs in Datasette,
  and the article explained the bugs. `## The Fix` spent 474 words on name resolution and
  permission checks with two passing mentions of a model. **`code_example.py` and `visualize.html`
  contained zero AI words between them**, and so did the ELI5. Delete "coding agent" from it and a
  complete application-security article remains.
- ✓ The same source, with the audit as the subject: how to task an agent for enumeration rather
  than for bugs, why several rounds beat one long session, why two models disagreeing is a signal,
  the two-human rule that makes a finding real, and what the triage actually costs. The
  authorization bugs become the worked example the agent is pointed at, not the payload.

Note what did **not** catch this, because it is the reason the test has to be explicit. The
category was `AI Engineering Practices`, the tags included `coding-agents`, and the title said
"With a Coding Agent" — so the existing rule that a title must name the AI system was satisfied.
Every mechanical signal read as AI while the body was about 1% AI by word count. A title naming
the AI is not evidence that the article is about it.

### Source concentration — one command, every day

`node build.js --mix` now prints a **Sources** block listing any domain that appears in 3 or more
of the last ten sessions. Read it before you pick, in the same glance as `DUE NEXT`.

A high count is not automatically wrong. `arxiv.org` will always be near the top and should be.
What the block is for is the case category balance cannot see: two sessions on the same project,
in *different* categories, reached through the same feed. The mix called both of those fine,
because it tracks tier and audience layer and has no idea what the article was about.

**If a single project or practitioner is carrying three of the last ten, open `journal.md` before
you commit to the candidate.** That is the whole rule. It costs one command and it is the check
that was missing on 2026-09-15.

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

## The Frontier track — sources only

Frontier is a **sourcing lane, not a second product.** A Frontier piece is written to the exact
same contract as a lab session: ELI5 first, basics before depth, all five artifacts,
`## Implementing It` as the longest section carrying *How you know it worked* and *When not to*,
the full glossary, and the same acceptance test — could a competent engineer ship (or reproduce)
this from the article alone? **Nothing about the writing changes. Only where the material comes
from, where it appears, and when it publishes.**

A paper is not an exception to any of that. The spec already says that when nothing is directly
shippable you implement the mechanism from scratch — that *is* the assignment here. *How you know
it worked* becomes "does your toy reproduce the effect the paper claims?", which is a sharper
verification than most lab sessions get. *When not to* becomes the honest read of where the
evidence stops.

**Never skip the ELI5 because the audience is advanced.** That instinct will return every time
you write for this track; refuse it every time. An article that assumes fluency serves only
readers who already have it — the smallest audience and the one that needs this site least. Depth
is earned in the back half of a piece, never bought by cutting the front.

### The Tier A tell — check this before you write

**If the candidate's honest category is Tier A, it is not a Frontier piece.** Added 2026-09-05,
after a Frontier session built on a university benchmark paper was filed under **Coding Agents &
Productivity** and the owner reported it as "weak for frontier category". The category was the
evidence, sitting in the file the whole time: Tier A is the *ship it this week* tier, the reader
changes how they work tomorrow. Frontier exists so frontier-lab research stops competing for the
daily slot, so a piece whose natural home is Tier A is by definition in the wrong track. Hold it
for a daily slot instead.

The selection failure underneath is worth naming, because it feels like good judgement while you
are doing it: you arrive at a shortlist through a papers feed, then rank the candidates by how
useful each is to the reader. That ranking is right for the daily lab and **wrong here**, because
it systematically promotes the least frontier-like paper on the list. **Frontier is a sourcing
lane, not a difficulty setting.** The question is whether the work is frontier-lab research, not
whether it arrived as a paper — an arXiv link is not a qualification.

The cadence rule makes the right answer cheap: Frontier skips a thin day, and a run that publishes
nothing is a successful run. There is never a reason to promote a daily-lab topic into this slot
to avoid an empty one.

### Where a Frontier session goes

`frontier/YYYY-MM-DD/` — same five files. Not `YYYY-MM-DD/`, not `learn/`. It never enters the
card grid, never appears in `journal.md`, and never counts toward `node build.js --mix`; the track
exists precisely so frontier material stops competing for the daily slot.

### Cadence: skip a thin day

The daily lab may never miss a day. **Frontier is the opposite: if nothing is worth publishing,
publish nothing.** Padding the track because the slot exists is the one failure mode that would
kill it — this audience will stop opening a tab that wastes their time once. Report the skip as a
normal outcome, not an error, and say what you looked at and why none of it cleared the bar.

### Sources

- **Primary** — https://arxiv.org/list/cs.AI/recent, https://arxiv.org/list/cs.LG/recent,
  https://arxiv.org/list/cs.CL/recent
- **Primary** — https://huggingface.co/papers — the daily filter; use it instead of raw listings
- **Primary** `[spine]` — https://www.anthropic.com/research — active, several posts a month
  (10, 9 and 4 September 2026 at the time of writing). **Not the same surface as
  `anthropic.com/engineering`**, which is a daily-lab source with a much slower cadence; the two
  are easy to conflate and only this one is a Frontier feed.
- **Primary** `[reference]` — https://transformer-circuits.pub/ — interpretability with unusual
  mechanical detail, but monthly to quarterly. Reach for it when the topic matches; it cannot
  carry a slot on demand.
- **Primary** `[spine]` — https://research.google/blog/ — several posts a week, and distinct from
  DeepMind's blog. Read it with a filter: much of it is science applications (genomics, climate,
  connectomics) that this audience has no use for, and the engineer-relevant work — tool-use
  datasets, forecasting foundation models — sits in the same feed.
- **Primary** — https://deepmind.google/discover/blog/ and https://ai.meta.com/research/
- Secondary `[reference]` — https://institute.deepmind.com/ — essays on AGI futures by Google
  and Google DeepMind researchers, published explicitly as discussion pieces rather than
  Google's position. **Never a primary source.** These are position and policy pieces, not
  methods, and a session built on one would have nothing in `Implementing It` — which is the
  hard reject at the top of this file, not a style preference. Two real uses: the wider-context
  slot in `articles.md`, and framing for a session whose mechanism comes from somewhere else.
  *The case for reasoning transparency* is the shape that works, paired with an interpretability
  result that can actually be implemented.
- **Primary** — https://www.interconnects.ai/ — post-training and model reviews from someone who
  trains them. Excellent for *finding* the thing worth explaining; go to the primary source to
  build on it
- Secondary — https://magazine.sebastianraschka.com/ and https://lilianweng.github.io/ — papers
  already translated into engineering terms; often a better route in than the paper itself
- Secondary — https://allenai.org/blog, https://mistral.ai/news, https://qwenlm.github.io/blog/,
  https://api-docs.deepseek.com/news/ — open-weights releases **with technical reports**
- Secondary — https://www.lesswrong.com/ and https://openreview.net/ for review threads when the
  argument about a paper is the story

The admission test, the subject test and the four source quality gates in
**Judging a source** above apply unchanged — a preprint from a
named lab passes admission, an anonymous write-up of it does not — with gate 3 reading: the source
must contain enough for you to implement the core mechanism from scratch. If it does not — no algorithm, no
released code, no reproducible detail — that is a thin day, and thin days are skipped.

## Worked example (last five sessions)

These already shipped. Use them as a calibration, not a schedule.

| Session | Why it would win or lose this rubric |
| --- | --- |
| Context Is a Budget (08-22) | **Win.** Reader 1 changes caching tomorrow. Primary: changelog + docs. |
| RAG chunk size (08-23) | **Win.** Reader 2 measures a pipeline they will ship. Action: grid-search chunk size. |
| Bigger VM / evals (08-23-s2) | **Win for reader 2.** Action: publish memory limits on the eval. Reader 1 still gets the "leaderboard gaps can be infra" warning. |
| Pixels Are Not Tokens (08-21) | **Borderline.** True and useful for vision cost, but Reader 1 has no Monday action unless they ship images. Prefer when Tier C is under weight. |
| Every Model Cheats (08-20) | **Lose today if Tier C is already heavy.** Strong paper, weak Monday action ("don't trust an anti-cheat prompt"). Hold for a week when A/B are due. |
