# How an Agent Decides What to Remember

**Category**: Building Agents & MCP
**Tags**: rag, context-engineering, benchmarks, paper
**Date**: 2026-08-31
**Level**: Deeper
**For**: Building agents
**Hook**: Agent memory gets better when you write fewer notes, not when you score them more cleverly.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine keeping a notebook on a long job. Every day you write down everything that happened.
Months later you need one fact and cannot find it — not because the notebook is badly organised,
but because you wrote five hundred pages of noise.

The fix is not a better index. It is writing three good sentences a day instead of five hundred
mediocre ones. What goes in the notebook matters far more than how you search it.

## The Problem

An agent that runs for weeks has to remember across sessions, and almost everyone builds it the
same way: write everything to a store, then retrieve by similarity. The improvements all go into
the scoring — recency, whether the memory helped last time, which tier it lives in — with the
weights learned from feedback.

MEMTIER, from Ben-Gurion University, built exactly that, then did what almost nobody does: it
ablated its own design and published the table.

Three of the five signals scored *negative*. Removing recency weighting improved accuracy by
0.012, removing the learned usefulness score by 0.014. Tuning the weights with reinforcement
learning moved the final number by exactly zero.

What worked was the step before any of that: **deciding what gets written down at all**. Instead
of storing every line and searching it later, a background pass reads the finished session and
keeps a handful of durable facts — the decisions, the constraints, the things that broke.
Retrieval then searches those, not the transcript.

That one change was worth more than every scoring adjustment combined.

## How Memory Consolidation Works

Everything below is measured on LongMemEval-S: 500 questions whose answers sit in 53-session
haystacks, with the conversations *not* in context at query time. A 7B model with no memory
scores 0.050; the full system scores 0.382, on a laptop with a 6 GB GPU.

### The episodic log

Every session appends entries to a daily JSONL file — append-only, project-scoped, sub-agents on
their own path. The log is raw material, not memory.

### Consolidation

A background daemon distils sessions into facts with an LLM call. This carries the result:
**+0.128 accuracy**, the largest term in the ablation, nearly tripling F1 from 0.142 to 0.412.

The mechanism is subtraction. Heuristic extraction produced about 509 facts per question; LLM
extraction produced about 3.1 — a 164x smaller index — and beat it, for about $0.05 across all
500 questions.

A smaller index is not just cheaper. It is more accurate, because there is less to be wrong
about.

### Two-stage scoping

Retrieval runs twice: stage one searches the distilled facts for the top few *session IDs*, stage
two loads episodic entries from those sessions alone. Removing it costs 0.040. Three sessions is
the practical minimum, and it saturates there.

### The signals that did not work

The scorer weights BM25 lexical match, time decay, the usefulness score and a tier bonus
`[0.35, 0.25, 0.25, 0.15]`. But raw BM25 is unbounded and the rest cap at 1.0, so it outweighs
them five- to tenfold and they only add noise. Five normalisation schemes produced *identical*
accuracy: rescaling cannot reorder a ranking BM25 already dominates.

The ceiling is the paper's most useful number. Inject the correct sessions by hand and accuracy
jumps from 0.350 to 0.550 — retrieval surfaces the right context only 39% of the time. A 284B
reader does not help either.

## For a Software Engineer

This is log compaction, and you have already shipped it.

A write-ahead log that keeps every mutation forever is correct and useless; what makes it
queryable is a compaction pass collapsing history into current state. Agent memory is the same
shape, and we are building the log without the compactor — then blaming the query planner.

The signal-weighting work is the tell. Adding recency and usefulness to the score is adding index
hints to a query that is scanning the wrong table. The hints are not wrong, just irrelevant next
to what the scan is looking at.

The number to hold onto: **3.1 facts beat 509**. If you have ever deleted two-thirds of a cache
and watched the hit rate go up because the evictions were finally hitting the right entries, you
already have the intuition. New to retrieval scoring? Start at AI basics →
[How Retrieval Works](#learn/retrieval).

## What This Means for You

**When this matters** — anything your agent is supposed to remember after the conversation ends.
That covers a chat assistant that should recall last week, a coding agent that keeps notes across
sessions, and the `CLAUDE.md`-style file you top up by hand. If you have ever watched an agent
confidently forget something it was told on Tuesday, this is the machinery that failed.

**How it affects you** — the obvious next move is the wrong one. Faced with an agent that forgets,
almost everyone reaches for better retrieval: more signals, better weights, a smarter ranker. That
work will not pay. Three of five signals here measured negative and learned weights moved nothing,
because an unbounded lexical score swamps everything else in a linear combination. The step nearly
everyone skips — deciding what is worth keeping at all — was worth more than every scoring change
combined.

**What to do about it** — start with the cheapest version, today: at the end of a session, ask the
model for the five things worth remembering and append *only those* to your notes file. That is
consolidation, done by hand, and it is most of the win. When you are ready to automate it, run
that as a background pass and retrieve against the facts rather than the transcript. Then measure:
write twenty questions whose answers you know, and count how often the answer appears in what came
back. If you already own a weighted scorer, set every non-lexical weight to zero for one run and
see whether anything moves — on this evidence, nothing will.

## Implementing It

**The change.**

*Agent builder — the episodic store.* Append-only, one file per day, project-scoped. Sub-agents
write to their own path so a parallel worker cannot pollute the parent's context:

```python
# memory/episodic/2026-08-31.jsonl — one JSON object per line, never mutated in place
{"id": "ep_8f21", "timestamp": "2026-08-31T14:02:11Z", "session_id": "s_412",
 "project": "checkout-api", "content": "Retries on the payment webhook are idempotent "
 "because we key on provider_event_id.", "tokens": 24,
 "promoted": false, "cognitive_weight": 0.0}
```

*Agent builder — the consolidation daemon.* This is the part that carries the result. Run it
asynchronously at session end, not on an interrupt mid-turn:

```python
CONSOLIDATE = """Read this session transcript. Emit only durable facts a future
session would need: decisions made, constraints discovered, things that broke and why.
Skip anything recoverable from the codebase. One fact per line, max 8 lines."""

def consolidate(session_text: str, llm) -> list[str]:
    facts = llm(CONSOLIDATE, session_text).splitlines()
    return [f.strip() for f in facts if f.strip()][:8]   # cap is the point
```

The cap is not a safety rail, it is the mechanism. Extraction that emitted ~509 facts per
question lost to extraction that emitted ~3.1.

*Retrieval tuner — two stages, then a small k.* Search the facts for sessions, then the raw log
inside them:

```python
def retrieve(query, facts, episodes, k1=3, k=2, token_budget=600):
    sessions = {f.session_id for f in bm25(facts, query)[:k1]}       # stage 1
    pool = [e for e in episodes if e.session_id in sessions]         # stage 2
    return truncate(bm25(pool, query)[:k], token_budget)
```

Those defaults are measured, not taste: `k=2` scored 0.402 against 0.382 at `k=4`, because a
small reader cannot filter noise you hand it. Raising the injection budget from 300 to 600 tokens
was worth +0.032. Stage-1 `k1=3` saturates — 5 and 10 score identically.

*The engineer tempted by the clever version.* The usefulness score updates from tool outcomes
after each session:

```python
# alpha=0.1, reward r in {-0.5, 0, +1.0}, attribution a_hat normalised across retrieved entries
cw = clip(cw + 0.1 * reward * a_hat, -1.0, 1.0)
```

It is coherent, and it did not pay: removing it *improved* accuracy by 0.014. Build it only after
you have normalised your lexical scores or moved to recall-first dense retrieval, which the
authors name as the precondition. Until then it is a signal that cannot reach the ranking.

**How you know it worked.** Count facts per session in your consolidation log — if it is above
ten, your prompt is summarising rather than extracting, and the index is growing back toward the
version that lost. Then measure Recall@k directly: build twenty questions whose answers you know,
and log how often the answer text appears in what you retrieved. Below ~0.40 you are in the
regime this paper describes, where no scoring change will help and the fix is upstream. Compare
against an oracle run with the correct sessions injected by hand; the gap between the two is your
retrieval headroom, and it was 0.200 here.

## When Consolidation Is the Wrong Tool

If your history fits in the context window, skip all of this. The same system scored identically
to a plain baseline on LoCoMo — 0.005 F1 apart — because that benchmark stuffs the whole
conversation into the prompt, making the architecture irrelevant.

Consolidation is also lossy on purpose, and unevenly so. Questions about preferences scored
0.067, the worst of any category, because subjective phrasing is exactly what an extraction
prompt discards. If your agent's value is remembering how someone likes things done, extraction
cuts the thing you needed.

Read the evidence for what it is, too: one lab, soft exact-match rather than the benchmark's own
judge, no multi-seed testing.

Three questions before adopting it. Does my history actually exceed the context window, or am I
solving a problem I do not have yet? Can I say what a "durable fact" is for my domain precisely
enough to put in a prompt? And if I injected the right sessions by hand, how much would accuracy
improve — because that gap, not my ranking function, is the work.
