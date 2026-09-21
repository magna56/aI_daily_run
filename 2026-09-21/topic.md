# How to Check Whether a Model's Confidence Score Means Anything

**Category**: Evals & Reliability
**Tags**: benchmarks, observability, from-scratch
**Date**: 2026-09-21
**Level**: Building
**For**: Shipping AI
**Hook**: TypeSafe's Jev model cannot return a malformed answer, but it can still be wrong — and the confidence number beside it is the only thing that tells you which one you got.
**Engineer's view**: This is a gauge wired to the wrong variable. You have shipped one: a health metric that read 100% all week, so the alert never fired. Not because the system was healthy, but because the number never moved. A confidence score you have not checked is that gauge.
**TLDR**: A schema guarantees the shape of an answer, never its truth. If your code branches on a confidence score, measure whether that score means what it says before you trust it.
**Time to read**: ~11 minutes

## Explain Like I'm 5

A weather app says it will rain. You want to know how much to trust it.

So you keep a notebook. Every time it says "70% chance," you write down whether it actually rained. After a hundred days you count. If it rained on about seventy of them, the app is honest. If it rained on thirty, the app is not lying about the weather. It is lying about itself.

You cannot tell which one you have by looking at any single forecast. You can only tell by counting.

## The Problem

You have shipped this bug before, and it had nothing to do with AI.

You added a health gauge to a service. It read 100%. It read 100% the next week, and the week after that. You had wired it to a counter that incremented on every lookup instead of every hit, so the number had only one value it could ever show.

The alert threshold you hung on it was decoration.

Nobody caught it, because a number that is always fine looks exactly like a system that is always fine. It took an outage to find out the gauge had never been measuring anything.

Now put a model in the loop.

Ask one for a decision and a confidence, and you get both. The confidence is usually high. It is high when the answer is right and high when the answer is wrong, because nothing in ordinary training forces that number to correspond to anything outside itself. You write `if confidence > 0.9` and you have rebuilt the gauge.

TypeSafe's Jev makes this sharp by removing a *different* failure first. It returns typed values, so the valid answers are fixed in the schema before the call and a malformed reply is impossible. The company describes this as a model that cannot hallucinate.

Read that claim precisely. What is guaranteed is the shape. A well-typed answer can still be wrong.

So the fix: stop trusting the confidence and start measuring it. Group your past predictions by the confidence they carried, then compare what each group claimed against what it actually delivered. That comparison is calibration, it is about twenty lines of code, and it is the only thing that tells you whether the number you branch on means anything at all.

```figure
{ "kind": "system",
  "title": "The whole argument: two failures, and only one of them has a schema",
  "lanes": [
    { "t": "an answer can fail", "nodes": [
        { "id": "parse", "t": "malformed, unparseable", "s": "bad" },
        { "id": "wrong", "t": "well formed but wrong", "s": "bad" } ] },
    { "t": "the typed schema", "nodes": [
        { "id": "kills", "t": "eliminates it", "s": "ok" },
        { "id": "blind", "t": "cannot see it", "s": "bad" } ] },
    { "t": "what is left to catch it", "nodes": [
        { "id": "cal", "t": "the confidence — if you measured it", "s": "new" } ] }
  ],
  "edges": [
    { "from": "parse", "to": "kills", "s": "ok" },
    { "from": "wrong", "to": "blind", "s": "bad" },
    { "from": "blind", "to": "cal", "t": "measure it or you are guessing", "s": "new" } ],
  "note": "\"Cannot hallucinate\" is a claim about the left column. Your wrong answers live in the right one." }
```

## The Fix: Measure the Confidence Before You Branch on It

Calibration is one property: **of all the cases where the model claimed 90%, it should be right about 90% of the time.** Nothing else. Not accuracy, not helpfulness.

### Why is it confident when it is wrong?

Because confidence and correctness come from different places. The number is a softmax over the model's own scores, and training pushes those scores apart to make answers decisive. Sharpening moves the reported number toward 1 without adding knowledge.

Run the Code tab and watch it happen. A model with 44.3% real accuracy, sharpened the way a decisive-sounding model is, claims over 90% confidence on 1,561 of 4,000 cases. It is wrong on 38.1% of them. You were promised under 10%.

### What does a calibrated number actually promise?

It promises you can do arithmetic with it. At 90% you expect to be wrong one time in ten, budget for that, and route those cases elsewhere. An uncalibrated 90% supports no arithmetic at all, which is why the threshold built on it is superstition rather than policy.

The repair is one number. Temperature scaling divides every score by a single scalar fitted on held-out data. In the simulation that takes calibration error from 0.342 to 0.046 without moving accuracy, because scaling every score alike never changes which option wins.

Then the uncomfortable part, which is the real finding. After the repair only **2** of those 4,000 cases still claim above 90%. The confident model was not more certain than the honest one. It was the same model, saying so more loudly.

### So does a typed answer help at all?

Yes, and it pays to be precise about what it buys. Jev exposes three primitives: `Choice` picks from a list, `Score` rates against a rubric, and `Noul` answers whether a statement is true. Each returns a typed value with a probability beside it, and each is scored independently against the same state, so a tenth question does not degrade the first.

That decomposition is the transferable idea, and it does not require their model. Split a judgment into small isolated questions and you get a probability per question instead of one number over a paragraph. A probability per question is something you can check.

## What This Means for You

**When this matters.** Any time code branches on a model's own confidence: routing, auto-approval, escalation, moderation, "only act when sure." If a number from a model decides what your system does next, this applies today.

**How it affects you.** Your threshold is probably not doing what you think. The common failure is not that the model is bad — accuracy may be fine — but that the score you filter on is compressed near 1, so the filter passes almost everything including the mistakes. You will not see this in an accuracy metric, because accuracy is unchanged by the distortion.

**What to do about it.** Start here, and it needs no new infrastructure and no retraining: take the last few thousand logged decisions where you know the outcome, bucket them by the confidence they carried, and print claimed accuracy against actual accuracy per bucket. Seven rows of output. If the two columns track each other, you are fine and you have spent ten minutes. If the claimed column sits well above the actual one, every threshold downstream is mis-set.

Then fit one temperature value on held-out cases and re-run the same table. That is the whole repair.

Be ready for the answer to be unwelcome. A calibrated model usually turns out to be sure about far less than the old number implied, and the work that follows is deciding what to do with the cases that no longer clear the bar — not celebrating a better score.

## Implementing It

**The change.** Three roles touch this, and only the first is the one people think of.

**Role 1 — whoever defines the decision.** Stop asking for a paragraph and parsing it. Ask typed questions, decomposed, so each one carries its own probability.

```python
# before — one prompt, one blob, one number you cannot check
resp = llm(f"Review this alert and reply JSON: {state}")
verdict = json.loads(resp)["action"]        # and a parse error is a 3am page

# after — small isolated questions, each with its own distribution
questions = [
    {"type": "choice", "id": "action", "options": ["close", "escalate", "contain"]},
    {"type": "noul",   "id": "customer_data_touched"},
    {"type": "score",  "id": "blast_radius", "rubric": "0 one host, 10 whole fleet"},
]
```

Each question is scored against the same state and in isolation, so the tenth one does not crowd the first. That property is what makes the per-question probabilities comparable.

**Role 2 — whoever owns reliability.** This is the role that gets skipped, and it decides whether any of the rest is real. The check — reliability buckets — runs on your own logs and needs no vendor.

```python
def reliability_buckets(confidences, correct, n=10):
    rows = []
    for i in range(n):
        lo, hi = i / n, (i + 1) / n
        hits = [(c, k) for c, k in zip(confidences, correct) if lo < c <= hi]
        if hits:                      # claimed vs actual, side by side
            rows.append((len(hits),
                         sum(c for c, _ in hits) / len(hits),
                         sum(1 for _, k in hits if k) / len(hits)))
    return rows
```

Weight the summary by bucket size when you collapse it to one number. A wild bucket holding four cases must not outvote a tight one holding four thousand. The full version, with the temperature fit, is in `code_example.py`.

**Role 3 — whoever wires the branch.** A calibrated score gives you three lanes, not two, and the middle one is the point.

```python
p = result["confidence"]
if p >= AUTO:          act(result["choice"])        # you accept 1-in-N wrong here
elif p >= REVIEW:      queue_for_human(result)      # the band you could not see before
else:                  escalate_to_larger_model(state)
```

Set `AUTO` from the error rate you can actually absorb, not from a round number. If you can live with one bad auto-approval in fifty, `AUTO` is 0.98 — and only once the buckets say 0.98 means 0.98.

**How you know it worked.** Two signals, both numbers you can watch.

First, the claimed and actual columns converge. In the Code tab's run, weighted calibration error falls from 0.342 to 0.046 while accuracy stays at 44.3%. If accuracy moved, you changed the decision and not just the reporting, and something is wrong with the fit.

Second, and this is the one that proves it in production: count the cases above your threshold and measure how many were wrong. At `AUTO = 0.9` that figure should sit near 10%. Before calibration it was 38.1%. If it still exceeds your threshold's promise, the fit did not take — usually because it was fitted on the same cases it is being scored on.

## When a Confidence Score Is the Wrong Tool

Calibration tells you how often the model is right. It never tells you why, and it cannot rescue a decision the model had no basis to make.

If the state you hand over does not contain the answer, a calibrated model gives you an honest low number and nothing else. That is more useful than a confident guess, but it is not a solution, and no amount of scaling turns missing evidence into a decision. Jev in particular knows only what you pass it and cannot look anything up. It is also the wrong tool whenever the output needs to be written rather than chosen — chat, code, or an explanation of its own reasoning.

Be skeptical of the comparison figures too, including the ones quoted above. The benchmarks are vendor-run, TypeSafe's own team wrote the workflows, and the reference answers are an average of two other models' outputs rather than human labels. So the reported accuracy measures agreement with an expensive model, not correctness. The company also says plainly it cannot prove the pricing is unsubsidized.

Three questions before you adopt any of this:

Do I have logged outcomes to calibrate against, or am I about to fit on guesses?

Is my decision one of a fixed set of answers, or does it need prose?

If the honest number turns out to be low, do I have somewhere to send those cases?

## Glossary

- **Calibration** — the property that claimed confidence matches observed accuracy, measured over many cases.
- **Confidence** — the probability a model assigns to the answer it picked. Meaningful only once calibrated.
- **Temperature scaling** — dividing scores by one fitted value to fix confidence without changing the answer.
- **Softmax** — turns raw model scores into probabilities that sum to one.
- **Reliability buckets** — predictions grouped by claimed confidence, so each group's claim can be checked.
- **Noul** — TypeSafe's primitive for "is this statement true", returned as a value from 0 to 1.
