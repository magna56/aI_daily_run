# How Self-Attention Works

**Category**: New Models & APIs
**Tags**: transformers, from-scratch
**Date**: 2026-08-23
**Level**: Building
**For**: How models work
**Hook**: Every word scores every other word, then pulls a weighted mix of their values.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

A kid is writing a story and has to pick the next word. Before they pick, they look back at every word already on the page and ask "how much do you matter for what I am about to say?" "Not" matters a lot if the next guess is "guilty." "The" barely matters. They mix the useful words together and then guess. That look-back-and-mix is attention.

## The Problem

Older sequence models walked the sentence left to right and tried to squeeze the past into one hidden state. Long prefixes drowned. Parallel training was awkward. The transformer replaced that walk with a table: every position may look at every earlier position (and, in some setups, future ones too) in one matrix multiply. If you do not know what that table is doing, "context window" and "attention sink" stay folklore.

## For a Software Engineer

For one head, each token becomes three vectors: query `Q`, key `K`, value `V` — three learned linear maps of the same hidden state. Scores are `Q Kᵀ / √d`. Softmax turns the scores into weights that add to 1. The output is those weights times `V`.

That is a gather, not a search engine. Nothing is retrieved from disk. The model is mixing *this request's* tokens. Causal masks zero out the future so token 5 cannot read token 6. Multi-head means several of these tables in parallel, then a concat and a projection.

Monday morning: when a model ignores a constraint in the middle of a long prompt, you are looking at a weighting failure, not a missing "understanding" module. Put the constraint closer to the end, repeat it, or cut tokens that steal weight.

## What This Means for You

**When this matters**: you are stuffing a prompt, debugging a "it forgot the spec" failure, or reading a KV-cache blog post.

**How it affects you**: attention is `n²` in sequence length for the naive score table. That is why long context is expensive and why a cache of keys and values exists. It is also why a buried instruction loses to a nearby example.

**What to do about it**: keep the useful tokens few and late. Do not paste two conflicting specs. When you hear "the model attended to the wrong thing," believe the weights, not the vibes.

## What It Is

Self-attention is the mixing rule inside a transformer block. "Self" means queries, keys, and values all come from the same sequence. Cross-attention (encoder-decoder, some multimodal stacks) lets one sequence query another.

The `1/√d` term keeps the dot products from growing with hidden size so softmax does not saturate into a one-hot that ignores everyone else. Softmax is the reason one token can dominate a head.

## Why It Matters

This is the mechanism behind "the model can use the whole prompt." It is also the mechanism behind "the model used the wrong sentence in the prompt." KV cache, sliding windows, and grouped-query attention are all ways to pay less for the same table.

You do not need to derive the paper to use the product. You do need the shape: scores, weights, weighted values. Everything else in the stack is how you compute that cheaper.

## Key Technical Details

**Background first.** A *token* is a vocabulary chunk. A *head* is one Q/K/V trio. *Causal* means position `i` may only see `≤ i`.

- **`Q Kᵀ` is a score, not a fact.** Large score means "this key looks useful to this query."
- **Softmax is a competition.** Weights sum to 1. One large score starves the rest.
- **`V` is what you mix.** Keys decide *who*; values decide *what you copy*.
- **Masking is a hard rule.** Future tokens are −∞ before softmax, not "please ignore."
- **Many heads split the job.** One head can track quotes; another tracks types.

## How It Connects to What You Know

A database index is "who matches this query." Attention is "how much does each already-loaded row matter," with soft weights instead of a boolean. A code review that highlights three lines and ignores the rest is the same habit. The transformer just does it with matrix multiplies.

Next: [How Model Calibration Works](#learn/calibration) — after the mix, the scores still have to be honest.

## Try It Yourself

`code_example.py` runs a 4-token toy attention by hand: one query, four keys, a causal mask, softmax, and the weighted values. Change the query and watch the weights move.

## Glossary

- **Query / key / value** — the three views of a token: what I am looking for, what I advertise, what I contribute.
- **Attention weights** — softmax of the scores; they sum to 1.
- **Head** — one independent Q/K/V mixer.
- **Causal mask** — forbids looking at future tokens.
- **KV cache** — stored keys and values from earlier tokens so the next step does not rebuild them.
- **Softmax** — turns unbounded scores into a probability vector.
