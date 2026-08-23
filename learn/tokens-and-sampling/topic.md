# Temperature Is a Knob, Not a Personality

**Category**: New Models & APIs
**Tags**: transformers, embeddings
**Date**: 2026-08-23
**Level**: Start here
**For**: How models work
**Hook**: The model scores every possible next piece of text. Temperature only changes how you roll the dice.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

The friend from lesson 1 does not pick a word out of thin air. First they tear your sentence into little tiles — sometimes a whole word, sometimes half of one. Then they give every tile in their box a score. If you tell them "just pick the top score," they become boring and repeat themselves. If you tell them "roll a dice, but keep the high scores more likely," they get more surprising. That dice setting is temperature. It is not a mood. It is how fairly they treat the runners-up.

## The Problem

People treat temperature like a personality slider — 0.2 is "serious," 0.9 is "creative" — and then wonder why a JSON tool call came back with a trailing comment, or why two identical requests diverged. The model already produced a score for every token. Temperature only reshapes those scores before the roll. If the top two tokens are almost tied, a small temperature change flips the answer. If one token is far ahead, temperature barely matters. You were turning a knob that does not mean what the UI implied.

## For a Software Engineer

Tokenization is a codec. The same letters can become a different number of tiles in two models, so "this prompt is 800 tokens" is not portable. Embeddings are the coordinates those tiles live in — nearby strings sit near each other. Softmax is the last step that turns raw scores into a probability distribution you can sample from.

Temperature divides the scores before softmax. At 0 you take the argmax every time (greedy). At 1 you use the model's native distribution. Above 1 you flatten it — runners-up get more mass. This is the same shape as a softmax temperature in a classifier or a Boltzmann distribution: you are not adding ideas, you are changing how peaked the distribution is.

The number worth feeling: drop temperature from 1.0 to 0.2 on a tool-call prefix and you often cut format breakage a lot, because the model stops sampling the long tail of "almost JSON." Raise it on a brainstorming prompt and you buy diversity you will then have to filter. Monday morning: set temperature by *failure mode*. Structured output and code edits → low. Ideation you will review → higher. Do not copy 0.7 from a blog post into a production agent.

## What This Means for You

**When this matters**: you ship a prompt that must return JSON, a patch, or a classification, and someone "tuned creativity" instead of the schema.

**How it affects you**: temperature does not make the model smarter. It changes variance. High variance on a tool call is a parse error. Low variance on a naming brainstorm is twelve near-identical names.

**What to do about it**: log the temperature with the request. For anything a parser will consume, start at 0–0.3 and constrain the grammar if the API allows it. Measure token counts on *your* tokenizer, not a friend's. If two runs disagree, check whether you were sampling at all before you rewrite the prompt.

## What It Is

A tokenizer is a trained split of text into vocabulary IDs. Byte-pair encoding and friends merge frequent chunks so common words are one tile and rare ones are several. You never send "raw characters" to the model. You send IDs.

Each ID maps to a vector (the embedding). The transformer mixes those vectors. The last layer produces a logit per vocabulary item. Softmax turns logits into probabilities. Sampling draws one ID. Decode that ID back to text. Repeat.

Top-k and top-p (nucleus) are extra filters on that distribution: keep only the k best, or keep the smallest set whose probabilities sum to p. They are also not personality. They are how much of the tail you are willing to roll.

## Why It Matters

Billing, context limits, and "why did it split my identifier" are tokenizer issues. "Why is this flake only in prod" is often sampling. A eval that runs temperature 0 and a product that runs 0.8 are not the same system. If you do not write the sampling parameters next to the prompt, you cannot reproduce a failure.

## Key Technical Details

**Background first.** *Tokens* are vocabulary IDs. An *embedding* is a vector for one ID. *Logits* are unnormalized scores. *Softmax* maps a vector of scores to a probability distribution. *Temperature* T scales logits as logit/T before softmax. *top-p* keeps the smallest prefix of sorted probabilities that sums to p.

- **Token count is model-specific.** `tiktoken` for OpenAI, a different file for Anthropic or Llama. Count with the one you will be billed on.
- **Greedy (T→0) is deterministic given the prefix.** Almost. Some stacks still have batching noise. For tests, pin seed if the API offers it, and pin temperature at 0.
- **The tail is where JSON dies.** A 1e-4 chance of emitting a backtick in a JSON field will hit you at volume. Constrained decoding beats hoping.
- **Embeddings are not magic meaning.** Cosine-near usually means "used in similar contexts in the training data." Good enough for retrieval (lesson 6). Not a proof of synonymy.

## How It Connects to What You Know

This is a random number generator on top of a scored list — like weighted load balancing, not like a mood ring. The tokenizer is a compression codec with a fixed codebook.

Previous: [The model only ever picks the next token](#learn/what-an-llm-does). Next: [Specs and examples beat vague prompts](#learn/prompting-that-holds-up).

## Try It Yourself

`code_example.py` tokenizes a few strings the naive way, scores a tiny vocabulary, and reprints the distribution at temperature 0.2, 1.0, and 1.5 so you can see the same logits become a spike or a smear.

## Glossary

- **Tokenizer** — the program that cuts text into vocabulary IDs and back.
- **Embedding** — the vector stored for one token ID.
- **Softmax** — maps scores to probabilities that sum to 1.
- **Temperature** — divides logits before softmax; lower is peakier.
- **Greedy decoding** — always pick the top-scoring token.
- **top-k / top-p** — discard the tail before sampling.
- **Nucleus sampling** — another name for top-p.
