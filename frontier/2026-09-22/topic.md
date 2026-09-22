# How to Stop Agent Auto-Tuning From Memorizing Your Benchmark

**Category**: Applied Research
**Tags**: agents, benchmarks, paper
**Date**: 2026-09-22
**Level**: Building
**For**: Building agents
**Hook**: A loop that edits an agent's prompts and tools until the score goes up is an optimizer, and an optimizer with only one benchmark to read will learn the benchmark.
**Engineer's view**: This is tuning a query against staging. You added indexes until the plan was perfect, shipped it, and production did not move, because staging had a tenth of the rows and none of the skew. You had not optimized the query. You had optimized it for staging.
**TLDR**: An automatic tuner will happily learn your benchmark instead of the task. In a study from Google Research, the version that scored worst on the set it tuned against was the one that generalized best.
**Time to read**: ~11 minutes

## Explain Like I'm 5

A student revises for an exam using last year's paper, with the answers printed at the back.

They practice until they get every question right. Perfect marks, every time.

Then this year's paper arrives and they are lost. They did not learn the subject. They learned that paper.

The marks were real — that is what makes this hard to spot. The only way to tell the two students apart is to hand them a question neither has seen.

## The Problem

You have shipped this before, and it had nothing to do with AI.

You tuned a slow query against your staging database. You read the plan, added an index, read it again, added another. By the end it was fast, and you had the numbers to prove it.

Production did not move.

Staging had a tenth of the rows and none of the real skew, so the plan you had lovingly shaped was a plan for staging. You had not optimized the query. You had optimized it against the only thing you were measuring.

Now put that loop under a machine and let it run all night.

An agent's capability comes mostly from its harness — the prompts, control flow, tools, memory and context handling wrapped around a frozen model. Several recent methods evolve that harness automatically: propose edits, score them on a benchmark, keep whatever scores higher, repeat. It works, and the scores climb.

That loop is an optimizer, and the benchmark is the only signal it can read. So it does what your index tuning did, except thousands of times and without mentioning it.

Google Research measured how bad this gets and published the fix as **RRSI**. So: constrain what the optimizer is allowed to propose, constrain what it is allowed to keep, and judge the result only on tasks it was never allowed to evolve against.

```figure
{ "kind": "system",
  "title": "The whole argument: what the search is allowed to read decides what it learns",
  "lanes": [
    { "t": "the search can read", "nodes": [
        { "id": "only", "t": "just the evolve set", "s": "bad" },
        { "id": "plus", "t": "evolve set, held-out kept back", "s": "ok" } ] },
    { "t": "so it keeps edits that", "nodes": [
        { "id": "name", "t": "name the tasks", "s": "bad" },
        { "id": "work", "t": "work anywhere", "s": "ok" } ] },
    { "t": "and you ship", "nodes": [
        { "id": "fake", "t": "100 tuned · 46 unseen", "s": "bad" },
        { "id": "real", "t": "77 tuned · 72 unseen", "s": "ok" } ] }
  ],
  "edges": [
    { "from": "only", "to": "name", "s": "bad" },
    { "from": "plus", "to": "work", "t": "critic rejects the rest", "s": "ok" },
    { "from": "name", "to": "fake", "s": "bad" },
    { "from": "work", "to": "real", "s": "ok" } ],
  "note": "Numbers from the Code tab. The higher tuned score is the one that means nothing." }
```

## The Fix: Constrain What the Search May Propose, and Keep a Split It Never Sees

Three regularizers, and they attach at two different points in the loop.

### Why would an automatic optimizer overfit a harness?

Because memorizing is cheaper than generalizing, and nothing in the loop prefers the harder route. An edit that hardcodes an answer for one task scores immediately. An edit that improves reasoning in general scores less, and later.

Run the Code tab to watch it happen. An unregularized search reaches **100.0** on the set it tunes against — a perfect score, which is the warning rather than the achievement — and manages **63.5** on unseen tasks from the same distribution and **46.5** on a different mix. The regularized search scores **76.6** on the tuned set and **72.4** on the different mix.

The paper's own table has the same shape at realistic magnitudes. RRSI took the *smallest* gain on the evolve split of any method tested, 90.5 against a rival's 93.0, and the *highest* out-of-distribution average, 43.6 against 40.6.

### What does the leakage critic actually reject?

It screens proposals before they are ever scored, and it rejects an edit that mentions task names, entity names, task-specific values, or answers from the evolve benchmark. It also rejects inert machinery — code added that does nothing. Generic improvements to a prompt survive.

This is the cheapest of the three and it does most of the work, because it attacks the shortcut directly rather than trying to detect it after the fact.

### How do you stop the harness accumulating dead weight?

A pruner, which removes a component on any of three findings: it produced no strictly positive gain in the recent window, it never contributed meaningfully, or the benefit it once had has since evaporated because later edits overtook it.

The third is the one people would not write themselves. A change that helped in round two can be pure cost by round nine, and nothing removes it unless something is looking.

## What This Means for You

**When this matters.** The moment anything automatic edits your agent and keeps what scores better. That includes prompt optimizers, tool-description tuners, and the loop you build yourself when you ask a model to improve its own system prompt against your evals.

**How it affects you.** If your eval set is also your tuning signal, your reported gain is partly fiction and you have no way to size the fiction. The failure is invisible in exactly the place you would look, because the number you are watching is the number being gamed.

**What to do about it.** Start here, and it costs one afternoon: split your eval tasks into a set the tuner may read and a set it may never read, and report both. If you have only one set, take a fifth of it, lock it, and treat any change in that fifth as the real result. Most teams running prompt optimizers have never done this, and it is the difference between a measurement and a story.

Then, when you compare two tuning runs, compare them on the locked split. A run that wins the tuned set by a wide margin and the locked split by a narrow one is telling you what it learned.

## Implementing It

**The change.** Three roles, and the first is the one that decides whether the other two matter.

**Role 1 — whoever owns the task splits.** This is the whole deliverable. Without a split the optimizer cannot read, there is nothing to regularize toward.

```python
# ids must be unique across splits — a memorizing edit that scores on both
# hides the entire effect, which is a bug I hit writing the Code tab
evolve   = load_tasks("evolve")      # the optimizer reads this
held_in  = load_tasks("held_in")     # same distribution, never read
ood      = load_tasks("ood")         # a different mix, never read
```

RRSI's repo expects exactly this: adding a domain means writing `domains/<name>/adapter.py` with task splits and an evaluation method.

**Role 2 — whoever writes the proposer.** Bound how many edits a candidate may bundle, and shrink that bound over time.

```python
def edit_budget(t, rounds, b_max=4, b_min=1):
    # cosine anneal: bundle freely early, one change at a time late
    return math.ceil(b_min + (b_max - b_min) * 0.5 * (1 + math.cos(math.pi * t / rounds)))
```

Early rounds may bundle several coordinated changes. Late rounds are sparse, so a gain in round nine is attributable to one edit rather than four — which is what makes the pruner's job possible at all.

That annealed budget buys a second property worth having on its own. A late round cannot quietly rewrite half the harness, so when a score drops you are reading a small diff rather than reconstructing which of four simultaneous changes did it.

**Role 3 — whoever writes the selector.** Two filters, one before scoring and one after.

```python
def critic_rejects(edit, benchmark_terms):
    # screens BEFORE the edit is ever scored, so the shortcut never gets a number
    return any(term in edit.text for term in benchmark_terms) or edit.is_inert

def pruner_rejects(component, gains, window=3):
    recent = gains.get(component.id, [])[-window:]
    return len(recent) >= window and max(recent) <= 0.0
```

Order matters. The critic runs before evaluation on purpose: once a leaky edit has a high score attached, every later comparison is against a poisoned baseline.

**How you know it worked.** Two signals, and the first is counterintuitive enough to write down before you start.

Your gain on the tuned set should get **smaller**, not larger. A regularized run that still tops the evolve split has not been regularized. In the paper RRSI gave up 2.5 points there and took 3.0 on the out-of-distribution average; in the Code tab it gives up 23.4 and takes 25.9.

Second, the harness should get smaller, or at least stop growing. The pruner is the only thing removing anything, so if component count only rises, it is not firing. RRSI's harness ran on 30% fewer tokens than the unregularized one.

## When Regularized Self-Improvement Is the Wrong Tool

If you have one benchmark and cannot split it, this method has nothing to hold on to — but that is an argument against running unregularized evolution too, not a licence for it. Hand-tuning a harness and measuring once is more honest than a search you cannot audit.

Be careful about the size of the win. The out-of-distribution averages in the paper sit around 40 out of 100, so the regularized harness is still failing most unfamiliar tasks. RRSI improves a bad number. If your reading is that auto-tuning now transfers, the table does not say that.

The search itself is expensive, and the 30% token saving is at inference, not during evolution. Running many candidates over many rounds against real benchmarks costs far more than the harness will save back on any small deployment.

Three questions before adopting it:

Do I have enough eval tasks to give one split away entirely?

Is anything in my pipeline already tuning against the numbers I report?

Would I still ship this if the tuned-set gain came out smaller than the baseline's?

## Glossary

- **Harness** — the prompts, control flow, tools, memory and context handling around a frozen model.
- **evolve split** — the tasks the optimizer is allowed to read and score against.
- **Out-of-distribution** — tasks from a different mix than the ones tuned on, used to check the gain is real.
- **Leakage** — an edit that encodes benchmark answers or names rather than general capability.
- **Pruner** — the step that removes harness components that stopped paying for themselves.
- **annealed budget** — a cap on edits per proposal that shrinks over rounds, making late gains attributable.
