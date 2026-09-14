# How to Fine-Tune a Model When Some of Your Preference Labels Are Wrong

**Category**: AI Safety & Alignment
**Tags**: fine-tuning, training, paper
**Date**: 2026-09-14
**Level**: Deeper
**For**: How models work
**Hook**: Some of the thumbs-up labels you train on are backwards, and standard preference training believes every one of them.
**Engineer's view**: This is a bad row in a batch job. You once merged a review queue where some clicks were wrong, and those rows were not skipped — they merged backwards. Preference training does the same. A reversed label trains your model at full strength in the wrong direction, and the damage lands in its answers.
**TLDR**: A wrong preference label does not waste a training step. It spends that step teaching the model the opposite of what you wanted.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine a student learning to draw. Every day a judge shows them two pictures and says which one is better. Most days the judge is right. But some days the judge is tired and points at the worse picture. And sometimes the two pictures are equally good, yet the judge still has to choose one.

If the student believes every answer completely, the tired days teach bad habits. A better student notices when one answer disagrees with everything else they have learned. They still listen. They just do not let that one answer count for full marks.

## The Problem

You have shipped this bug before, and it had nothing to do with machine learning. You built a review queue. Two records appear side by side, a person clicks which one is the duplicate, and a nightly job merges the pair.

It worked for months. Then someone clicked too fast.

The job did not skip that pair. It did not flag it either. It merged the good record into the stale one and moved on. One wrong click cost you more than ten missing clicks would have. A missing click leaves a row alone. A wrong click acts, at full confidence, in the wrong direction.

Preference training is that nightly job at a much larger scale. You collect pairs: one prompt, two answers, and a label saying which answer people preferred. The labels come from thumbs-up clicks, rushed annotators, or one model grading another. Some of them are backwards. Others are not preferences at all — the two answers were equally good, and the annotator had to pick something anyway.

Standard training treats every pair the same way. In the toy run below, 110 backwards labels out of 600 drag ranking accuracy from 93.0% down to 76.3%.

The fix: stop trusting the label on its own, and let the model's own confidence route each pair three ways — keep it, reverse it, or cancel it.

```figure
{ "kind": "system",
  "title": "The whole argument: one labeled pair, two ways to train on it",
  "lanes": [
    { "t": "what you collected", "nodes": [
        { "id": "pair", "t": "a prompt, two answers, one label" } ] },
    { "t": "what training does", "nodes": [
        { "id": "trust", "t": "trust the label, full strength", "s": "bad" },
        { "id": "route", "t": "weigh three readings of it", "s": "new" } ] },
    { "t": "with 110 of 600 backwards", "nodes": [
        { "id": "low", "t": "76.3% ranking accuracy", "s": "bad" },
        { "id": "high", "t": "78.3%", "s": "new" } ] }
  ],
  "edges": [
    { "from": "pair",  "to": "trust", "s": "bad" },
    { "from": "pair",  "to": "route", "t": "same data", "s": "new" },
    { "from": "trust", "to": "low",   "s": "bad" },
    { "from": "route", "to": "high",  "s": "new" } ],
  "note": "Clean labels score 93.0%. Correction recovers part of the damage; it does not undo it." }
```

## The Fix: Route Each Pair Three Ways

Every preference pair already produces one number during training, and almost nobody looks at it. It is called the margin. It measures how much more the model now prefers the winner over the loser, compared to the reference model it started from.

Read it as evidence and it says something useful. A large positive margin means the model agrees with this label. A margin near zero means the model has no opinion about this pair. A negative margin means the model has learned the opposite of what the label claims.

That number is already computed. It costs nothing to use.

### Why not just drop the suspicious pairs?

Filtering throws away the part you can still use. A backwards label is not noise. It is a real comparison with its sign inverted, so reversing it recovers a usable training example instead of deleting one. Ties are worse to filter. A tie carries genuine information: these two answers should score about the same, and training the model to say so is a real update.

Routing keeps all three readings. Each pair gets three weights that add up to one, and the loss becomes a blend of three losses — keep the label, reverse it, or push the margin toward zero.

```figure
{ "kind": "route",
  "title": "Where one pair's margin sends its training signal",
  "source": "one pair's margin, after warm-up",
  "parts": [
    { "t": "far above the other pairs", "to": 0, "via": "model agrees", "s": "ok" },
    { "t": "far below the other pairs", "to": 1, "via": "model disagrees", "s": "new" },
    { "t": "sitting near the middle",   "to": 2, "via": "no opinion", "s": "neutral" }
  ],
  "dests": [
    { "t": "keep the label", "s": "ok" },
    { "t": "reverse it", "s": "new" },
    { "t": "cancel the direction", "s": "neutral" }
  ],
  "note": "The three weights are soft and sum to one. No pair is ever hard-labeled as bad." }
```

### Isn't this the model grading its own homework?

Partly, and the method is built around that risk. Three guards hold it back.

**Warm-up.** For the first quarter of training the correction is switched off entirely. Routing an untrained model would just lock in whatever the first few batches happened to suggest.

**Calibration.** The margin is standardized against a running mean and variance of every margin seen so far. This matters more than it sounds. In the run below, correctly labeled pairs end training with an average margin of +1.95, and backwards ones average +0.30. Both are positive. The evidence is relative, not absolute, and only centering turns that gap into a signal.

**Confidence gating.** When the three weights are close to even, the router has learned nothing about this pair, so its vote is scaled down toward plain training.

## What This Means for You

**When this matters.** You are fine-tuning on preference data that you did not curate by hand. Thumbs-up and thumbs-down from your own app, rankings from a judge model, a crowd-labeled set bought in bulk. The more automated your labeling, the more of this you are carrying.

**How it affects you.** Wrong labels do not average out. A missing label costs you one training example. A reversed label costs you two: the update you did not get, and the update you got in reverse. Ties are the quieter problem, because nothing marks them. Every forced choice between two equally good answers becomes a confident preference the model is asked to learn.

**What to do about it.** Start by counting your ties, which takes one query and needs nothing else in place. Open your feedback table and count the pairs where both answers scored the same, or where two annotators disagreed. Those pairs are being trained as preferences today. On the paper's own datasets, this group is large enough to move results across 57 dataset-model-benchmark cells.

Then, if that count is meaningful, add the routing loss to your training step. That is the next section. If you cannot change the loss, the cheaper version is to record ties as ties at collection time and drop them, which fixes one of the two problems and costs you nothing at training time.

## Implementing It

Three roles touch this change: whoever collects the labels, whoever writes the training loop, and whoever decides it worked. The paper is written for the second one. The first is where the cheapest win is.

**The change, for whoever collects labels.** Stop forcing a binary choice. A tie is a real answer, and a schema that cannot express one manufactures noise at the source.

```python
# before: the annotator must pick a side
{"prompt": p, "chosen": a, "rejected": b}

# after: a tie is representable, and disagreement is preserved
{"prompt": p, "response_a": a, "response_b": b,
 "verdict": "a" | "b" | "tie",      # "tie" is a valid, useful label
 "n_annotators": 3, "agreement": 0.67}
```

**The change, for the training loop.** Compute the margin as DPO already does, detach it, standardize it, and turn it into three weights. The full router, with the warm-up and confidence gate, is in `code_example.py`; these are the lines that carry the idea.

```python
z = (margin.detach() - running_mean) / running_std.clamp(min=1e-2)
logits = torch.stack([
    math.log(0.80) + z / tau_dir,      # clean: model agrees with the label
    math.log(0.10) - z / tau_dir,      # flip:  model has learned the opposite
    math.log(0.10) - z.abs() / tau_tie  # tie:   no directional evidence
], dim=-1)
q = logits.softmax(dim=-1)

loss_plc = (q[..., 0] * -F.logsigmoid(margin)        # keep the label
            + q[..., 1] * -F.logsigmoid(-margin)     # reverse it
            + q[..., 2] * F.softplus(margin.abs()))  # cancel the direction
```

Blend it with plain DPO rather than replacing it. `gamma` is zero for the warm-up fraction, and confidence scales the rest down when the router is unsure:

```python
w = gamma * ((q.max(dim=-1).values - 1/3) / (2/3)) ** kappa
loss = (1 - w) * loss_dpo + w * loss_plc
```

On TRL, this is one method. Subclass the trainer rather than forking it, so the reference-model plumbing and logging stay where they are:

```python
# trl==0.9.6
class RoutedDPOTrainer(DPOTrainer):
    def dpo_loss(self, pol_chosen, pol_rejected, ref_chosen, ref_rejected):
        margin = self.beta * ((pol_chosen - ref_chosen) - (pol_rejected - ref_rejected))
        return routed_loss(margin), pol_chosen.detach(), pol_rejected.detach()
```

**How you know it worked.** Run the control before you trust anything. Train once on your real data and once on data you know is clean, and log the mean flip weight for both. In the run below those come out at 20% and 21% — nearly identical. That is the result worth internalizing: the flip weight is a training signal, not a measurement of how much of your data is wrong. The paper says the same thing, that the routing weights are not a ground-truth audit of the dataset.

The honest check is an injected-noise test. Take a slice you believe is clean, reverse a known 10% of its labels, and train both ways. Routing should recover part of the accuracy that the corruption cost. If it recovers none of it, your margins are not separating, and the usual cause is too few pairs per response for consensus to form. Watch for the failure signature too: flip weight climbing above roughly 40% means the router is fighting your data rather than cleaning it, and warm-up is the first knob to lengthen.

## When Routing Preference Labels Is the Wrong Tool

If your labels are clean, this buys you nothing and costs you two hyperparameters. The control run scores 93.0% with plain training and 92.8% with routing. That is not a win, and on a curated expert set written by people you can name, plain DPO is the correct choice.

It also needs consensus to work. The evidence that a label is backwards is that the model, taught by every other pair, disagrees with it. If each response appears in only one pair, there is nothing to disagree with, and the router falls back to its prior. Small datasets and one-shot comparisons are the weak case.

The deepest objection is that the model's confidence is not neutral. It encodes whatever the model already believes, including its biases. A pair that contradicts a bias the model learned in pretraining looks exactly like a backwards label from the inside. Routing will quietly reverse it. That is self-confirmation, and warm-up and confidence gating reduce it without removing it.

Three questions before adopting this:

- Do you know the rate of backwards labels in your data, or are you guessing?
- Does each response appear in enough pairs for a consensus to exist?
- If the model reversed a label that was actually correct, would any test you run catch it?

## Glossary

- **preference pair** — one prompt, two responses, and a label saying which response is better.
- **margin** — how much more the model prefers the winner than the reference model did.
- **reference model** — the frozen copy the model started from, used as the baseline for every margin.
- **tie** — a pair whose two responses are equally good, so no direction should be learned.
- **routing weights** — the share of a pair's training signal assigned to keep, reverse, or cancel.
- **warm-up** — the opening fraction of training during which correction is off and plain training runs.
