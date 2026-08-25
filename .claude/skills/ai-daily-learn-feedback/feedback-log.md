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
