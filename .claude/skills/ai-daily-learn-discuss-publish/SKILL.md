---
name: ai-daily-learn-discuss-publish
description: >
  Decide the article together, then publish it. This is /ai-daily-learn-pick followed by the
  publish step from /ai-daily-learn-publish, in one command: it researches today's candidates,
  puts three worked proposals in front of the user, stops for the decision, shapes the article's
  content in that conversation, writes the five artifacts against the agreed brief, and then
  commits to main, deploys to theaicommit.com and the gh-pages mirror, and sends the newsletter.
  Use when: "discuss and publish", "let me pick then publish it", "ai-daily-learn-discuss-publish",
  "choose together and put it live", or whenever the user wants a say in the topic AND wants the
  result live in the same sitting. Use /ai-daily-learn-pick when they want the same conversation
  but nothing published, and /ai-daily-learn-publish when they do not want to be asked at all.
  Accepts an optional theme: /ai-daily-learn-discuss-publish "MCP" narrows the search without
  narrowing it to one answer.
argument-hint: "[optional-theme] [--frontier]"
# Same reason both parents pin it: the proposals are a decision the user makes, and the output
# goes live to theaicommit.com, the mirror and the newsletter. Never a smaller model.
model: opus
---

# AI Daily Learn — Discuss, then publish

**This skill is `ai-daily-learn-pick` plus the publish half of `ai-daily-learn-publish`.** It
deliberately restates neither, so none of the three can drift apart. Everything about *how to
research, propose and write* lives in the pick skill; everything about *how to gate, push and
deploy* lives in the publish skill. This file only says how the two join and what changes at the
seam.

## Why this exists

`/ai-daily-learn-pick` ends on purpose without publishing, because the user might want to sit with
the article before it goes live. `/ai-daily-learn-publish` never asks, because the 11:00 job has
nobody to ask. Neither fits the common case: **the user is at the keyboard, wants to choose the
topic, and wants it live when the conversation is over.** Running pick and then publish by hand
works, and the only thing this skill saves is the second command — but that second command is the
one people forget, which leaves a finished article sitting unpublished on disk.

## The invocation argument

Identical to `/ai-daily-learn-pick` — see **The invocation argument** in
`../ai-daily-learn-pick/SKILL.md` for the full table. In short: the argument is a **theme, not a
topic**, it narrows where you look and never collapses the answer to one candidate, and
`--frontier` switches tracks.

| Invocation | What it means |
| --- | --- |
| `/ai-daily-learn-discuss-publish` | Research whatever `node build.js --mix` says is due, propose three, discuss, write, publish. |
| `/ai-daily-learn-discuss-publish "MCP"` | All three candidates serve that theme. Still three, still discussed, still published at the end. |
| `/ai-daily-learn-discuss-publish --frontier` | Frontier track. **Nothing today is still a legitimate outcome** — if no candidate clears the bar, say what you looked at and stop. A skipped Frontier day is a successful run, and reaching the publish step is not the goal. |

**A named article is not this skill.** If the user hands over one URL or title and wants it
written and published, there is nothing to choose — run `/ai-daily-learn-publish "<topic>"`.

## Step 1: Run the pick workflow, Steps 1 through 7

Execute `ai-daily-learn-pick` Steps 1-7 exactly as written: ask what is due, research wide, narrow
to three that genuinely differ, work each one up, **present and stop**, shape the content in the
conversation, lock the brief, then write the session against it.

```
Skill(skill="tp-mcp-config:ai-daily-learn-pick", args="<the theme, if the user gave one>")
```

If the Skill tool is unavailable, read `./.claude/skills/ai-daily-learn-pick/SKILL.md` and follow
it directly.

**Step 4 of that skill is a hard stop and this skill does not soften it.** Present the three
candidates and end the turn. Knowing that publishing follows is not a reason to pre-empt the
choice, pick a favorite and start writing, or collapse the three to one because one looks
strongest. The decision is the product; publishing is only what happens afterwards.

Note the exact session directory it produced — `YYYY-MM-DD`, `YYYY-MM-DD-s2`, or
`frontier/YYYY-MM-DD`. Steps 2 and 3 need it.

## Step 2: Gate it, exactly as the publish skill does

Run **Step A½ of `ai-daily-learn-publish`** against that directory, unchanged: the content-contract
lint, then the audience gate. That file lists which warnings block and which are advisory; do not
re-derive that list here or relax it because the article was agreed in conversation. An agreed
topic can still ship a section under its word band.

One thing genuinely does change. The audience gate's instruction is to regenerate for the due
category if it exits 3 — but **here the user chose this topic knowing what was due**, which
`/ai-daily-learn-pick` Step 4 required you to tell him. So do not silently regenerate. Say the mix
was breached, name what it costs, and let him decide whether to publish anyway or pick again. That
is the same trade the pick skill already hands him; it does not get taken back at the gate.

## Step 3: Publish

Run **Steps B and C of `ai-daily-learn-publish`** against the same directory: `publish.sh`, then
the discoverability checks against the live site, then `node build.js --mix` for what is due next.

**This is the step where `/ai-daily-learn-pick` Step 8 is overridden**, and it is the only
override. That skill ends "This skill never publishes" and offers the command; here you run it.
No second confirmation is needed before pushing — agreeing the brief in Step 1 *is* the
authorization, and asking twice for one decision is friction, not care.

Two things still deserve to be said out loud in the report rather than assumed, because they leave
the machine:

- **the newsletter goes to real subscribers** on a daily-lab publish, and it cannot be recalled
- **a Frontier publish sends no newsletter** — mention the piece in the next daily email instead

## Step 4: Report

Use the `ai-daily-learn-publish` Step C summary — the published deep link rather than the local
"Read it" block — and add the two lines `/ai-daily-learn-pick` Step 8 asks for, because they are a
record of a decision the user made:

- **what we chose and what we passed on**, the two losers by name with the reason each lost
- **where the article followed the brief and where it could not**, if anywhere

Then the **DUE NEXT** line, so tomorrow starts informed.

## Error Handling

Inherited whole from both parents; only the seam is new.

- **Nothing clears the bar on `--frontier`** → report it, name what you checked, stop. Do not fall
  through to Step 2. There is no article to gate and nothing to publish.
- **The user does not choose** — they go quiet, or ask for different candidates → you are still in
  Step 1. Never write or publish an article nobody picked.
- **The user picks, then rejects the draft** → fix it against the brief and re-gate. Do not publish
  a draft he has already said is wrong on the grounds that the topic was agreed.
- **`publish.sh` warns `site deploy failed`** → the session is on `main` but is **not live**, and
  the newsletter may have announced a page nobody can reach. Report it as a failed publish, give
  `make deploy` as the retry, and do not print the read link.
- **A lab day must never end empty.** If the conversation stalls and no article gets chosen, that
  is a missed day, which the daily cadence does not allow. Say so plainly and offer
  `/ai-daily-learn-publish` to fill the slot unattended. This is the one case where the discussion
  losing is worse than the choice being made for him.
- Everything else → `ai-daily-learn-pick` and `ai-daily-learn-publish` Error Handling.

## Scope

Writes `~/ai_learning/YYYY-MM-DD/` (or `frontier/YYYY-MM-DD/`), the brief in
`~/ai_learning/.briefs/`, and `journal.md`; then commits to `main`, deploys to both hosts and
sends the newsletter. **Every content rule lives in `../ai-daily-learn/`** — change it there,
through `/ai-daily-learn-feedback`, never here. This file should stay short: if it grows a rule of
its own, that rule almost certainly belongs in one of the two skills it composes.
