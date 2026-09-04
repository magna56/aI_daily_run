# Why GPT-6 Astra Has Two Scores on ARC-AGI-3: 63% and 99%

**Category**: Evals & Reliability
**Tags**: benchmarks, context-engineering, cost
**Date**: 2026-09-04
**Level**: Start here
**For**: Shipping AI
**Hook**: The same model ran the same benchmark twice and came out thirty-seven points apart. What changed was the code around the model, not the model.
**Time to read**: ~10 minutes
**Engineer's view**: This is benchmarking two branches when one had a warm cache. The scaffolding around the model sits inside the number, not outside it: what it keeps between steps, and how long context gets shortened. So a score you did not produce tells you about somebody else's setup as much as the model.
**TLDR**: One model ran the same benchmark twice and the scores were thirty-seven points apart. Only the code around the model changed, so a published score describes a setup as much as it describes a model.

## Explain Like I'm 5

Imagine testing a chef by asking them to cook the same dish twice.

The first time, they work on a bare counter. Every time they turn around, someone clears away their
prep, so each step starts from nothing. The second time, their station stays exactly as they left
it.

Same chef, same recipe, and the second dish is far better. You did not learn how good the chef is.
You learned how much the kitchen was helping.

## The Problem

You have shipped this bug before, and it had nothing to do with AI. You benchmarked two versions of
a service and the new one came out three times faster. You wrote it up and sent it round. Then
somebody asked whether both runs had a warm cache, and the answer was no. The number was real. It
just measured your setup rather than your change.

That is a nasty class of bug, because nothing looks broken. Both runs finished. Both produced a
number. The number even reproduced, as long as you reproduced the mistake along with it.

Model benchmarks have this exact shape, and the setup has a name. The harness is the code around the
model that decides what carries from one step to the next, how a long conversation gets shortened,
and what the model sees when it acts again.

This week a benchmark's own maintainer ran GPT-6 Astra through one benchmark, ARC-AGI-3, two ways.
Same games, same actions, same limits, same scoring. Under their neutral harness it scored 62.7%.
Under a harness using the model provider's own context management it scored 99.9%. Nothing about the
weights changed between those runs.

**The fix is to treat every score as belonging to a pair — the model and the harness — and to
record both.** A number with only one half named cannot be compared with anything.

## The Fix: Record the Harness Next to the Score

### What is a harness, exactly?

It is everything around the model that survives between steps. In this case the two differed on one
axis. The **neutral harness** lets the model carry forward notes it chooses to keep, through an
interface that is identical for every provider. The **provider harness** preserves the model's own
opaque reasoning state between requests and uses compaction to shorten long conversations, so it can
reuse prior work instead of reconstructing it.

Only the scaffold moved.

### Which knob actually mattered?

The maintainer published every reasoning-effort setting under both harnesses:

| Reasoning effort | Neutral harness | Provider harness |
| --- | --- | --- |
| None | 35.2% | 96.7% |
| Low | 17.5% | 98.0% |
| Medium | 38.6% | 98.4% |
| High | 54.8% | 99.9% |
| Extra high | 59.3% | 98.4% |
| Max | 62.7% | 98.6% |

Read down the first column and effort is the whole story: 45 points between low and max. Read down
the second and it is worth about three. Same weights, opposite conclusions.

Look harder at that first column and it is not even in order. Turning reasoning off scores 35.2%,
which beats turning it to low at 17.5%. A knob that runs backwards is a property of the scaffold,
not of the model underneath it.

### Why didn't this show up on the older benchmarks?

Because they barely carry state. Astra scores 97.5% on ARC-AGI-1 and 95.0% on ARC-AGI-2, near the
ceiling at every effort setting. Those are one-shot puzzles. ARC-AGI-3 is interactive, so the model
takes actions in an environment over many steps.

That is the rule to take away. **The harness owns a share of the score in proportion to how much
state the task carries across steps.** A one-shot classifier barely notices it. An agent that works
for twenty minutes is mostly measuring it.

And this is not a story about spending more to score more. The provider runs were about 3.66 times
faster, used 49% fewer tokens, and cost less: $18,817 against $26,098.

## What This Means for You

**When this matters.** Any time you compare two numbers you did not both produce. Picking a model
from a launch post, reading a leaderboard, or trusting last quarter's eval run after somebody
rewrote your agent's memory layer in between.

**How it affects you.** The risk is not that you get a slightly wrong number. It is that you draw a
confident conclusion that reverses under a different scaffold. Somebody runs an ablation, finds that
reasoning effort is worth 45 points, and rebuilds the product around a setting that is worth three.

**What to do about it.**

1. Next time you see a benchmark number, find out what harness produced it before you compare it
   with anything. That is one question and it costs you nothing. If the answer is not published,
   the number is a claim rather than a measurement.
2. Write the harness into every eval result you keep, not just the model name and the score.
3. Run your ablations on the harness you actually ship. A conclusion from a clean scaffold does not
   transfer to a production one.
4. When you qualify a new model, hold your harness fixed and change one thing. `Implementing It`
   has the guard that stops you comparing across a change you forgot about.

## Implementing It

**The change.** Three roles, and the second is the one that saves you.

*The eval author.* A result is not a score. It is a score plus what produced it, and the harness has
to be fingerprinted rather than named, because the name never changes when the behavior does:

```python
import hashlib, json

def fingerprint(harness):
    """Everything that changes what the model sees between steps."""
    facts = {"carry": harness.carry_policy,        # notes | reasoning_state | none
             "compaction": harness.compaction,      # off | summarize | evict_oldest
             "window": harness.context_window,
             "tools": sorted(harness.tool_names),
             "version": harness.version}
    return hashlib.sha256(json.dumps(facts, sort_keys=True).encode()).hexdigest()[:12]

Result = namedtuple("Result", "model harness_fp score effort n_tasks")
```

Hash the behavior, not the label. A harness called `default` in March and `default` in September is
two different harnesses, and the name is the one field guaranteed never to tell you so. Fingerprint
the fields that change what the model sees, and store the digest on the row itself rather than in a
README nobody opens.

*The comparer.* Refuse the comparison rather than reporting a difference nobody can interpret. This
is the whole intervention, and it is eight lines:

```python
def delta(a: Result, b: Result):
    if a.harness_fp != b.harness_fp:
        raise ValueError(
            f"harness differs ({a.harness_fp} vs {b.harness_fp}) — "
            f"this delta measures the scaffold too. Re-run one side, or "
            f"compare a matrix instead.")
    if a.effort != b.effort:
        raise ValueError(f"effort differs ({a.effort} vs {b.effort})")
    return b.score - a.score
```

*Whoever picks the model.* Stop reporting a list and report a matrix. One row per model, one column
per harness, because the interesting number is how much each model gains from its own scaffolding:

```python
for model in candidates:
    for harness in (neutral, ours):
        results.append(run_eval(model, harness))   # both, always
```

That matrix costs twice the compute and answers the question you actually have, which is whether a
model is good or merely well scaffolded. A model that gains forty points from its provider's context
management is telling you something useful about what you would have to build yourself.

**How you know it worked.** Three signals.

Point `delta()` at two records from before you adopted this and watch it raise. If every historical
pair compares cleanly, you are not fingerprinting enough fields — add the one that changed most
recently and try again. A guard that never fires is not protecting anything.

Then re-run one ablation you already believe, under two harnesses. If the ranking of your settings
survives both, the conclusion was about the model. If it flips, you just found out that a number in
your planning doc belongs to your scaffold.

Finally, watch what happens when someone edits the agent's memory layer. The fingerprint should
change in that commit, and every dashboard comparing across it should break loudly rather than
drawing a smooth line through a discontinuity.

## When Pinning the Harness Is the Wrong Tool

Pinning answers one question well and a different one badly, and the maintainer here runs both
harnesses on purpose for exactly that reason. A neutral scaffold tells you how models compare on
equal terms. It does not tell you what your users will get, because your users get the provider's
context management too. Report only the neutral number and you will systematically understate the
thing you ship.

Fingerprinting also costs you history. Every harness change invalidates the comparisons that cross
it, which is correct and still painful, because trend lines are how most teams notice a slow
regression. Version the fingerprint and keep the old records readable rather than freezing the
harness to protect a chart.

Skip the ceremony entirely on short single-turn evals. Where a task carries no state, the scaffold
has almost nothing to do, and the earlier benchmarks in this family sitting at 97.5% across every
setting are the evidence for that.

And be careful how far you carry the number. This is one model on one benchmark. The mechanism
generalizes; 37 points does not.

Three questions before you change anything:

1. How much state does my task carry between steps? That is the size of the exposure.
2. Am I comparing numbers I produced, or numbers I read?
3. When my harness changes, does anything currently break?

## Glossary

- **harness** — the code around a model that decides what carries between steps and what it sees next
- **compaction** — shortening a long conversation so a model can keep working within its context window
- **reasoning effort** — a per-request setting that controls how much thinking a model spends before answering
- **fingerprint** — a hash of the harness settings that change behavior, stored with every result
- **ablation** — changing one setting at a time to find out how much that setting is worth
