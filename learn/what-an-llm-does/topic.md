# How an LLM Predicts the Next Token

**Category**: New Models & APIs
**Tags**: transformers, training
**Date**: 2026-08-23
**Level**: Start here
**For**: How models work
**Hook**: A language model only ever picks the next word. Everything else — training, temperature, the whole transformer — exists to make that one pick good.
**Kind**: Learn
**Time to read**: ~14 minutes

> **You'll be able to:** explain what a model is actually doing when it answers you — no lookup, no search, just a distribution over next tokens — say where its knowledge physically lives, and set `temperature` deliberately instead of accepting a default.

## Explain Like I'm 5

You have a friend who has read an enormous pile of books, but can only ever say one word at a time. You start a sentence; they guess the next word. You add that word to the sentence; they guess again. They are not looking anything up. There is no filing cabinet behind them. They are playing "finish this sentence" extremely well, and every answer you have ever seen from them was built one guess at a time.

Later, teachers sat with your friend and said "that reply was better than this one," thousands of times. The guessing did not change. What changed is which guesses now look right — so they started sounding like a helpful colleague instead of a random page from the internet.

## For a Software Engineer

**This is a lookup table, a pile of matrix multiplies, and a weighted random choice.** No database is queried when you send a prompt. Nothing is retrieved. The model's knowledge is *distributed* across billions of floating-point numbers, the way a hash function's behaviour is distributed across its arithmetic rather than stored in a table of inputs and outputs.

| What you already know | The LLM equivalent |
|---|---|
| String interning / a symbol table | **Tokenization** — text becomes integer IDs before anything else happens |
| A hash map from ID to a feature vector | **The embedding table** — token ID to a dense float vector |
| A weighted `reduce` over a window | **Attention** — each token's output is a weighted sum over the tokens before it |
| Memoizing expensive prefix work | **KV cache** — never recompute keys and values for tokens already processed |
| `random.choices(population, weights=...)` | **Sampling** — the model outputs a distribution, not a word |
| A compiled binary, fixed at build time | **Weights** — what training produced, frozen |
| Argv and environment, different every run | **Context** — what you hand it right now |

**The number worth internalizing:** attention cost grows with the **square** of sequence length. Doubling your context does not double the work, it roughly quadruples it. That is why context windows were historically small, why the KV cache exists, and why "just paste in more context" has a real cost curve behind it.

**What to do differently on Monday:** stop thinking of temperature as a creativity slider and start thinking of it as *a divisor on the scores before they become probabilities*. At temperature 0 the model is deterministic — same input, same output. If you need reproducibility (classification, extraction, anything you will diff in a test), that is not a style preference, it is a correctness requirement.

## The One Job: Predict the Next Token

Everything below serves a single operation. Given the text so far, produce a probability for **every token in the vocabulary** as the next one.

```
input:  "The capital of France is"
        ↓
output: {" Paris": 0.71, " a": 0.06, " the": 0.05, " located": 0.03, ... }   ← ~200,000 entries
        ↓
pick one, append it, run the whole thing again
```

Three consequences fall straight out of that shape, and most surprises about LLMs are one of them:

- **The model never produces a sentence.** It produces one distribution, you sample one token, and the loop runs again with a longer input. A paragraph is a few hundred repetitions.
- **The output is a distribution, not an answer.** "What did the model say?" is really two questions: what odds did it assign, and what did the sampler pick. Those are separable, and only the second one is yours to control.
- **Nothing is looked up.** There is no retrieval step to fail. When the plausible continuation happens to be false, we call it a hallucination — but nothing different is happening internally, which is why "don't hallucinate" does not work as an instruction.

## GPT = Generative + Pre-trained + Transformer

The name is the recipe, and each word answers a question people actually ask.

| Letter | What it means |
|---|---|
| **G** — Generative | It creates sequences one token at a time. Not classifying, not searching. |
| **P** — Pre-trained | The expensive training happened *before* you ever touched it. You use a finished artifact. |
| **T** — Transformer | The architecture: attention and MLP blocks stacked deep. Replaced RNNs in 2017 because it parallelises across a sequence instead of walking it one step at a time. |

**LLM** — Large Language Model — names the *result*, not the recipe. Every modern one is a transformer. Claude is not a GPT: it is Anthropic's model, built with related but different techniques, and "GPT" is a specific family name rather than a generic term.

## The Three Stages That Produce a Model

### Stage 1 — Pre-training

Predict the next token, over and over, across an enormous amount of text. No labels, no human answers: the text itself is the answer key, because the next word is already there.

**Produces** a *base model* that can continue text and will not follow instructions. Ask it a question and it may well continue with more questions, because that is what a page of questions looks like.

**Costs** tens of millions of dollars and up, which is why only a handful of organisations produce frontier models and everyone else builds on top.

### Stage 2 — Post-training

This is where a text-continuer becomes an assistant, in two moves:

- **Supervised fine-tuning (SFT)** — train on (prompt, good response) pairs written by people. Teaches the *shape* of being helpful.
- **Preference training (RLHF or DPO)** — people rank competing responses; the model learns which one humans prefer. Teaches the *style and the refusals*.

Nothing here teaches new facts about the world. It changes behaviour, not knowledge — which is precisely why fine-tuning is the wrong tool for "make it know our documentation."

### Stage 3 — Deployment

The frozen weights sit behind an API. Every request is one *inference*: your whole conversation goes in, one token at a time comes out. The model learns nothing from you, and the next request starts from the same frozen weights as the last.

## Where the Knowledge Lives

Two things determine an answer, and confusing them is the most expensive mistake in this whole subject.

| | Weights | Context |
|---|---|---|
| What | Compressed patterns from training | What the model can read right now |
| Set when | Training time — then frozen | This message, this session |
| Changes | Never | Every turn |
| How it gets there | Implicitly, from the corpus | Explicitly — you put it there |
| Changing it costs | A training run | A paste |

**Weights are what it learned. Context is what you show it.** No amount of context teaches the model something new about the world; it only puts facts in front of it for this one request. That single distinction is the difference between fine-tuning and RAG, and it is why people reach for the wrong one — Lesson 6 makes retrieval concrete.

## From Scores to a Word

The final layer emits one raw score — a **logit** — per vocabulary token. Logits are unbounded and not probabilities. **Softmax** turns them into a distribution that sums to 1, and `temperature` divides the logits *before* that happens:

```
logits ÷ temperature → softmax → probabilities → sample one token
```

Which is why the knobs behave the way they do:

- **`temperature` 0** — always take the highest-probability token. Deterministic in principle. Use it for anything you need to reproduce.
- **`temperature` < 1** — divides by a small number, spreading the logits apart, so the leader wins more often. Sharper, more repetitive.
- **`temperature` > 1** — flattens the distribution toward uniform. More surprising, and more wrong.
- **`top_k`** — keep only the k most likely tokens, renormalise, sample from those.
- **`top_p`** (nucleus) — keep the smallest set of tokens whose probabilities add up to p. Adapts to how confident the model is at this step, where `top_k` does not.

Temperature changes *the odds among eligible tokens*. Top-k and top-p change *which tokens are eligible at all*. Lesson 2 goes further into tokens and sampling, and its runnable example implements all three of these knobs from scratch so you can watch them move.

## Quick Reference

| Term | Plain English |
|---|---|
| Token | A chunk of text (~4 characters). The atomic unit the model works with. |
| Vocabulary | Every token the model knows — typically 100K–200K of them. |
| Logit | The raw score the model emits per token, before it becomes a probability. |
| Softmax | Turns logits into a probability distribution that sums to 1. |
| Temperature | Divides logits before softmax. 0 = deterministic; higher = flatter. |
| Top-k / top-p | Truncate *which* tokens can be sampled, before temperature reshapes the odds. |
| Weights | What training produced. Frozen. Billions of floats. |
| Context | What you hand the model this turn. Re-sent every turn. |
| Inference | One forward pass producing one token. What you are billed for. |
| Base model | Post-pre-training, pre-instruction. Continues text, does not obey. |
| SFT | Supervised fine-tuning on (prompt, good answer) pairs. |
| RLHF / DPO | Training on human preferences between responses. |
| Hallucination | A fluent, confident, wrong continuation. Not a separate failure mode. |
| Autoregressive | Each output token is appended to the input and the whole thing runs again. |

## Do It Today

**Step 1 — watch the three stages move the same table, 2 minutes.** Run the example:

```bash
python3 learn/what-an-llm-does/code_example.py
```

It builds a tiny count-based next-word table from four sentences, then applies pre-training, SFT and preference training as plain data operations — no neural net, no API. **You know it worked** when `P(next | 'the')` starts at **29% cat / 29% model**, tips to **58% cat** after SFT, and lands at **60% cat with `model` and `question` driven to 0%** after the preference step. The machine never changed. Only the counts did, which is the entire point of the three stages.

**Step 2 — break it on purpose.** Open the file and add a sentence to the pretrain corpus that uses a word already in the table — say `the model sat on the mat .` — then re-run. **You know it worked** when the distribution after pre-training shifts but the *shape* of the SFT and preference steps does not: those stages still just reweight whatever pre-training produced. That is the difference between teaching the model a fact and teaching it a behaviour, and it is the reason fine-tuning cannot install knowledge.

**Step 3 — go set a temperature on purpose.** Find one place where your code or your team's calls an LLM API for something that should be reproducible — a classifier, an extractor, a test fixture — and set `temperature=0` explicitly. Most defaults sit near 1.0, which means you are currently opting into randomness nobody chose. Lesson 2's example lets you watch exactly what that default is doing to your odds.

## Gotchas

- **Tokens are not words and not characters.** Asking a model to count the r's in "strawberry" asks about something it structurally cannot see. That is a representation limit, not a reasoning failure.
- **Temperature 0 is not a determinism guarantee in production.** It is deterministic in principle, but batching, floating-point reduction order on GPUs, and load balancing across differently configured nodes can still change the output run to run. Treat it as "as reproducible as you can get".
- **Top-k and top-p interact.** Set both and the more restrictive one wins at each step, which makes one of them look ignored. Change one at a time.
- **A bigger context window is not a free one.** Attention cost grows roughly with the square of the sequence, and the whole window is re-sent every turn. "It fits" and "it's cheap" are different questions.
- **The model does not have a database.** If it does not *know* something, more context will not teach it — context only lets it read what you pasted. That is the fine-tuning versus RAG decision in one sentence.
- **"Pre-trained" does not mean finished.** A base model is genuinely unhelpful; everything you recognise as assistant behaviour came from post-training, which is also where refusals and tone live.

## How It Connects to What You Know

Tokenization is string interning: variable-length text collapsed to integer IDs before any real work happens. The embedding table is a hash map from ID to feature vector. Attention is a weighted `reduce` over a window, except the weights are computed per query rather than fixed — closer to a soft, differentiable dictionary lookup than to a convolution. The KV cache is memoization: the keys and values for token 500 do not change when you append token 501, so you keep them. Autoregressive generation is a `while` loop that appends its own output to its input. And sampling from logits is `random.choices` with weights — softmax just turns arbitrary real-valued scores into a valid weight vector first.

Next: [Tokens and Sampling](#learn/tokens-and-sampling) — what a token actually costs, and how to budget a context window before you send it.
