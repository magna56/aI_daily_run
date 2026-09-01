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

## 2026-08-27 — 2026-08-27
- **Note**: "The Problem shortne the section ans the what it is section the text is too long and
  the overall articles felt so wrong that even I the owner of the site lodt interest even after
  multiple trailes... the topic it start intresting but the details felt too specfic and boring".
  Read on the GitHub Pages mirror; reported as happening across multiple sessions, not just this
  one.
- **Verdict**: compliance gap (the density half) + standing rule (the borrowed-detail half).
  SKILL.md already said *"our sessions drift toward uniform dense blocks, which is what makes them
  tiring rather than long"* — as advice, unmeasured, and every session ignored it. Diagnosis was
  confirmed by measurement rather than impression: `The Problem` was **183 words in one paragraph**
  and the mechanism section contained an **89-word single sentence** enumerating the source paper's
  eight-layer taxonomy. Both passed every existing check, because every length rule in the spec is
  measured per *section* while a reader gives up inside a *paragraph*.
- **Changed**: `build.js` — new date-gated `READING_RHYTHM_SINCE = 2026-08-28` lint over the three
  on-ramp sections (`Explain Like I'm 5`, `The Problem`, the mechanism section): warns on any
  paragraph over 110 words, any sentence over 45 words, and a single-block `The Problem`. The
  sentence warning quotes the offending clause back, because in practice it is always a list of the
  source system's own terms. Verified to fire on all three of 2026-08-27's defects and on no
  back-catalog session.
- **Changed**: `SKILL.md` (mechanism-section rules) — the one genuinely new rule, from Lindsay
  Brunner's technical-storytelling piece: **every detail must change a decision the reader makes,
  enable an action they can take, or alter an outcome they care about**, plus an explicit ban on
  transcribing the source system's taxonomy, with this article's eight-layer paragraph as the ✗ and
  a three-layer version as the ✓. This is the rule that owns "the details felt too specific and
  boring" — the density lint only catches the symptom.
- **Changed**: `SKILL.md` — the "vary the paragraph rhythm" bullet now names the enforced caps
  instead of asking nicely; `The Problem`'s rules gain "never one block."
- **Changed**: `contract.md` — reading rhythm promoted into the hard contract next to the section
  order, with the uncheckable companion rule (detail must earn its place against the reader, not
  the source) stated alongside it.
- **Not changed**: the seven-section order, the `Implementing It` longest-section rule, and the
  per-section word guidance. The complaint was density and detail-selection *within* sections, not
  the shape of the document — and the same measurement showed `Implementing It` and the
  counter-case were already well-paced. Weakening the depth rules to make articles shorter would
  trade the site's payload for readability; the fix is that depth must be the reader's, not the
  source's.

## 2026-08-27 — (spec-wide, no target session)
- **Note**: "also the new article the skill /ai-daily-learn-publish and /ai-daily-learn-github
  SHOULD ALWAYS use opus". Said directly after rejecting a session that had been generated on
  Sonnet 5.
- **Verdict**: standing rule, and a compliance gap in how the existing rule was written.
  `ai-daily-learn`'s Session Parameters already asked for Opus, but phrased it as flag-and-ask —
  which was satisfied on 2026-08-27 by generating the entire session on Sonnet and mentioning the
  model in the closing summary. A warning delivered after the work is finished costs a whole
  session.
- **Changed**: `ai-daily-learn-publish/SKILL.md` and `ai-daily-learn-github/SKILL.md` — added
  `model: opus` to the YAML frontmatter. This is a real Claude Code skill field (confirmed against
  code.claude.com/docs/en/skills: "Model to use when this skill is active... applies for the rest
  of the current turn"), so it now enforces the model rather than asking for it. The turn-scoped
  override also covers the nested `ai-daily-learn` run in Step A of both skills.
- **Changed**: `ai-daily-learn/SKILL.md` Session Parameters — rewritten to say the model is pinned
  in three places (`run_daily.sh --model opus`, plus both skills' frontmatter), and that the one
  remaining uncovered path is a manual `/ai-daily-learn`. On that path the instruction is now to
  **stop and ask for `/model opus` before generating**, not to generate and flag afterwards.
- **Not changed**: no `model:` field added to `ai-daily-learn` itself. The user named the two
  publishing skills, and the local-only skill has a legitimate quick-draft use where forcing Opus
  is the user's call, not the spec's. Worth revisiting if a manual local run ever ships badly.

## 2026-08-27 — 2026-08-27 (follow-up: total length)
- **Note**: "hold on did you shorten just the oiblem section or the overall article?" — a correct
  challenge. The first pass shortened `The Problem` by 47 words and left the mechanism section
  9 words *longer*; the article dropped 2.2% overall while being reported as fixed.
- **Verdict**: standing rule, and a genuine gap the first pass missed. The rhythm caps added
  earlier that day enforce *density* and say nothing about *size*. Reviewing the spec for this
  showed there was **no overall length rule at all**: every rule governs proportion
  (`Implementing It` longest, ELI5 3-5 sentences, `The Problem` 3-6) and none governs the total,
  which is how sessions reached ~1,700 words with every check green. `**Time to read**` was a
  number the author typed, validated by nothing.
- **Changed**: `build.js` — `MAX_TOPIC_WORDS = 1300` over all sections, fenced code excluded,
  under the same `READING_RHYTHM_SINCE` date gate. Warning text says "cut, do not redistribute",
  because moving words between sections is the obvious way to satisfy a total.
- **Changed**: `contract.md` and `SKILL.md` — the budget stated in both, with the target at ~1,200
  and the cap as ceiling, plus the rule that the explanatory sections absorb the cut and
  `Implementing It` is protected.
- **Changed**: `2026-08-27/topic.md` cut 1,717 → 1,300 words (−24%), user-chosen target. Every
  section reduced except `Implementing It` (308, untouched by design): ELI5 −28, The Problem −47,
  mechanism −119, For a Software Engineer −47, What This Means −66, counter-case −84. Passes all
  new caps and the existing longest-section rule (`Implementing It` + counter-case = 452 vs
  mechanism 407).
- **Not changed**: the `Implementing It` longest-section rule, deliberately — the budget is
  enforced *around* the payload, never by trimming it. A shorter article that cut the code
  guidance would fix the symptom the user named and destroy the reason the site exists.

## 2026-08-27 — 2026-08-27 (follow-up: title flow)
- **Note**: "the title's ebglish somhow I fins it confusing the format is good... 'So a borket
  layer cant hide' confused me and doest feel the flow like the first part and seond part feel
  little disconnected".
- **Verdict**: standing rule. The existing title rules covered *shape* (four allowed forms), *
  vocabulary* (no product-specific glyph) and a *cold-reader check* — but nothing about a title's
  internal grammar, so a title could pass every rule and still not hold together.
- **Diagnosis**: `How to Test an AI Agent So a Broken Layer Can't Hide` joins two clauses with a
  purpose conjunction and gives each a **different subject** — the first half's is the reader, the
  second half's is "a broken layer." Two compounding faults: "layer" is the source paper's
  vocabulary, undefined at title-read time (which the existing Cursor-only-engineer rule should
  have caught and did not), and "hide" is given no object, though the thing it hides *from* — the
  passing aggregate score — is the article's whole idea.
- **Market check**: ByteByteGo's titles are near-uniformly one clause with one subject ("Why is
  Kafka so fast?", "How does ChatGPT work?", "How to Choose a Message Queue?", "A Crash Course in
  Kubernetes"). None uses a two-clause purpose construction. The instinct was confirmed by the
  reference publication rather than asserted.
- **Changed**: `SKILL.md` title rules — new "One clause, one subject" rule with this exact title as
  the ✗ and the chosen replacement as the ✓, plus two acceptance tests: do both halves share a
  subject or object, and does the second half introduce an unmet noun. Notes that a needed purpose
  clause usually means the article's real subject has not been named yet.
- **Changed**: title updated to `How to Catch the Broken Step Your Agent's Tests Miss` (user's pick
  from four researched options) in all three places it appears — `topic.md` H1, `articles.md`
  "Further Reading" header, `journal.md` entry heading. `Time to read` corrected ~11 → ~8 min to
  match the shortened article.
- **Not changed**: the four title shapes. This is a grammar check applied to whichever shape was
  chosen, not a fifth shape — same relationship as the 2026-08-25 cold-reader check.

## 2026-08-29 — 2026-08-29 (How an Agent Calls a Tool That Takes Twenty Minutes)
- **Note**: "Dont seem great source to select and write articles we aonly need ti consider
  reputable and vetteed industry sources" — about `mlconcepts.viveksingh-heritage.workers.dev`
  cited in `articles.md`, and about `github.com/modelcontextprotocol/ext-tasks` used as the
  article's primary authority.
- **Verdict**: standing rule (both halves). Not a judgement lapse on the day: the ML Concepts page
  was **mandated** by the spec — `SKILL.md` Step 9 said "include one ML Concepts page … as the
  intermediate / basics slot" whenever a session touched agents, it was listed in `selection.md`'s
  everyday sources, and the Cursor runner said "Every scan must include" it. The generator was
  obeying the spec, so the spec was the bug.
- **Diagnosis**: the spec had four source *quality* gates (dated/primary, something changed,
  implementable, verified) but no *admissibility* gate. Every gate assumed the publisher was
  already acceptable and only asked whether the content was good enough. A personal Cloudflare
  Workers deployment with no institutional backing and no publicly identifiable author standing
  passes all four and should never have been citable. Separately, nothing said that a working spec
  repo is not the citation surface when a published, versioned revision of the same text exists.
- **Changed**: `selection.md` — new "### The admission test — is this source citable at all?"
  placed above the four quality gates. Two conditions, both required: you can name the institution
  or person accountable for the page, and a senior engineer would accept it as a citation in a
  design doc. Explicitly admits named practitioners on personal domains (Willison, Husain, Yan,
  Weng, Raschka) and rejects unvetted personal sites — the bar is accountability, not domain shape,
  and pedagogical usefulness does not buy admission. Plus three recurring rejections: published
  spec never the working repo (with the ext-tasks ✗/✓ pair), aggregators for noticing never citing,
  vendor launch posts are not primary sources.
- **Changed**: `selection.md` — ML Concepts bullet deleted from "Every day, whatever is due";
  replaced by a "**The basics on-ramp slot**" rule pointing at this site's own `learn/` track first
  (`#learn/<slug>` inline), then a Tier 1 conceptual doc or Tier 3 named practitioner. HN relabelled
  "noticing only, never cited". Frontier section now names the admission test alongside the gates.
- **Changed**: `SKILL.md` Step 2 — ML Concepts bullet deleted; HN relabelled noticing-only; a new
  paragraph requires every source built on *or cited* to pass the admission test, noting it applies
  to `articles.md` as hard as to the primary source because those links are published.
- **Changed**: `SKILL.md` Step 9 — the mandated ML Concepts slot deleted and replaced with the
  `learn/`-track on-ramp. "Rank by teaching value, not by authority" retained but scoped: it now
  reads "**above the admission floor**", because as written it argued *against* the new rule.
  Surfaced as a conflict rather than silently overwritten — the ranking rule governs choice among
  admissible sources; it never governed admission.
- **Changed**: `.cursor/skills/ai-daily-learn/SKILL.md` — the runner's "Every scan must include
  [ML Concepts]" mandate replaced with the admission test. Touching the Cursor twin was warranted
  here because it carried its own hard content mandate rather than linking to the canonical rule.
- **Changed (follow-up, same session)**: the "rank by teaching value, not by authority" rule was
  first *scoped* to sit above the admission floor, and the user then tightened it further — "It
  needs to be vetted and backed by strong evidence if unknown engineer; if possible avoid this flow
  as much as possible." So standing is now a **tiebreaker above the floor**, not a neutral factor:
  prefer the first-party doc, spec revision, lab engineering post or named practitioner with a
  public track record, and reach for an unplaceable author only when nothing better covers the
  point *and* the post carries its own strong evidence (reproducible benchmark, public repo,
  production numbers, a re-runnable method). "It explains it well" is explicitly not evidence.
  Written into `SKILL.md` Step 9 and mirrored as a fourth recurring rejection in `selection.md`.
- **Not changed**: the four source quality gates, and their numbering — the admission test is a
  precondition above them, not a fifth gate, so the Frontier section's "gate 3" reference still
  resolves. No published session was edited.

## 2026-08-31 — spec-wide (per-section word bands replace the document total)
- **Note**: "the quliaty of articles has gone down they seems very speefic , some times to deep
  not application focssueued take a deep and find ou t what went wrong", then, on being shown the
  cause: "rather than a 1300 word limit lets do section limit".
- **Verdict**: standing rule, and a **spec regression introduced by this log's own 2026-08-27
  entry** — the rarest and most important kind to catch. The total-length rule did what it said;
  what it said was wrong.
- **Diagnosis, measured before editing**: `MAX_TOPIC_WORDS = 1300` was paired with "cut, do not
  redistribute: the explanatory sections carry the excess, and `Implementing It` is the payload
  that survives the trim." A document-wide cap can only be paid out of whichever sections have the
  weakest rule protecting them, so it was. Comparing the last two pre-cap articles (08-25, 08-26)
  with the four written under it (08-28..08-31): `The Problem` 266 → 138 words (−48%), `What This
  Means for You` 246 → 154 (−37%), mechanism 469 → 288 (−39%), `Implementing It` 421 → 323 (−23%,
  protected by the longest-section rule). All four post-cap articles sat within five words of the
  ceiling, so the cap was binding on every one of them. The visible symptom was the article's
  entry condition: `When this matters` became a compound precondition ("you maintain an MCP server
  *and* have a tool that exceeds your proxy timeout") where 08-26 had given three graduated
  actions, the first with no precondition at all. That is the "not application focused" the note
  names — the words that generalised a narrow topic were the ones being cut.
- **Changed**: `build.js` — `MAX_TOPIC_WORDS` deleted, replaced by `SECTION_BANDS` (floor/cap per
  section) under a new `SECTION_BANDS_SINCE = 2026-09-01`. Bands taken from 08-25/08-26, the last
  two articles written before the cap: ELI5 60-120, `The Problem` 170-280, mechanism 0-340 (cap
  only — a simple topic may explain itself briefly, but this is where a spec dump lands),
  `For a Software Engineer` 120-210, `What This Means for You` 200-300, `Implementing It` 300-460,
  counter-case 150-250. Deliberately placed at top level rather than inside the
  `READING_RHYTHM_SINCE` block where it was first written: nesting it would have silently retired
  the rule if that gate ever moved, and it also hid the cap-side warnings on 08-25/08-26 during
  testing.
- **Changed**: `contract.md` and `SKILL.md` — the band table, and the replacement of "cut, do not
  redistribute" with "fix it in the section named": a section over its cap is cut where it stands,
  a section under its floor is **owed words back, not trimmed further**. Both files state why the
  total was removed, so the next person to notice there is no overall length rule does not
  reinstate the thing that caused this.
- **Verified both directions**: with the gate temporarily dropped to 2026-08-25, floors fire on
  every article written under the total (08-28..08-31 and frontier-08-29/08-30 — the regression
  reached the Frontier track too, which had not been measured) and caps fire on the pre-cap ones
  (08-25 mechanism 513, 08-26 425, 08-27 376, all against a 340 cap). Restored to 2026-09-01, the
  lint is clean at 10 pre-existing warnings, none of them length.
- **Not changed**: the `Implementing It` longest-section rule, the paragraph/sentence rhythm caps,
  and the seven-section order — all three are orthogonal and none of them caused this. Also not
  changed: the published articles 08-28 through 08-31, which is why the gate starts at 2026-09-01.
  They are a dated log; the bands are aimed at the next session, not at a backlog.

## 2026-08-31 — spec-wide (`Key insight`, the second sentence)
- **Note**: "the key insights section I got lost at the second like see todays ands last 5
  artciles I found it confusing"
- **Verdict**: standing rule **plus** a compliance gap. The spec already required plain language
  throughout and at most one number; nothing enforced either, and five of the six entries broke
  the number rule. A second sentence saying the same thing would have changed nothing, so the
  existing rules were made enforceable and the missing rule was added beside them.
- **Diagnosis, measured across 08-26..08-31**: every entry was *inside* the size caps — 3
  sentences, 52-69 words against a ~70-word cap — so size was never the defect. The pattern was
  positional. Sentence one hooks in plain words; sentence three lands a takeaway; **sentence two
  had become the evidence sentence**, where the article's proof, quantities and vocabulary
  arrived. It cannot go there: the box renders above `Explain Like I'm 5`, so at sentence two the
  reader has met none of the article's terms. Examples — 08-31 put four quantities and two
  undefined terms ("retrieval signals", "reinforcement learning") in one sentence; 08-27 wrote a
  garden-path clause ("caught the same break as up to a 95-percentage-point drop instead of a
  barely-visible one"); 08-26 opened a new, unconnected subject; 08-28 left "four times its own
  context" without a referent. The one clean entry, 08-29, is the only one whose second sentence
  *continues* the first instead of arguing with it, and it carries no numbers at all.
- **Root cause in the spec**: the journal template line read `[plain first sentence, then the
  detail — see below]`. "Then the detail" licenses exactly the density that breaks, and it
  contradicted the bullet three lines below it ("Plain language throughout — not just the first
  sentence"). The author reads the template first.
- **Changed**: `SKILL.md` Step 10 — template line now reads `[three plain sentences: the surprise,
  its consequence, the takeaway]`, plus a table giving each sentence its job and the rule that
  **sentence two must continue sentence one's subject and introduce no noun that needs
  explaining**. ✗/✓ pair uses 08-31's second sentence against 08-29's.
- **Changed**: `build.js` — `Key insight` had **no lint at all**; it was parsed, rendered at the
  top of every Overview pane, and checked by nothing. Added `KEY_INSIGHT_SINCE = 2026-09-01` with
  four checks: sentence count (3), word count (80), number count (1), and any backticked /
  snake_case / camelCase identifier. "one" is exempt from the number count — it is an article more
  often than a quantity, and counting it fired on entries that read fine.
- **Verified**: with the gate dropped to 2026-08-26, the number check fires on 08-31 (five
  numbers) and 08-28 (two) and stays silent on the four that read acceptably, including the clean
  08-29. No false positives on the jargon or size checks across the corpus.
- **Not changed**: the ~70-word and 3-sentence caps, which were never the problem and are kept as
  a backstop; the `**Hook**` field in `topic.md`, which is a different string with a different job.
  The six published entries are untouched pending the user's call.

## 2026-08-31 — 2026-08-31 (`The Problem` never names the fix)
- **Note**: "in current article see the pr0blem section it;s too long and in the article what is
  toe solution fo the pobrle is not clear to me or atleast not crearly states think about it"
- **Verdict**: standing rule. Both halves of the note are one defect, and the "think about it"
  was warranted — the literal reading is wrong and following it would have made the article worse.
- **Diagnosis**: `The Problem` was **119 words, the shortest in the recent run and below the floor
  set earlier the same day**. So "too long" was not word count. It was that all four paragraphs
  were setup, the section closed on "What worked was upstream of all of it" — a direction naming
  nothing — and the mechanism section then opened with ninety more words of benchmark numbers and
  an episodic-log subsection before reaching the answer. The word "consolidation" first appeared
  as a `###` sub-heading. From the reader's seat the problem ran ~210 words before anything was
  resolved, which is why it measured short and read long. **The variable is latency to the answer,
  not length.**
- **Checked against the run**: 08-31 is the outlier, which is what makes this a rule rather than
  an excuse. Every other recent article names the fix at the handoff — 08-27 "The fix: stop
  grading the agent once, and grade each step separately", 08-29 names the protocol extension in
  its first line, 08-30 defines the subagent chain immediately, and 08-26 names the answer inside
  `The Problem` itself.
- **Changed**: `SKILL.md`, the `## The Problem` rules — new rule "Name the fix before the section
  ends. Never hand off on a tease", with the failing sentence as ✗ and two shipped examples as ✓,
  and the escape hatch that a fix which genuinely needs build-up may open the mechanism section
  instead. The bar: the reader must not reach a `###` sub-heading still not knowing what the
  article proposes.
- **Changed**: `2026-08-31/topic.md` — `The Problem` now names consolidation in plain language
  before it ends (119 → 180 words, inside the new band), and the mechanism section no longer opens
  on benchmark setup. Also rewrote `What This Means for You` (164 → 263): its entry condition was
  a compound precondition, now widened to "anything your agent is supposed to remember after the
  conversation ends", and the first action is the no-precondition one (ask the model for five
  things worth remembering, append only those) with the automated version after it.
- **Incidental fix**: a bolded phrase ending in `.**` defeated the sentence splitter in the rhythm
  lint, merging two sentences into a phantom 51-word one. Moved the period outside the bold.
- **Not changed**: the `The Problem` band floor of 170. It fired on this article for the right
  reason by accident — the missing words were exactly the missing answer — but the floor measures
  the symptom and this new rule states the cause. Both stay.

## 2026-08-31 — spec-wide (six-section order; the article as one argument)
- **Note**: "also what it means for for a sfotware enginner the articles and sections doesnt seem
  a single flow anf almosy all articles there no clear soltuin to the proble we introdcues take
  time understadn introspect come up with options this is a complete reartcitecture of the entire
  article strcture we need help enginners to learn as they are giving us time in thier super busy
  schedule". Follow-up: "for the software engineer line it should explicitly start with from
  'froma a software engineering prespective' or some thinglike that".
- **Verdict**: standing rule, and the largest structural change since the seven-section order.
  Handled as the note asked — diagnosed, three architectures designed with their trade-offs, and
  the user chose. Not implemented unilaterally.
- **Diagnosis, by reading 2026-08-30 end to end rather than by metric**: the spine ran problem →
  mechanism → **analogy again** → **applicability restated** → the fix, fifth → caveat. Three
  faults, and the note's first sentence names two of them. (1) **Two analogy sections**: `Explain
  Like I'm 5` opens with one, `For a Software Engineer` gives another *after* the mechanism, where
  momentum should be building toward the fix. (2) **The problem stated three times** — in `The
  Problem`, again in the engineer analogy, again in "When this matters". (3) **The solution is
  never announced as one**: `How X Works` presumes the reader already accepted X as the answer, so
  the first actionable content is `Implementing It` at section six.
- **Options put to the user**: (1) tighten the spine to six sections; (2) rename every heading to
  the reader's question ("What to Do Instead", "Why That Works"), rejected as it would have undone
  the 2026-08-25 topic-named-heading decision; (3) a fast path at section 3 with depth after,
  rejected for inviting two code sections that duplicate. **User chose (1)**, and chose to demote
  the engineer anchor to a sentence rather than keep or relocate the heading.
- **Changed**: `build.js` — `SIX_SECTION_SINCE = 2026-09-01`, `FIXED_SECTIONS_V6`, a date-branched
  spine check so the back catalog still validates against the seven-section order, `For a Software
  Engineer` and `What This Means for You` added to the retired list from that date, and
  `ENGINEER_ANCHOR_RE` requiring the mechanism section's first paragraph to begin "From a software
  engineering perspective, …". Bands re-cut for the new shape: `The Problem` 190-320 (it now
  carries "when this matters" and must name the fix), mechanism cap 370 (it now carries the anchor
  sentence), new `What to Do About It` 150-260.
- **Changed**: `contract.md` and `SKILL.md` — the six-section table, the spine stated as *problem →
  the fix, named → how it works → what to do → build it → when not to*, the engineer-anchor rule
  with its required opener and a ✗/✓ pair, and `What to Do About It` as one beat whose **first
  action must carry no precondition**.
- **Verified both directions** with a scratch 2026-09-01 session, since a new order that only ever
  passes is untested: the correct shape draws no structural warning, dropping the "From a software
  engineering perspective" opener fires the anchor check, and reinstating either retired heading
  fires the retired check. Scratch session deleted; lint back to its 10 pre-existing warnings.
- **Not changed**: `Explain Like I'm 5` stays first — a standing user preference, and no option
  proposed touching it. The topic-named mechanism and counter-case headings stay. The back catalog
  is untouched and still validated against the seven-section contract by date.

## 2026-08-31 — spec-wide + reader (craft borrowed from ngrok's prompt-caching post)
- **Note**: "see this article https://ngrok.com/blog/prompt-caching I really like the flow ,
  organization the diagrams in bettween I was able to understand the article the solution and it
  was egnging learn from it even if we have to completly change the strcutr or reinvent our
  seleves understand and discuss". After discussion: "1. tow space, for 2. Most valuable ver
  The ###-as-reader's-question rule. ageress I agree on this … lets stay on our soul see what we
  can learn from it but we DO not want to comprise on our mission of application based software
  engineering focused partical AI articles and labs".
- **Verdict**: standing rules, three of them, adopted after reading the reference article closely
  and discussing options rather than copying it.
- **What the reference does well, and why**: (1) it opens with a price fact and a question, then
  spends a `By the end of this post you will…` section making an explicit promise — that promise
  is what lets it withhold its answer until ~80% through without losing the reader; (2) every H3
  is the reader's own interruption in the reader's voice ("Hold up, what're these WQ and WK
  variables?", "Wait, what about temperature?"), so the objection is spoken before it can become
  irritation; (3) seven diagrams sit inline at each point of difficulty, several interactive, with
  prose setting up and the figure doing the explaining; (4) it is ~6,000 words and the user
  enjoyed it, which settles that length was never the complaint.
- **Explicitly NOT copied**: the reference has no implementation at all — no code to ship, no
  configuration, no Monday action — and closes on a product plug. The user's instruction was to
  keep "our soul". Both shapes therefore keep `Implementing It`, `What to Do About It` and the
  five artifacts unchanged. Any future restructuring that quietly reduces the payload should be
  refused on these grounds however good the rest of it looks.
- **Changed**: `build.js` — `CONTRACT_SECTION` ("By the End of This You Will"), which declares the
  Explainer shape by its presence rather than a metadata key so the two cannot drift; the v6 spine
  check now accepts it at position 2. `READER_QUESTION_RE` warns when a mechanism section has two
  or more sub-headings and none is phrased as a question. `INLINE_FIGURE_SINCE = 2026-09-01` warns
  when a session ships a visualizer and never places `[[visualize]]`.
- **Changed**: `index.html` — `overviewBody()` splits `topic.md` on `[[visualize]]` / `[[diagram]]`
  lines and splices the artifact into the Overview prose there. `md()` escapes `<` and `>`, so an
  HTML comment cannot survive as a marker and the body is split before rendering rather than
  after. A session that inlines the visualizer loses the now-duplicate Visualize tab; sessions
  without a marker are untouched, which is the whole back catalog.
- **Changed**: `contract.md`, `SKILL.md`, `visualize.md` — the two shapes, the reader-question
  sub-heading rule with ✗/✓ pairs, and the figure-placement rule.
- **Bug found and fixed during verification**: the inline-figure check was first written above the
  `let visualize` declaration, so it threw a temporal-dead-zone `ReferenceError` for any session
  dated on or after the gate. There is no try/catch around `compile()`, so the build crashed — and
  because the verification grepped for the session id, the stack trace produced no matches and the
  test *reported clean*. Two lessons applied: the check moved below the artifact resolution, and
  negative tests are now run unfiltered so a crash cannot present as a pass.
- **Verified** on a scratch 2026-09-02 session, both directions: the Explainer spine with a
  `[[visualize]]` marker and reader-question sub-headings draws no structural warning; replacing
  the sub-headings with subject labels, removing the marker, and moving the contract section out
  of position 2 each fire their own warning. Scratch session deleted.
- **Not changed**: the Fix shape stays the default, `Explain Like I'm 5` stays first in both, and
  the word bands are untouched — the reference being 6,000 words is a reason not to tighten them,
  not a reason to widen them yet.

## 2026-08-31 — sibling skills (the contract change had not propagated)
- **Note**: "did you update the skill /ai-daily-learn-publish ?"
- **Verdict**: compliance gap, and a serious one — the answer was no.
- **What was broken**: `publish.sh` gates a publish by grepping `--check` output for a hard-coded
  list of blocking warning patterns. Every rule added in the six-section rewrite was missing from
  it, so a session breaking them would have published. Worst case was the word bands: the pattern
  read `words of prose \(cap`, which matches an over-cap warning and **silently misses**
  `words of prose (floor …)`. The floors are the load-bearing half — the regression being fixed
  was sections getting *drained* — so the gate would have passed every article that caused the
  original complaint.
- **Changed**: `publish.sh` — floors added alongside caps, plus section order, retired sections,
  the engineer anchor, an unplaced `[[visualize]]`, and `Key insight`. The reader's-question
  sub-heading check is deliberately left advisory: it is a heuristic over heading phrasing and can
  reasonably be wrong about a given article.
- **Changed**: `ai-daily-learn-publish/SKILL.md` and `ai-daily-learn-github/SKILL.md` — both
  described the blocking set in prose and both still named the 1,300-word total.
- **Changed**: `ai-daily-learn-video/SKILL.md` — it sourced the video's engineer beat from
  `## For a Software Engineer`, a section that no longer exists. It now reads the mechanism
  section's opening sentence.
- **Verified**: a scratch session with drained sections, an over-cap mechanism section, and a
  missing engineer anchor each produce warnings the gate's regex matches.
- **Standing lesson**: a contract change is not finished at `.claude/skills/ai-daily-learn/`.
  At least four other files consume it, and the gate's regex is the one that fails silently.

## 2026-08-31 — full audit of every skill (follow-up to "all skills updated?")
- **Note**: "all skills updated?"
- **Verdict**: compliance gap, second pass. The first propagation fix was itself incomplete.
- **Found and fixed**: `ai-daily-learn-github/scripts/publish_github.sh` carried a byte-identical
  copy of the stale blocking regex. `publish.sh` had been updated an hour earlier and this twin
  had not — the same silent-drift failure the earlier fix existed to correct, repeated inside the
  fix itself. Both gates now carry the identical pattern and a comment saying they must stay that
  way. Also corrected: two "seven-section order" references in `SKILL.md` that now describe six,
  and every "no Visualize tab" phrasing, which stopped being the whole truth once the artifact
  could be inlined at `[[visualize]]`.
- **Changed**: `CLAUDE.md` — its one-paragraph description of the article shape still named the
  old flow ("engineer-bridge → What This Means for You → technical depth"). It now states the
  six-section spine, the Explainer variant, the bands with floors, and the inline figure marker.
  This file is read at the start of every session in this repo, so a stale shape here outranks a
  stale skill.
- **Audited and clean**: `video.js` parses no named sections; `build.js` is the only root script
  reading `topic.md`; all six Cursor twins are thin runners that link to the canonical files
  rather than copying them, so they need no content edits when the contract moves.
- **Standing lesson, strengthened**: the consumers of this contract are
  `ai-daily-learn/{SKILL,contract,visualize,selection}.md`, **both** publish gates
  (`publish.sh` and `publish_github.sh` — they are copies), the two publish SKILL.md prose
  descriptions, `ai-daily-learn-video/SKILL.md`, and `CLAUDE.md`. The gates fail silently; the
  rest merely go stale.

## 2026-08-31 — spec-wide (the six-section order is reverted)
- **Note**: "think again I feel the newstrcure is nota lot different from we have come up wchich
  is easy to read espcial the middlw secions we had", then: "lets revert to waht we had before
  just mellow the software enginer path in problem and make key insights easy to understand and
  each idnfivual section limit rather than over all limit and for th rest lets revert".
- **Verdict**: the six-section change is withdrawn. The user was right on both counts and the
  measurement backs him.
- **What was actually delivered, measured**: the "rearchitecture" was two edits — delete
  `For a Software Engineer`, shrink `What This Means for You`. Everything else was identical. On
  the article it was applied to, the middle went from **three sections and 710 words to two and
  524**: 186 words and a heading removed from the part the owner reads as the readable one.
- **Why the middle reads well**: it alternates modes. Mechanism, then the translation into
  something the reader has already shipped, then what to do — three ways of thinking, three
  headings, each scannable. Merging them produced one 358-word mechanism monolith followed by a
  single action beat, and the alternation was gone.
- **The direction was backwards.** Counted properly, the reference article that prompted this
  carries ~5 top-level stages, 8 reader-question sub-headings and 7 inline figures across ~6,000
  words. Its readability comes from **more small units, each answering one question with a
  figure**. "Every section must advance the argument" was read as "merge sections" and went the
  opposite way.
- **Changed**: `build.js` — `SIX_SECTION_SINCE`, `FIXED_SECTIONS_V6` and `ENGINEER_ANCHOR_RE`
  deleted; the spine is the seven-section order again; bands restored for `For a Software
  Engineer` (120-210) and `What This Means for You` (200-300); the `[[visualize]]` marker is
  supported but no longer required; the reader-question check is date-gated from 2026-08-31 so the
  back catalog stays clean.
- **Kept, each endorsed separately**: per-section word bands instead of a document total, the
  `Key insight` lint, reader-question sub-headings, and inline figures. Also kept: the software
  -engineering framing now appears **twice at two weights** — a light clause inside `The Problem`
  that hints at the shape without spending the analogy, and the full comparison in its own section.
- **Changed**: `contract.md`, `SKILL.md`, `CLAUDE.md` — all three now state the seven-section order
  and record that the merge was tried and reverted, so it is not proposed again.
- **Changed**: both 2026-08-31 sessions restored to seven sections and republished.
