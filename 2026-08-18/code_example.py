"""
Prefill-Pressure Adaptive Scheduling (P-PAS) — why max_num_batched_tokens has no right value.

Simulates a vLLM-style continuous-batching scheduler with chunked prefill and shows the
load-dependent inversion at the heart of arXiv:2608.15171:

  * LOW load  -> a LARGE token budget wins (finish prefill in one shot, nobody to stall)
  * HIGH load -> a SMALL token budget wins (long prefill iterations stall every decode seq)

No static budget is optimal in both regimes. P-PAS adapts the budget from live queue state.

Run:  python3 code_example.py      (pure stdlib, no deps, no API keys, ~2s)
"""

import random
import statistics

# --- iteration cost model -------------------------------------------------------------
# An engine step costs a fixed launch/overhead term plus a per-token compute term.
# Numbers are A100-ish for a 7B model; the *shape* is what matters, not the constants.
T_BASE_MS = 8.0     # kernel launch + sampling + scheduling overhead per iteration
K_TOK_MS = 0.020    # marginal ms per batched token
MAX_NUM_SEQS = 64   # concurrency cap (KV cache pressure proxy)
MBT_MIN, MBT_MAX = 1024, 8192


class Req:
    __slots__ = ("rid", "arrive", "prompt", "out", "left", "gen", "ttft", "done")

    def __init__(self, rid, arrive, prompt, out):
        self.rid, self.arrive, self.prompt, self.out = rid, arrive, prompt, out
        self.left = prompt   # prompt tokens not yet prefilled
        self.gen = 0         # output tokens emitted
        self.ttft = None
        self.done = None


def workload(n, rate_per_s, seed=7):
    """Long-context RAG shape: big prompts, short outputs (the regime the paper targets)."""
    rng = random.Random(seed)
    t, reqs = 0.0, []
    for i in range(n):
        t += rng.expovariate(rate_per_s) * 1000.0  # ms
        reqs.append(Req(i, t, rng.randint(4000, 16000), rng.randint(32, 256)))
    return reqs


# --- scheduling policies --------------------------------------------------------------
def static_policy(mbt):
    return lambda n_decode, waiting_tokens: mbt


def ppas_policy(n_decode, waiting_tokens):
    """Shrink the prefill budget as prefill pressure and decode population rise.

    Backlog counts only tokens BEYOND one full budget: a single queued request is not
    pressure, it is just work. Decode population is weighted because every decoding
    sequence pays the whole iteration latency for each token it emits.

    pressure ~ 0 (one request, nothing decoding) -> budget ~ MBT_MAX, best TTFT
    pressure high                                -> budget -> MBT_MIN, decodes flow
    """
    backlog = max(0.0, waiting_tokens - MBT_MAX) / MBT_MAX
    pressure = backlog + n_decode / 6.0
    return int(MBT_MIN + (MBT_MAX - MBT_MIN) / (1.0 + pressure))


def simulate(reqs, policy):
    reqs = [Req(r.rid, r.arrive, r.prompt, r.out) for r in reqs]  # fresh copies
    pending, running, finished = list(reqs), [], []
    t = 0.0

    while pending or running:
        if not running and pending and t < pending[0].arrive:
            t = pending[0].arrive  # idle: fast-forward to next arrival

        while pending and pending[0].arrive <= t and len(running) < MAX_NUM_SEQS:
            running.append(pending.pop(0))

        decodes = [r for r in running if r.left == 0]
        prefills = [r for r in running if r.left > 0]
        waiting_tokens = sum(r.left for r in prefills) + sum(
            r.prompt for r in pending if r.arrive <= t)

        budget = policy(len(decodes), waiting_tokens)

        # Decode-priority (stall-free) batching: every running decode emits one token,
        # then whatever budget remains is spent on chunked prefill.
        batched = len(decodes)
        chunks = []
        for r in prefills:
            room = budget - batched
            if room <= 0:
                break
            c = min(room, r.left)
            chunks.append((r, c))
            batched += c

        if batched == 0:
            t = pending[0].arrive if pending else t + 1.0
            continue

        t += T_BASE_MS + K_TOK_MS * batched

        for r, c in chunks:
            r.left -= c
            if r.left == 0:
                r.ttft = t - r.arrive       # prefill complete = first token out
                r.gen = 1
        for r in decodes:
            r.gen += 1
        for r in list(running):
            if r.left == 0 and r.gen >= r.out:
                r.done = t - r.arrive
                running.remove(r)
                finished.append(r)

    return finished


def report(name, fin, wall_hint=None):
    ttft = sorted(r.ttft for r in fin)
    e2e = sorted(r.done for r in fin)
    p = lambda xs, q: xs[min(len(xs) - 1, int(q * len(xs)))]
    print(f"  {name:<22} TTFT p50 {p(ttft,.5)/1000:6.2f}s | "
          f"E2E p50 {p(e2e,.5)/1000:6.2f}s  p99 {p(e2e,.99)/1000:7.2f}s")
    return p(e2e, .5)


def main():
    print(__doc__.split("Run:")[0].strip())
    print("\n" + "=" * 78)

    policies = [
        ("static MBT=1024", static_policy(1024)),
        ("static MBT=2048", static_policy(2048)),
        ("static MBT=8192", static_policy(8192)),
        ("P-PAS (adaptive)", ppas_policy),
    ]

    regimes = [("LOW  (1 req/s)", 1.0), ("MID  (4 req/s)", 4.0), ("HIGH (8 req/s)", 8.0)]
    winners, regret = {}, {n: 0.0 for n, _ in policies}

    for label, rate in regimes:
        print(f"\n{label}   200 requests, prompts 4k-16k tok, outputs 32-256 tok")
        print("-" * 78)
        reqs = workload(200, rate)
        scores = {name: report(name, simulate(reqs, pol)) for name, pol in policies}
        best_score = min(scores.values())
        winners[label] = min(scores, key=scores.get)
        for name, s in scores.items():  # % worse than the best policy for THIS regime
            regret[name] = max(regret[name], 100.0 * (s - best_score) / best_score)
        print(f"  -> best E2E p50: {winners[label]}")

    print("\n" + "=" * 78)
    print("THE INVERSION — best static budget per regime")
    for k, v in winners.items():
        print(f"  {k:<18} {v}")
    print("""
  The optimal STATIC budget flips with load, so any value baked into a deploy
  config is wrong for part of the day. Large chunks are free when nothing is
  decoding and ruinous when 40 sequences each pay the iteration latency per
  token. P-PAS reads that state at schedule time instead of at config time.""")

    print("\nWORST-CASE REGRET ACROSS ALL THREE REGIMES (lower = more robust)")
    for name, r in sorted(regret.items(), key=lambda kv: kv[1]):
        print(f"  {name:<22} +{r:5.1f}% worse than the per-regime winner")
    print("""
  Note the honest result: P-PAS does not win any single regime outright -- a
  perfectly tuned static budget beats it there. It wins by never being the
  wrong answer, which is what you actually want from a config you cannot
  retune per hour.""")

    print("\nBUDGET P-PAS ACTUALLY PICKS")
    for nd, wt in [(0, 8000), (4, 20000), (20, 60000), (48, 200000)]:
        print(f"  {nd:>3} decoding, {wt:>7,} tok queued -> budget {ppas_policy(nd, wt):>5}")


if __name__ == "__main__":
    main()
