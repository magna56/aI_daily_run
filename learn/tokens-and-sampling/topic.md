# How Tokens and Sampling Work

**Category**: New Models & APIs
**Tags**: transformers, embeddings
**Date**: 2026-08-23
**Level**: Start here
**For**: How models work
**Hook**: The model scores every possible next piece of text. Temperature only changes how you roll the dice.
**Kind**: Learn
**Time to read**: ~13 minutes

> **You'll be able to:** estimate what a piece of text will cost before you send it, explain why the same prompt is cheaper in English than in JSON, and set `temperature`, `top_k` and `top_p` by failure mode instead of by vibe.

## Explain Like I'm 5

The friend from lesson 1 does not pick a word out of thin air. First they tear your sentence into little tiles — sometimes a whole word, sometimes half of one. Then they give every tile in their box a score.

If you tell them "just pick the top score," they become boring and repeat themselves. If you tell them "roll a dice, but keep the high scores more likely," they get more surprising. That dice setting is temperature. It is not a mood. It is how fairly they treat the runners-up.

## For a Software Engineer

**Tokenization is a codec, and temperature is a die.** Neither is a personality setting, and both get treated as one.

| What you already know | The equivalent here |
|---|---|
| A character encoding — UTF-8 vs UTF-16 | **Tokenizer** — the same text is a different number of units in a different model |
| Chunk size in a streaming parser | **Token** — ~4 characters of English, far worse for code and identifiers |
| Buffer capacity — a hard limit, not a suggestion | **Context window** — everything outside it does not exist |
| `random.choices(population, weights=...)` | **Sampling** — draw one token from the distribution |
| A softmax temperature in a classifier | **`temperature`** — divides the scores before they become probabilities |
| `LIMIT 5` vs `WHERE p > 0.9` | **`top_k` vs `top_p`** — fixed cut versus adaptive cut |

**The number worth internalizing:** English prose lands near **3.8 characters per token** — the familiar "~4" rule. Nothing else does. JSON runs about **2.3**, a UUID about **1.4**, Japanese about **1.0**. The same information, expressed as JSON instead of prose, can cost you nearly double. You are billed per token, not per character, and the gap between your estimate and your bill is exactly this spread.

**What to do differently on Monday:** set temperature by *failure mode*, not by feel. Structured output, tool calls and code edits go low (0–0.3), because the failure there is a parse error and every point of variance buys you one. Ideation you will review yourself can go higher. Do not copy `0.7` out of a blog post into a production agent.

## What a Token Actually Is

A token is a chunk of text, produced by a trained split rather than by any rule you would write yourself. Byte-pair encoding and its relatives merge the most frequent character sequences into single units, so common words become one token and rare ones become several.

```
"Hello world"          → 2 tokens
"getuserapi"           → 3 tokens   (get | user | api)
"I work in finance"    → 4 tokens
"f47ac10b-58cc-4372"   → 12 tokens  (a UUID is nearly one token per 1.4 chars)
```

The model never sees letters. Text becomes integer IDs before anything else happens, and only IDs reach the network. That is why a model miscounts the r's in "strawberry": it is being asked about something structurally invisible to it, which is a representation limit rather than a reasoning failure.

Two consequences that cost real money:

- **Token counts are not portable.** "This prompt is 800 tokens" is a claim about one tokenizer. Measure on the one you are actually billed by.
- **Content type dominates cost.** Prose is efficient because the vocabulary was built from prose. Identifiers, minified JSON, base64 and non-Latin scripts all fall off the vocabulary and get spelled out in pieces.

## The Context Window, and Why It Is Re-Sent

Context is the model's working memory: everything it can see while producing this response.

```
┌──────────────────────────────────────────────────────┐
│                   CONTEXT WINDOW                     │
│  System prompt        ← the harness's instructions   │
│  Tool schemas         ← every tool you exposed       │
│  Project config       ← your CLAUDE.md or equivalent │
│  Message 1            ← your first question          │
│  Reply 1              ← the model's first answer     │
│  Message 2  …         ← grows with every exchange    │
└──────────────────────────────────────────────────────┘
```

Three facts follow, and the third one is the one that surprises people:

- **There is no memory outside this window.** A new session starts from nothing.
- **It is a hard limit, not a soft one.** Overflow is an error or a truncation, not a graceful degradation.
- **The entire window is re-sent on every turn.** The model is stateless; the transcript is replayed each time. So "just add it to the context" is not a one-off action — it is a per-turn cost for the rest of the session. Lesson 7 turns that into an actual bill.

## From Scores to a Token: Temperature

The last layer emits one **logit** — a raw, unbounded score — per vocabulary entry. **Softmax** turns those into probabilities that sum to 1, and temperature divides the logits *before* softmax:

```
logits ÷ temperature → softmax → probabilities → draw one
```

Run the same four logits through it and the ordering never changes, only the confidence:

```
Same logits: {'return': 3.4, 'raise': 1.1, 'retry': 0.6, 'rm': -0.8}
     T    return     raise     retry        rm
   0.2    100.0%      0.0%      0.0%      0.0%
   0.7     94.5%      3.5%      1.7%      0.2%
   1.0     85.0%      8.5%      5.2%      1.3%
   1.5     69.9%     15.1%     10.8%      4.2%
```

`return` wins at every temperature. What changes is how often the runners-up get a turn. That is the whole mechanism, and it explains the two behaviours people misread: when the top two tokens are nearly tied, a small temperature change flips the answer; when one token is far ahead, temperature barely matters at all.

At `temperature=0` you take the argmax every time. Deterministic in principle — worth knowing that batching and floating-point reduction order in production can still shift it.

## Truncation: top-k and top-p

Temperature reshapes the odds among eligible tokens. Truncation changes **which tokens are eligible at all**, and that is a different lever:

- **`top_k`** — keep the k highest-probability tokens, drop the rest, renormalise. A fixed-size cut.
- **`top_p`** (nucleus) — keep the smallest set whose probabilities add up to p. An *adaptive* cut: when the model is confident one token can clear the bar alone; when it is unsure the set widens.

The example below prints exactly this on the same four logits — `top_p=0.9` keeps 2 of 4 tokens, `top_p=0.99` keeps all 4, while `top_k=2` keeps two regardless of how confident the model was. That adaptivity is the entire argument for nucleus sampling.

## Quick Reference

| Term | Plain English |
|---|---|
| Token | A chunk of text (~4 chars of English, worse for everything else). |
| Tokenizer | The trained split from text to token IDs. Model-specific. |
| BPE | Byte-pair encoding — merge the most frequent pairs, repeatedly. |
| Vocabulary | Every token the model knows, typically 100K–200K. |
| Embedding | The dense vector a token ID maps to. Nearby meanings, nearby vectors. |
| Context window | Maximum tokens visible at once. Hard limit. Re-sent every turn. |
| Logit | Raw per-token score from the last layer, before softmax. |
| Softmax | Turns logits into probabilities summing to 1. |
| Temperature | Divides logits before softmax. 0 = argmax; >1 = flatter. |
| `top_k` | Keep the k most likely tokens. Fixed-size truncation. |
| `top_p` | Keep the smallest set summing to p. Adaptive truncation. |
| Greedy decoding | `temperature=0`. Always the top token. |
| Inference | One forward pass producing one token. What you are billed for. |

## Do It Today

**Step 1 — watch the same scores produce different answers, 2 minutes.**

```bash
python3 learn/tokens-and-sampling/code_example.py
```

It trains a tiny byte-pair tokenizer on a short corpus, encodes a string with it, then softmaxes one fixed set of logits at four temperatures. **You know it worked** when `encode('lowest newest')` returns **5 tokens for 13 characters**, and when `return` holds first place at **every** temperature while sliding from 100% at `T=0.2` to 69.9% at `T=1.5`. The model's opinion never moved; only the dice did.

**Step 2 — see truncation do something temperature cannot.** The same run ends with a truncation table. **You know it worked** when `top_p=0.9` keeps **2 of 4** tokens and `top_p=0.99` keeps **4 of 4**, while `top_k=2` keeps two either way. That difference — the nucleus widening when the model is unsure — is the reason to prefer `top_p` for open-ended generation.

**Step 3 — measure your own text.** Take the largest file you routinely paste into a model and count its characters, then divide by 3.8 for a prose estimate and by 2.3 if it is JSON or config. Multiply by the number of turns in a typical session, because it is re-sent every turn. Most people discover their "one big paste" is the dominant line on the bill.

## Gotchas

- **A token is not a word and not a character.** "About 750 words per 1000 tokens" holds for English prose and fails badly for code, identifiers and non-Latin text.
- **Token counts are not portable across models.** Two providers can disagree by 20% on the same string.
- **"Add it to context" is not free.** It consumes window capacity *and* is re-sent every turn. It feels like a one-off and bills like a subscription.
- **`top_k` and `top_p` interact.** Set both and the more restrictive one wins at each step, which makes the other look ignored. Change one at a time.
- **Temperature does not make the model smarter.** It changes variance. High variance on a tool call is a parse error; low variance on a naming brainstorm is twelve near-identical names.
- **`temperature=0` is not a determinism guarantee in production.** Batching and floating-point reduction order can still move it. Treat it as "as reproducible as you can get."
- **A bigger context window is not an instruction to fill it.** Capacity and cost are separate questions, and retrieving more is not retrieving better.

## How It Connects to What You Know

Tokenization is string interning with a trained dictionary: variable-length text collapsed to integer IDs before any real work. Embeddings are a hash map from ID to feature vector, except neighbours are meaningful. Softmax is the same normalisation you have used to turn arbitrary scores into weights, and temperature is the same knob a Boltzmann distribution has — you are not adding ideas, you are changing how peaked the distribution is. Sampling is `random.choices` with weights. And the context window is a fixed-size buffer whose contents are replayed on every call, which is exactly the cost model of a stateless protocol that carries its own session state.

Next: [Prompting That Holds Up](#learn/prompting-that-holds-up) — how to write the context so the distribution lands where you want it.
