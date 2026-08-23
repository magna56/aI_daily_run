# What an LLM does

**Category**: New Models & APIs
**Tags**: transformers, training
**Date**: 2026-08-23
**Level**: Start here
**For**: How models work
**Hook**: A language model only ever picks the next word. Training teaches it which pick looks right.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

You have a friend who has read a huge pile of books, but they can only ever say one word at a time. You start a sentence. They guess the next word. You add that word. They guess again. They are not looking up an answer in a filing cabinet. They are playing "finish this sentence" very, very well. Teachers later sat with them and said "that reply was better than this one," so their guesses started sounding like a helpful coworker instead of a random page from the internet.

## The Problem

Most of us meet these models as a chat box that "answers questions." That story hides the machine. If you think it is a search engine, you will be shocked when it invents a function your repo does not have. If you think it is a planner with a secret inner monologue, you will be shocked when it agrees with a wrong premise and then writes three confident paragraphs about it. The machine is narrower than the product: it scores the next piece of text, picks one, and repeats.

## For a Software Engineer

This is autocomplete taken to an extreme — the same job as your phone keyboard, with a much longer prefix and a much larger guess list. There is no second engine under the words at runtime. A 400-word answer is roughly 400 of those picks (often more, because pieces of words count too). If a fact was rare or missing in training, the model still has to pick *something*. Fluency is cheap. Correctness is a different loss.

The number worth feeling: after all the training drama, serving still does one thing. Pretraining, supervised fine-tuning, and preference training change *which* token is likely. They do not change the loop. Monday morning: when an output is bad, ask "what prefix made this next token likely?" before "why doesn't it understand?" A missing file, a vague spec, or a contradictory earlier sentence is a prefix problem.

## What This Means for You

**When this matters**: you are about to trust a generated answer, write a prompt, or decide whether a coding agent "knows" your codebase.

**How it affects you**: the model does not retrieve a stored answer. It generates a continuation. That is why it can write a plausible API that does not exist, flip a boolean and keep going, and change its mind when you add one file to the prompt.

**What to do about it**: treat the prompt plus the files you attach as the only state it has. Put the constraint in the prefix ("do not invent endpoints; if the handler is missing, say so"). Prefer an agent that can read the repo over a paste box. When someone says "the model was trained to…", map that to one of the three stages below.

## What It Is

Given the tokens so far, the network scores every item in a fixed vocabulary. Sampling turns those scores into the next token. The token is appended. The network runs again. That is the runtime.

ChatGPT, Claude, Gemini, a local Llama — same loop, plus a tokenizer, a context window, and a serving stack. The helpful voice is not native. A base model trained only on internet text will continue a Stack Overflow thread or a rant, whichever the prefix looks like. Later stages paint on the assistant.

The architecture that made this scale is the transformer: every position can use earlier positions, so the guess for token 200 can see tokens 1–199. You do not need the matrix math to use the product. You do need the implication: there is no scratchpad unless the model *writes* one into the token stream, and there is no memory of last Tuesday unless that text is in this request.

## Why It Matters

Three product mysteries stop being mysteries.

Fluency is the pretraining objective. "Looks like a good answer" and "is a good answer" are different. That is why a model can write a beautiful, wrong unit test.

The assistant personality is trained on later. Same architecture, different checkpoint: raw completer vs product chatbot.

"The model knows how to use tools" is usually example data in fine-tuning, not a hidden runtime. If your tool names do not match the ones in that data, the next-token guesses get worse. Lesson 8 is that trap.

## Key Technical Details

**Background first.** A *token* is a chunk of text the model can emit — a word, a piece of a word, or punctuation. The *vocabulary* is the fixed list of those chunks. *Logits* are the raw scores before they become probabilities. *Pretraining* predicts the next token on a huge unlabeled corpus. *Supervised fine-tuning* (SFT) trains on (prompt, ideal reply) pairs. *RLHF* and nearby methods take ranked pairs and push the model toward the preferred reply.

- **Inference is pick, append, repeat.** Nothing checks the answer unless a product team added a tool, a linter, or a verifier *outside* the model.
- **Pretraining is compression plus prediction.** A base checkpoint completes text. It is not trying to be useful.
- **SFT is the format change.** Probability mass shifts from "continue the user's sentence" to "start a helpful reply." Tool-call examples live here too.
- **Preference training is the taste change.** SFT shows one "right" reply. Humans often disagree. Pairwise ranking is how refusals, hedges, and tone get into the weights.
- **Context is the working set.** Tokens that do not fit are not there. A coding agent that "remembers" your repo is re-reading files into the window.

## How It Connects to What You Know

A compiler emits the next valid construct according to an exact grammar. This model emits the next *likely* construct according to a statistical one. IDE autocomplete is the same job at 20 candidates; this is autocomplete with a 100,000-wide list and a longer prefix.

Next: [How tokens and sampling work](#learn/tokens-and-sampling).

## Try It Yourself

`code_example.py` builds a tiny next-token table from a handful of sentences — no neural net, no API. It applies the three stages as data operations and prints the distribution after each one, so you can see the same pick-the-next-token machine become a completer, then an assistant, then a preferred tone.

## Glossary

- **Token** — a chunk of text the model reads and writes. Lesson 2 is how text is cut.
- **Vocabulary** — the fixed list of tokens it is allowed to emit.
- **Next-token prediction** — the only job at runtime: score every vocabulary item and pick one.
- **Logits** — raw scores, before probabilities.
- **Context window** — the maximum tokens in one request (prompt plus reply so far).
- **Transformer** — the architecture: each position can use earlier positions.
- **Base model** — trained mostly on unlabeled text; completes, does not assist.
- **Pretraining** — first stage: next-token prediction on a huge corpus.
- **SFT** — supervised fine-tuning on (prompt, reply) pairs.
- **RLHF** — preference training from human (or stand-in) rankings.
- **DPO** — a preference method that skips a separate reward-model loop.
