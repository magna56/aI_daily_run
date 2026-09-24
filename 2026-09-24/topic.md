# How Much of Your Work a 15B Model Can Actually Close

**Category**: Applied Research
**Tags**: benchmarks, paper, multimodal
**Date**: 2026-09-24
**Level**: Deeper
**For**: How models work
**Hook**: Microsoft's small vision-reasoning model decides for itself whether to think before answering, and that decision was trained into the data mix rather than coded around the model.
**Engineer's view**: This is the fast path and slow path you run. A cache hit returns in milliseconds, a miss does the full query, and the hard part was never the two paths — it was the predicate that picks between them. Here the predicate is trained into the model rather than written in front of it.
**TLDR**: A small model can be taught when to reason by putting mode tokens in its training mix, instead of wrapping a router around it. The averaged benchmark score hides a subset where more thinking buys nothing at all.
**Time to read**: ~12 minutes

## Explain Like I'm 5

A good mechanic listens to your car for a few seconds and tells you what is wrong.

For most problems that is the whole job. Occasionally they stop, go quiet, and get the manual out.

What makes them good is not the manual. Everyone has the manual. It is knowing, in the first few seconds, which kind of problem this is — and not wasting an hour on the ones they could have answered straight away.

## The Problem

You have shipped this before, and it had nothing to do with AI.

You built a service with a fast path and a slow path. A cache hit answered in milliseconds; a miss ran the real query. Both paths were easy. The part that took the week was the predicate in front of them — the thing deciding which request got which.

Get that wrong in one direction and you serve stale answers. Get it wrong in the other and the cache buys nothing.

Reasoning models handed everybody that same problem, and most teams took the worse of the two options.

You can turn thinking on for every request and pay for it on the ones that never needed it. Or you can write a router: a classifier, a heuristic, a cheap model in front of the expensive one. Now you maintain a second system, and its mistakes stay invisible until the bill arrives.

Microsoft Research's **Phi-4-reasoning-vision-15B** takes a third route, and it is the reason the report is worth reading. The switch is not in front of the model. It is inside it, put there by the training data. The mix pairs reasoning and non-reasoning examples with **explicit mode tokens**, so one model emits fast direct answers on simple work and chain-of-thought on hard work.

So the fix: stop building the predicate and start labelling the mix. Tag examples with the mode they deserve and keep the split weighted toward direct answers. Let the model learn the boundary, then measure what it closes on the hard subset separately.

```figure
{ "kind": "system",
  "title": "The whole argument: where the switch lives",
  "lanes": [
    { "t": "you can put the switch", "nodes": [
        { "id": "front", "t": "in a router in front", "s": "bad" },
        { "id": "inside", "t": "in the training mix", "s": "ok" } ] },
    { "t": "which costs you", "nodes": [
        { "id": "second", "t": "a second system to maintain", "s": "bad" },
        { "id": "label", "t": "labelling the data once", "s": "ok" } ] },
    { "t": "and neither fixes", "nodes": [
        { "id": "ceiling", "t": "the work past the model's ceiling", "s": "bad" } ] }
  ],
  "edges": [
    { "from": "front", "to": "second", "s": "bad" },
    { "from": "inside", "to": "label", "t": "mode tokens", "s": "ok" },
    { "from": "second", "to": "ceiling", "s": "bad" },
    { "from": "label", "to": "ceiling", "s": "bad" } ],
  "note": "The switch is a real saving. The ceiling is the thing an averaged score hides." }
```

## The Fix: Put the Mode Token in the Training Mix

A mode token is not a clever abstraction. It is a literal token in the sequence, so the model emits it and then conditions on what it just emitted.

### Why not put a router in front instead?

Because a router is a second model with its own training set, its own drift and its own failures, and it decides before it has seen the work. By the time the decision is due, the model has already read the image and the question. That is strictly more information than any predicate in front of it had.

There is a maintenance argument too. A router that is wrong costs you either accuracy or money, and neither shows up as an error. It shows up as a number that is slightly worse than it should be, forever.

### What does the resolution ablation actually show?

That perception is upstream of reasoning, which the report states plainly: accurate perception is a prerequisite for high-quality reasoning. Their ablation on a smaller 5B variant compares resolution strategies. Dynamic resolution at 2,048 max tokens scores **45.2** on MathVista and **81.5** on ScreenSpot. A multi-crop approach given *more* tokens, at 3,096, scores 43.4 and 67.8.

More visual tokens did not win. Better-shaped visual tokens did. That is the same lesson as the data-quality finding one paragraph up, and the report says it outright: data quality remains the primary lever for model performance.

### Where does a 15B model stop?

On the hard subset, and the same ablation table shows it. Against MathVista scores in the forties and ScreenSpot in the seventies and eighties, the ScreenSpot-Pro column reads **9.4, 5.4, 10.6, 9.2**.

Single digits. That benchmark is professional, high-resolution interface grounding, and no resolution strategy in the table moves it meaningfully. The positioning claim in the report is carefully worded and worth repeating exactly: competitive with much slower models that need more time and tokens, and more accurate than similarly fast ones. It is a claim about a frontier, not about beating larger models.

## What This Means for You

**When this matters.** Any time you are choosing between a small model plus structure and a frontier model, and any time somebody quotes you an averaged benchmark score for a model you might deploy.

**How it affects you.** The headline number for a small model is an average over two populations you should be treating separately: work it closes comfortably, and work it cannot close at any thinking budget. If those are pooled, the average tells you almost nothing about whether the model fits *your* traffic, because your traffic is not distributed like the benchmark's.

**What to do about it.** Start here, and it needs no training run: take a sample of your own tasks, score them by how hard they are for a model rather than for a human, and check what fraction falls in the hardest decile. That fraction is the part a small model will not close, and it decides the question. Most teams have never split their traffic this way and are arguing about averages.

Then, if you are fine-tuning anything, label the mix by mode rather than building a classifier. Assign the reasoning label by difficulty, keep it a minority, and you have bought the routing decision for the price of a data-labelling pass.

## Implementing It

**The change.** Three roles, and the first is the one the paper is actually about.

**Role 1 — whoever builds the training mix.** The mode token is the mechanism, and *how you assign it* is the whole lesson.

```python
def build_mix(tasks, think_share=0.20):
    # Assign by DIFFICULTY, never at random. A mix that labels random examples
    # THINK teaches the model that the token means nothing, which is worse than
    # having no token at all.
    ordered = sorted(tasks, key=lambda t: -t.difficulty)
    cut = int(len(ordered) * think_share)
    return [
        {"prompt": t.prompt,
         "mode": "<think>" if i < cut else "<nothink>",
         "target": t.reasoning_trace if i < cut else t.direct_answer}
        for i, t in enumerate(ordered)
    ]
```

Keep the reasoning share a minority. The report's mix is weighted heavily toward direct answers. That ratio is what makes the fast path the default rather than the exception, and it is the cheapest dial you have: raising it costs tokens on every request that never needed them.

**Role 2 — whoever runs the evaluation.** Report the hard subset on its own line. This is the role that prevents a bad deployment decision.

```python
overall = solved / len(tasks)
hard    = solved_hard / len(hard_tasks)      # the decile nothing rescues
print(f"overall {overall:.1%}  |  hard subset {hard:.1%}  |  n_hard={len(hard_tasks)}")
```

An averaged figure across four benchmarks is what the report itself uses for its efficiency comparison, and it is fine for that purpose. It is not fine for deciding whether a model covers your workload.

**Role 3 — whoever picks the model.** Compare on accuracy per token, not accuracy, because that is the axis the whole design is arguing about.

```python
for policy in ("always_direct", "always_reason", "hybrid"):
    acc, tokens = evaluate(tasks, policy)
    print(f"{policy:<15} {acc:.1%}  {tokens:>5.0f} tok  {acc / (tokens / 1000):.2f} acc/Ktok")
```

**How you know it worked.** Two numbers, and the second is the one that stops a bad decision.

First, the hybrid should hold nearly all of the always-reason accuracy at a fraction of the tokens. In the Code tab it keeps **96.3%** of it for **25%** of the tokens. If your hybrid is much below that, your difficulty labels do not match what the model actually finds hard, and the threshold has landed in the wrong place.

Second, the hard-subset score should be flat across policies. In the simulation, tasks past the ceiling score **0.0%** whether the model thinks or not. If yours improves as you spend more, those tasks were not past the ceiling. They were merely hard, and that is a budget problem rather than a capability one. Those are different problems with different fixes, and the averaged number cannot tell them apart.

## When a Small Reasoning Model Is the Wrong Tool

When the hard decile is your product. If the work you actually care about lives where ScreenSpot-Pro lives, a 15B model returns single digits and a better prompt does not change that. Buying a frontier model is the honest answer, and the efficiency argument is irrelevant because the cheap option does not do the job.

Be careful with the report's numbers too. The resolution ablation runs on a smaller 5B variant built for testing, so those rows are evidence about the design choice rather than about the shipped model. And the efficiency comparison averages four benchmarks, which is exactly the aggregation the section above warns you not to deploy on.

There is also a training-data cost that the framing hides. Assigning modes by difficulty means you need difficulty labels, and producing those for your own domain is the expensive part. The report's own conclusion points the same way: the biggest gains came from filtering, error correction and synthetic augmentation, not from architecture.

Three questions before choosing a small model:

What share of my traffic sits in the hardest decile, measured rather than guessed?

Can I produce difficulty labels for my domain, or am I about to assign modes at random?

If the hard subset never improves, is the feature still worth shipping?

## Glossary

- **Mode token** — a literal token in the training sequence marking an example as reasoning or direct.
- **chain-of-thought** — the model writing out intermediate steps before answering, which is what the reasoning mode emits.
- **Dynamic resolution** — varying how many visual tokens an image gets instead of fixing the count.
- **Hard subset** — the tasks past a model's ceiling, where extra thinking changes nothing.
- **ScreenSpot-Pro** — a professional high-resolution interface grounding benchmark, where 15B models score in single digits.
- **Accuracy per token** — the axis this design argues on, rather than accuracy alone.
