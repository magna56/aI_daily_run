# A Chat Reply Is a Stack of Tiny Next-Token Guesses

**Category**: New Models & APIs
**Tags**: from-scratch, transformers, training
**Date**: 2026-08-23
**Level**: Building
**For**: How models work
**Hook**: Tokenize, look back, mix, score the next piece — that stack is the whole model.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

You cut a sentence into fridge magnets. Each magnet looks at the magnets before it, mixes what it sees, and votes for the next magnet. You stick that magnet on the fridge and vote again. A long reply is just that vote, many times. Nobody in the pile is "thinking about your question" as a separate job.

## The Problem

Product screens hide the stack. You type a question; a paragraph appears. That makes people invent a second machine — a planner, a database, a soul — under the text. When you build even a tiny language model, the second machine fails to appear. There is a tokenizer, a table of vectors, a few blocks of attention plus a small MLP, a linear map to vocabulary scores, and a sampler. Chat is that loop with a prettier prefix.

## For a Software Engineer

The forward pass is a pipeline you could draw on a whiteboard:

1. Tokenizer: string → token ids.
2. Embedding: id → vector.
3. `N` blocks: self-attention (mix) then MLP (per-token think), plus residuals and layer norm.
4. Unembed: last vector → logits over the vocabulary.
5. Sample: pick an id, append, repeat.

Training is the same pipeline plus a loss: predict the next id. Chat fine-tuning changes the data, not the verbs. Tool use is tokens that a harness parses. There is no side channel.

Monday morning: when an output is wrong, ask which stage failed. Bad tokenize (you split an identifier). Bad prefix (the prompt contradicts itself). Bad sample (temperature turned a rare token into a sure one). Bad data (the stack never saw that API). The stack itself is rarely "broken."

## What This Means for You

**When this matters**: you want to know what you are calling when you hit an API, or you are about to train a toy model to learn the shape.

**How it affects you**: every product feature — tools, memory, RAG — is extra text or extra code *around* this stack. If you expect the stack to grow a new verb by itself, you will wait forever.

**What to do about it**: read one tiny implementation (this folder's code, or nanoGPT). Trace one token. Then look at your production prompt and name which stage you are actually trying to change.

## What It Is

A decoder-only language model is a next-token classifier with shared weights across time. "Build an LLM" in this primer means: stand up the five stages on a toy vocabulary and watch a string come out. It does not mean "reproduce GPT-4." The industrial versions add kernels, parallelism, and a lot more `N`. The verbs stay.

Two flavors you will meet: a *base* model trained to continue internet text, and a *chat* model trained on (prompt, reply) pairs so it starts answers like an assistant. Same stack. Different data.

## Why It Matters

You cannot debug a ghost. Once the stack is real, "the model refused" is a sampled token sequence. "The model used a tool" is a token sequence your harness recognized. "The model remembered" is text you put back in the window.

This is also why training from scratch is almost never the Monday job. The stack is easy to write and expensive to feed. Use a pretrained checkpoint; change the prefix, the adapter, or the data.

## Key Technical Details

**Background first.** A *residual* adds the block's input to its output so gradients have a highway. *Layer norm* keeps the vectors from drifting. *MLP* is usually two linears with a nonlinearity in the middle.

- **The loss is next-id classification.** Cross-entropy on the shifted sequence.
- **Depth is more blocks, not a new machine.** `N = 2` and `N = 96` are the same diagram.
- **Context is the working set.** Tokens that do not fit are not in the mix.
- **Sampling is not training.** Temperature and top-p do not add facts.
- **Chat is data.** The special tokens and the turn format are part of the prefix.

## How It Connects to What You Know

A compiler frontend is tokenize → parse → IR → emit. This stack is tokenize → mix → classify next → emit, looping. An interpreter's eval loop is the closer cousin: one step, append, again. You do not look for a second interpreter inside `eval`.

Next: [The loop is cheap; serving is the job](#learn/agents-in-prod) — wrapping this stack in tools and a bill.

## Try It Yourself

`code_example.py` trains a two-layer toy model on a handful of sentences (pure Python, no framework) and prints the next-token table before and after a few steps, then samples a short continuation.

## Glossary

- **Tokenizer** — cuts text into ids the table knows.
- **Embedding** — id to vector.
- **Block** — attention plus MLP, with residual and norm.
- **Logits** — vocabulary scores before sampling.
- **Base model** — trained to continue text, not to assist.
- **Chat model** — same stack, trained on conversational pairs.
