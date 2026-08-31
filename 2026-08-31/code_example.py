"""
Agent memory: consolidation vs. scoring.

Builds a 53-session haystack where every topic is *discussed* often and *resolved*
once, then measures what actually moves recall: how much you extract per session,
versus how cleverly you score it. Follows MEMTIER's ablation (arXiv:2605.03675).

The gap in the first table is wider than the paper's +0.128 (a toy corpus with one
answer per topic exaggerates it); the direction and the flat second table are the
findings.

Run: python3 code_example.py
"""

import math, random, re
from collections import Counter

# Knobs. Change these and watch the conclusion move.
FACT_CAP = 8       # max memories the consolidator keeps per session
K1_SESSIONS = 3    # stage-1 sessions to scope to; 1 over-scopes, >=3 saturates
SEED = 7

def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())

class BM25:
    """Okapi BM25, canonical constants. Scores are unbounded -- which is why adding
    a bounded 0..1 signal to them in a linear sum changes nothing."""

    def __init__(self, docs, k1=1.5, b=0.75):
        self.k1, self.b, self.docs = k1, b, [tokenize(d) for d in docs]
        self.avgdl = sum(len(d) for d in self.docs) / max(len(self.docs), 1)
        self.df, self.n = Counter(), len(self.docs)
        for d in self.docs:
            self.df.update(set(d))

    def score(self, query, i):
        freqs, dl, total = Counter(self.docs[i]), len(self.docs[i]), 0.0
        for term in tokenize(query):
            if term not in freqs:
                continue
            idf = math.log(1 + (self.n - self.df[term] + 0.5) / (self.df[term] + 0.5))
            tf = freqs[term]
            total += idf * tf * (self.k1 + 1) / (
                tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return total

    def top(self, query, k):
        return sorted(range(self.n), key=lambda i: -self.score(query, i))[:k]

def two_stage_retrieve(query, memory, k1=K1_SESSIONS, k=2, weights=None):
    """Stage 1 picks candidate sessions; stage 2 ranks memories inside only those.
    Lift this. What you can retrieve is bounded by what consolidation stored."""
    if not memory:
        return []
    scoped = {memory[i]["session_id"]
              for i in BM25([m["content"] for m in memory]).top(query, k1)}
    pool = [m for m in memory if m["session_id"] in scoped]
    sub = BM25([m["content"] for m in pool])
    if not weights:
        return [pool[i] for i in sub.top(query, k)]
    # Raw BM25 runs 5-10x larger than these bounded extras, so the linear sum cannot
    # reorder anything they disagree with. That is the whole finding.
    wd, wc = weights
    order = sorted(range(len(pool)), key=lambda i: -(
        sub.score(query, i) + wd * pool[i]["decay"] + wc * pool[i]["cw"]))
    return [pool[i] for i in order[:k]]

DURABLE = re.compile(r"\b(because|decided|turned out|root cause)\b")

def _mem(session, line):
    # Bounded auxiliary signals, both in 0..1, as the paper defines them.
    return {"session_id": session["id"], "content": line,
            "decay": math.exp(-0.05 * (session["id"] % 30)),   # ~14-day half-life
            "cw": 0.5 + 0.5 * math.sin(session["id"])}

def consolidate_durable(session):
    """What an extraction prompt approximates: keep resolutions, drop chatter."""
    keep = [ln for ln in session["lines"] if DURABLE.search(ln)]
    return [_mem(session, ln) for ln in keep[:FACT_CAP]]

def consolidate_everything(session):
    """The heuristic baseline: every line is a memory. More coverage, worse index."""
    return [_mem(session, ln) for ln in session["lines"]]

TOPICS = ["payment webhook", "search index", "auth token", "image upload",
          "rate limiter", "billing export", "cache warmer", "audit log",
          "session store", "webhook replay", "invoice job", "email digest",
          "thumbnail queue", "sync worker", "report builder", "device token"]

def build_corpus(rng, n_sessions=53):
    """Each topic is asked about constantly, resolved once. Chatter echoes the
    question wording, so it competes with the answer at retrieval time."""
    sessions = [{"id": i, "lines": []} for i in range(n_sessions)]
    answers = {}
    for i, topic in enumerate(TOPICS):
        # One resolution in four carries no durable marker, so extraction drops it.
        # A filter you can state in a prompt is never perfect.
        answers[topic] = (f"the {topic} is safe to retry because we key on the "
                          f"event id" if i % 4 else
                          f"the {topic} keys on the event id so a retry is a no-op")
        sessions[rng.randrange(n_sessions)]["lines"].append(answers[topic])
    for s in sessions:
        for _ in range(11):
            t = rng.choice(TOPICS)
            s["lines"].append(rng.choice([
                f"someone asked in standup whether the {t} is safe to retry again",
                f"rebased the {t} branch and reran the whole suite this morning",
                f"moved the {t} ticket back into the review column for now",
                f"paged about the {t} overnight, nothing actionable in the logs",
                f"nobody has signed off the {t} yet because the owner is away",
            ]))
        rng.shuffle(s["lines"])
    return sessions, [{"question": f"why is the {t} safe to retry", "answer": a}
                      for t, a in answers.items()]

def recall(sessions, questions, consolidator, k=2, weights=None):
    memory = [m for s in sessions for m in consolidator(s)]
    hits = sum(1 for q in questions
               if any(m["content"] == q["answer"] for m in
                      two_stage_retrieve(q["question"], memory, K1_SESSIONS, k, weights)))
    return hits / len(questions), len(memory) / len(sessions)

def main():
    sessions, questions = build_corpus(random.Random(SEED))
    print(f"{len(sessions)} sessions, {sum(len(s['lines']) for s in sessions)} raw "
          f"lines, {len(questions)} questions\n")

    print("consolidation policy        memories/session   recall@2   recall@8")
    for name, fn in (("index everything", consolidate_everything),
                     ("index durable only", consolidate_durable)):
        r2, per_s = recall(sessions, questions, fn, k=2)
        r8, _ = recall(sessions, questions, fn, k=8)
        print(f"  {name:<26} {per_s:>7.1f}   {r2:>8.3f}   {r8:>8.3f}")

    print("\nnow add the clever signals on top of the good index")
    for label, w in (("bm25 only", None), ("+ recency", (0.25, 0.0)),
                     ("+ usefulness", (0.0, 0.25)), ("+ both", (0.25, 0.25)),
                     ("+ both, doubled", (0.50, 0.50))):
        r, _ = recall(sessions, questions, consolidate_durable, weights=w)
        print(f"  {label:<26} recall@2 {r:.3f}")

    print("\nFirst table is the lever. Second is where the effort usually goes.")

if __name__ == "__main__":
    main()
