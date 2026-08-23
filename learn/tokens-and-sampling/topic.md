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
Before the model can guess the next bit of a sentence, it cuts your words into puzzle pieces. Some pieces are whole words. Some are leftover scraps like "ing" or "tion." The model then gives every piece in its giant box of pieces a score — "this one is very likely next, that one is not." Those scores are not yet a choice. A second step turns the scores into a roll of the dice. You can make the dice almost always land on the top-scoring piece, or you can make them willing to pick a surprising one. That second knob is not a personality. It is how loaded the dice are.

## The Problem
Engineers treat temperature like a creativity slider and tokens like words. Both mistakes show up in production. Someone sets temperature to 0 and expects "the right answer," then is confused when a different tokenizer or a different model still disagrees. Someone sets temperature to 1.2 for a SQL generator and wonders why the column names wander. Someone counts words to estimate cost and is off by 2× because `"unbelievable"` is one English word and several tokens. The machine is simpler than the folklore: text is encoded into tokens, tokens become vectors, the network emits scores, and sampling turns scores into the next token.

## For a Software Engineer
This is a codec plus a categorical draw. The tokenizer is the encoder: a deterministic, many-to-one mapping from bytes to a list of integer IDs. The embedding table is a lookup: each ID becomes a vector the network can compute with — the same idea as an enum mapped to a learned feature vector, not a magic meaning-space you can eyeball. The last layer of the network emits one number per vocabulary item (logits). Softmax is the function that turns those numbers into a probability distribution that sums to 1. Temperature divides the logits *before* softmax. It does not add knowledge, remove knowledge, or "make the model think harder."

The number worth feeling: English prose is often about 0.7 to 0.8 tokens per word for common OpenAI-style tokenizers, but code, URLs, and rare identifiers run much hotter — a long `getUserByEmailAndTenantId` can be many tokens, and a JSON blob of UUIDs is a cost trap. Temperature 0 is greedy decoding (always pick the top logit). Temperature 1 is "use the softmax as-is." Above 1 the distribution flattens; below 1 it sharpens. None of those values is "smarter."

Monday-morning action: for anything you need to be stable (SQL, config, a structured patch, a grader), drive temperature to 0 or near it *and* constrain the output (schema, enum, tests). For brainstorming, raise it — and expect variance. Never use word count as a cost estimate; count tokens with the model's tokenizer.

## What This Means for You
**When this matters**: you are setting `temperature` on an API call, estimating context cost, or debugging why two runs of the same prompt disagreed.

**How it affects you**: tokens are what you pay for and what fills the context window. Sampling is why a coding agent can take a different path on the same request. Embeddings are why "similar" in retrieval is a vector-distance problem, not a string-match problem. If you confuse these, you will tune the wrong knob — raising temperature to "fix" a missing file, or stuffing more words into a prompt that is already over the token budget.

**What to do about it**: look up the tokenizer for the model you actually call (they are not interchangeable). Log `prompt_tokens` and `completion_tokens` from the API rather than guessing. Pick a temperature policy per *task*, not per "how creative I feel today": 0 for extract / classify / generate code against a spec, something in the 0.3–0.8 range for writing, and treat anything above 1 as an explicit experiment. If you need diversity, sample several times at a moderate temperature rather than cranking one request to 1.5.

## What It Is
A tokenizer splits text into tokens from a fixed vocabulary, then maps each token to an integer ID. Modern language-model tokenizers are usually a form of byte-pair encoding: start from bytes (or characters), repeatedly merge the most common adjacent pairs, and stop when you have a vocabulary of the size you want. The same text always becomes the same IDs for a given tokenizer. Different vendors' tokenizers will cut the same string differently.

Those IDs index an embedding table: a matrix of size `vocab_size × hidden_size`. Row 15496 is "the vector for whatever token has ID 15496." The transformer then mixes those vectors across positions (the last chapter). At the end you get a vector the size of the vocabulary — one logit per possible next token.

Sampling is the last mile. Softmax turns logits `z` into probabilities `softmax(z / T)`, where `T` is temperature. You then draw from that categorical distribution (or take the argmax if you want greedy). Nucleus (top-p) and top-k are extra filters: ignore the long tail before you draw, so you do not sample a token the model barely believes in.

## Why It Matters
Cost, latency, and reproducibility all sit on this stack.

You are billed per token, not per word and not per character. A prompt that looks short in the editor can be expensive if it is full of punctuation-heavy code. A "small" system prompt that you send on every request is a tax you pay on every turn.

Latency is sequential on the output side. The model can read a long prompt in a parallel prefill, but it emits completion tokens one by one. A 2,000-token reply is about 2,000 serial steps. Temperature does not change that. `max_tokens` does.

Reproducibility is a sampling question. Temperature 0 plus a deterministic serving stack is as close as you get to a stable function. Temperature 0.7 is a distribution. Logging only the prompt and not the temperature, seed, or sampler settings is how two "identical" evals disagree.

Embeddings matter outside generation too. Retrieval-augmented generation embeds a query and a pile of chunks into the same vector space and pulls nearest neighbors. That is a different use of "embedding" than the model's input table, but the idea is the same: discrete tokens or texts become vectors so distance is defined.

## Key Technical Details

**Background first.** A *token* is one item from the model's vocabulary. An *embedding* is a vector standing in for a token (or a whole string, in retrieval). *Logits* are the raw next-token scores. *Softmax* is the standard way to turn a vector of scores into a probability distribution: exponentiate each score, then divide by the sum, so everything is positive and adds to 1. *Temperature* is a positive number you divide the logits by before softmax. *Sampling* is drawing a token from that distribution instead of always taking the maximum.

- **Tokenizers are codecs, not linguists.** `"hello world"` might be two tokens. `"unbelievable"` might be three. A space before a word is often part of the token (`" world"` ≠ `"world"`), which is why sloppy string concatenation changes tokenization and can change the model's next guess.
- **Byte-pair encoding builds a vocabulary from frequency.** It is the same instinct as a compression dictionary: common pairs get their own symbol. That is why English common words are cheap and novel identifiers are expensive.
- **The embedding table is a learned lookup.** Training moves those vectors so that tokens which appear in similar contexts end up with vectors the rest of the network can use. You almost never inspect them directly in application code; you just know that IDs go in and contextual vectors come out.
- **Softmax is not optional if you want a distribution.** Logits can be any real numbers, including negative. Softmax makes them comparable as probabilities. The *relative* gaps between logits decide how peaked the distribution is.
- **Temperature rescales those gaps.** `T < 1` stretches gaps (the winner wins by more). `T > 1` shrinks gaps (runners-up get more mass). As `T` goes to 0 you approach greedy. As `T` goes to infinity you approach uniform. There is no temperature that adds a fact the logits did not already encode.
- **Top-k and top-p clip the tail.** Top-k keeps the k highest logits. Top-p (nucleus) keeps the smallest set of tokens whose probabilities sum to p (often 0.9–0.95). Both exist because a huge vocabulary has a long, noisy tail; sampling from it produces garbage tokens. Many APIs combine a moderate temperature with a nucleus cutoff.
- **Greedy is stable, not necessarily correct.** The top token is the model's mode, not the truth. For code, greedy plus tests is usually better than a high-temperature "creative" patch. For naming a variable, a little noise can help. Match the sampler to the loss you actually care about.

## How It Connects to What You Know
A tokenizer is `encode` / `decode` on a wire format — like protobuf field IDs, not like `str.split()`. An embedding table is an enum-to-vector map, closer to a learned `nn.Embedding` than to a thesaurus. Softmax-plus-temperature is the same shape as a Boltzmann distribution or as `exp(score / T)` in a softmax classifier you have already written. Sampling is `random.choices(population, weights)`.

This page is a chapter in the Learn track. The previous chapter established that the model only picks the next token; this one is what a token is and how that pick is drawn. The daily lab is the case-study feed — later dated posts about context cost, tokenizer mismatches, or a new serving sampler are applications of this chapter, not a replacement for it.

## Try It Yourself
`code_example.py` implements a tiny byte-pair tokenizer on a short corpus, embeds tokens as small vectors you can print, then takes a fixed vector of logits and shows softmax at several temperatures. It samples the same logits twenty times at T=0.2 and T=1.2 so you can see a knob, not a personality: the scores never change, only the dice do.

## Glossary
- **Token** — a vocabulary item the model reads or writes; the billing and context unit.
- **Tokenizer** — the program that cuts text into tokens and maps them to integer IDs (and back).
- **BPE** (Byte-Pair Encoding) — a tokenizer that starts from bytes or characters and merges frequent pairs into longer tokens.
- **Vocabulary** — the fixed list of tokens, typically tens or hundreds of thousands of entries.
- **Embedding** — a vector used as the numeric stand-in for a token (inside the model) or a string (in retrieval).
- **Hidden size** — the width of those vectors; a model hyperparameter, not something you set per request.
- **Logits** — raw next-token scores, one per vocabulary item, not yet probabilities.
- **Softmax** — the function that turns a vector of scores into a probability distribution that sums to 1.
- **Temperature** — a positive scalar that divides logits before softmax; lower is peakier, higher is flatter.
- **Sampling** — drawing the next token from the probability distribution instead of always taking the top score.
- **Greedy decoding** — always picking the highest-probability next token; the T → 0 limit.
- **Top-k** — keep only the k highest-scoring tokens before sampling.
- **Top-p / nucleus** — keep the smallest set of tokens whose probabilities add up to p, then sample.
- **Prefill** — the parallel pass that reads the prompt; distinct from the serial loop that emits new tokens.
- **SQL** — a structured query language; a task where you usually want greedy, low-temperature decoding so column names do not wander.
- **UUID** — a long unique identifier; tokenizes into many pieces and is a common cost trap in JSON blobs.
- **JSON** — a structured text format; punctuation-heavy, so token count is often higher than it looks.
- **CI** (Continuous Integration) — the pipeline where you can count tokens with the model's tokenizer without guessing.
