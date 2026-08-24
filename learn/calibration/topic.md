# Calibration

**Category**: Evals & Reliability
**Tags**: reliability, benchmarks
**Date**: 2026-08-23
**Level**: Building
**For**: Shipping AI
**Hook**: A model that says eighty percent should be right eight times in ten.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

A weather app says "80% chance of rain." If it says that on ten days, you want rain on about eight of them. If it rains twice, the app is a confident liar. Calibration is the habit of checking that the number on the badge matches the world.

## The Problem

Classifiers and language models emit a number that looks like confidence. Teams treat it as a probability: route the 0.9s to auto-send, send the 0.4s to a human. If the 0.9s are wrong half the time, the router is a bug with a slider. Accuracy can look fine while the probabilities are junk. That is how you ship an "80% sure" path that is a coin flip.

## For a Software Engineer

Accuracy asks "how often is the top label right?" Calibration asks "when the model says `p`, is it right about `p` of the time?" The picture is a reliability diagram: bin predictions by confidence, plot accuracy in each bin against the bin's average confidence. A diagonal is honest. A line under the diagonal is overconfident.

Expected Calibration Error (ECE) is the average gap between those two numbers, weighted by how many items landed in the bin. Temperature scaling is the cheap fix at the end: divide logits by `T > 1` to soften, `T < 1` to sharpen, fit `T` on a held-out set. It does not invent new features. It rescales a softmax you already have.

Monday morning: do not put a confidence threshold in production until you have plotted the bins on *your* data. A leaderboard accuracy of 91% does not tell you what 0.8 means.

## What This Means for You

**When this matters**: you auto-reply, auto-merge, or auto-refund above a score, or you show a user a "confidence" badge.

**How it affects you**: overconfidence sends bad work through the happy path. Underconfidence floods the review queue. Both look like "the model is fine" if you only watch accuracy.

**What to do about it**: hold out a calibration set. Plot the reliability diagram. Fit a temperature. Re-check after every prompt or checkpoint change. If you cannot plot it, do not threshold on it.

## What It Is

A model is calibrated when `P(correct | confidence ≈ p) ≈ p`. That is a frequency claim, not a vibe. Modern nets are often overconfident: they learned to be right *and* to shout. Language models add a second mess — next-token softmax is not "probability the answer is true." Token confidence is not task confidence unless you measured it that way.

## Why It Matters

This is the difference between a useful router and a coin flip with a progress bar. Interviewers ask it because it separates people who ship thresholds from people who ship plots. Production incidents hide here: "we set the cutoff to 0.85 after a demo" with no bin chart.

It also tells you when to stop. Temperature scaling is a one-parameter bandage. If the diagram is still a banana after `T`, you need a better model, more data, or you should stop treating the score as a probability.

## Key Technical Details

**Background first.** *Logits* are raw scores before softmax. *Temperature* `T` divides logits. *ECE* is a weighted average of `|acc(bin) − conf(bin)|`.

- **Accuracy ≠ calibration.** You can be accurate and badly calibrated.
- **Bins need counts.** An empty 0.9 bin is not a green light.
- **Fit `T` on held-out data.** Fitting on the test set is lying.
- **Softmax over tokens is not truth.** "The model is 70% sure of the next word" is not "70% sure the invoice is paid."
- **Recalibrate after you change the prompt.** The scores moved.

## How It Connects to What You Know

A unit-test pass rate of 80% is not the same as a flaky test that *says* 80% and fails half the time. A load balancer that routes on a health score you never validated is this bug in ops clothing. You would not page on an uncalibrated metric. Do not auto-send on one either.

Next: [Embeddings](#learn/embeddings) — another number people treat as truth without measuring it.

## Try It Yourself

`code_example.py` builds a toy overconfident classifier, prints a reliability table, computes ECE, then fits a temperature and shows the bins move toward the diagonal.

## Glossary

- **Calibration** — when a stated probability matches the observed frequency.
- **Reliability diagram** — accuracy vs confidence by bin; the diagonal is the goal.
- **ECE** — expected calibration error; average gap across bins.
- **Temperature scaling** — divide logits by `T` to soften or sharpen.
- **Overconfidence** — stated `p` is higher than how often you are right.
- **Held-out set** — data you did not train on, used to fit `T` or measure ECE.
