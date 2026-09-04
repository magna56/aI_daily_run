# How to Turn a Repo Into a Skill Your Agent Can Actually Run

**Category**: Building Agents & MCP
**Tags**: context-engineering, reliability, paper
**Date**: 2026-09-03
**Level**: Building
**For**: Building agents
**Hook**: A skill written by reading a project's documentation mostly does not help. The ones that help are the ones somebody checked by running them.
**Time to read**: ~10 minutes
**Engineer's view**: This is a package registry with no continuous integration. You write skill files the way you write a README, then publish them straight to the shelf your agent reads from. Nothing ran, so nothing caught the step that stopped working, and your agent loads confident instructions that fail on contact.
**TLDR**: Researchers distilled a large library of code repositories into skills for an agent, and enforced one rule. Nothing joins the library until its own instructions have been run and passed.

## Explain Like I'm 5

Think about a recipe card someone wrote by skimming a cookbook. It looks right. Every ingredient is
listed and the steps are in order.

But nobody ever cooked it. So nobody noticed that step four asks you to use a pan that was never
heated. You find out halfway through dinner.

Now imagine writing thousands of those cards for someone who cooks very fast and never questions the
card. The fix is boring and it works. Before a card goes in the box, somebody cooks it once.

## The Problem

You have shipped this bug before, and it was in a README. The setup section said to run
`make bootstrap`. That target had been deleted eight months earlier, in a cleanup nobody linked back
to the docs. It stayed wrong because nothing ever ran it. Then a new hire followed it on their first
morning and lost half a day, and you heard about it from them rather than from your build.

The fix your team reached was to stop trusting prose. You moved the setup steps into a script, and
you made continuous integration run that script on every commit. The documentation could still be
wrong, but now it was wrong loudly.

An agent skill is that README again, with the new hire arriving a thousand times a day and never
pushing back.

A skill is a file you write once that an agent loads whenever it decides the topic is relevant. Most
are written the way documentation is written: read the project, summarize what it does, save the
file. Nothing is executed at any point. So the skill goes wrong exactly the way your README went
wrong, except the reader is now a system that does not stop to ask whether the command still exists.

**The fix is to refuse a skill entry into the library until its own instructions have been run and
passed.** Split the source into three layers, check the result by executing it, and write down what
you could not check.

## The Fix: Run the Skill Before You Shelve It

Researchers at the Beijing Academy of Artificial Intelligence and three universities built this
pipeline, called DisCo, and pointed it at a thousand machine learning repositories. It produced
5,353 skills across 20 areas and 178 capability families.

### What is actually in a skill?

Three layers, and the split is the point. Each is loaded at a different moment:

| Layer | Job | When it loads |
| --- | --- | --- |
| `SKILL.md` | The usage policy: goals, key concepts, worked examples, failure modes | On open |
| `references/` | The substrate: detailed docs, algorithm specifics, parameter settings | Only when needed |
| `scripts/` | The execution interface: callable wrappers with declared inputs and outputs | When invoked |

`scripts/` is what separates this from a summary. The agent calls a wrapper instead of
reimplementing the method from a description, so the knowledge arrives as something that runs rather
than something to rewrite under pressure.

### How do you check a file you just wrote?

Four stages: **scope** which capabilities deserve to be skills, **ground** each one in evidence
pulled from the source, **construct** the three layers, then **verify** before admission.

Verification uses whatever the repository already offers. Assertion-backed cases built from its own
examples. Its safe tests. Command-line checks, tiny-fixture checks, smoke scripts. A failure blamed
on the skill triggers a local repair and a rerun of the affected checks. Nothing enters the library
without passing.

What survives is a construction record holding three things: the evidence used, the checks
performed, and any gap that is still open. Unresolved gaps are recorded rather than quietly dropped,
which is the difference between a known limitation and a lie.

### Won't five thousand skills bury the context window?

They would, if the agent read them. It does not. It starts at a router that describes candidates by
scope and intended use, follows an area-to-family path, and opens only the entry points a task
needs. Every skill opens with a short use description so the agent can tell in one line whether to
keep reading, and links let it walk to a referenced skill without touching unrelated branches.

The library grows. The context does not.

## What This Means for You

**When this matters.** The moment you have more than a handful of skills, or the moment one of them
wraps a dependency that ships breaking changes. A skill nobody executes decays on exactly the same
schedule as a README nobody runs, which is to say silently and continuously.

**How it affects you.** You are probably writing skills by hand right now, from a project's docs,
and shipping them unrun. The failure is not that the agent ignores them. It is worse: the agent
trusts them, follows a stale command, and spends real tokens recovering from advice you gave it.

**What to do about it.**

1. Open a skill you already wrote and run its commands yourself, in order, in a clean directory.
   This takes ten minutes and needs no tooling. Most people find at least one dead step.
2. Move the part that has to work out of prose and into `scripts/`, so it can be invoked and tested
   rather than paraphrased by a model at run time.
3. Put the checks in continuous integration, so the skill is re-verified when its dependency moves.
   `Implementing It` has the gate.
4. Give every skill a one-line use description at the top. That line is what makes selective loading
   possible, and it is the cheapest thing on this list.

## Implementing It

**The change.** Three roles, and the middle one is the one nobody builds.

*The skill author.* Give the file a use description and put the executable claim in `scripts/`,
not in a paragraph:

```
skills/faiss-index/
  SKILL.md          # use description, worked example, failure modes
  references/       # loaded on demand
  scripts/build_index.py   # declared inputs and outputs, callable
```

```markdown
---
name: faiss-index
use: Build and query a vector index when a task needs approximate nearest neighbors.
---
Run `python3 scripts/build_index.py --dim 768 --metric ip`. It writes `index.faiss`
and exits non-zero if the dimension does not match the vectors it is given.
```

*The verifier.* This is the gate, and it belongs in continuous integration. Pull every command the
skill claims, run it against a small fixture, and refuse the skill on failure:

```python
def verify(skill, fixture):
    """Return (ok, gaps). A skill only ships when ok is True."""
    gaps = []
    for cmd in skill.commands:            # the claims the file makes
        rc, out = run(cmd, cwd=fixture)   # actually execute them
        if rc != 0:
            gaps.append(f"{cmd} exited {rc}: {out[:80]}")
    for case, expected in skill.cases:    # assertions from the repo's own examples
        if evaluate(case, fixture) != expected:
            gaps.append(f"{case} != {expected}")
    return (not gaps), gaps
```

Wire it as a gate, not a report. A report that lists failures beside a published skill has changed
nothing, because the skill is already on the shelf and the agent will still load it. A skill that
fails gets one repair pass and a rerun of the affected checks; if it still fails, it stays out and
the reason is written down:

```python
ok, gaps = verify(skill, fixture)
if not ok:
    skill = repair(skill, gaps)          # one pass, then re-check
    ok, gaps = verify(skill, fixture)
record(skill, evidence=skill.sources, checks=skill.commands, gaps=gaps)
if not ok:
    raise SystemExit(f"rejected {skill.name}: {gaps}")
```

*The retrieval side.* Progressive disclosure is what keeps a large library affordable. Index skills
by area and family, hand the agent only the router, and load a body only when its use description
matches:

```python
router = [(s.area, s.family, s.name, s.use) for s in library]   # ~20 tokens each
opened = [s for s in library if selects(task, s.use)]            # bodies, only these
```

**How you know it worked.** Three signals, in order of how fast they arrive.

Point the gate at a skill you already trust and watch it fail. If every skill you own passes on the
first run, the checks are not executing anything — that is the usual bug, and it looks identical to
success. Break one command on purpose and confirm the gate exits non-zero.

Then check the record. Every admitted skill should name the evidence behind it and the checks that
ran, and a skill with an open gap should say so. An empty gap list across a whole library is a
warning sign, not a clean bill of health.

Finally, watch the token count of your loaded context as the library grows. Adding fifty skills
should move it by roughly fifty router lines, not by fifty skill bodies. If context grows in
proportion to the library, selective loading is not working and the use descriptions are the place
to look.

## When Distilling a Repo Into a Skill Is the Wrong Tool

Distillation is not free and the paper says so: about $40 of compute per repository. Across a
thousand repositories that is a real budget line, spent before a single task runs.

It also creates a maintenance surface you now own. A verified skill is only verified against the
dependency version it was checked on. Point it at a library that ships breaking changes every few
weeks and the gate has to run again on a schedule, or the guarantee quietly expires and you are back
to a confident, stale file.

Skip it entirely when the source is small enough to read. If a project is four files, the agent can
open them, and a skill is a layer of indirection over something already cheap.

Be honest about the evidence too. The reported gains compare an agent holding these skills against
the same agent holding none, on a fixed backbone and budget: 134.3% higher on one machine learning
benchmark, 34.4% and 14.0% on two others, 9.2% on a fourth. That is a strong result for the library.
It is not a measurement of what the verification gate contributes on its own, because no ablation
isolates it. The gate is argued for here, not proven.

Three questions before you build this:

1. How often does the source move? Anything faster than monthly needs scheduled re-verification.
2. Can the capability be executed, or only described? Only the first kind survives a gate.
3. Would reading the source cost less than distilling it?

## Glossary

- **skill** — a file an agent loads on demand, holding instructions and callable scripts for one capability
- **use description** — the one-line summary that lets an agent decide whether to open a skill
- **progressive disclosure** — loading a router first and skill bodies only when selected
- **construction record** — the evidence, checks and open gaps kept for each admitted skill
- **router** — the index of use descriptions an agent reads first, to decide which skill to open
- **fixture** — the small fixed input a skill's checks run against, so a failure points at the skill
