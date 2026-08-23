# RAG Without Mystique — Chunk, Retrieve, Stuff the Prompt

**Category**: Hands-on Techniques
**Tags**: rag, embeddings
**Date**: 2026-08-23
**Level**: Start here
**For**: Shipping AI
**Hook**: Retrieval is cut the docs, find the nearest pieces, and paste them into the prompt.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5
Imagine a friend who has never been in your library. You cannot send them the whole building, so you tear each book into pages and pin pages that talk about the same thing near each other on a wall. When a question arrives, you walk to the closest pins, pull those pages down, staple them to the question, and hand the stack over. Your friend does not search. They only read whatever you stapled. If you tore the pages too small, the answer is split and they miss it. If you tore them too big, they get the answer buried under a chapter they did not need.

## The Problem
"RAG" gets sold as a product — a vector database, a framework, a platform — before anyone writes down the three steps. Teams then debug "the model hallucinated" when the real bug is that the right paragraph was never in the stapled stack, or it was in the stack along with eight other chunks that drowned it. The mystique is expensive: you cannot tune what you think is magic.

## For a Software Engineer
This is **search plus string concatenation**. You already know the pieces. Chunking is splitting a log into records. An embedding is a lossy hash that preserves neighborhood: similar meanings land nearby in a vector space, the way similar documents land nearby in a search index. `top_k` is `LIMIT`. Stuffing the prompt is rendering a template: `system + retrieved_chunks + user_question`. There is no hidden retrieval API inside the model. If a chunk is not in the string you sent, the model cannot cite it.

The surprising number is how much of that string is usually padding. The daily case study from 2026-08-23 ran a labeled sweep and found a naive `chunk_size=250`, `top_k=8` sent **1,367 words** of context to match the quality of a tuned `150` / `30%` overlap / `top_k=3` that sent **165** — same recall, 88% less text. The extra words were not extra answers. They were the same answer repeated inside larger slices.

Monday-morning action: print the exact prompt your pipeline sends. If you cannot point at the concatenated chunks, you do not have RAG yet. You have a framework.

## What This Means for You
**When this matters**: you are adding "chat with our docs," or answers went vague after you raised `top_k`, or you have never printed the stuffed prompt.

**How it affects you**: every retrieved word is a word the model must read, pay for, and can get distracted by. A wrong chunk size misses the answer or buries it. A high `top_k` feels safer and often makes the answer worse.

**What to do about it**: pick a chunk size that holds one idea (a section, not a sentence and not a chapter), retrieve a small `top_k`, and paste those chunks into the prompt with clear separators. Then measure — the 2026-08-23 session is the next page: grid-search `chunk_size` / overlap / `top_k` against a labeled set before you buy another retrieval feature.

## What It Is
Retrieval-augmented generation is three verbs.

**Chunk.** Cut each document into overlapping windows. `chunk_size` is how many words (or tokens) per window. Overlap is how many words neighboring windows share, so a sentence that sits on a cut is not lost. Each chunk becomes one retrievable record.

**Retrieve.** Turn the question into the same kind of vector you used for chunks — an embedding. Rank chunks by similarity (cosine is the usual stand-in). Keep the top `k`. You can do this with a vector database, or with an in-memory list and a dot product. The database is an index, not the idea.

**Stuff.** Concatenate the winning chunks into the prompt. A typical shape is: instructions, then a `Context` block of chunk text, then the user question. The generator is an ordinary completion. It does not "know" it retrieved anything. It reads a string.

That is the whole pipeline. Rerankers, query expansion, and contextual embeddings are extras you add *after* this loop is visible and measurable.

A useful debugging habit: save the stuffed prompt for any bad answer. You will sort failures into three buckets in about a minute. *Miss* — the answer sentence is not in the stack, so no generator can cite it. *Padding* — the sentence is there, buried under neighbors, and the model latched onto the wrong neighbor. *Stale* — the chunk is from an old version of the doc. None of those is "the model hallucinated" in the interesting sense. They are indexer bugs you can see because stuffing is just a string.

## Why It Matters
You do not need to fine-tune a model on your wiki to answer questions about your wiki. You need the right paragraphs in the prompt. That is why RAG won: it is deployable by an application team, it updates when the documents update, and its failures are inspectable — look at the chunks.

It also explains the characteristic bugs. Hallucination after retrieval usually means the stack was empty, stale, or padded. Raising `top_k` to "be safe" is how you recreate the problem RAG was meant to solve: too much irrelevant text. Shrinking chunks until no window holds a complete fact is how you retrieve a true fragment that cannot answer the question.

## Key Technical Details
**Background first.** An *embedding* is a list of numbers that represents a piece of text. Training an embedding model is out of scope here; using one is "text in, vector out." *Cosine similarity* is the angle between two vectors: 1 means they point the same way, 0 means they are unrelated. *Stuffing* means concatenation — there is no second channel. The model sees one token stream.

- **Chunk size is the record size.** Too small and a fact is split across records, so the nearest chunk is a fragment. Too large and one record mixes topics, so a match on the wrong half still drags in the rest. Start near a section (100–300 words) and measure; do not copy a blog's 512-token default.
- **Overlap exists for cut points.** If a sentence spans two chunks and overlap is zero, whichever side the retriever misses loses the sentence. 10–30% is the usual band. Overlap is not free: it duplicates words into the index and, if both neighbors retrieve, into the prompt.
- **`top_k` is how many records you paste.** `k=1` is brittle. `k=8` on large chunks is how you spend a thousand words to repeat the same sentence. The 2026-08-23 sweep kept quality at `k=3` with smaller chunks. More `k` is not more knowledge — it is a longer string.
- **The prompt is just concatenated context.** A useful separator is a heading plus source id (`## docs/billing.md #chunk-4`) so the model can cite, and so you can see what it saw. If your framework hides this string, log it.
- **Embeddings rank neighborhood, not truth.** "Refund window" and "return policy" should land nearby. They can also rank a marketing page above the contract clause. That is a retrieval miss, not a generation bug. Fix the index or the query before you blame the model.
- **Keyword search still counts.** BM25 on the same chunks is a valid retriever. Many production stacks blend lexical and vector scores. RAG does not require a neural embedding — it requires a ranked list you then stuff.
- **Ids on chunks are for you, not the model.** `billing.md#chunk-0` in the stuffed prompt lets you jump from a wrong answer back to the record that caused it. If your pipeline stores chunks as anonymous UUIDs and never prints them, you have given up the only cheap eval you have: "was the answer in the string?"
- **This session's retriever is a bag of words.** Cosine over term counts is enough to watch a fact fall out of a too-small window and reappear when the window grows. A hosted embedding model changes the ranking, not the three verbs. Do not wait on an API to understand stuffing.

## How It Connects to What You Know
This is the same shape as a search microservice: index documents, query, take the top hits, render an HTML snippet. The generator is the template renderer with opinions. Caching, pagination, and "don't send the whole table to the client" all apply — the client here is the model's context window.

The daily lab on 2026-08-23 (*Nobody Re-Tests Their RAG Chunk Size*) is the measurement half of this lesson. This page is why those three knobs exist. That page is what happens when you actually sweep them: same recall, 88% less context. Read this first if the knobs felt like folklore; read that next if you already ship a pipeline and have never scored it.

## Try It Yourself
`code_example.py` chunks two short documents, embeds each chunk with a bag-of-words vector (no API), ranks a question by cosine similarity, and prints the *exact* stuffed prompt for several `chunk_size` × `top_k` pairs. You will see a small chunk miss the answer, a medium chunk catch it, and a large `top_k` bury it in extra words. Pure Python, no network.

## Glossary
- **RAG** (Retrieval-Augmented Generation) — fetch relevant text first, then generate an answer from the prompt you built.
- **Chunk** — one slice of a document stored as a retrievable record.
- **Chunk size** — how large each slice is, usually in words or tokens. It decides whether a fact fits in one record.
- **Overlap** — words shared by neighboring chunks so a cut does not drop a sentence.
- **Embedding** — a vector that represents a piece of text so similar meanings are nearby.
- **Cosine similarity** — a score from the angle between two embeddings; higher means closer.
- **top-k** — how many highest-scoring chunks get pasted into the prompt.
- **Stuffing** — concatenating retrieved text into the prompt. The model just reads the string.
- **BM25** — a keyword ranking function. A retriever does not have to be neural.
- **Context window** — the maximum tokens the model can read in one request. Retrieved chunks spend that budget.
