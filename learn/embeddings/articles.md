# Further Reading: Nearby Points Are the Retrieve Decision

## Primary Sources

### 1. [Embeddings: What they are and why they matter](https://simonwillison.net/2023/Oct/23/embeddings/)
**Source**: simonwillison.net | **Read time**: ~15 min
> Neighborhood-preserving vectors, cosine, and a local SQLite path. The right mental model before you buy a database.

### 2. [Sentence-BERT](https://arxiv.org/abs/1908.10084)
**Source**: arXiv | **Read time**: ~25 min
> Reimers & Gurevych. Why a generative checkpoint is a weak document index, and why a bi-encoder exists.

### 3. [Dense Passage Retrieval](https://arxiv.org/abs/2004.04906)
**Source**: arXiv | **Read time**: ~30 min
> Karpukhin et al. Dual encoders for retrieve-then-read. The pattern behind most RAG indexes.

## Background & Ecosystem

### 4. [Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval)
**Source**: anthropic.com | **Read time**: ~12 min
> What you add after nearest-neighbor works: chunk-specific prefixes, optional BM25, optional rerank.

### 5. [Retrieval without mystique](https://theaicommit.com/#learn/retrieval)
**Source**: theaicommit.com | **Read time**: ~10 min
> Day-1 lesson: chunk, retrieve, stuff. This primer is the vector; that lesson is the three verbs.

## The one-line takeaway
Embed the corpus offline. Embed the query online. Distance picks the chunks. If the answer is not in top-k, no prompt will save you.
