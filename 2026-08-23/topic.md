# Nobody Re-Tests Their RAG Chunk Size — One Grid Search Cut It 88%

**Category**: Hands-on Techniques
**Tags**: rag, benchmarks, cost
**Date**: 2026-08-23
**Time to read**: ~10 minutes

## Explain Like I'm 5
Imagine you're perfecting a recipe with five ingredients you can each adjust — how much, how
chopped, how long to cook. Testing every possible combination of all five at once would take
forever, so instead you fix everything else, try several amounts of ingredient one, keep whichever
tasted best, and only then move on to adjusting ingredient two around that winner. You never taste
the full cross product of every combination — you taste your way there one ingredient at a time,
carrying the best choice forward.

## The Problem
`chunk_size`, `overlap`, and `top_k` almost always get set once, early, by feel — and then nobody
touches them again, because checking whether a different value actually helps means re-running the
pipeline and having a human (or an expensive LLM judge) grade the outputs. That cost makes tuning
feel optional, so teams ship a guess and never learn how much of their context budget it's wasting.
The Red Hat demo found the guess was costing 88% of the context for zero retrieval benefit.

## For a Software Engineer
This is a hyperparameter search problem, the same shape as tuning a JVM's GC flags or a database's
connection-pool size — except most teams don't treat it that way. Chunk size, chunk overlap, and
how many chunks to retrieve (`top_k`) get set once, by feel, early in a project, and then nobody
revisits them because there's no cheap way to score a change.

The fix is to stop treating "did retrieval quality improve" as something only a human eyeballing
outputs can judge. `context_recall` (did the retrieved text contain the answer?) and `MRR` (how
high did the first correct chunk rank?) are both computable from a small labeled query set —
20 to 100 questions with known answers — with zero LLM calls. That turns retrieval tuning into a
sweep you run in seconds, not a debate in a design review.

The number worth feeling: a real demo on a 1-billion-parameter model found a configuration that
matched a naive default's retrieval quality exactly (100% recall, same MRR) while sending the
model **88% fewer context words** (1,367 → 165). The naive setting wasn't retrieving more relevant
text — it was retrieving the same relevant text buried in far more padding. Monday-morning action:
if you've never grid-swept `chunk_size` / `overlap` / `top_k` against a labeled eval set, you don't
know whether your RAG pipeline's cost is buying you anything.

## What This Means for You
**When this matters**: you set `chunk_size`, `overlap`, or `top_k` once — during the demo, before
you had real usage data — and haven't touched them since, or you're paying to send more context per
query than a smaller retriever config would need.

**How it affects you**: every extra word in a retrieved chunk is a word the model has to read, pay
for, and potentially get distracted by. If your defaults are padding rather than signal, you're
paying inference cost and eating context budget for no accuracy gain — and you have no way to know
that without measuring it.

**What to do about it**: build a 20-100 question labeled eval set for your own documents (question
+ which chunk should answer it), then grid-sweep `chunk_size`/`overlap`/`top_k` scored by
`context_recall` and `MRR` alone — no LLM judge, no generation calls needed. If your current
settings already sit near the Pareto frontier, you've confirmed the cost is earned; if not, you've
found free savings.

## What It Is
AutoRAG (Marker-Inc-Korea, arXiv:2410.20878) is an open-source framework that treats a
retrieval-augmented-generation pipeline as a DAG of swappable nodes — retrieval, optional query
expansion, optional reranking/filtering, prompt-maker, generator — where each node accepts a list
of candidate modules and parameter values in a YAML config. For every node, it exhaustively grid-
searches the modules and parameters listed for *that node only*, scores each combination with a
metric appropriate to what the node does, and keeps the winner. That winner — not every candidate
— is what the next node's sweep is built on top of.

A follow-up practitioner writeup (Red Hat Developer, Aug 2026) ran this against a small 1B-parameter
model with a 21-question evaluation set and a fully deterministic scorer, showing the pattern
end-to-end with no LLM judge anywhere in the loop.

## Why It Matters
RAG pipelines accumulate hand-picked constants — chunk size, overlap, `top_k`, prompt template —
that nobody re-derives once the demo works. Each one is usually chosen by a single manual test, not
measured against alternatives, because measuring alternatives against real LLM-judged quality is
slow and expensive. AutoRAG's insight is that the retrieval half of the pipeline doesn't need an
LLM judge at all: recall and rank are computable directly against a labeled answer set. That
collapses the cost of a sweep from "run the model N times and grade the answers" to "run a
substring search N times," which is why it's practical to run dozens to hundreds of configurations
before ever calling the generator.

It also matters most for exactly the models that can least afford to be sloppy: small, cheap, or
self-hosted models have less capacity to ignore irrelevant context, so shrinking the noise in what
they're handed narrows — though never closes — the accuracy gap to a larger model.

## Key Technical Details

**Background first.** A RAG pipeline's retrieval stage works like this: a document gets cut into
overlapping *chunks* (`chunk_size` = how many words per chunk, `overlap` = how much neighboring
chunks share, so a sentence spanning a cut point isn't lost entirely). A query is compared against
every chunk, the chunks are ranked, and the top `top_k` are handed to the language model as context.
`context_recall` asks a binary question per query — was the actual answer inside *any* of the
retrieved chunks? `MRR` (Mean Reciprocal Rank) asks a sharper one — if chunk rank 1 held the answer
that's a score of 1/1, if it took until rank 3 that's 1/3, and 0 if it never showed up at all.

- **The scorer is one formula, and it's LLM-free.** The Red Hat demo used
  `context_recall + 0.05·MRR − 0.00002·avg_context_words` — reward finding the answer, reward
  finding it early, lightly penalize sending more words than necessary. Because none of those three
  terms requires calling a model, sweeping dozens of configurations costs a substring search, not a
  generation call.
- **Each node is grid-searched independently, in full.** Listing `chunk_size: [10,15,20,30,45,60]`,
  `overlap: [0.0,0.15,0.3]`, `top_k: [1,2,3,5]` in a node's config means every combination gets
  tried — this session's code sweeps that exact grid and evaluates all 72 combinations.
- **Only the winner crosses into the next node's sweep — that's the "greedy" part.** The prompt-
  maker node doesn't re-test every retrieval config against every prompt template; it inherits the
  one retrieval config that already won, then sweeps its own options on top of it. This is what
  keeps the search tractable: this session's code tests 72 retrieval configs + 3 prompt-template
  configs = 75 runs total, versus 72 × 3 = 216 if every node's options were cross-tested against
  every other node's — a 65.3% reduction in work for a pipeline with only two tunable nodes, and
  the saving compounds with every additional node.
- **Nodes without their own ground truth borrow the next node's score.** Query expansion and
  prompt-maker changes don't have a direct "was this correct" signal of their own, so AutoRAG
  evaluates them by how well the *node after them* performs — a prompt template is judged by the
  generation it produces, not by anything intrinsic to the template.
- **The published real-world result reshuffled which knobs mattered.** The naive default (chunk
  size 250, no overlap, `top_k` 8) and the found optimum (chunk size 150, 30% overlap, `top_k` 3)
  scored identically on recall and MRR — the naive setting's extra chunks and larger size weren't
  finding more of the answer, just repeating it inside more padding.
- **It narrows model weakness, it doesn't fix it.** As the source article puts it: AutoRAG "does
  not make a 1-billion-parameter model accurate. It narrows the gap" — a cleaner, smaller context
  window helps a small model use what it's given; it can't give the model reasoning it lacks.

## How It Connects to What You Know
This is the same move as replacing "eyeball the graph and pick a learning rate" with a proper
hyperparameter sweep during training — except applied to the retrieval half of a RAG system, which
usually gets none of that rigor because it's assumed to be a solved, one-time decision. It's also
the same instinct as an eval harness for agents (see 2607-01916, the ContextSniper session from
07-04, and the P-PAS scheduler session from 08-18): stop trusting a config choice you've never
actually measured against alternatives. And the greedy per-node search is the same tradeoff a
compiler makes with local optimization passes instead of a global one — it gives up guaranteed
global optimality in exchange for a search that finishes at all.

## Try It Yourself
`code_example.py` implements a minimal, pure-Python version of exactly this: a synthetic two-
document corpus, a keyword-overlap retriever standing in for embeddings, the same
`context_recall + 0.05·MRR − 0.00002·avg_ctx_words` scorer, a 72-way grid search over
`chunk_size` × `overlap` × `top_k`, and a second node (prompt-template overhead) that sweeps only
against the first node's winner. It prints the naive-vs-optimized comparison and the greedy-vs-
full-cross-product config count, so you can see both mechanisms end to end without calling any
model at all.

## Glossary
- **RAG** (Retrieval-Augmented Generation) — an LLM pipeline that fetches relevant text from a
  document store before generating an answer, instead of relying only on what the model
  memorized during training.
- **Chunk** — a fixed-size slice of a document (measured here in words) that gets embedded or
  indexed as one retrievable unit.
- **Chunk overlap** — how much of a chunk's words are shared with its neighbor, so information
  near a cut boundary isn't lost by falling entirely into one chunk or the other.
- **top_k** — the number of highest-ranked chunks handed to the language model as context after
  retrieval.
- **Context recall** — whether the retrieved chunks contain the actual answer to a query at all;
  a yes/no per query, averaged across a query set.
- **MRR** (Mean Reciprocal Rank) — how early the first chunk containing the answer appears in the
  ranked results; 1 divided by its rank, averaged across queries, so finding the answer at rank 1
  scores higher than finding it at rank 5.
- **Grid search** — trying every combination of a set of listed parameter values, rather than
  guessing one and moving on.
- **Greedy search** — at each stage, keep only the single best result found so far and build the
  next stage on top of it, instead of keeping every option alive for later combination — faster,
  but not guaranteed to find the true global best.
- **Node / DAG** (Directed Acyclic Graph) — AutoRAG's term for one stage of the pipeline
  (retrieval, prompt-maker, generator, etc.); a DAG is a sequence of stages with no loops, so each
  node's output flows only forward.
- **YAML** — a plain-text config format; listing multiple values for one setting in a YAML file is
  how AutoRAG is told which combinations to grid-search.
