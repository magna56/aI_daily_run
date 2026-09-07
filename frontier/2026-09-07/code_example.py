"""Why a coin flip matches a scorer: the KV cache, from scratch.

Simulates one layer of attention heads, each with its own KV cache and its own
eviction decision, and asks the only question that matters after eviction: can
the model still recover the facts it needs?

No torch, no transformers, no network. The point is the policy and the counting.

Three things it shows:
  * a scoring policy and a random one land in the same place, once both pin
    the prompt
  * the random one collapses without the pin, and it collapses on prompt facts
    specifically -- which is the paper's whole claim
  * recovery across heads is superadditive, so a draw that keeps a token in a
    few heads is as good as keeping it everywhere

Run: python3 code_example.py

Set PIN_PROMPT = False to watch the random policy fall over.
"""

import random

# --- knobs ---------------------------------------------------------------
HEADS = 8              # each head caches and evicts independently
PROMPT_LEN = 400       # positions written during prefill
TRACE_LEN = 3600       # positions the model generated
BUDGET = 1024          # positions each head may keep
RECENCY = 64           # most recent positions, always kept
PIN_PROMPT = True      # the entire finding, as a boolean
TRIALS = 200
SEED = 7

# A fact lives at some positions. Prompt facts are written once. Trace facts get
# restated as the model works, which is the redundancy the paper leans on.
RESTATEMENTS = 4
# Retrieval succeeds if enough heads still hold the fact. Measured on a planted
# fact by Wang et al.: 1 head 3%, 2 heads 60%, 3 heads 83%, 8 heads 99%.
RECOVERY = {0: 0.00, 1: 0.03, 2: 0.60, 3: 0.83, 4: 0.93, 5: 0.96, 6: 0.98, 7: 0.99, 8: 0.99}


def make_facts(rng):
    """Ten facts the answer depends on. Two live in the prompt, said once."""
    facts = []
    for i in range(2):
        facts.append(("prompt", [rng.randrange(PROMPT_LEN)]))
    for i in range(8):
        first = rng.randrange(PROMPT_LEN, PROMPT_LEN + TRACE_LEN - 400)
        facts.append(("trace", [first + k * 90 for k in range(RESTATEMENTS)]))
    return facts


def keep_random(total, prompt_len, budget, rng, pin):
    """Random Attention: pin the prompt, then draw uniformly. Reads no signal."""
    keep = set(range(prompt_len)) if pin else set()
    keep |= set(range(max(0, total - RECENCY), total))
    room = budget - len(keep)
    lo = prompt_len if pin else 0
    pool = [i for i in range(lo, total - RECENCY) if i not in keep]
    if room > 0:
        keep |= set(rng.sample(pool, min(room, len(pool))))
    return keep


def keep_scored(total, prompt_len, budget, rng, pin, tilt=0.3):
    """A SnapKV-shaped scorer: rank by attention from recent queries.

    Two properties are modelled, and both are real. Attention drifts toward
    recent positions, so without an explicit pin the score systematically
    starves the prompt -- that is the accident the published methods were
    living on. And each head attends differently, so heads disagree about
    what to drop, which is the same cross-head diversity a random draw gets
    for free.
    """
    keep = set(range(prompt_len)) if pin else set()
    keep |= set(range(max(0, total - RECENCY), total))
    room = budget - len(keep)
    if room <= 0:
        return keep
    lo = prompt_len if pin else 0
    pool = [i for i in range(lo, total - RECENCY) if i not in keep]
    # score = a recency tilt this head shares with the others, plus this head's
    # own attention pattern. The tilt is the bias; the noise is the diversity.
    pool.sort(key=lambda i: -((i / total) * tilt + rng.random()))
    keep |= set(pool[:room])
    return keep


def run(policy, pin, rng):
    """One decode. Evict per head, then see which facts survive in enough heads."""
    total = PROMPT_LEN + TRACE_LEN
    facts = make_facts(rng)
    heads = [policy(total, PROMPT_LEN, BUDGET, rng, pin) for _ in range(HEADS)]
    got = {"prompt": [], "trace": []}
    for kind, positions in facts:
        holding = sum(1 for kept in heads if any(p in kept for p in positions))
        got[kind].append(RECOVERY[min(holding, HEADS)])
    return got


def sweep(policy, pin):
    """Per-fact recovery, split by fact kind, plus the chance ALL ten survive.

    The last column is the one that decides an answer. A fact recovered 99% of
    the time is fine; two facts at 14% end the request, however healthy the
    other eight look.
    """
    rng = random.Random(SEED)
    tot = {"prompt": 0.0, "trace": 0.0}
    n = {"prompt": 0, "trace": 0}
    all_ten = 0.0
    for _ in range(TRIALS):
        got = run(policy, pin, rng)
        joint = 1.0
        for k in tot:
            tot[k] += sum(got[k])
            n[k] += len(got[k])
            for v in got[k]:
                joint *= v
        all_ten += joint
    return tot["prompt"] / n["prompt"], tot["trace"] / n["trace"], all_ten / TRIALS


def main():
    total = PROMPT_LEN + TRACE_LEN
    print("cache %d positions, budget %d per head, %d heads, compression %.1fx\n"
          % (total, BUDGET, HEADS, total / BUDGET))

    print("  %-22s %13s %12s %14s" % ("policy", "prompt facts", "trace facts", "all 10 intact"))
    rows = [
        ("scorer, prompt pinned", keep_scored, True),
        ("random, prompt pinned", keep_random, True),
        ("scorer, no pin", keep_scored, False),
        ("random, no pin", keep_random, False),
    ]
    for label, policy, pin in rows:
        p, t, j = sweep(policy, pin)
        print("  %-22s %12.1f%% %11.1f%% %13.1f%%"
              % (label, p * 100, t * 100, j * 100))

    print("\n  The last column asks for ten independent survivals at once, so read")
    print("  the ratio between rows and not the level. Pinning the prompt moves it")
    print("  by more than 10x, for both policies. The scoring does not.")
    print("\n  The scorer trails the coin flip even when pinned, and the reason is")
    print("  in the middle column: a ranking every head agrees with makes the heads")
    print("  drop the same tokens. An independent draw per head does not.")

    print("\nWhy a few heads are enough (planted-fact recovery)\n")
    print("  %-10s %s" % ("heads", "retrieval"))
    for h in (1, 2, 3, 8):
        bar = "#" * int(RECOVERY[h] * 40)
        print("  %-10d %-42s %.0f%%" % (h, bar, RECOVERY[h] * 100))
    print("\n  Two copies are worth twenty times one. That superadditivity is why")
    print("  an independent draw per head does not need to be a good draw.")


if __name__ == "__main__":
    main()
