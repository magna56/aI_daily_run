# Further Reading: AutoRAG: Treating a RAG Pipeline Like a Hyperparameter Search, Not a Guess

## Articles

### 1. [AutoRAG: Optimizing RAG for small models](https://developers.redhat.com/articles/2026/08/04/autorag-optimizing-rag-small-models)
**Source**: Red Hat Developer | **Date**: August 4, 2026 | **Read time**: ~8 min
> A hands-on walkthrough running AutoRAG against a 1-billion-parameter model with a 21-question
> evaluation set and a fully deterministic, LLM-free scorer. Shows the naive-vs-optimized
> configuration side by side — 100% recall and 0.976 MRR held constant while context words dropped
> 88% (1,367 → 165) — and states the limitation plainly: it narrows a small model's accuracy gap,
> it doesn't close it.

### 2. [AutoRAG documentation — How optimization works](https://marker-inc-korea.github.io/AutoRAG/optimization/optimization.html)
**Source**: Marker-Inc-Korea (project docs) | **Read time**: ~10 min
> The canonical explanation of the node/DAG structure: which nodes are mandatory (retrieval,
> prompt-maker, generator), how YAML lists expand into grid-searched combinations, why nodes
> without their own ground truth (query expansion, prompt-maker) borrow the next node's evaluation
> score, and the three result-selection strategies (best, normalize, rank).

### 3. [AutoRAG GitHub repository](https://github.com/marker-inc-korea/autorag)
**Source**: Marker-Inc-Korea | **Read time**: ~5 min
> The open-source implementation and sample YAML configs referenced throughout this session —
> useful for seeing the actual config shape (`sample_config/rag/`) that produces the grid searches
> described in the docs and the paper.

## Papers

### [AutoRAG: Automated Framework for optimization of Retrieval Augmented Generation Pipeline](https://arxiv.org/abs/2410.20878)
**Authors**: Marker-Inc-Korea team | **Published**: October 2024 (actively maintained through 2026)
> The original paper motivating the framework: manually finding RAG modules that perform well on a
> specific dataset is expensive and non-transferable across datasets, so AutoRAG automates the
> search instead of relying on one-off manual tuning.

### [AutoRAGTuner: A Declarative Framework for Automatic Optimization of RAG Pipelines](https://arxiv.org/pdf/2605.02967)
**Authors**: (2026 follow-up work) | **Published**: May 2026
> A more recent declarative take on the same automated-optimization idea, useful as a cross-check
> on how the "grid-search each pipeline stage" approach has been extended since the original
> AutoRAG paper.

### [Evaluating Prompt Engineering Techniques for RAG in Small Language Models: A Multi-Hop QA Approach](https://arxiv.org/pdf/2602.13890)
**Published**: 2026
> Evaluates 24 prompt templates (9 established + 14 novel hybrids) on HotpotQA multi-hop QA,
> finding up to a 6% accuracy gain from prompt design alone — relevant context for why the
> prompt-maker node in this session's code is worth sweeping separately from retrieval, not folded
> into it.
