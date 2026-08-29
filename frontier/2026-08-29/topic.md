# How a Model Trains Itself Without Knowing the Right Answer

**Category**: Applied Research
**Tags**: training, distillation, paper, benchmarks
**Date**: 2026-08-29
**Level**: Deeper
**For**: How models work
**Hook**: On hard problems a model's own majority vote is wrong about 85% of the time — and it turns out you can still train on it, as long as you use the disagreement rather than the agreement.
**Time to read**: ~8 minutes

## Explain Like I'm 5

A class sits a hard test with no answer key. The teacher decides to grade by popular vote: whatever most of the class wrote becomes the official answer. On the hardest questions the crowd is usually wrong, so that official answer is bad. But something else is reliable — the handful of students who wrote something different from the crowd are almost always wrong too, each in their own separate way. So even a bad answer key still tells you something true: not "the crowd is right", but "the loners are wrong".

## The Problem

The methods that made models good at reasoning all need an answer key. Reinforcement learning needs a reward, self-distillation needs a teacher signal, and both bottom out in somebody knowing which answer was correct.

That rules them out at test time, which is exactly where you would most like to use them — on the new, hard distribution the model is failing on right now.

The obvious substitute is to let the model vote. Sample the same question a dozen times, take the most common answer, treat it as truth. It fails badly: an incorrect vote corrupts the teacher and then misleads the update on every single token. And votes are not occasionally wrong. On hard prompts roughly **85% of them are wrong**, so the naive version poisons training hardest precisely where the model needs help most.

Which looks like a dead end, until you notice the failure is lopsided.

## How TTPO Splits Agreement From Disagreement

### The Asymmetry

The measurement the whole method rests on: on hard prompts, about **85% of majority-vote pseudo-labels are incorrect** — and about **79% of the rollouts that disagree with those wrong pseudo-labels are also wrong**.

The vote being wrong does not promote the dissenters to being right. A correct answer is one specific string; wrong answers scatter across many, so the majority cluster can be a wrong answer that merely attracted the most mass.

Agreement is a weak signal. Disagreement is a strong one.

### Majority Voting as a Router

TTPO — Test-Time Policy Optimization — samples K trajectories per prompt, clusters equivalent answers, takes the largest cluster as the pseudo-label, and uses it to *route* rather than to *supervise*.

### The Two Branches

**Agreeing rollouts** get on-policy self-distillation (OPSD) — a forward-KL pull toward the model's own agreeing trajectories. Gentle on purpose: with the label often wrong, a hard supervised push toward it is the thing to avoid.

**Disagreeing rollouts** get a grouped RL penalty (the GRPO family, scoring each rollout against its group rather than an absolute reward). Penalising a rollout that is ~79% likely to be wrong stays well-grounded even when the label that flagged it was wrong.

### Token-Level Selection

Both branches then narrow from trajectories to single tokens, so a noisy signal cannot smear across a sequence. Distillation **down-weights already-converged positions**. The penalty **masks to confident errors only** — a disagreeing rollout is punished where it was sure of itself, and its correct reasoning is left alone.

## For a Software Engineer

You have shipped this exact trust structure before: a Bloom filter. It is never wrong when it says *not in the set*, and it is only maybe-right when it says *in the set*. You do not therefore throw it away — you build the system so the trustworthy direction carries the load, and the untrustworthy one gets a real check behind it.

TTPO is that, applied to a model's own vote. Disagreement is the "definitely not" direction and gets a firm penalty. Agreement is the "maybe" direction and gets a soft distillation nudge instead of hard supervision.

The number to feel is the 85%. If someone proposed a labelling pipeline whose labels were wrong 85% of the time, you would reject it without discussion — and you would be right, for supervision. The insight is that the *same* labels are still good enough to sort rollouts into two bins, and one of those bins is 79% pure. Cheap, wrong labels can be excellent routers.

## What This Means for You

**When this matters.** You have an unlabelled set of hard inputs, you can sample your model several times per input, and answers can be compared for equivalence — maths, structured extraction, code that either passes tests or does not.

**How it affects you.** Not this week, honestly: TTPO is a training procedure that wants GPUs, and the reported results are 1.7B–8B models on maths competitions. What transfers immediately is the routing idea, which needs no training at all. If you are sampling n times and taking a majority vote today, you are throwing away the more reliable half of that signal.

**What to do about it.** Stop discarding the minority rollouts. Log them: any input where a rollout disagrees with the majority is a high-precision candidate for a hard case, and roughly four in five of those disagreeing samples are genuinely wrong. Use that to mine an eval set or filter synthetic training data — the vote tells you where to look even when it cannot tell you the answer.

## Implementing It

**The change**

The routing is the part worth lifting, and it is small. Three pieces move.

**1. The voter.** Cluster on a canonical form, never on the raw string — `0.5`, `1/2` and `\frac{1}{2}` are one answer, and treating them as three silently inflates disagreement:

```python
def majority_vote(rollouts, canon):
    clusters = {}
    for r in rollouts:
        clusters.setdefault(canon(r.answer), []).append(r)
    winner = max(clusters.values(), key=len)
    return canon(winner[0].answer), winner
```

**2. The router.** The pseudo-label picks the branch; it is never used as a target:

```python
label, agreeing = majority_vote(rollouts, canon)
disagreeing = [r for r in rollouts if canon(r.answer) != label]

for r in agreeing:     loss += W_DISTILL * opsd_loss(r)      # soft, forward-KL
for r in disagreeing:  loss += W_PENALTY * grouped_rl_loss(r)  # firm penalty
```

If you write `loss += supervised_ce(r, label)` anywhere, you have rebuilt the naive version that the 85% figure kills.

**3. The token masks.** Each branch is narrowed before it is applied:

```python
# distillation: skip positions the policy has already converged on
w = (token_entropy > CONVERGED_EPS).float()

# penalty: only punish tokens the rollout was confident about
m = (token_logprob > CONFIDENT_LOGPROB).float()
```

Drop the masks and both branches spray gradient across whole sequences, which is how a wrong pseudo-label does its damage in the naive setup.

**How you know it worked**

- **Measure the asymmetry on your own data first**, before training anything. Sample K per prompt, take the vote, and — on a small labelled slice — print two numbers: what fraction of votes are wrong, and what fraction of disagreeing rollouts are wrong. If the second is not far higher than chance, the mechanism has no fuel on your task and you should stop here.
- **Watch the two branch losses separately.** They must not converge to the same value. If the penalty branch goes quiet, disagreement has vanished and you are distilling into a mirror.
- **Track vote entropy per prompt as training runs.** Self-supervision is supposed to tighten as the model improves, so the clusters should concentrate. Flat entropy with falling loss means the model is agreeing with itself more confidently without getting better.

## When TTPO Is the Wrong Tool

It needs K samples of every prompt, so inference cost multiplies before any training happens. And on open-ended generation, where two good answers are simply different text, the clustering step has nothing to bite on — which rules out most chat and writing workloads.

The sharper limit is systematic bias. The method assumes wrong answers scatter while right ones concentrate. If your model is confidently wrong the *same* way every time — a shared misconception, a bad pretraining prior — the majority cluster is that error, the dissenters are the ones getting it right, and TTPO penalises precisely them. Nothing inside the method can detect this, because it has no labels.

Three questions before adopting it:

1. Can you canonicalise answers well enough that equivalent ones cluster? If not, nothing downstream works.
2. On a labelled slice, are disagreeing rollouts much likelier to be wrong than chance? That ratio is the whole engine.
3. Can you afford K rollouts per prompt at test time, on top of the training?
