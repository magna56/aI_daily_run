# How Keeping Four Tokens Beats Retraining a Model

**Category**: Applied Research
**Tags**: inference-serving, transformers, cost, paper
**Date**: 2026-09-01
**Level**: Deeper
**For**: Shipping AI
**Hook**: A whole research direction retrained models to cap their memory growth. Changing which tokens the model may look at does better, costs no training at all, and the difference is four tokens.
**Time to read**: ~11 minutes

## Explain Like I'm 5

Imagine someone taking notes in a long meeting who can only keep the last page. Everything older
gets thrown away, so their notes never grow — but they also lose the first page, the one with
everybody's names and what the meeting is about.

Keep that first page and the rest still makes sense. Throw it away and every page after it slowly
turns to nonsense, even though nothing else changed. The fix is not a better note-taker. It is
holding on to one page.

## The Problem

A model's memory grows with every token it reads. Each one adds a key and a value to the KV cache,
and that cache is kept for the whole conversation, so cost and memory climb without limit. This is
the single largest reason long context is expensive.

The field's most fashionable answer is linear attention: replace the quadratic mechanism with one
that keeps a fixed-size state instead of a growing cache. Retrofitting an existing model to use it
is not cheap — the published methods spend between 40 million and 100 billion tokens of
post-training, across one to three stages, to convert a model that already worked.

The obvious cheap baseline is a sliding window: let each token attend only to the last few hundred.
Every one of those papers compared against it and beat it comfortably. If that sounds like
benchmarking a new cache against a baseline nobody bothered to configure properly, hold that
thought.

Because they compared against a **sink-free** sliding window, and it has been known since 2024 that
this collapses catastrophically the moment the first few tokens scroll out. **Pin them: attend to
the last *w* tokens and, always, to the first four.** That is the whole change, it is a mask
applied at inference, and Microsoft's Applied Sciences Group found it beats the retrained models
with zero post-training.

## The Fix: Pin the First Four Tokens

Write it as **SWA(w, s)**: each token attends to the *w* tokens before it, plus the first *s*
tokens of the sequence, always. In the paper *w* ranges from 64 to 512 and *s* is fixed at 4. That
is the entire change. It is a mask, applied at inference, to a model nobody retrained.

The memory story falls straight out of it. The cache stops growing at *w + s* entries per layer,
so a hundred-thousand-token conversation costs the same per step as a five-hundred-token one.

### Why do the first four tokens matter that much?

Because attention has to put its weight somewhere. Softmax forces the scores to sum to one, so on a
step where nothing in the window is relevant, the model still has to distribute attention across
something. Trained models learn to dump that surplus on the first few tokens — they become
**attention sinks**, a parking space for weight that has nowhere useful to go.

Take the parking space away and the surplus is forced onto tokens that *are* in the window,
distorting every score that mattered. That is why sink-free windows fail so completely, and why
four tokens fix it.

### So is linear attention simply worse?

No, and the paper is careful here. On BABILong at zero added context, LoLCATs scores 56% against
SWA's 55% — a retrained linear model is competitive when the context is short. The gap opens with
length: at 2K it is 19% for SWA against 10%, and at 4K, 15% against 3%.

On single needle-in-a-haystack with Llama 3.1 8B at 4K, SWA recovers 17.2–23% of full attention's
accuracy, while LoLCATs reaches at most 5.8% and Liger-GLA at most 0.8%. On general knowledge,
SWA(64, 4) recovers 93.2% of the base model's MMLU with **zero** post-training tokens; the best
linear method managed 83.2% after 40 million.

## For a Software Engineer

This is a ring buffer with pinned entries, and you have shipped one.

Every eviction policy has the same failure: the entry that everything else depends on ages out like
any other, and the cache stays technically warm while becoming useless. You solve it the same way
every time — you pin the handful of entries that must never be evicted, and let the rest scroll.
Attention sinks are that pin, and the whole result is that nobody had tried pinning them before
concluding the simple approach did not work.

The number worth holding onto: **zero post-training tokens against forty million**, for a better
score. That is not a tuning win, it is a baseline that was never run properly — and the reason it
was never run properly is that the broken version was already in the literature and everyone
inherited it.

## What This Means for You

**When this matters.** You serve a long-context model and your bill or your latency is dominated by
KV cache growth, or you are evaluating a vendor offering a "linearized" version of a model you
already run.

**How it affects you.** The cheap option is much better than the literature suggests and needs no
training run, no specialised kernels and no new checkpoint. It is a serving configuration. And if
you are being sold a retrofitted linear model, the comparison that justifies it was probably made
against a baseline missing four tokens — which is a fair question to ask before you migrate.

**What to do about it.** Today, without changing any serving configuration at all: find out
whether the sliding-window implementation you already have pins its first tokens. That is a
five-minute read of one config file or one function, and it decides whether every window benchmark
you have run so far was measuring the broken variant. Then, on a model you already serve: turn on
sliding-window attention with four sink tokens and measure recall at your real context length. Most serving stacks expose the
window as a config value, so this is a restart rather than a project. Compare against your current
full-attention numbers and decide whether the recall you lose is worth the memory you stop paying
for — and note that on the paper's own long-context numbers, what you lose is substantial.

## Implementing It

**The change.**

*Anyone serving a model.* The window and the sinks are configuration, not code. In a Hugging Face
config the window is already a first-class field:

```json
{
  "sliding_window": 256,
  "use_sliding_window": true,
  "num_sink_tokens": 4
}
```

Set `sliding_window` to the paper's range (64–512) and start at 256; 64 was enough for knowledge
tasks, longer windows helped on retrieval. The sink count stays 4 — the paper never varies it, and
neither should you without measuring.

Check what your stack actually does with that field before trusting it. Several serving runtimes
implement the window but not the sinks, which gives you precisely the configuration the paper
identifies as catastrophic. If you cannot find a sink setting, grep the attention implementation
for where the mask is built; the absence of a pinned prefix is the thing to look for.

*Anyone implementing the mask from scratch.* It is a boolean mask, and writing it once is the
fastest way to stop treating this as magic:

```python
def swa_sink_mask(seq_len, window, sinks=4):
    """True where token i may attend to token j."""
    mask = [[False] * seq_len for _ in range(seq_len)]
    for i in range(seq_len):
        for j in range(seq_len):
            causal = j <= i
            in_window = i - j < window
            is_sink = j < sinks                  # the parking space, never evicted
            mask[i][j] = causal and (in_window or is_sink)
    return mask
```

Delete the `is_sink` term and you have the sink-free version every linear-attention paper used as
its baseline. Running both against the same prompt, and printing the two masks side by side, is the
whole experiment — and it takes about a minute. `code_example.py` does exactly that and scores the
result, so you can see where the sink-free version starts losing the earlier tokens it needed.

*Anyone evaluating a linearization claim.* Before migrating, re-run the vendor's own benchmark with
SWA-plus-sinks as the third arm. The question to put in writing:

```text
Your comparison lists full attention and sliding-window attention.
Was the sliding-window arm run WITH attention sinks (first 4 tokens always attended)?
If not, please re-run it — sink-free SWA is known to collapse, and SWA(64,4)
recovers 93.2% of MMLU with no post-training at all.
```

**How you know it worked.** Watch two numbers, not one. KV cache memory per sequence should go
**flat** — it stops tracking conversation length and parks at roughly `(window + 4)` entries per
layer, which is the entire point and is visible in the first minute. Then measure recall at your
real context length with a needle test you write yourself, because the published numbers are on
Llama 3.1 8B at 4K and yours are not. If accuracy falls off a cliff as context grows past the
window, that is expected behaviour, not a misconfiguration — you are seeing the trade you just
made, and the decision is whether to accept it.

## When a Sliding Window Is the Wrong Tool

The honest reading of these numbers is that **both** approaches are bad at long context, and one is
merely much less bad. SWA recovers 25% of baseline performance on BABILong at 4K. That is a large
improvement over LoLCATs' 5%, and it is still three-quarters of your accuracy gone.

So this is the wrong tool whenever the task genuinely needs information from outside the window.
Anything that must reason across a whole document, reconcile facts stated far apart, or find a
detail whose location you cannot predict wants full attention or retrieval — not a cheaper mask. A
sliding window is a memory-cost decision that you pay for in recall, and the paper's contribution
is making the exchange rate visible rather than favourable.

It is also worth being clear about what has been shown. This is one paper, on models from 1.3B to
70B, with long-context results on a single base model at up to 4K context. The comparison it makes
is overdue and the mechanism is well established; the exact figures are not a law of nature.

Three questions before switching. Is my cost actually dominated by KV cache growth, or am I
optimising the wrong line? What is my real recall requirement at my real context length, measured
rather than assumed? And if I am being sold a linearized model, was the baseline it beat missing
its sinks?
