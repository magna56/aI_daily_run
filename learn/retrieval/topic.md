# How retrieval works

**Category**: Hands-on Techniques
**Tags**: rag, embeddings
**Date**: 2026-08-23
**Level**: Start here
**For**: Shipping AI
**Hook**: Retrieval is cut the docs, find the nearest pieces, and paste them into the prompt.
**Kind**: Learn
**Time to read**: ~10 minutes

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

## How It Connects to What You Know

This is search, then a template. Lucene + a mail merge. The vector index is another posting list.

Previous: [What a skill is](#learn/skills). Next: [Context and the harness](#learn/context-and-harness).

Lab: [Nobody re-tests their RAG chunk size](#2026-08-23).

## Try It Yourself

`code_example.py` chunks a tiny handbook, embeds with a toy vector, retrieves `top_k`, and prints how much text you would stuff — so you can see padding without a vendor.

## Glossary

- **RAG** — retrieval-augmented generation: retrieve text, then generate with it in the prompt.
- **Chunk** — one slice of a document you store and retrieve.
- **Embedding** — a vector for a chunk or a question.
- **top_k** — how many chunks you paste.
- **Context recall** — whether the retrieved text contained the answer.
- **Stuff** — concatenate retrieved chunks into the prompt.
