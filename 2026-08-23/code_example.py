"""
AutoRAG-style greedy per-node grid search for a RAG pipeline.

Mirrors the core idea in Marker-Inc-Korea's AutoRAG (arXiv:2410.20878): treat a
retrieval-augmented-generation pipeline as a DAG of swappable nodes (retrieval ->
prompt-maker -> generator), grid-search each node's module/parameter combinations
against a deterministic, LLM-free scorer, and freeze only the WINNING config
before sweeping the next node. This avoids testing the full cross product of
every node's options against every other node's options.

Run: python3 code_example.py
"""

# Punctuation stripped up front so exact-substring "did we retrieve the answer"
# checks don't trip on a trailing period or comma.
DOCS = {
    "doc1": ("Retrieval augmented generation pipelines fetch external text before the "
              "language model writes an answer The system was first deployed in 2026 "
              "across three production regions and cut hallucination rates by half "
              "Many teams still hand-tune chunk size instead of measuring it "
              "Overlap between neighboring chunks helps preserve context across boundaries "
              "Retrieval quality is usually the first thing to check when answers go wrong"),
    "doc2": ("Vector databases index embeddings for approximate nearest neighbor search "
              "Chunk size controls how much text each embedding represents "
              "The optimal chunk size for the finance dataset was found to be one hundred "
              "and fifty words with thirty percent overlap between chunks "
              "Top-k controls how many chunks are handed to the language model "
              "Smaller top-k values reduce noise but risk missing the answer entirely"),
}

QUERIES = [
    {"q": "when was the rag pipeline first deployed and what did it cut",
     "doc": "doc1", "answer": "cut hallucination rates by half"},
    {"q": "what chunk size and overlap worked best for the finance dataset",
     "doc": "doc2", "answer": "one hundred and fifty words with thirty percent overlap"},
]


def chunk_text(text, size, overlap):
    words = text.split()
    step = max(1, int(size * (1 - overlap)))
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + size]))
        if i + size >= len(words):
            break
        i += step
    return chunks


def retrieve(chunks, query, top_k):
    qwords = set(query.lower().split())
    scored = [(len(qwords & set(c.lower().split())), c) for c in chunks]
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:top_k]]


def score_retrieval(chunk_size, overlap, top_k):
    """LLM-free node scorer: context_recall + 0.05*MRR - 0.00002*avg_ctx_words."""
    recalls, mrrs, ctx_words = [], [], []
    for item in QUERIES:
        chunks = chunk_text(DOCS[item["doc"]], chunk_size, overlap)
        retrieved = retrieve(chunks, item["q"], top_k)
        hit_rank = next((r for r, c in enumerate(retrieved, 1) if item["answer"] in c), None)
        recalls.append(1.0 if hit_rank else 0.0)
        mrrs.append(1.0 / hit_rank if hit_rank else 0.0)
        ctx_words.append(sum(len(c.split()) for c in retrieved))
    recall, mrr = sum(recalls) / len(recalls), sum(mrrs) / len(mrrs)
    avg_words = sum(ctx_words) / len(ctx_words)
    return recall, mrr, avg_words, recall + 0.05 * mrr - 0.00002 * avg_words


def sweep_retrieval_node():
    chunk_sizes, overlaps, top_ks = [10, 15, 20, 30, 45, 60], [0.0, 0.15, 0.3], [1, 2, 3, 5]
    results = []
    for cs in chunk_sizes:
        for ov in overlaps:
            for k in top_ks:
                recall, mrr, avg_words, score = score_retrieval(cs, ov, k)
                results.append((cs, ov, k, recall, mrr, avg_words, score))
    results.sort(key=lambda r: -r[-1])
    return results


def sweep_prompt_maker_node(fixed_recall, fixed_mrr, fixed_words):
    """Node 2 is fed only the WINNING config from node 1 -- not every retrieval
    config re-tested against every template. Quality is unaffected by template
    choice here, so cost (overhead words) alone breaks the tie."""
    templates = {
        "bare": 0,
        "labeled_sections": 8,
        "chain_of_thought_instructions": 40,
    }
    results = []
    for name, overhead in templates.items():
        total_words = fixed_words + overhead
        score = fixed_recall + 0.05 * fixed_mrr - 0.00002 * total_words
        results.append((name, overhead, total_words, score))
    results.sort(key=lambda r: -r[-1])
    return results


if __name__ == "__main__":
    print("=== Node 1: retrieval (chunk_size x overlap x top_k) ===")
    retrieval_grid = sweep_retrieval_node()
    best = retrieval_grid[0]
    naive = next(r for r in retrieval_grid if r[0] == 60 and r[1] == 0.0 and r[2] == 5)
    print(f"configs tried: {len(retrieval_grid)}")
    print(f"naive default   chunk={naive[0]:>3} overlap={naive[1]:.2f} top_k={naive[2]} "
          f"-> recall={naive[3]:.3f} mrr={naive[4]:.3f} ctx_words={naive[5]:.0f} score={naive[6]:.4f}")
    print(f"AutoRAG winner  chunk={best[0]:>3} overlap={best[1]:.2f} top_k={best[2]} "
          f"-> recall={best[3]:.3f} mrr={best[4]:.3f} ctx_words={best[5]:.0f} score={best[6]:.4f}")
    reduction = 100 * (1 - best[5] / naive[5])
    print(f"same recall/mrr, {reduction:.0f}% fewer context words ({naive[5]:.0f} -> {best[5]:.0f})")

    print("\n=== Node 2: prompt maker, fed ONLY node 1's winner ===")
    template_grid = sweep_prompt_maker_node(best[3], best[4], best[5])
    for name, overhead, total_words, score in template_grid:
        print(f"{name:<30} overhead={overhead:>3} total_words={total_words:>5.0f} score={score:.4f}")
    print(f"prompt-maker winner: {template_grid[0][0]}")

    print("\n=== Combinatorial explosion avoided ===")
    greedy_count = len(retrieval_grid) + len(template_grid)
    full_cross_product = len(retrieval_grid) * len(template_grid)
    savings = 100 * (1 - greedy_count / full_cross_product)
    print(f"greedy per-node total configs tested: {greedy_count}")
    print(f"full cross product would have tested: {full_cross_product}")
    print(f"greedy sweep avoids {savings:.1f}% of the work a full grid search would require")
