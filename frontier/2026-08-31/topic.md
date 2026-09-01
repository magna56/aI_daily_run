# How to Tell If Your Model's Confidence Score Means Anything

**Category**: Applied Research
**Tags**: reliability, benchmarks, paper, production
**Date**: 2026-08-31
**Level**: Deeper
**For**: Shipping AI
**Hook**: Asking a model how sure it is returns a number. Whether that number tracks anything inside the model is a separate question, and usually the answer is no.
**Time to read**: ~11 minutes

## Explain Like I'm 5

Ask someone how sure they are and they will give you a number. That number is a thing they said,
not a reading taken off a dial inside their head.

Most people say "ninety percent" about almost everything. It is a habit of speech. If everyone
answers ninety to every question, the number still sounds informative, but it can no longer tell
you which answers were the shaky ones — and telling those apart was the only reason you asked.

## The Problem

A very common pattern in production looks like this: ask the model for an answer and a confidence
score, then route anything under a threshold to a human, a bigger model, or a retry. It is cheap,
it needs no special API access, and it feels principled.

The question nobody checks is whether that spoken number has any relationship to the model's own
internal uncertainty. Researchers at Dartmouth and Oakland measured exactly that across 30 models
from the Llama, Mistral and Qwen families, on eight classification tasks and two generation tasks.

Averaged across settings, the two agree reasonably well: Pearson **r = 0.483**. That is the number
that would end up in a slide, and it is reassuring.

At the level of individual answers — which is the only level a threshold operates at — the average
correlation is **r = 0.135**. And when the models are split by type, base models manage r = 0.261
while **instruction-tuned models come in at r = −0.0048, with p = 0.961**: statistically
indistinguishable from no relationship at all.

Instruction-tuned models are the ones nearly everyone ships.

## How a Model Reports Confidence

There are two separate channels here and the article turns on not confusing them.

**Internal confidence** is a quantity the machinery already computes. For a classification-shaped
answer it is the softmax probability over the answer tokens. For free generation it is fuzzier,
and the paper uses semantic entropy — sample several answers, group the ones that mean the same
thing, and measure how spread out the meanings are. It requires access to logits or to repeated
sampling.

**Linguistic confidence** is text. You asked the model to say how sure it was, and it produced a
number the way it produces any other token. Nothing in the architecture connects that number to
the softmax distribution over the answer. Whether they agree is an empirical question, not a
guarantee, and that is the whole finding.

### Three axes that are not interchangeable

The paper's most useful contribution is refusing to collapse "is this confidence any good?" into
one number. It measures three things separately.

**Association** asks whether the two move together across instances — does the model say a lower
number on the questions where its internal probability is lower? **Magnitude agreement** asks
whether the two are numerically close. **Calibration** asks whether a reported 80% is right about
80% of the time.

These come apart in practice. A model can have strong association and still be systematically
overconfident. It can sit close on average while carrying no instance-level information at all.
Passing one axis tells you nothing about the other two.

### Why instruction tuning makes it worse

The mechanism is distributional, and it is the part worth internalising.

Instruction tuning pushes models toward confident, agreeable phrasing. Their reported confidence
collapses into a narrow band near the top — lots of 90s, a few 85s. Their internal probabilities
compress toward 1 as well. When almost every instance gets almost the same number, there is
nothing left to correlate, because correlation is a statement about variation and the variation
is gone.

The paper's phrase for this is a **lossy channel**: linguistic confidence carries some of the
internal signal, and how much survives depends mostly on how spread out the reported numbers are.
Prompting changes the spread but not the grounding. Attitude cues — telling the model to be
careful, or confident — move the numbers without improving alignment.

## For a Software Engineer

This is an unvalidated telemetry source, and you have shipped one of those.

It is the same shape as a health-check endpoint that returns 200 because the handler is reachable,
not because the dependency behind it is alive. The signal is present, well-formed, cheap to read,
and load-bearing in your routing logic — and nobody ever confirmed it moves when the thing it
supposedly measures moves.

The number to hold onto: **r = 0.135 at the instance level, and r ≈ 0 for instruction-tuned
models.** If you have a threshold branch keyed on `confidence`, that branch is close to a coin
flip weighted by phrasing habits. New to this? Start at AI basics →
[How Model Calibration Works](#learn/calibration).

## What This Means for You

**When this matters.** You have a prompt that asks for a confidence score, and code somewhere that
branches on it — escalate below 0.7, auto-approve above 0.9, retry in between. That covers most
LLM-in-the-loop pipelines that were not built by someone with logits access.

**How it affects you.** Your gate is probably sorting on something close to noise, and it fails
silently: the pipeline still runs, the numbers still look sensible in a dashboard, and the
escalations you receive are not the cases that needed escalating. Worse, the aggregate statistic
you would naturally compute to check it (r = 0.48) looks fine, because averaging across tasks and
models hides the instance-level collapse.

**What to do about it.** Before touching the threshold, look at the *spread* of the confidence
scores you are already logging. If 90% of them fall in a band of ten points, stop — a collapsed
distribution cannot rank anything, and no threshold you pick will help. That is a five-minute
query against data you already have. Then, if you have logprob access, run the three-axis
diagnostic below; if you do not, use sampling agreement as the internal channel instead.

## Implementing It

**The change.**

*Whoever logs the model's output.* Record the reported confidence and an internal signal side by
side, per instance. Without both channels there is nothing to compare, and this is the step most
pipelines skip:

```python
resp = client.messages.create(..., top_logprobs=5)   # or n=8 samples if unavailable
row = {
    "id": item_id,
    "verbal": parse_confidence(resp.text),        # what the model said, 0..1
    "internal": answer_token_prob(resp),          # softmax over the answer tokens
    "correct": grade(resp.text, gold),            # needed for the calibration axis
}
```

*Whoever owns the gate.* Run the three axes separately and never average them into one score. They
answer different questions and the paper's whole point is that they diverge:

```python
from scipy.stats import pearsonr, spearmanr

assoc_r, _  = pearsonr(verbal, internal)     # do they move together?
assoc_rho,_ = spearmanr(verbal, internal)    # rank-only version, robust to scale
magnitude   = mean(abs(v - i) for v, i in zip(verbal, internal))
ece         = expected_calibration_error(verbal, correct, bins=10)
```

Read them as a set. High association with a large magnitude gap means the ranking is usable but
the numbers are not probabilities — use it to sort, never to threshold. Small magnitude gap with
near-zero association means the scores happen to sit near the right average while telling you
nothing about any individual case, which is the instruction-tuned failure and the dangerous one.

*Whoever writes the prompt.* Before any of that, check dispersion — it is the dominant driver and
the cheapest thing to measure:

```python
spread = statistics.pstdev(verbal)
distinct = len(set(round(v, 2) for v in verbal))
# spread < 0.05 or distinct < 5 -> the channel is collapsed; association is not recoverable
```

If it is collapsed, changing the threshold is wasted work. Widen the reported range first, by
supplying score exemplars that span the scale rather than telling the model to be careful. The
paper is explicit that attitude cues move the mean without improving grounding — a more confident
model is not a better-informed one.

*Whoever has no logprob access at all.* Use consistency as the internal channel: sample the same
prompt several times at temperature and measure how often the answers agree, clustering by meaning
rather than string equality. It costs N times more per item, so run it on a sample of a few
hundred, not in the live path.

**How you know it worked.** Plot verbal against internal for a few hundred logged instances. A
useful signal is a visible upward cloud; a collapsed channel is a horizontal stripe near the top,
and you will recognise it immediately. Then compare escalation sets: take the bottom decile by
verbal confidence and the bottom decile by internal confidence and measure the overlap. If it is
near 10%, your gate is selecting a random tenth of traffic. Track that overlap as the number that
has to move before you trust the threshold again.

## When a Confidence Score Is the Wrong Tool

If you already have logprobs in the response, skip the verbal channel entirely. It is a lossy copy
of something you can read directly, and the whole problem disappears.

Verbal confidence is also fine where you only need ordering and never a probability — surfacing
the ten least-certain items for review each morning works on rank alone, and the paper's finding
is that rank information is the part most likely to survive. It stops being fine the moment a
number crosses a threshold and something automatic happens.

Read the evidence for its shape, too: these are open-weight models from three families, and the
internal channel is a softmax probability the authors are explicit is itself imperfect. They are
not claiming logits are truth. They are claiming the two channels disagree, which is a weaker and
more useful claim.

Three questions before you keep the gate. Do I know the spread of confidence values in my logs, or
am I assuming? Could I read the internal signal directly instead? And if I replaced the gate with
a coin weighted to fire at the same rate, would any dashboard I own look different?
