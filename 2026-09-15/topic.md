# How to Find Permission Bugs in Your Code With a Coding Agent

**Category**: AI Engineering Practices
**Tags**: security, coding-agents, reliability
**Date**: 2026-09-15
**Level**: Start here
**For**: Using tools
**Hook**: Three models audited one codebase and sent back seven claims. Four were real, and a test found the one bug all three missed.
**Engineer's view**: This is a flaky test suite you learned to ignore. An audit by three models returns claims the way a noisy linter returns warnings — some real, some invented, some you cannot even check. Until you can settle a claim mechanically, the pile is not findings. It is homework.
**TLDR**: A coding-agent audit does not return bugs. It returns claims, and in the run below barely half of them survived checking.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine hiring three inspectors who never get tired. You send them through a building and ask them to try every door. They come back with a long list of doors they say were unlocked.

Some of those doors really were unlocked. Some were locked all along. One is a door that does not exist. And one genuinely unlocked door is on nobody's list.

So you do not act on the list. You cut a master key and walk every door yourself. You use their list for one thing only: to learn which kinds of doors are worth walking.

## The Problem

You have shipped this, and it had nothing to do with AI. You turned on a stricter linter on a codebase that had never run one. It reported nine hundred warnings.

You read the first twenty. You fixed four that were obviously right, opened a ticket for the rest, and moved on. Nobody turned the linter off. Nobody read it either.

The warnings were real work. They arrived as an unsorted pile with no proof attached, and the pile won.

A tool that produces more claims than you can check produces nothing.

Point a coding agent at your codebase and ask it for a security audit, and this is exactly what arrives. Datasette's maintainers ran one across three models and several rounds, and the permission bugs it turned up are real and worth knowing — that is [2026-09-11's session](#2026-09-11). This one is about the other half, the half that decides whether an audit is worth running twice: what you do with the pile.

The fix: stop reading the findings, and build something that settles each one mechanically. Then use the models for the only thing they are uniquely good at here — telling you which shapes to check.

```figure
{ "kind": "system",
  "title": "The whole argument: what an audit returns, and what settles it",
  "lanes": [
    { "t": "3 models, 3 rounds", "nodes": [
        { "id": "raw", "t": "25 raw findings" } ] },
    { "t": "checked mechanically", "nodes": [
        { "id": "real", "t": "4 real", "s": "ok" },
        { "id": "noise", "t": "2 noise", "s": "bad" },
        { "id": "unt", "t": "1 not testable", "s": "neutral" } ] },
    { "t": "the checker also finds", "nodes": [
        { "id": "miss", "t": "1 bug nobody reported", "s": "new" } ] }
  ],
  "edges": [
    { "from": "raw", "to": "real", "t": "7 distinct", "s": "ok" },
    { "from": "raw", "to": "noise", "s": "bad" },
    { "from": "raw", "to": "unt", "s": "neutral" },
    { "from": "real", "to": "miss", "s": "new" } ],
  "note": "Twenty-five findings collapse to seven claims. The checker outlives the audit." }
```

## The Fix: Settle Each Claim With a Checker, Not a Reviewer

A finding is not a bug. It is a sentence a model wrote, and it comes in one of three states. Sorting it into the right one is the whole job, and only the first two can be done by a machine.

- **Real.** It names something specific, and checking shows the something is true.
- **Noise.** It names something specific, and checking shows it is false. Often confidently so: one model below reported a backup table that is not in the schema.
- **Not testable.** It names nothing specific. *"The permission logic may be inconsistent in places"* is a sentence no checker can settle, so it costs a human an hour and usually ends in nothing.

What settles the first two is an **oracle** — code that answers the audit's question from your own schema, independently of anything a model said. Here it walks the schema and reports which requests reach data they should not. Another class of claim needs a different oracle. The independence is the property that matters.

### Why does the oracle have to be independent?

Because otherwise you have measured nothing. If you build the checker out of the cases the model reported, it will confirm every one of them and find nothing else, and you will have written an expensive way to agree with yourself. The oracle has to derive its cases from the system, so it can disagree with the model in both directions. In the run below it does: it rejects two claims and finds one bug no model mentioned.

### How do I decide which claims to look at first?

Count how many models said it. That is the only ordering signal available before you have written any tests, and it is a strong one.

```figure
{ "kind": "bars",
  "title": "Agreement predicts truth, before you have checked anything",
  "bars": [
    { "label": "reported by two or more models", "v": 100, "d": "3 of 3 real", "s": "ok" },
    { "label": "reported by one model only", "v": 25, "d": "1 of 4 real", "s": "bad" }
  ],
  "note": "Same 25 findings, same checker. Triage the agreed ones first and the noise waits." }
```

### When do I stop running rounds?

When the marginal round stops paying. Going from two rounds to three took the run below from 15 raw findings to 25, and precision fell from 67% to 57% — the pile grew faster than the truth in it. Measure that on your own repo rather than trusting a number from mine, because it depends on how narrowly you tasked the models.

## What This Means for You

**When this matters.** Any time a model hands you a list you are expected to act on: a security audit, an automated code review, a dependency triage, a migration plan. The longer the list, the more this decides whether the tool helped.

**How it affects you.** The failure is not that models are wrong. It is that a claim and a verified bug look identical in a list, so the whole pile inherits the trust level of its weakest item. That is why audits get run once and never again, the same way the linter got installed once and never read.

**What to do about it.** You can do the first step with output you already have, and it needs nothing built. Take the last automated review or scan anyone on your team ran, and sort twenty of its items into the three states above by hand. Ten minutes. The number worth noticing is how many land in *not testable*, because that bucket is what quietly consumed the week.

Then write the oracle for one class of claim — one function, derived from your own config. That is the next section. Only after that is it worth running more models or more rounds, because until the checker exists, every extra finding costs you time instead of saving it.

## Implementing It

Three roles, and the middle one is the one that gets skipped: whoever tasks the models, whoever writes the oracle, and whoever triages what comes back.

**Tasking.** Do not ask for bugs. Ask for an enumeration, because enumeration is exhaustive, boring and checkable, which is the shape of work a model is genuinely better at than you. Google's Big Sleep team did the same thing — they handed the model a specific commit and diff and asked for variant analysis of the current code rather than open-ended bug hunting. A prompt that produces triageable output looks like this:

```text
Enumerate, for this schema, every distinct way a caller can name a table,
including case variants, derived tables and engine-internal tables.
For each name, list the tables whose rows a request for it can read.
Output one JSON object per name: {"request": <name>, "reaches": [<tables>]}.
Do not assess whether anything is a vulnerability.
```

That last line is the one that matters. A model asked to judge returns prose; a model asked to list returns rows you can feed to a checker.

**The oracle.** One function, answering the same question from the schema itself. This is the independence that makes the numbers mean anything:

```python
def leaks(name):
    """Does the naive check allow this name while it reaches private rows?"""
    allowed = name not in PRIVATE          # the bug: exact string, typed name
    return allowed and bool(reachable(SCHEMA, name) & PRIVATE)
```

**Triage.** Give every finding a verdict, then group by target and count distinct models. `code_example.py` runs the whole pipeline; these are the two pieces to lift:

```python
def verify(finding):
    """real | noise | untestable -- the only judgment a machine can make."""
    name = finding["request"]
    if not name:
        return "untestable"                # no target: a human has to read it
    if not reachable(SCHEMA, name):
        return "noise"                     # a table that does not exist
    return "real" if leaks(name) else "noise"

groups = {}
for f in collected:                        # one entry per model per round
    g = groups.setdefault(f["request"] or f["claim"],
                          {"verdict": verify(f), "models": set()})
    g["models"].add(f["model"])
```

Sort the groups by `len(g["models"])` descending and work down. Never delete the noise — keep it, because the ratio is your only read on whether the next round is worth running.

**How you know it worked.** Three numbers, and you should be able to say all three out loud. Precision: in the run below, 4 of 7 distinct claims survived, which is 57%. The agreement split: 3 of 3 real when two or more models agreed, against 1 of 4 for single-model claims. And coverage: the oracle found 5 reachable private tables where the models named 4, so `members` was a real bug that three frontier models missed and a twelve-line function caught.

That last number is the one that tells you the audit worked. If your oracle never finds anything the models missed, it is not independent of them, and you are measuring your own assumptions.

## When a Coding-Agent Audit Is the Wrong Tool

If you cannot write the oracle, do not run the audit. The value of the output is capped by your ability to settle it, and without a checker you have bought a document that makes everyone feel unsafe and tells nobody what to do. Write the checker first. If it turns out the checker alone finds everything, you have saved the model fees.

It cannot supply the threat model either. Whether a row is sensitive is a product decision, and a model will flag a public table while staying quiet about the one that matters. In the run below it did exactly that, reporting a notes table that leaks nothing.

Run it on code you own. Datasette shipped its fixes and deliberately held some tests back so people could upgrade before the details were public, which is the same discipline pointed the other way.

Three questions before you start:

- Can you write, today, a function that settles the class of claim you expect back?
- Does that function derive its cases from your system rather than from the model's list?
- If two models disagree, do you know which one you would check first?

## Glossary

- **finding** — one claim from an audit: a sentence a model wrote, not yet a bug.
- **oracle** — code that answers the audit's question from your own system, independently of the model.
- **triage** — sorting findings by verdict and agreement so the checkable ones get checked first.
- **precision** — the share of distinct claims that survive checking; 57% in the run in the Code tab.
- **not testable** — a finding naming nothing specific, so no checker can settle it either way.
- **variant analysis** — handing a model one known bug and asking where else that shape occurs.
