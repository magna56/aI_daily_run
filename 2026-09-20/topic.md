# How to Measure What One AI Task Costs in Dollars and Watts

**Category**: AI in Production
**Tags**: cost, observability, inference-serving, benchmarks
**Date**: 2026-09-20
**Level**: Building
**For**: Shipping AI
**Hook**: Google publishes two different energy numbers for the same prompt, and the only thing that changed between them is where they drew the line around the system.
**Engineer's view**: This is a bill priced per row that was really priced per query plan. You have read one: the unit looked like what users do, and it was really what your code does. A watt-hour per query is that mistake again. Users finish tasks, and a task is several queries plus retries.
**TLDR**: Companies publish an energy figure for a single query, and the numbers cannot be compared. Google's own figure for the same prompt moves 2.4x depending only on where they draw the line around the system.
**Time to read**: ~11 minutes

## Explain Like I'm 5

Two people weigh the same suitcase. One puts it on the scale by itself. The other steps on the scale holding it, subtracts their own weight, then adds the small bag clipped to the side.

They get different numbers. Both of them are telling the truth.

Nothing about the suitcase changed. What changed is where each person decided the suitcase ends. If you want to compare two suitcases, you have to agree on that line first. Otherwise you are not comparing luggage. You are comparing two opinions about where luggage stops.

## The Problem

You have shipped this bug before, in a system that had nothing to do with AI.

You put a dollar figure on a feature. You took the cost of one call, multiplied it by the number of calls in the log, and wrote the number in a planning doc. A month later, finance asked why the bill was triple.

The call cost was right. The unit was wrong.

Your log counted the calls that returned 200. Production also ran the timeouts, the retries, and the second attempt that finally worked. Users do not buy calls. They finish tasks, and a finished task costs whatever it took.

Now the same bug, one scale up.

Three companies have published what a single query costs in energy. Google reports 0.24 watt-hours for the median text prompt. Microsoft Research reports a range of 0.16 to 0.60, with a median near 0.31. Sam Altman put a ChatGPT query at 0.34. Those look like three measurements of one thing.

They are not, and you cannot rank them.

Google makes this easy to see, because they published both of their own numbers. The same prompt is 0.10 watt-hours if you count only the accelerator. It is 0.24 if you also count the idle machines, the host processor and memory, and the cooling. No model changed. No hardware changed. Only the line around the system moved.

So the fix: stop reporting a number and start reporting a measurement. State four things — the hardware, the instrument, the system boundary, and what counts as one task — and make the task the unit instead of the call.

```figure
{ "kind": "system",
  "title": "The whole argument: one prompt, two boundaries, two true answers",
  "lanes": [
    { "t": "you measure", "nodes": [
        { "id": "prompt", "t": "one Gemini text prompt", "s": "neutral" } ] },
    { "t": "you draw the line at", "nodes": [
        { "id": "chip", "t": "the accelerator only", "s": "bad" },
        { "id": "whole", "t": "the whole serving system", "s": "ok" } ] },
    { "t": "so you report", "nodes": [
        { "id": "low", "t": "0.10 Wh", "s": "bad" },
        { "id": "high", "t": "0.24 Wh", "s": "ok" } ] }
  ],
  "edges": [
    { "from": "prompt", "to": "chip", "s": "bad" },
    { "from": "prompt", "to": "whole", "s": "ok" },
    { "from": "chip", "to": "low", "t": "excludes idle, host, cooling", "s": "bad" },
    { "from": "whole", "to": "high", "t": "includes them", "s": "ok" } ],
  "note": "Both numbers are Google's, for the same prompt. The boundary is the whole difference." }
```

## The Fix: Report the Boundary With the Number, and Make the Task the Unit

A number on its own is a claim. A number with its boundary is a measurement. The difference is whether anyone else can check it.

### Why can't I just compare the published figures?

Because they are not the same shape. Google's 0.24 is a median over text prompts, on a boundary they describe. Microsoft's is a range with a median near 0.31, measured across production serving. The ChatGPT figure is an average, and no boundary is given with it.

A median, an average and a distribution do not compare. Google's own pair proves the point without leaving one company: 0.10 and 0.24 differ by 2.4x on the same prompt, and the gap is entirely idle capacity, host processor and memory, and cooling overhead.

Google's own language for the narrow version is worth borrowing. They call it "theoretical efficiency instead of true operating efficiency at scale", and an optimistic scenario at best.

### What are the four things I have to state?

**Hardware.** Which accelerator, how many, and what else shares the box.

**Instrument.** Where the reading came from. A meter, a vendor counter, or a published table. These disagree, and a published table is an assumption, not a reading.

**System boundary.** What is inside the line. Accelerator only, plus host processor and memory, plus idle capacity, plus cooling. Each layer you add raises the number.

**Task definition.** What counts as one finished unit of work, including the attempts that failed on the way.

Leave any of the four out and the number is not wrong. It is unfalsifiable, which is worse, because nobody can argue with it.

### Why the task and not the query?

Because the query is your unit, not your user's. A user asks for one thing. Your system may make four model calls, retry two of them, and discard one branch. The per-query number is honest about each call and silent about the work.

This is the same correction that per-token pricing needs. Microsoft names what drives the variation: how many tokens are read and generated, how fast the hardware runs them, how large the model is, and how well the whole system is managed. Three of those four are yours.

## What This Means for You

**When this matters.** The moment anyone asks what an AI feature costs, or compares two providers on price or energy. Also the moment you read a vendor efficiency claim and want to know whether it applies to you.

**How it affects you.** Your per-call number is probably too low, and by a factor you have not measured. The gap is retries, discarded branches and multi-step tasks, and it grows as the feature gets more agentic. Any energy figure you quote is carrying someone else's boundary, usually the narrow one, because narrow numbers are the flattering ones and they travel further.

**What to do about it.** Start here, and it needs no new infrastructure: take yesterday's logs and divide total tokens by the number of *finished user tasks*, not by the number of calls. Compare that to the per-call number in your planning doc. The ratio is your retry and fan-out multiplier, and it is the single most useful number in this article.

Then, when you want the figure to survive a meeting, instrument it properly. Wrap the task, count every attempt, and attach the four statements to the number. Print the boundary next to the value so nobody has to ask.

If you quote a public energy figure, quote its boundary in the same sentence. "0.24 watt-hours" is a fragment. "0.24 watt-hours, median text prompt, including idle capacity and cooling" is a fact.

## Implementing It

**The change.** Three roles touch this, and only one of them is the call site.

**Role 1 — the engineer instrumenting the task.** The unit of measurement becomes the task, so the meter has to outlive the call. Open it once, record every attempt inside it, and close it when the user's request is satisfied or abandoned.

```python
# before — the meter is the call, so a retry is invisible
resp = call_model(prompt)
log.info("tokens=%d cost=%f", resp.total_tokens, price(resp))

# after — the meter is the task, so it outlives the retry loop
meter = TaskMeter(task_id, RATES)
for step in plan:                        # fan-out: several calls per task
    while True:
        resp = call_model(step.prompt)
        meter.record(step.model, resp.prompt_tokens, resp.output_tokens, resp.ok)
        if resp.ok:
            break                        # the retry re-sends the prompt: tokens paid twice
report(meter)                            # closes when the user's request is satisfied
```

`TaskMeter` itself is twelve lines and lives in `code_example.py`. The decision is where you
open it and when you close it, not what it does inside.

**Role 2 — whoever owns the rate table.** This is the role that gets skipped, and it is where the boundary actually lives. A rate is not a float. It is a float plus where it came from, so make the type refuse to be created without one.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Rate:
    usd_in: float
    usd_out: float
    wh_per_token: float
    boundary: str      # "accelerator only" | "whole serving system"
    instrument: str    # "vendor published table" | "node power meter"
    source: str        # the URL the figure came from
```

A bare `0.00006` in a dictionary is how a narrow vendor figure ends up in your capacity plan wearing a comprehensive label. Making `boundary` required means nobody can add a rate without deciding.

**Role 3 — whoever reads the number.** The report prints the boundary beside the value, every time, so the figure cannot be quoted without it.

```python
def report(meter):
    usd, wh, calls = meter.totals()
    b = {meter.rates[m].boundary for m, *_ in meter.attempts}
    print(f"task {meter.task_id}: ${usd:.5f}, {wh:.4f} Wh over {calls} attempts")
    print(f"  boundary: {', '.join(sorted(b))}")
```

If that set has more than one member, you are adding watt-hours measured at different boundaries, and the total means nothing. Assert on it rather than printing it.

**How you know it worked.** Two signals, and both are numbers you can watch move.

First, attempts per task should be greater than one. If your meter reports exactly 1.0 across a day of production traffic, it is counting calls and you have not changed anything. The retry path is not going through the meter.

Second, cost per task should exceed cost per call by the same multiplier you calculated from yesterday's logs. If the two disagree, the meter is closing early — usually because a background retry finishes after the response is returned to the user.

The failure you will actually see is a `KeyError` on a model name the rate table does not carry. Let it crash. A missing rate is a task priced at zero, and a silent zero is how the original number got wrong.

## When Measuring Cost per Task Is the Wrong Tool

Per-task measurement costs you something, and it is worth naming.

It adds a span to every request path, and the meter has to survive retries and background work, which means it has state and state has bugs. If your feature is one model call with no retry and no fan-out, per-task and per-call are the same number, and you have paid for a wrapper that tells you nothing.

The energy half is weaker than the dollar half, and you should say so out loud when you present it. Dollars come from a price you are actually charged. Watt-hours come from a published table, which means the number is an assumption with a citation, not a reading. Without a meter on the machine, you are reporting someone else's measurement at someone else's boundary.

There is a third case, and it is the one that should stop you. When the spread between your runs is driven by task *definition* rather than efficiency, you are benchmarking your own prompt. Tighten the task before you compare anything.

Three questions before you adopt this:

Does my feature actually retry or fan out, or am I instrumenting a single call?

Can I state all four things today, or am I about to publish a number I cannot defend?

If the answer moves by 2x, does any decision I am making change?

## Glossary

- **Boundary** — the line around what a measurement counts: accelerator, host, idle capacity, cooling.
- **Instrument** — where a reading came from: a power meter, a vendor counter, or a published table.
- **Task** — one finished unit of user work, including every attempt it took to finish.
- **Attempts** — all calls a task made, including the ones that timed out or were discarded.
- **Watt-hours** — energy, not power: one watt drawn for one hour. The unit vendors publish per query.
- **Median** — the middle value. It does not compare to an average, which is what makes the public figures unrankable.
