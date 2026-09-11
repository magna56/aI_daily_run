# How Predicting a Whole Idea Beats Predicting the Next Token

**Category**: Applied Research
**Tags**: transformers, training, paper
**Date**: 2026-09-11
**Level**: Deeper
**For**: How models work
**Hook**: A model trained to guess only the next token learns to be fluent before it learns to be going anywhere. Adding a second target — the next chunk of meaning — reached the same training loss on about half the data.
**Engineer's view**: You have written an autocomplete that predicted the next character. It was fluent and aimless, because it could not commit to a word three characters out. Predicting the next whole word made it plan. Same model, longer unit, and the longer unit is where the structure lives.
**TLDR**: Next-token prediction gives a model one short-range target and nothing that spans a phrase. Adding a coarse second target over groups of tokens reaches the same loss on roughly half the data.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine learning to write by guessing the next letter of a sentence, over and over. You
would get very good at spelling. You would not get good at planning a sentence, because
nothing ever asked you what the sentence was about. Now imagine also being asked, every few
letters, to guess roughly what idea comes next. You are still spelling. But now something
is checking whether you know where you are going.

## The Problem

You have hit this in a system with no model in it. You wrote a validator that checked one
character at a time. It caught every illegal character and it never once caught a malformed
expression, because an expression is not a property any single character has. The check was
not weak. It was operating at a granularity where the thing you cared about did not exist.

Next-token prediction has that shape. A model reads a prefix and is scored on one token.
Every gradient it ever receives is about the next token, so the only structure it is ever
directly asked about is short-range. Anything longer — where a sentence is going, whether a
derivation reaches an answer — has to be learned indirectly, as a side effect of getting a
great many single tokens right.

It works, which is why nobody argues with it. But it is expensive in the specific way a
weak signal is expensive: you pay for it in data. The longer-range structure is in there,
and the objective is only ever pointing at it sideways.

**The fix is to add a second target at a coarser grain**, so the model is asked about the
span as well as the token.

## The Fix: Predict the Next Chunk as Well as the Next Token

The Intern-NCP Team published a technical report on 9 September 2026 that scales this to
8.9B parameters over 5.73T tokens of Dolma-3. The headline is not the benchmark lift. It is
that the model reaches **OLMo-3-7B's final pretraining loss using 51.3% of the tokens** —
the same place, on about half the data.

```figure
{ "kind": "system",
  "title": "The whole argument: one forward pass, two targets",
  "lanes": [
    { "t": "the model reads", "nodes": [
        { "id": "prefix", "t": "a prefix of tokens" } ] },
    { "t": "is scored on", "nodes": [
        { "id": "ntp", "t": "the next token", "s": "neutral" },
        { "id": "ncp", "t": "the next concept", "s": "new" } ] },
    { "t": "which teaches", "nodes": [
        { "id": "local", "t": "what comes immediately", "s": "neutral" },
        { "id": "plan",  "t": "where the span is going", "s": "new" } ] }
  ],
  "edges": [
    { "from": "prefix", "to": "ntp" },
    { "from": "prefix", "to": "ncp", "t": "spans 4-8 tokens", "s": "new" },
    { "from": "ntp", "to": "local" },
    { "from": "ncp", "to": "plan", "s": "new" } ],
  "note": "Both losses, one model, trained together. The second target is the one that spans more than a token." }
```

### What is a concept here, concretely?

Not a word and not a topic. It is a discrete code derived from the model's own hidden
states, so the vocabulary is built rather than written down.

Take the hidden state at an intermediate layer, for a span of four to eight tokens. Split
that vector into several sub-vectors. Quantize each one against its own small codebook —
around 256 entries each. A concept is the tuple of codebook indices. That is **product
quantization**, and it is used here for the reason it is used in retrieval: a handful of
small codebooks covers an enormous space of combinations without an enormous table.

```figure
{ "kind": "route",
  "title": "Turning hidden states into a concept vocabulary",
  "source": "hidden state for a span of tokens",
  "parts": [
    { "t": "sub-vector 1", "to": 0, "via": "codebook 1", "s": "new" },
    { "t": "sub-vector 2", "to": 0, "via": "codebook 2", "s": "new" },
    { "t": "sub-vector M", "to": 0, "via": "codebook M", "s": "new" }
  ],
  "dests": [
    { "t": "a tuple of indices = one concept", "s": "ok" }
  ],
  "note": "M codebooks of 256 entries describe 256^M combinations, with M x 256 vectors to store." }
```

### Why does the coarse target help if it is derived from the model itself?

Because it is not new information, it is a new *question*. The concept vocabulary is a
compression of what the model already computes, and compressing it forces a choice: which
distinctions survive quantization. Predicting the surviving distinctions is a harder task
than predicting a token, and it is harder in the direction you want — it is about the span.

Training is joint. A concept-prediction loss over the concept vocabulary, a token loss so
generation stays token-level, and a commitment loss so the hidden states and the codebooks
do not drift apart. The predicted concept is fed back to guide the tokens that follow, so
the coarse guess conditions the fine one rather than living beside it.

## What This Means for You

**When this matters.** You are training or pretraining, or you are deciding what to believe
about scaling claims. If you only ever call an API, this changes nothing you do today — it
is a statement about where the next generation of base models may get cheaper, not about
your prompt.

**How it affects you.** It is evidence for a specific and useful idea: the objective, not
just the data or the parameter count, is a place where efficiency lives. A 48% reduction in
tokens to reach the same loss did not come from more compute or a bigger model. It came
from asking a second question during the same forward pass.

It also gives you a transferable trick with a name. Product quantization on your own
representations turns continuous vectors into a discrete vocabulary you can predict,
count, cache or index. That applies well outside pretraining, and it is the part of this
paper most likely to be useful to you this year.

**What to do about it.**

1. Run the toy in `code_example.py` and look at how much the concept constrains the tokens
   that follow. That number is the whole argument, at a scale you can read.
2. Then look at where you already have continuous representations and only ever compare
   them with cosine similarity. Those are candidates for a discrete code.
3. If you evaluate base models, start asking what the pretraining objective was, not just
   the token count. Two models trained on the same trillions are no longer comparable.
4. Read the ablation on concept span before you pick one. Four to eight tokens is the
   reported range, and it is a tuning decision rather than a constant.

## Implementing It

**The change.** Three pieces, and the first is the one worth lifting on its own.

*Build the codebooks.* Product quantization is k-means run separately on slices of the
vector, and nothing more:

```python
def fit_pq(vectors, m_books=4, k=256, iters=12):
    """Split each vector into m_books slices; cluster each slice on its own."""
    dim = len(vectors[0]) // m_books
    books = []
    for b in range(m_books):
        slices = [v[b * dim:(b + 1) * dim] for v in vectors]
        books.append(kmeans(slices, k, iters))      # k centroids for this slice only
    return books, dim

def encode(vec, books, dim):
    """A concept id: one codebook index per slice."""
    return tuple(nearest(vec[b * dim:(b + 1) * dim], bk)
                 for b, bk in enumerate(books))
```

Four books of 256 describe 256⁴ combinations while storing 1,024 centroids. That ratio is
why this works at vocabulary scale, and it is the reason product quantization is used here
rather than one flat codebook: a single book large enough to cover that space would be
untrainable, because most of its entries would never be visited.

*Derive the concept sequence.* One concept per span, from the span's pooled hidden state:

```python
SPAN = 4                                     # the paper's reported range is 4-8
def concepts_of(hidden_states, books, dim, span=SPAN):
    out = []
    for i in range(0, len(hidden_states) - span + 1, span):
        pooled = mean_vector(hidden_states[i:i + span])
        out.append(encode(pooled, books, dim))
    return out
```

*Train on both.* The concept head predicts the next concept from the same trunk, and its
output conditions the token head:

```python
loss = ntp_loss + alpha * ncp_loss + beta * commitment_loss
```

`commitment_loss` is what keeps the codebooks and the hidden states from drifting apart —
without it the vocabulary describes representations the model no longer produces, and the
coarse target goes stale mid-training. `alpha` decides how much gradient the span target
gets, and setting it too high makes the model optimize a compression of itself rather than
the text.

**How you know it worked.** The check is whether the concept actually carries span-level
information, and you can measure it before training anything large. Compute the entropy of
the next token given the previous token, then given the current concept. If the concept
does not reduce it, your span or your codebook size is wrong and no amount of training will
fix that.

At scale the signal is loss-per-token against a next-token-only baseline on identical data.
That is the claim being made — same loss, fewer tokens — so it is the curve to reproduce,
and it is visible long before the end of a run.

**When not to.** Do not add the second loss to a fine-tune. The codebooks are built from
pretraining-scale statistics, and a short run cannot move them, so you pay the cost and
inherit a vocabulary describing someone else's representations.

## When Predicting Concepts Is the Wrong Objective

This is a pretraining result, and pretraining results transfer badly to everything else.

The clearest limit is scale. The argument rests on one 8.9B run against one baseline, and
"reaches the same loss on half the tokens" is a claim about that pair on that data. It is a
strong signal and it is not a scaling law; nobody has shown the gap holds at 70B or narrows
to nothing.

There is also the question of what the concepts are. They are codes over the model's own
hidden states, which means the objective is partly self-referential — the model is being
asked to predict a compression of what it would have computed anyway. That is defensible,
and it is also why the commitment term matters more here than in retrieval, where the
vectors are fixed.

And the cost is not free. You carry an extra head, an extra loss and a codebook update
through every step. The reported figure is about 85% of standard computation, so a 48% token
reduction has to clear that overhead — real, but a smaller margin than the token number
suggests.

Three questions before taking this seriously for your own run:

- Am I pretraining, or am I hoping a pretraining result applies to a fine-tune?
- Does my data have span-level structure a concept could capture, or is it short and
  independent?
- Have I measured whether a concept reduces next-token entropy on my corpus at all?

## Glossary

- **Next-token prediction** — the standard pretraining objective: read a prefix, be scored
  on the single token that follows. Every gradient is about one token.
- **Product quantization** — splitting a vector into slices and quantizing each against its
  own small codebook. M books of K entries describe K^M combinations while storing M×K
  vectors.
- **Codebook** — the set of centroid vectors one slice is quantized against. A code is the
  index of the nearest centroid.
- **Concept** — here, the tuple of codebook indices for a span of four to eight tokens. A
  discrete label derived from the model's own hidden states, not a word or a topic.
- **Commitment loss** — the term that pulls hidden states toward their assigned centroids,
  so the representations and the codebooks stay in agreement as training moves.
- **Pretraining loss** — the average next-token loss over the training corpus. Reaching a
  given value on fewer tokens is the efficiency claim this session is about.
