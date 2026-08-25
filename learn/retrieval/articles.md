# Further Reading: How Retrieval Works

## Articles

### 1. [Retrieval Augmented Generation](https://huggingface.co/docs/transformers/en/model_doc/rag)
**Source**: huggingface.co | **Read time**: ~12 min
> The Transformers docs for the original RAG models: a retriever plus a generator, with the retrieved passages concatenated into what the generator reads. Dry and useful — it treats stuffing as an implementation detail, not a mystery.

### 2. [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
**Source**: arxiv.org | **Read time**: ~25 min (paper)
> Lewis et al., 2020 — the paper that named the pattern. A parametric generator conditioned on documents a non-parametric retriever selected. Read the setup, not the leaderboard: chunk, retrieve, condition.

### 3. [Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval)
**Source**: anthropic.com | **Read time**: ~12 min
> What you add *after* the three verbs work: prepend chunk-specific context before embedding, optionally blend with BM25, optionally rerank. Reports a 49% drop in retrieval failures (67% with reranking). The extras make more sense once stuffing is not magic.

### 4. [Embeddings: What they are and why they matter](https://simonwillison.net/2023/Oct/23/embeddings/)
**Source**: simonwillison.net | **Read time**: ~15 min
> A practitioner explanation of embeddings as neighborhood-preserving vectors, with sqlite-utils and cosine similarity you can run locally. The right mental model before you buy a vector database.

### 5. [Prompt engineering: give the model relevant context](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
**Source**: docs.anthropic.com | **Read time**: ~8 min
> Provider-side reminder that the model only sees the string you send. Retrieval is how you choose that string; the completion API does not search your corpus for you.

## The one-line takeaway
Cut the docs, rank the nearest slices, concatenate them into the prompt. Everything else is an optimization on those three verbs.
