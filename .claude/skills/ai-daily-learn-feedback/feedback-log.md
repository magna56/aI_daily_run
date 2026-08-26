# Feedback Log

> Every note that changed (or deliberately did not change) the AI Daily Learn spec.
> Appended by the `ai-daily-learn-feedback` skill, newest at the bottom.
>
> This exists because spec edits compound. Without a record, a later note can quietly
> reverse an earlier one and leave the spec contradicting itself, with nobody able to
> say which rule was intended to win.

---

## 2026-08-24 — 2026-08-24 (MCP Deleted Its Handshake)

- **Note**: "it lack depth and also lacked what a client needs to do; we want our articles to be
  implementation heavy, this seems very advertisement type — how can you improve it so the
  engineers can actually use it"
- **Verdict**: standing rule (all four points)
- **Changed**: `SKILL.md` — "Depth means implementation detail, not more description": a longer
  account of what a release *says* is still a summary, however many numbers it quotes.
- **Changed**: `SKILL.md` — new required `## Implementing It` section between Key Technical
  Details and How It Connects: real code or a literal payload in fenced blocks *in topic.md
  itself*, before/after pairs, and separate code for **every role the change touches** — not
  only the role the source announcement was written for. This is the rule that answers "lacked
  what a client needs to do".
- **Changed**: `SKILL.md` — new `## Why It Matters` rules block banning momentum reporting
  ("largest revision since launch", "adoption was unusually fast", a vendor advocate quoted
  approving of it). That prose is what read as advertisement. Named quotes now have to carry a
  checkable technical claim.
- **Changed**: `SKILL.md` — top-of-file rule: write for the engineer who has to implement it,
  never for the ecosystem that shipped it; report adoption only where it decides something.
- **Changed**: `SKILL.md` — `What to do about it` must contain at least one *change*, not only
  an audit. "Go check whether your client honours the TTL" now owes its "and here is the fix"
  half, pointing at `Implementing It`.
- **Changed**: `SKILL.md` Step 6 — `code_example.py` must **implement** the mechanism, not only
  price it. Byte counts and cost curves are a result the implementation prints, never the whole
  script. (Today's example was a pure cost model — it measured the change without ever showing
  a compliant client.)
- **Changed**: `contract.md` — `Implementing It` added to the required section order and written
  up as a hard requirement: at least one fenced code block in `topic.md`, both roles covered, a
  link to `code_example.py` does not satisfy it.
- **Changed**: `selection.md` — new **Implementable** gate in the shortlist scoring (can you
  name the code that changes, for every role?) and a new hard reject for topics whose honest
  write-up would be a description of an announcement.
- **Changed**: `build.js` — `--check` now warns when a daily session dated on/after
  `IMPLEMENT_SECTION_SINCE` (2026-08-25) has no `## Implementing It` heading, or has the heading
  but no fenced code block anywhere in `topic.md`. Date-gated on purpose: the back catalog
  predates the rule, and warning on forty old folders trains everyone to ignore the warnings.
- **Not changed**: the published 2026-08-24 article. Offered, not done — the back catalog is a
  dated log and the standing preference is to leave old sessions alone. The spec change is what
  the note was for.

### Follow-up, same note — the publish path

Asked to bring `/ai-daily-learn-publish` into accordance. It already delegates the whole session
workflow to `/ai-daily-learn` and deliberately restates none of it, so the new content rules
reached it for free — the real gap was that nothing *gated* the live push.

- **Changed**: `ai-daily-learn-publish/SKILL.md` — new **Step A½: Gate the session before it goes
  live**, between generation and publish. Re-runs `node build.js --check` and blocks on any
  content-contract warning naming today's id (`Implementing It`, fenced code block, anything
  about `visualize.html`). Other warnings stay advisory — a `code_example.py` that exits non-zero
  is a rendered traceback by design. Also names the two rules no linter can see: both roles
  covered, no momentum reporting.
- **Changed**: `ai-daily-learn-publish/scripts/publish.sh` — the same gate as a deterministic
  `content_gate()` that runs before staging and exits 1 with the offending warnings. The prose
  gate only binds a model that reads it; the 11:00 LaunchAgent runs unattended with nobody
  reading the log, which is exactly where a non-compliant article would ship unnoticed.
  `ADL_SKIP_GATE=1` is the deliberate override.
- **Changed**: `ai-daily-learn/SKILL.md` Step 11 — the two new warnings added to the fix-before-
  you-stop list, plus the by-eye pair. Step 11 was the checklist the workflow already ran, so the
  rule lands where it will actually be read rather than only in the section that defines it.
- **Not changed**: the Cursor twins. Both are thin runners that link to the canonical files and
  copy no section list, so they inherit all of this.

## 2026-08-24 — publish path, discoverability

- **Note**: "we had pages for rss feed, would they be updated on new publish, will our skill do
  that? if not update the skill — we want our articles discoverable"
- **Verdict**: mostly a false alarm, one real doc defect, one missing verification
- **Not changed**: the mechanism. `feed.xml`, `sitemap.xml` and `site/og/<id>.png` are build
  outputs — `build.js` regenerates all three from the session folders on every build, and
  `deploy.sh` runs `make site` before publishing, so every publish already carries them to both
  hosts. No skill step was missing and nothing is hand-maintained. Verified live: the newest
  session appears in `feed.xml` and `sitemap.xml`, its OG card serves 200, and every generated
  session page carries `<link rel="alternate" type="application/rss+xml">`.
- **Changed**: `ai-daily-learn-publish/SKILL.md` — the "site deploy failed" note said only the
  reader goes stale. That was true before the RSS/OG commit and is now wrong: a failed deploy also
  leaves the article out of the feed, out of the sitemap, and without an OG card, so it is
  invisible to aggregators, crawlers and social previews. Reworded as a failed *publish*.
- **Changed**: `ai-daily-learn-publish/SKILL.md` Step C — renamed to "Confirm it is discoverable,
  then report" and given three curl checks (feed, sitemap, OG card) to run before reporting the
  session as live. The failure mode being guarded is a deploy that reports success while serving
  stale output, which is indistinguishable from a good one without asking the live site.

## 2026-08-24 — corpus-wide, audience mix

- **Note**: "audience is engineers... many are learning AI for productivity and code writing,
  some are creating skills/MCPs/agents, some are deploying in prod, fewer are doing LLM
  modelling or inference. I felt some articles are tough to understand and not implementation
  focused. What topics, content and difficulty should we focus on?"
- **Verdict**: standing rule, and a compliance gap — the rule already existed and was not
  being followed, because nothing made it checkable on the day.
- **Measured first** (22 daily sessions): `For: Using tools` 9% vs `For: How models work` 32%,
  an inverted pyramid; Tier C at 32% overall and 40% of the last 10 against a documented 20%
  cap, including three consecutive Tier C sessions (08-19, 08-20, 08-21); Tier A at 41% against
  a 50% floor; `Coding Agents & Productivity` 1 of 22 despite the spec naming it the single most
  relevant category; Level skewed `Deeper` 36% vs `Start here` 23%.
- **Changed**: `build.js` — `CATEGORY_TIERS` is now the source and `CATEGORIES` is derived from
  it, so tier membership is machine-readable and cannot drift from the list. Added a trailing-10
  audience-mix model (`MIX_BANDS`, `mixRows`, `mixSummary`, `mixDrift`) with a new read-only
  `--mix` flag that prints the mix, DUE NEXT and AVOID without building or running any code, and
  drift warnings that surface in every build and `--check`.
- **Changed**: `selection.md` — rewritten around an explicit **reader pyramid** keyed on `For`
  rather than category alone, with per-10 targets (3 / 3 / 3 / 1), and a new Step 0 that runs
  `--mix` before any source is opened. A `For` layer named as due now outranks the category
  rotation.
- **Changed**: `SKILL.md` Step 2 — same Step 0, plus a Level budget of 3 `Start here` / 6
  `Building` / 1 `Deeper` per ten, with `Deeper` called out as rationed.
- **Changed**: `Makefile` (`make mix`) and `CLAUDE.md` command list.
- **Not changed**: the back catalog. Bands are deliberately loose (ten sessions cannot land on
  50/30/20 exactly) so the warning can actually go quiet once the mix is corrected.

## 2026-08-24 — sources, keyed to category

- **Note**: "I'm concerned about the quality — what sources will we use to gather info and
  generate articles? Give me a list for each category."
- **Verdict**: standing rule, and the root cause of the tier drift logged above.
- **Diagnosis**: the Sources section was keyed to *reader* (Reader 1 / Reader 2 / Frontier), not
  to category — but selection picks a category first. Six of eleven categories had no list of
  their own, while arXiv was listed, always fresh and always fetchable. The path of least
  resistance ran straight to Tier C. A category with no sources loses to a category that has
  them, every time.
- **Changed**: `selection.md` — Sources rewritten per category, in tier order, each entry marked
  Primary (what a session is built on) or Secondary (second perspective, articles.md), with a
  note on what each feed is good for. Coding Agents & Productivity and AI Engineering Practices
  got the deepest benches, matching their 3-per-10 targets and the measured audience pain
  (11.4 hrs/week reviewing AI-written code; 84% use, 29% trust).
- **Changed**: `selection.md` — new **Source quality gates**: dated and primary; something
  changed; implementable from what the source says (enough to write `## Implementing It` with
  code for every role); verified by fetching, never written from recollection.
- **Verified**: all 52 URLs in the file return 200. One candidate (`blog.langchain.com/tag/
  langsmith/`) 404'd and was dropped rather than shipped.

## 2026-08-24 — publish path honours the audience mix

- **Note**: "update the skill which publishes so we honour this from next articles"
- **Verdict**: standing rule. The generator already inherits the mix rules through Step 0; what
  was missing was enforcement at the moment of publishing.
- **The distinction that shaped the design**: trailing-window *drift* must never block a publish,
  because the only way out of drift is to publish the sessions that correct it — a blocking drift
  check deadlocks. What can be blocked is a *per-session* question: did this session take a slot
  that was already at cap in the ten before it? That has a yes/no answer on the day, which is
  exactly what nobody could evaluate when three consecutive Tier C sessions shipped.
- **Changed**: `build.js` — `--mix <id>` judges one session against the window strictly preceding
  it and exits 3 if its tier or `For` layer was already at cap. Bare `--mix` still prints the
  readout. Verified retroactively: 2026-08-22 passes, 2026-08-21 (the third consecutive Tier C)
  is caught with both reasons named.
- **Changed**: `publish.sh` — the audience gate runs inside `content_gate()` and refuses the
  publish on exit 3. Output is captured rather than piped, so the check does not depend on
  `PIPESTATUS` and therefore on which shell ran the script.
- **Changed**: `ai-daily-learn-publish/SKILL.md` — Step A½ documents both gates and states plainly
  that drift warnings are advisory; Step C now prints `--mix` after publishing so the next run
  starts from the moved mix; Error Handling names the blank-day trade-off explicitly and points at
  `ADL_SKIP_GATE=1` as the deliberate override.
- **Trade-off recorded**: a blocked publish means no article that day. Accepted on the grounds
  that a fourth consecutive frontier session costs more than a blank day and the block is
  recoverable by regenerating. Flagged to the user as reversible to warn-only.

## 2026-08-24 — no gate may cost a day

- **Note**: "we can't have a blank day"
- **Verdict**: standing rule, and it reverses a trade-off accepted an hour earlier in this same
  log. Recorded loudly for that reason: the audience gate was deliberately designed to block a
  publish, and that design is now wrong.
- **Changed**: `publish.sh` — the audience gate warns and continues instead of exiting 1. The
  violation is still printed in full, with a pointer to run `--mix` for tomorrow's pick.
- **Changed**: `ai-daily-learn-publish/SKILL.md` — Step A½ moves the action earlier rather than
  softening it: on exit 3, regenerate for the due category *while the article is still cheap to
  change*, because a wrong-mix session costs a slot in a ten-session window that takes ten days
  to work off. But if regeneration is not on the table, publish anyway and record the miss.
- **Changed**: Error Handling now states the constraint as a rule with no third branch — fix it,
  or publish it as-is and say so. "Never end a run with the session unpublished and the day
  empty." The 11:00 job is unattended, so any gate that can deadlock it silently stops the site,
  which is worse than any single article's shortcomings.
- **Content gate**: still blocks, but its recovery is an in-place edit the same run can make and
  retry, and the skill now says so explicitly and offers `ADL_SKIP_GATE=1` as the last resort
  rather than leaving "abort" as an implied option.
- **Design principle for future gates**: a gate may warn freely, and may block only where the fix
  is an in-place edit the same run can perform. It may never be designed such that the correct
  response to failing it is to skip the day.

## 2026-08-24 — implementation as the shape, not a section

- **Note**: "the articles need to be implementation focus, engineering implementation — an
  engineer reading this should be able to take something and implement it in their work. Not
  shallow or space filler, but generates real value. Assume you are teaching / upskilling your
  engineers for practical implementation."
- **Verdict**: standing rule. Second pass on the same concern as the first entry in this log,
  which added `## Implementing It`. That fix was necessary and insufficient.
- **Measured before editing**: the 2026-08-24 article is **97% explanatory prose, 3%
  implementation, zero fenced code blocks**, with the Glossary at 21% — as long as every
  technical section combined. One required section cannot outweigh nine explanatory ones; the
  document's *shape* was the defect, not a missing rule.
- **Changed**: `SKILL.md` — an **acceptance test** governing the whole document: could a
  competent engineer ship the change from the article alone, without opening the source? Plus the
  register: you are the senior engineer writing the internal doc that upskills your team, not a
  reporter filing on a development.
- **Changed**: `SKILL.md` — structural rule: **`Implementing It` must be the longest section in
  the document**, with the 97/3 measurement as its justification. Tighten the explainers; never
  pad the implementation.
- **Changed**: `SKILL.md` — `Implementing It` now has three labelled parts. **How you know it
  worked** (the number that moves, the log line, the assertion — "make sure caching works" is not
  a verification) and **When not to** (the counter-case and the cost) are new and are the two
  that turn a tutorial into an engineering document.
- **Changed**: `SKILL.md` — an explicit anti-filler list naming the patterns that produce padding
  (the same point restated across three sections, a `Why It Matters` that says it matters,
  history the reader does not need to make the change), and a Glossary cap of one sentence per
  term.
- **Changed**: `contract.md` — the four conditions restated as a checklist, with the acceptance
  test behind them.
- **Changed**: `build.js` — added `splitSections()` (fence-aware) and three new checks: the two
  labelled parts, and whether `Implementing It` is the longest section. Verified both ways: an
  explainer-shaped article trips all three; a correctly-shaped one is clean.

## 2026-08-24 — the teaching mission, applied to every artifact

- **Note**: "the focus on leaving engineers with a practical idea — this philosophy should be
  used in selecting content or links, writing articles, writing code. Assume you are teaching
  your engineers to become AI engineers, the best on the planet."
- **Verdict**: standing rule, and a framing one. The previous two passes fixed the write-up; the
  same philosophy had not reached source selection, `code_example.py` or `articles.md`, which is
  where the user pointed.
- **Changed**: `SKILL.md` — a **Mission** section now opens the file and everything hangs from
  it. One test — *does the reader leave with something they can build with?* — mapped explicitly
  onto all five decisions (topic, sources, write-up, code, diagram/visualizer), with the line
  that resolves ambiguity: a session that leaves an engineer better informed but no more capable
  has failed. Accuracy and sourcing are table stakes; capability is the product.
- **Changed**: `SKILL.md` Step 6 — rewritten around liftability rather than runnability. Put the
  reusable core at the top as a named function so one piece can be copied out; comment the
  decisions rather than the syntax, because that is what transfers judgement; print the numbers
  the article quotes so the claim is verified rather than asserted; put the interesting parameter
  at the top so a reader can change one number and watch the conclusion move.
- **Changed**: `SKILL.md` Step 9 — curation reframed as teaching. Summaries say what the reader
  will be able to *do*, not what the piece covers, with a ✗/✓ pair; each link says who it is for
  and when to read it; at least one link must be something openable in an editor (repo, reference
  implementation, spec with examples); rank by teaching value over authority; never pad to five.
- **Changed**: `visualize.md` — the same test at the top: build intuition for a mechanism the
  reader is about to implement, not decoration that restates the write-up.
- **Changed**: `selection.md` — a sixth shortlist gate, **Leaves them capable**: name what an
  engineer can do afterwards that they could not before. "Understand X better" fails it.

## 2026-08-24 — the Frontier track

- **Note**: a separate track for frontier-lab research and papers, for advanced AI engineers, on
  its own tab and never in the card grid. Then, across the design: "still explain from basic ELI5,
  a software engineer learning before diving deep", "just the source changes for sourcing the
  articles, our core vision still remains same", "if there is a thin day you feel it's not worth
  it we don't publish", "we need SEO and searchability on Google", "all should be covered in our
  /ai-daily-learn-publish skill".
- **Verdict**: new track, one contract. Two proposals were made and rejected during the design,
  both worth recording because both will be tempting again.
- **Rejected — "assume fluency, drop the ELI5 for an advanced audience."** It optimises for
  readers who already understand the material: the smallest audience and the one least served by
  this site existing. The mission is carrying a working software engineer from an analogy to
  implementing the mechanism. Depth is earned in the back half, never bought by cutting the front.
- **Rejected — a separate Frontier contract** with its own acceptance test, dominant section and
  code rule. Over-engineering, and a second standard to maintain and drift. The existing contract
  fits research *better* than the fork did: "implement the mechanism from scratch" is already the
  rule for papers, *How you know it worked* becomes "does your toy reproduce the claim?", and
  *When not to* becomes where the evidence stops.
- **Changed**: `build.js` — compiles `frontier/YYYY-MM-DD/` with `kind: "frontier"` and a
  `frontier-` id prefix (a lab and a Frontier piece can share a date and would otherwise collide
  on `site/<date>/`). Excluded from the grid, from category pages and from `mixRows()`; included
  in the sitemap, RSS, search, its own OG card and a new crawlable `/frontier/` landing page with
  `CollectionPage` JSON-LD.
- **Changed**: `index.html` — nav pill, `#frontier` route, the dated index list (no cards), the
  homepage strip showing the newest piece, `← Frontier` back link. Pill and strip stay hidden
  until the track has content: an empty tab is worse than no tab.
- **Changed**: `selection.md` / `SKILL.md` / `contract.md` — the Frontier sourcing lane, the
  two-track table, and one line making explicit that `contract.md` governs both. No new contract
  file, by design.
- **Changed**: `publish.sh` + the publish skill — publishes `frontier/<date>`, skips the audience
  gate as not applicable, names the track in the commit subject, and states that a Frontier run
  publishing nothing is a **successful** run.
- **Not changed**: skipped days render silently — no gap row in the index.

## 2026-08-25 — 2026-08-25 (`Bash(rm *)` hooks session)

- **Note**: "Why It Matters is momentum reporting — 'hooks are becoming the standard… Cursor
  shipped… 2.1.243 alone added modelPicker… the governance surface is growing fast.' That is
  market, not mechanism."
- **Verdict**: compliance gap — `## Why It Matters` already banned momentum reporting, and it
  shipped anyway, because nothing but eyesight was checking.
- **Changed**: `SKILL.md` `## Why It Matters` rules — added "Never cite another vendor's changelog
  as proof the topic matters", with the ✗/✓ pair taken verbatim from this session's own two
  paragraphs. `build.js` — `Why It Matters` now warns on a version string, a rival product name,
  or adoption language (date-gated from 2026-08-26).

- **Note**: "visualize.html is not done without CSP + Reset + session `data-visualizer`" — this
  file had a bare marker, no CSP, no Reset, `body.scrollHeight` only.
- **Verdict**: compliance gap for CSP / Reset / `documentElement` height (all three already in
  `visualize.md`); standing rule for the marker carrying the session id, which was previously
  "value optional".
- **Changed**: `visualize.md` — marker must be `data-visualizer="<session-id>"`; Reset must return
  every input to the article's own numbers; a closing note that four of the contract items are now
  build warnings. `build.js` — warns on missing CSP meta, wrong/empty marker value, missing
  `documentElement.scrollHeight` + `ResizeObserver`, and missing Reset control.

- **Note**: "code_example.py is 171 lines (limit 150). The combo demo at the bottom is the cut."
- **Verdict**: compliance gap — the cap was written down and unenforced.
- **Changed**: `build.js` — warns over 150 lines. `SKILL.md` Step 6 — says the linter enforces it
  and names the combined "and now all of it together" finale as the usual cut.

- **Note**: "`Bash(rm *)` is a Claude Code glyph. A Cursor-only scroller does not know that
  language. The Hook sentence is the actual title for that reader."
- **Verdict**: standing rule. The title section said "write it for someone who has only used
  Cursor" but never said what disqualifies a title under that test.
- **Changed**: `SKILL.md` title rules — "No glyph only one product's users can read", with the
  ✗/✓ pair and the swap test (if the `Hook` line is the better title for that reader, use it).
  Also added to the Step 11 by-eye checklist, replacing the momentum item that is now linted.

- **Not changed**: the softer misses — `Level: Building` on a `Using tools` job, the 311-word
  glossary, five articles where three would do, and the `guard.sh` regex needing a sentence
  saying it is still not a parser. All four are real, but the spec already caps the glossary
  ("one sentence each"), already sets 3-5 articles, and already defines the Level ladder; these
  are judgment calls on the day, not missing instructions. Adding a sentence for each would grow
  the spec without changing what a future session does.
- **Not changed**: the session folder itself, and the new checks are gated from 2026-08-26 so the
  published record does not warn forever. Offered to fix the title, the Why It Matters tail, the
  visualizer contract and the 21 extra code lines in place.

## 2026-08-25 — spec-wide (the article/code division of labour)

- **Note**: "the article should be practical enough for the engineers to implement; the code we
  provide should complement it, not make the article itself an implementation."
- **Verdict**: standing rule, and a **deliberate rebalancing of an existing one** — flagged here
  because it modifies rules written on 2026-08-24 rather than adding beside them. Those rules
  ("`Implementing It` must be the longest section", "a link to `code_example.py` does not satisfy
  the fenced-block requirement") were correct against the failure of the day, which was an
  article with *no* code at all. Applied without a ceiling they push the other way, until the
  write-up becomes the program and the Code tab repeats it.
- **Changed**: `SKILL.md` — a division-of-labour table at the structural rule. `topic.md` owns
  the **decisions** (what changes, which file, which role, the real config key, how you know it
  worked, when not to) and shows the lines that *change*; `code_example.py` owns the **complete
  runnable artifact**. Neither restates the other: "if someone could read the article and find
  nothing new in the Code tab, this file has not done its job; if they could skip the article
  because this file contains it all, the article has not done its."
- **Changed**: `SKILL.md` + `contract.md` — the longest-section rule is now measured on **prose,
  with fenced code excluded from every section's count**. This is the load-bearing part: with
  code counted, the cheapest way to pass the rule was to paste the program into the write-up,
  which is exactly the failure this note names. The 97/3 justification is unchanged — the rule
  still says the explainers may not outweigh the implementation, it just can no longer be bought
  with a code dump.
- **Changed**: `SKILL.md` Step 6 — `code_example.py` written up as the *completion* of the
  article rather than an appendix to it.
- **Changed**: `build.js` — `proseOnly()` and `fencedBlocks()` helpers; the longest-section check
  measures prose; a single fenced block in `Implementing It` over **30 lines** warns; a block
  more than **70% verbatim `code_example.py`** (on lines over 24 characters, so shared imports
  and `def` headers do not trip it) warns. Verified on a throwaway fixture: an oversized block
  and a pasted block each trip their own warning, and no real session trips either.
- **Not changed**: `Implementing It` stays required, with its three labelled parts. The note was
  about the *balance* between the two artifacts, not about dropping the section — checked against
  the first entry in this log before editing, per the rule at the top of this file.

## 2026-08-25 — spec-wide (house title form, and what to learn from ByteByteGo)

- **Note**: "these titles are better, they are inspired by ByteByteGo and ByteByteAI — update the
  skill to have titles like these in future, and see ByteByteGo articles on AI for style, content
  and depth, we need to take some inspiration from them." Clarified immediately after: "we keep
  our own persona, just learn from them what we can do better, not copy them."
- **Verdict**: standing rule, and it **demotes an existing rule** — flagged here rather than done
  quietly. "Lead with the surprise, the cost, or the question" is no longer the primary
  instruction for titles.
- **Changed**: `SKILL.md` title rules — the explanatory form is now the default, with a table of
  the four shapes drawn from real ByteByteGo titles (`How X Works` / `How X Does Y`; `A vs B`;
  `Name: plain-English gloss`; `A Guide to X`). The surprise is explicitly optional and belongs in
  `Hook`, the first paragraph and `Key insight`, where it has room to be true. Every ✓ example in
  the anti-academic list was rewritten into the house form so the examples stop teaching the old
  rule.
- **Changed**: `SKILL.md` — the colon form needed disambiguating, because the spec already bans
  `Method: Formal Description via Mechanism`. The colon is allowed when the tail is plain English
  about what the thing does for the reader (`GraphRAG: How AI Answers Questions Hidden Across Many
  Documents`) and banned when it is a formal restatement (`LUMI: Tokenizer-Agnostic LLM-Based
  Lossless Image Compression`).
- **Changed**: `SKILL.md` — new "What to borrow from ByteByteGo — and what stays ours" block under
  the register rule: open on the specific failure rather than a definition; scaffold through
  concrete scenarios before the solution; vary paragraph rhythm and land ideas in one-sentence
  paragraphs; let the diagram carry a step of the argument. Written from two of their AI pieces
  (*How Agentic RAG Works*, *A Guide to LLM Evals*), not from memory.
- **Not changed, deliberately**: their AI articles carry no code and end at understanding. The
  block says so explicitly and keeps `Implementing It`, `code_example.py`, **How you know it
  worked** and **When not to** as ours — "borrow their clarity, keep our payload." The user's
  clarification about persona is quoted into the spec in that form so a future session cannot
  read this as a licence to imitate.
- **Not changed**: the no-product-glyph rule and the "readable to someone who has only used
  Cursor" test. The house form reinforces both — its ✓ example was updated to the shipped title.

## 2026-08-25 — spec-wide (the seven-section order)

- **Note**: "the section order seems difficult to follow — like Key Technical Details, What It Is
  after software engineer's perspective, and Key Technical Details being at the last." Followed by
  market research on ByteByteGo and comparable publications, then: Option B, drop the Glossary and
  try it ByteByteGo's way for now, keep ELI5, and use topic-named headings.
- **Verdict**: standing rule. The largest structural change the spec has taken.
- **Measured before editing**: the old order explained the topic **four times** (ELI5, For a
  Software Engineer, What It Is, Key Technical Details) and named the object only in the fifth
  section. Five of eleven headings were function labels that could sit on any article. Across the
  last eight sessions: ~2,250 prose words, which is inside ByteByteGo's ~2,100-2,300 band — so
  length was never the problem, repetition was, and it was created by the order rather than by
  the writing.
- **Also measured**: `For a Software Engineer` and `How It Connects to What You Know` were the
  same move done twice, 150 lines apart, in three of four sampled sessions (08-24 said "session
  affinity … moved off `JSESSIONID`" in one and "if you have ever migrated a web app off
  server-side sessions onto signed tokens" in the other). That duplication, not the bridge
  section itself, was the thing to cut.
- **Changed**: `contract.md` + `SKILL.md` — seven sections: ELI5 → The Problem → **How <the
  thing> Works** → For a Software Engineer → What This Means for You → Implementing It → **When
  <the thing> Is the Wrong Tool**. Sections 3 and 7 are named for the topic and matched by
  pattern (`^How `, `^When `); the other five are fixed. `###` sub-headings inside section 3 are
  named for their subject, ByteByteGo-style.
- **Changed**: `SKILL.md` — `For a Software Engineer` moved from third to fourth, *after* the
  mechanism. While it ran third it had to teach the topic before it could draw the analogy, which
  is why it was the second-longest section (304 words on 2026-08-25). It is now capped at
  ~150-200 words and told to compare, not re-explain. It stays: no comparable publication
  translates AI topics into engineering the reader has already shipped, which makes it the most
  distinctive section on the site.
- **Changed**: the counter-case is promoted out of `Implementing It` into section 7 with its own
  heading, and closes on the questions a reader should ask before adopting — the move Eugene Yan
  and ByteByteGo both end on.
- **Changed**: **no Glossary.** Terms are defined in the sentence that first needs them. The
  discipline it enforced (every acronym glossed, units explained by what they buy you) is kept,
  inline. Reversible if it reads worse in practice — the user asked to try it this way for now.
- **Changed**: `build.js` — `SECTION_ORDER_SINCE` (2026-08-26), `FIXED_SECTIONS`, `MECHANISM_RE`,
  `COUNTERCASE_RE`; warns on a missing fixed section, a missing/unnamed mechanism or counter-case
  heading, any retired section still present, and wrong order. The momentum check moved from
  `Why It Matters` to `The Problem`, and the "When not to" check inside `Implementing It` now
  only applies to sessions before the cutover. Verified with two fixtures: correct order clean,
  old order trips all seven warnings.
- **Not changed**: `Explain Like I'm 5` stays, at the user's explicit call — it is the site's
  persona and no reference publication has it. The 41 back-catalog sessions keep the old order
  and are not warned on.

## 2026-08-25 — 2026-08-25 (first article rewritten into the seven-section order)

- **Note**: "update it and publish" — rewrite the current session into the new shape.
- **Two rule corrections found by doing it**, both logged because they change a rule written
  hours earlier:
  1. **The counter-case is now counted with `Implementing It`.** Carving `When not to` out into
     its own section mechanically took ~140 words off the implementation, so the longest-section
     rule started firing on an article that had not padded anything. The rule's purpose is that
     the explainers must not outweigh the implementation, and the counter-case *is*
     implementation guidance — when not to apply the change. `build.js` now sums section 6 and
     section 7 and compares that against the largest single explanatory section.
  2. **A bare version number is no longer a momentum tell.** The heuristic flagged "Version
     2.1.243 shipped a fix for the noisy direction", which is a mechanism claim, not market
     news. Rival product names and adoption language stay; `\d+\.\d+\.\d+` is dropped. The
     warning also stopped hardcoding "Why It Matters" now that the section can be "The Problem".
  3. The old `Implementing It` must contain "When not to" check now passes if the session has a
     counter-case *section* instead — either shape satisfies it, which keeps the Frontier track
     and the back catalog valid without a date branch.
- **Changed**: `2026-08-25/topic.md` — 11 sections to 7. `What It Is` + `Key Technical Details`
  merged into `## How the Two Filters Read Your Rule` and compressed 594 → 513 words with three
  topic-named `###` sub-headings; `Why It Matters` folded into `The Problem`; `For a Software
  Engineer` moved after the mechanism and cut 304 → 226 words, now comparing rather than
  re-explaining; the counter-case promoted to `## When a Hook Is the Wrong Tool` and closed on
  three questions; `How It Connects` reduced to one pointer line; `Try It Yourself` and the
  Glossary dropped, with every glossary term redefined inline at first use.
- **Changed**: `index.html` — the reader's Publish teaser cut from 103 to 68 characters and no
  longer leads with "public repo", which the user said could put people off. The disclosure stays
  where the action is: the Code pane's Publish button still says it creates a public repo.
- **Result**: `2026-08-25` is clean under the full new contract, and `SECTION_ORDER_SINCE` moved
  to 2026-08-25 so it is the enforced first article in the new shape rather than an exception.

## 2026-08-26 — 2026-08-26 (the CI-gate article's own title)

- **Note**: "I'm not very happy with the title... play a role of an engineer reading this title
  and discuss with me what should the title [be]." Then, after picking one of three proposed
  alternatives: "update the skill on how to set titles i.e by becoming an engineer reader and
  thinking what does the title mean, is it useful enough for me to click on it and read... title
  is our start point it needs to be better."
- **Verdict**: standing rule. The site already had title *rules* (explanatory form, no
  product-glyph, ban academic formatting); it had no title *check* — nothing that made the
  generator actually read a draft title the way a cold reader would before accepting it.
- **Changed**: `2026-08-25/topic.md`'s own title, live: `How an AI Code Review Becomes Something
  CI Can Gate On` → `How to Turn AI Code Review Comments Into a CI Gate` — swapped once in
  `topic.md`'s H1, `articles.md`'s `# Further Reading:` header, and the `journal.md` entry
  heading, all three checked for consistency before pushing.
- **Changed**: `SKILL.md` — a new required pass under the title rules: read the draft title as
  the cold engineer, not as its own author, and ask "what does this tell me I'd be able to do,
  and is that specific enough to click." Names the actual failure pattern from this title as the
  thing to catch: a **placeholder word standing in for the real one** — vague nouns ("something,"
  "a way") and weak/passive verbs ("becomes," "involves") where the article's own concrete noun
  or verb belongs instead. Uses this exact before/after as the worked example, since it is the
  case that prompted the rule.
- **Not changed**: the four title shapes (`How X Works`, `A vs B`, `Name: gloss`, `A Guide to X`)
  from the 2026-08-25 house-style change. This is a check applied *before* accepting whichever
  shape was chosen, not a fifth shape.
