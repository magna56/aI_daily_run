---
name: ai-daily-learn-pick
description: >
  Research today's candidates, put three worked article proposals in front of the user, decide
  together, then write the session. This is /ai-daily-learn with the topic decision handed back
  to the user: it fetches 8-12 live sources, builds three genuinely different one-page proposals
  (title, primary source, mechanism, what the reader can do afterwards, the code Implementing It
  would show, the honest weakness), stops and discusses them, shapes the article's content in
  that conversation, locks the agreement as a brief, and only then runs the full five-artifact
  session against it. Saves to ~/ai_learning/YYYY-MM-DD/ and nothing else — publishing is a
  separate, explicit step. Use when: "pick an article", "give me three options", "what should
  I write today", "ai-daily-learn-pick", "research and let me choose", "I want to choose the
  topic", or whenever the user wants a say in what gets written. Use plain /ai-daily-learn when
  they want it chosen and written unattended. Accepts an optional theme:
  /ai-daily-learn-pick "MCP" narrows the search without narrowing it to one answer.
argument-hint: "[optional-theme] [--frontier]"
# The proposals are the product of this skill and the article is written straight from the
# conversation about them — a weak candidate set wastes the user's decision, not just a run.
# Same reason the publish skills pin this: never a smaller model.
model: opus
verified: llm
---

# AI Daily Learn — Pick (choose the article together)

## Why this skill exists

`/ai-daily-learn` shortlists three candidates internally, picks one, and names the two losers in
the summary afterwards. On 2026-08-30 the user said plainly that he did not like the quality of
the articles being selected. A shortlist reported after the fact is not a choice — by the time he
saw the reasoning, the article was written.

This skill moves the decision to before the writing. **The three proposals are the product of
Steps 1-3; the article is what happens after the user has chosen.** A run that produces a good
article from a candidate set the user was never shown has failed at the one thing it is for.

Two consequences worth stating up front, because both instincts will push the other way:

- **Do not pick for him.** You may recommend, in one line, at the end. You may not present two
  makeweights beside a favourite — three proposals means three you would be content to write.
- **Do not start writing until he has chosen.** Not the title, not the outline, not "a quick
  draft of the strongest one while we talk". Step 4 ends the turn.

Everything else — the contract, the five artifacts, the section order, the source gates — is
unchanged and lives in the existing spec. This skill does not restate it, so the two can never
drift apart.

## The invocation argument

The argument is a **theme, not a topic**. It narrows where you look; it never collapses the
answer to one candidate.

| Invocation | What it means |
| --- | --- |
| `/ai-daily-learn-pick` | No theme. Research whatever `node build.js --mix` says is due, and propose three. |
| `/ai-daily-learn-pick "MCP"` | All three candidates must serve that theme. Still three, still discussed, still fetched. If the theme cannot yield three honest candidates today, say so and offer the ones it can plus what else is strong. |
| `/ai-daily-learn-pick "Anthropic changelog"` | A source, not a subject: read it and propose three different articles you could write *from* it. |
| `/ai-daily-learn-pick --frontier` | Frontier track. Same three-proposal protocol, Frontier sources, and *nothing today* is a legitimate outcome — see the cadence rule in `selection.md`. |

A theme never suspends the audience gate. If the theme is at cap, propose inside it anyway and say
in the presentation which cap it breaks, so the trade-off is the user's to make rather than yours.

**A named article is not this skill.** If the user hands over one specific URL or title and wants
it written, there is nothing to choose — run `/ai-daily-learn "<topic>"` instead.

---

## Step 1: Ask what is due

```bash
cd ~/ai_learning && node build.js --mix
```

Read `journal.md` for what has already been covered. This is the same Step 1-2 opening as
`ai-daily-learn`, and it plays the same role — but here `--mix` sets the *search*, not the
verdict. Its DUE NEXT line is context you show the user in Step 4, not a decision you make on
his behalf.

Read [`../ai-daily-learn/selection.md`](../ai-daily-learn/selection.md) now: the reader pyramid,
the source lists keyed by category, the admission test, and the four source quality gates all
apply here in full. This skill changes who decides — never what qualifies.

## Step 2: Research wide, then narrow to three that actually differ

Fetch **8-12 items** across at least three categories. Prefer changelogs, docs, engineering
blogs and technical reports over papers, and honour the paper budget (at most one arXiv-led
session per seven). Skimming titles is not researching — an item you have not opened cannot
become a candidate.

Then narrow. The three you carry into Step 3 must satisfy all of:

- **Different articles, not three angles on one story.** Two candidates built on the same release
  are one candidate with a spare.
- **At least two categories** between them, and at most one arXiv-led.
- **At least one serves the `For` layer `--mix` named as due.** If none can today, say that in the
  presentation rather than quietly substituting.
- **Every one clears the source quality gates in `selection.md`.** A candidate that fails a gate
  is not a candidate you present with a caveat — it is cut, and you find another.

If fewer than three survive, present what did and say what you looked at and why the rest failed.
Two honest proposals beat three with a filler.

## Step 3: Work each candidate up before showing it

Fetch and read the primary source for **all three**, not just the one you like. The point of a
worked proposal is that the user is choosing between real articles, so the parts that decide an
article — is there code to show, is the mechanism actually explained anywhere, does the reader end
up more capable — have to be answered before he chooses, not discovered afterwards.

Present each in exactly this shape:

```
### Candidate N — <working title: one clause, one subject>

Source     <URL> — <what it is: changelog / spec revision / eng blog / report>, dated <date>
Slot       <Category> · Tier <A|B|C> · For: <layer>   <"due" | "at cap" | "over-weight">
Claim      <one sentence: what changed, in the reader's language>
Mechanism  <a short paragraph of why it works — the thing the article would actually teach>
Reader can now  <the concrete thing an engineer can do after reading that they could not before.
                "Understand X better" is not an answer; if that is the honest answer, cut it>
Implementing It would show
           <the roles it touches and the real code each writes — API, payload, config key.
            A code sketch of 3-6 lines, from the source, not invented>
Visualize  <what the interactive would let them play with>
Weakness   <the honest one. Thin source, no numbers, narrow audience, dated next month>
```

Then one comparison table across the three (slot, what the reader gains, source strength,
strongest objection), and **one line** of recommendation at the end with the reason.

## Step 4: Present, and stop

End the turn on the proposals. No file has been written, no directory created.

What the user does next is one of: pick one; ask for a deeper pass on one; reject all three and
send you back to Step 2 with a steer; or take a candidate and change it — which is the normal
case and the second half of the point.

## Step 5: Shape the content, not just the winner

The choice covers the article's content too. Before anything is written, settle in conversation
and read back:

- **Title** — one clause, one subject; explanatory, and readable by an engineer who has only used
  Cursor.
- **The angle** — which of the possible articles this is, and which reader it is aimed at.
- **What `## Implementing It` shows** — the roles covered and the code for each. This is the
  longest section and the reason the reader stays; agreeing it here is worth more than agreeing
  the title.
- **What is deliberately cut** — the tempting sub-topic that would turn one claim into a survey.
- **The visualizer's one idea**, and anything the user already knows he wants to see.

Ask about anything the proposal left genuinely open. Do not re-ask what the user has already
settled — read it back in one block and move.

## Step 6: Lock the brief

Write the agreement to `~/ai_learning/.briefs/YYYY-MM-DD.md` (gitignored, never published) so the
session is written against a fixed target and the decision survives a compaction:

```markdown
# Brief — YYYY-MM-DD

**Title**: <agreed title>
**Category**: <one of the 11>   **Tier**: <A|B|C>   **For**: <layer>   **Level**: <Start here|Building|Deeper>
**Primary source**: <URL>
**Also cite**: <URLs>

## The angle
<2-4 sentences: what this article argues and for whom>

## Reader can now
<the concrete new capability>

## Implementing It must cover
- <role> — <what code>
- <role> — <what code>

## Visualize
<the one idea the interactive makes playable>

## Out of scope
<what was cut, and why>

## Mix note
<what --mix said was due, what we chose, and why — one line. Blank if they agree.>
```

Show the brief and get a yes before Step 7. This is the last cheap moment to change direction.

## Step 7: Write the session against the brief

Run the full existing workflow — do not re-derive it here:

```
Skill(skill="tp-mcp-config:ai-daily-learn", args="<the agreed title>")
```

If the Skill tool is unavailable, read `./.claude/skills/ai-daily-learn/SKILL.md` and its
`selection.md`, `visualize.md` and `contract.md`, then execute Steps 1 and 3-12 directly.

Two amendments, and only two:

1. **Step 2 is already done.** The topic is decided. Do not re-run selection, do not re-shortlist,
   do not let a fresher-looking link found during research displace the agreed article.
2. **The brief outranks the generator's own judgement** on title, angle, scope and what
   `Implementing It` covers. Everything else in the contract — the section order, ELI5 first, all
   five artifacts, readability limits, source gates — binds exactly as written. The brief can
   narrow the article; it cannot lower the bar. If following the brief would breach the contract,
   stop and say so rather than shipping either violation.

For `--frontier`, the same three amendments as the publish skill apply: Frontier sources, output
to `frontier/YYYY-MM-DD/`, and Step 10 (`journal.md`) skipped.

## Step 8: Report, and leave publishing to him

Use the `ai-daily-learn` Step 12 summary, with two additions:

- **What we chose and what we passed on** — the two losers by name, with the reason each lost. Here
  that is a record of a decision the user made, so it is worth being accurate about.
- **Where the article followed the brief and where it could not**, if anywhere.

Then stop. **This skill never publishes.** Offer the next command and let him run it:

```
Local only. To publish:  /ai-daily-learn-publish   (or: bash .claude/skills/ai-daily-learn-publish/scripts/publish.sh YYYY-MM-DD)
```

## Scope

Writes `~/ai_learning/YYYY-MM-DD/` and `~/ai_learning/.briefs/YYYY-MM-DD.md`, and updates
`journal.md` via the nested session run. Touches no git state: no commit, no push, no deploy, no
newsletter. Every content rule lives in `../ai-daily-learn/`; change it there, through
`/ai-daily-learn-feedback`, never here.
