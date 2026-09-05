# The Two Things Missing From Most Coding Agent Requests

**Category**: Coding Agents & Productivity
**Tags**: benchmarks, prompt-engineering, paper
**Date**: 2026-09-06
**Level**: Start here
**For**: Using tools
**Hook**: The field worth eight points appears in one request out of twenty, and the fields people carefully fill in are worth almost nothing.
**Time to read**: ~10 minutes
**Engineer's view**: This is a test suite built entirely from well-formed input. The benchmark's bug reports are long, formal and complete, while the ones you type are two lines that assume things the agent cannot see. So the pass rate you read about was measured on requests almost nobody sends, including you.
**TLDR**: Coding agent benchmarks are built from long, carefully written bug reports, and almost nobody writes those. Rewrite the same tasks the way people actually ask and success drops about six points, but a couple of small additions win most of it back.

## Explain Like I'm 5

Imagine handing a builder a note that says the kitchen tap is broken. They arrive, look at it, and
now they have to guess. Did you want it to stop dripping? Did you want hotter water? Did you want
the whole thing replaced because you are selling the house?

A good note takes one extra line. Say what you want to be true when they are finished, and say why.

Most notes never say either. That is the whole finding.

## The Problem

You have shipped this before, and it had nothing to do with AI. Your integration tests passed for
months. You had written the fixtures yourself, so every payload had all its fields, sensible values
and clean encoding. Then real traffic arrived with trailing spaces, a missing field and an emoji in
a name column, and the service fell over on input your tests never contained. The tests were not
wrong. They were unrepresentative.

Coding agent benchmarks are that fixture set.

They are built from curated bug reports, and curated bug reports are unusually good. Researchers at
Sungkyunkwan University compared them against 718 real requests pulled from over six thousand
developer sessions with agents. **88% of the real requests are a problem statement and nothing
else, against 7% of benchmark problems. 87% of real requests are casually written, against 94% of
benchmark problems written formally.**

So when the same underlying bugs and the same fixes are rewritten the way people actually ask,
resolution rates fall by 6.4 points on average, and one model climbs from fourth place to second.
Part of the leaderboard order was an artifact of how the prompts were typed.

**The two things are the desired behavior and the motivation.** Say what should be true once the
task is done, and say why you want it. That is one extra line each, they are worth almost all of the
gap, and the details you were trained to include instead turn out not to be.

## The Fix: Say What You Want to Be True, and Why

The study takes a fixed set of tasks and varies only how they are written. Every variant in a
task family has the same bug and the same correct patch, so any change in the score belongs to the
writing.

### What did they actually vary?

Two axes, kept apart on purpose. The **information** was split into named parts: for a bug, the
problem statement, the desired behavior, reproduction steps and environment details; for a feature,
the problem statement and the motivation.

The **style** was varied along four dimensions: formality, imperative against declarative, confident
against hedged, and first person against not.

### Which parts were worth anything?

The result is lopsided, and the two fields the title promised are the top two rows:

| What you remove | What it costs |
| --- | --- |
| Desired behavior | 7.1 to 8.9 points, on every model tested |
| Motivation | 3.4 points |
| Reproduction steps and environment details, together | about 1.8 points |
| Any of the four style dimensions | small, and it varies by model |

Style barely registers. Writing casually, hedging, or using the imperative does not meaningfully
change whether the agent fixes your bug, which means the effort many people put into sounding
precise is spent in the wrong place.

Reproduction steps and environment details are the surprise on the other side. They are the fields
every bug template asks for, and together they are worth about a fifth of what one sentence of
desired behavior is worth.

### So why does nobody write it?

Because it feels redundant. You are reporting a bug, so surely the desired behavior is that the bug
stops happening. **Only 5% of the real requests included it.** The most valuable thing you can add
appears in one request out of twenty.

It is not redundant, because "this crashes" has many correct endings. Should it raise a clear error,
skip the row, retry, or accept the input that currently crashes it? Each is a different patch, and
the agent picks one. Naming the ending you want is not extra detail. It is the difference between
the agent solving your problem and solving a neighboring one.

## What This Means for You

**When this matters.** Every request you type into a coding agent, and most of all the short ones.
The shorter your request, the larger the share of it that should be the desired behavior, because
there is nothing else in there to disambiguate the ending you want.

**How it affects you.** Two habits are worth swapping. Stop polishing tone, because the measurement
says it does not pay. Start ending every request with what should be true afterwards, because that
single sentence is worth more than everything else you might add.

It also changes how you read agent comparisons. A leaderboard built on curated issues is measuring
partly the curation, and the ranking moved when that changed.

**What to do about it.**

1. On your next request, add one sentence beginning "when this is fixed, ...". No tooling, no
   setup, and it is the whole finding.
2. Look back at your last ten requests and count how many said what the finished state should be.
   Most people find one or two, which is roughly the rate in the study.
3. For feature work, add why you want it. Motivation is worth about half what desired behavior is
   worth for bugs, and it is equally absent.
4. Then put it in the template your team already uses, so it stops depending on memory.
   `Implementing It` has the wording and a check that catches a request missing it.

## Implementing It

**The change.** Three places, and the third is what makes it stick.

*The request itself.* One extra sentence, at the end, in your own words:

```text
The importer crashes on rows where the date column is empty.

When this is fixed, an empty date should be treated as unknown and the row
kept, rather than the whole import failing. We need it because a supplier
sends partial files on purpose and we cannot reject their whole batch.
```

Two sentences after the problem statement. The first is desired behavior, the second is motivation.
Nothing about the environment, nothing about repro steps, and by the study's numbers that is the
right trade.

*Your project's instructions file.* Make it the default rather than a thing you remember:

```markdown
## Writing requests in this repo

End every task with what should be true when it is done. If you are asking for
a change rather than a fix, add one line on why.

Do not spend effort on formality or hedging — it does not change the outcome.
Reproduction steps and environment details are optional; ask for them only when
the failure is not reproducible from the description.
```

*A check that catches the omission.* The point is to fail loudly before the agent starts, not to
discover afterwards that it fixed a neighboring problem:

```python
CUES = ("when this is fixed", "should ", "expected", "we want", "so that")

def missing_desired_behavior(request: str) -> bool:
    """True when nothing in the request says what the finished state is."""
    body = request.lower()
    return not any(cue in body for cue in CUES)

if missing_desired_behavior(prompt):
    warn("no desired behavior — the agent will pick an ending for you")
```

Wire it wherever your requests originate: a git hook on issue templates, a wrapper around your
agent command, or a linter on the file you paste from. Keep it a warning rather than a block,
because a genuinely exploratory request has no desired behavior yet and that is fine.

The cue list is deliberately crude, and it should stay that way. Its job is to make you notice
before you hit enter, not to grade your writing, and a false alarm costs you one glance.

**How you know it worked.** Two signals, one immediate and one slower.

The immediate one is that you stop getting patches that fix a real problem you did not have. That
failure has a signature worth learning: the change is competent, the tests pass, and it is not what
you meant. If that has been happening, this is usually why.

The slower one is worth the setup if you drive an agent daily. Keep your last twenty requests, rerun
the ones that failed with a desired-behavior line added, and count how many succeed the second time.
You are looking for something near the study's eight points, on your own repository rather than a
benchmark. If you see nothing, your requests were already carrying the information some other way,
and you can stop.

## When Adding More to a Request Is the Wrong Fix

More words is not the lesson, and reading it that way would make your requests worse. The study
found that most of what people add is worth almost nothing, so a longer request full of environment
details and careful hedging buys you the cost of writing it and no more.

Some requests have no desired behavior yet, and forcing one is harmful. "Why is this slow?" is an
investigation. Inventing an ending for it tells the agent to stop looking and start fixing, and you
will get a confident answer to a question you were still asking.

The numbers themselves come with an edge. This is one benchmark family, built from SWE-bench tasks
and rewritten by the authors, and the real-request corpus comes from one dataset of agent sessions.
The direction is well evidenced across seven models. The exact eight points are not a promise about
your repository.

Three questions before you change how you write:

1. Does my request have one correct ending, or several?
2. Am I asking for a fix, or still asking a question?
3. If I got a competent patch that was not what I meant, would I notice?

## Glossary

- **desired behavior** — one sentence saying what should be true once the task is finished
- **motivation** — why you want the change, which matters most on feature requests rather than bugs
- **resolution rates** — the share of tasks where the agent's patch actually fixes the problem
- **task family** — one underlying bug and fix, written several ways, so only the wording varies
- **variant** — one way of writing a task, differing from its siblings only in the words used
