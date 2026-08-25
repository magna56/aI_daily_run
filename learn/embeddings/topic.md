# How Embeddings Work

**Category**: Hands-on Techniques
**Tags**: embeddings, rag
**Date**: 2026-08-23
**Level**: Start here
**For**: Shipping AI
**Hook**: Text becomes a point in space; nearby points are the ones you retrieve.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

You put every sentence on a map. Sentences about refunds sit near other refund sentences. Sentences about passwords sit somewhere else. When a customer asks about money back, you walk to that neighborhood and read the street signs. You did not "understand" the question. You measured who lives nearby.

## The Problem

Search used to be words in common. That fails when the user says "undo the charge" and the doc says "refund window." Embeddings turn each chunk into a list of numbers so "nearby" means "similar use," not "same string." Teams then treat the vector database as magic and never look at who actually got retrieved. The Monday bug is almost always "the nearest neighbors are the wrong neighbors," not "the model cannot read."

## For a Software Engineer

An embedding model is a function `text → R^d`. You store the vectors. At query time you embed the question and take cosine similarity (or dot product if you normalized). Top-k are the chunks you stuff into the prompt.

Pooling is how a sequence of token vectors becomes one vector: mean of tokens, or the last token, or a special pooler. Bi-encoders embed query and doc separately so you can index docs offline. Cross-encoders read the pair together and are too slow to scan a million rows — use them to rerank the shortlist.

Monday morning: print the top-5 chunks for five real questions before you tune the generator. If the answer is not in those chunks, no prompt will save you.

## What This Means for You

**When this matters**: you are wiring RAG, semantic search, or "find similar tickets."

**How it affects you**: a pretty chat answer can cite the wrong paragraph. Distance in embedding space is the retrieval decision. Chunk size, overlap, and which model you embed with change that space.

**What to do about it**: lock an embedding model. Measure recall of the gold span. Do not swap models because a blog said so. Normalize vectors if you use cosine. Keep a tiny fixture set of queries and expected chunk ids in CI.

## What It Is

Embeddings are neighborhood-preserving vectors. Training pulls related texts together and pushes unrelated ones apart. The geometry is the product. There is no hidden English inside the 1024 numbers — only directions that happened to be useful for the contrastive (or next-token) objective the vendor used.

A chat model's last-layer state is an embedding too, but it was trained to predict the next token, not to be a document index. Dedicated embedding models usually win at retrieval. Do not casually embed docs with a generative checkpoint unless you measured it.

## Why It Matters

This is the first half of RAG. Generation cannot use a fact that never entered the window. It is also why "we added a vector database" changes nothing if the chunks are two pages long or the query is a different dialect than the corpus.

Cost hides here: embedding a corpus is a batch job; embedding every query is a live tax. Cache query embeddings when the same search repeats.

## Key Technical Details

**Background first.** *Cosine similarity* is the cosine of the angle; 1 is identical direction. *Normalize* means divide by the vector length so cosine equals a dot product.

- **Index offline, query online.** Re-embed the corpus when the model or the docs change.
- **Pooling is a choice.** Mean vs last-token changes neighbors.
- **Bi-encoder for retrieve, cross-encoder for rerank.** Do not run the slow one on the whole corpus.
- **Same model both sides.** Mixing vendors' vectors is mixing units.
- **Nearest ≠ relevant.** Measure recall. Then argue about prompts.

## How It Connects to What You Know

A hash table is exact match. An embedding index is nearest-neighbor search — the same family as "find similar images" and "users also bought." You already distrust a fuzzy search that you never fixture-tested. This is that, with more dimensions.

Next: [How to Build a Tiny LLM](#learn/build-an-llm) — what happens after the neighbors land in the prompt.

## Try It Yourself

`code_example.py` embeds a handful of sentences with bag-of-words vectors (no API), ranks them by cosine against a query, and shows how a paraphrase still wins while a shared stopword loses.

## Glossary

- **Embedding** — a vector that stands in for a piece of text.
- **Cosine similarity** — how aligned two vectors are; common retrieve score.
- **Bi-encoder** — embed query and doc in separate forwards.
- **Cross-encoder** — score a (query, doc) pair together; rerank, not scan.
- **Pooling** — collapse token vectors into one vector.
- **Top-k** — the k nearest chunks you keep.
