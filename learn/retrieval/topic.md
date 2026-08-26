# How Retrieval Works

**Category**: Hands-on Techniques
**Tags**: rag, embeddings
**Date**: 2026-08-23
**Level**: Start here
**For**: Shipping AI
**Hook**: Retrieval is cut the docs, find the nearest pieces, and paste them into the prompt.
**Kind**: Learn
**Time to read**: ~12 minutes

> **You'll be able to:** explain retrieval as three plain steps instead of a product, know when you actually need it versus when you should just paste the file, and read a chunk-size sweep instead of guessing at one.

## Explain Like I'm 5

You cannot carry the whole library to the table. You tear chapters into index cards, write a short hint on each, and when someone asks a question you grab the few cards whose hints match, stack them next to the question, and only then ask your well-read friend. If you grabbed the wrong cards, the friend still sounds sure — they are just finishing a sentence about the wrong chapter.

## The Problem

"RAG" gets sold as a product — a vector database, a framework, a platform — before anyone writes down the three steps. Teams then debug "the model hallucinated" when the right paragraph was never in the stack, or it was in the stack under eight other chunks that drowned it. You cannot tune what you think is magic.

## For a Software Engineer

This is an index plus a prompt template. **Chunk** the docs. **Retrieve** the nearest chunks for the question. **Stuff** them into the prefix and ask. The database is an index, not the idea. You can do the same job with an in-memory list and a dot product.

The number worth feeling: the daily lab on 2026-08-23 ran a labeled sweep and found a naive `chunk_size=250`, `top_k=8` sent **1,367 words** of context to match the quality of a tuned `150` / overlap / `top_k=3` that sent **165** — same recall, 88% less text. The extra words were not extra answers. They were the same answer repeated inside larger slices.

Monday morning: write 20 questions whose answers live in your docs. Sweep chunk size, overlap, and `top_k` against `context_recall` (did the chunk contain the answer?) before you buy a reranker. If you have never scored retrieval without generating an answer, you do not know whether your context bill is buying anything.

## What This Means for You

**When this matters**: you have a chatbot over internal docs, or you are about to add "memory" by pasting search results into a prompt.

**How it affects you**: generation quality cannot beat retrieval quality. A fluent wrong answer usually means the right card never made the stack — or ten wrong cards did.

**What to do about it**: pick a chunk that holds one idea (a section, not a sentence and not a chapter), retrieve a small `k`, paste with clear separators. Then measure. The 2026-08-23 session is the lab for the sweep.

## What It Is

**Chunk.** Cut documents into overlapping windows. Too small and you lose the sentence that made the paragraph true. Too large and you retrieve the same fact wrapped in padding. Overlap is so a sentence on a boundary is not split in half with no home.

**Retrieve.** Embed the question the same way you embedded chunks. Rank by cosine (or whatever your index uses). Keep top `k`. Hybrid search (keywords + vectors) is allowed. It is still "find the cards."

**Stuff.** Put the chunks in the prompt with source tags. Ask the model to answer only from them, and to say when they are not enough. That instruction is a spec (lesson 3). It is not a guarantee — it is a prefix that makes "I don't know" more likely than a confident guess.

A vector database is a nearest-neighbor index you do not have to write. It does not "understand" your docs.

## Why It Matters

Most RAG failures are retrieval failures labeled as model failures. Chunk size set once in week one is a hyperparameter you never re-ran (the 2026-08-23 write-up). `top_k=8` on large chunks is how you spend a thousand tokens repeating one sentence. Getting this lesson straight is what makes that lab useful instead of folklore.

## Key Technical Details

**Background first.** An *embedding* is a vector for a string. *Cosine similarity* is the usual stand-in for "near." *`top_k`* is how many records you paste. *Context recall* is "was the answer in the retrieved text?" — you can compute it with labels, no LLM judge.

- **Chunk by structure if you can.** Headings beat a blind 512-token window.
- **`k` is not knowledge.** `k=1` is brittle. `k=8` on fat chunks is padding. The 2026-08-23 sweep held quality at `k=3` with smaller chunks.
- **Stuffing is just a string.** Separators, titles, and "use only these sources" are prompt engineering (lesson 3) on top of an index.
- **If retrieve is empty, say so.** A fallback that "just asks the model" is how you ship confident fiction.

## When You Actually Need It

Retrieval solves exactly one problem: too many documents to fit in context. Below that point it is pure overhead — an index, an embedding step, a failure mode (empty results) that pasting never has.

```
Fits in context — skip retrieval:
  1 file          → just paste it in
  10 files        → paste them all in
  100 files       → often still fits

Does not fit — retrieval earns its cost:
  100,000 files   → you need to find the relevant 5
  a whole corpus  → retrieval is not optional anymore
```

"RAG" names the *pattern* — retrieve, then generate with what you found — not one specific implementation. A link graph, a keyword index, and a vector database are all valid ways to do the retrieving; the model never touches any of them directly. Retrieval is infrastructure you build around the model, to solve a context-fit problem, not a capability the model has on its own.

## Quick Reference

| Term | Plain English |
|---|---|
| RAG | Retrieval-augmented generation: retrieve text, then generate with it in the prompt. |
| Chunk | One slice of a document, stored and retrieved as a unit. |
| Embedding | A vector for a chunk or a question; nearness approximates meaning. |
| Cosine similarity | The usual stand-in for "how near two embeddings are." |
| `top_k` | How many chunks you paste into the prompt. |
| Context recall | Whether the retrieved text actually contained the answer. Computable with labels, no judge model needed. |
| Stuff | Concatenate the retrieved chunks into the prompt, with source tags. |
| Hybrid search | Keywords plus vectors in the same retrieval step. |

## Do It Today

**Step 1 — watch a chunk size lose the answer, 2 minutes.**

```bash
python3 learn/retrieval/code_example.py
```

It chunks a tiny handbook at several sizes, retrieves `top_k`, and prints a hit/miss table plus the exact stuffed prompt. **You know it worked** when `chunk_size=8` misses at every `top_k` because the fact is split across slices, `chunk_size=20, top_k=2` hits with **36 words** and no padding, and `chunk_size=40, top_k=2` also hits but at **63 words** — the same fact, wrapped in more text for no gain.

**Step 2 — read the stuffed prompt at the bottom of the output.** That block, source tags and all, is the entire mechanism. There is no step where the model "searches" — it reads a string exactly like this one, assembled before it ever sees the question.

**Step 3 — write 20 questions whose answers live in your own docs**, and sweep chunk size, overlap, and `top_k` against context recall before you reach for a reranker or a bigger `top_k`. The [2026-08-23 daily lab](#2026-08-23) is the full version of this sweep: a tuned `150`/overlap/`top_k=3` matched a naive `250`/`top_k=8` at **165 words instead of 1,367** — 88% less text for the same recall.

## Gotchas

- **`k` is not knowledge.** `k=1` is brittle; `k=8` on fat chunks is padding, not safety margin.
- **A vector database does not understand your docs.** It is a nearest-neighbor index. The understanding, such as it is, happens when the model reads the stuffed prompt.
- **Chunk by structure when you can.** Headings and sections beat a blind fixed-token window — a window that splits a sentence in half loses the fact that made the paragraph true.
- **Empty retrieval needs to say so.** A fallback that "just asks the model anyway" is how confident fiction ships instead of "I don't know."
- **"We should add RAG" often means "we should just paste the file."** Check the fits-in-context table above before building an index for ten documents.

## How It Connects to What You Know

This is search, then a template. Lucene plus a mail merge. The vector index is another posting list, and "stuff the prompt" is string concatenation with source tags on it.

Previous: [How Skills Work](#learn/skills). Next: [How the Chat Is Re-Read Every Turn](#learn/context-and-harness).

Lab: [Nobody re-tests their RAG chunk size](#2026-08-23).
