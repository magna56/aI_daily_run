"""Why a committed reader misses what a cold reader sees.

Two auditors look at the same stream of observations from one agent run. One
reads them in order, carrying a running belief. The other sees each item once,
alone, with no task and no history.

The difference is not knowledge -- both see every observation. It is whether a
conclusion already exists when each piece arrives.

Pure standard library. The "model" here is a scoring rule, not a network call,
so the asymmetry is visible rather than asserted.

Run: python3 code_example.py

Raise COMMITMENT toward 1.0 and watch the in-context reader stop noticing.
"""

import random

SEED = 7
RUNS = 500
TURNS = 18
COMMITMENT = 0.85      # how strongly a held belief reweighs new evidence
BASE_SKILL = 0.80      # chance of reading one observation right, uncommitted

# Observations an agent might see. `real` is the ground truth we are hiding.
OBSERVATIONS = [
    ("resolved host to 203.0.113.42", True,  0.75),
    ("TLS cert issued to an unfamiliar company", True, 0.80),
    ("rate limited with Retry-After: 120", True, 0.55),
    ("package index accepted an upload", True, 0.85),
    ("target returned a canned fixture payload", False, 0.70),
    ("hostname ends in .test", False, 0.85),
    ("latency 0.4 ms, same every call", False, 0.65),
    ("response body contains lorem ipsum", False, 0.90),
]


def cold_read(obs, rng):
    """One observation, no context. Skill only."""
    _text, is_real, salience = obs
    p = BASE_SKILL * salience + (1 - salience) * 0.5
    correct = rng.random() < p
    return is_real if correct else not is_real


def committed_read(obs, belief, rng):
    """Same observation, but a belief is already held.

    Evidence agreeing with the belief is accepted easily; evidence against it
    has to overcome COMMITMENT. That is the whole mechanism -- no new facts
    are hidden from this reader.
    """
    _text, is_real, salience = obs
    p = BASE_SKILL * salience + (1 - salience) * 0.5
    if belief is not None and is_real != belief:
        p *= (1 - COMMITMENT)
    if rng.random() < p:
        return is_real
    # Mistakes fall toward the belief, not at random. Symmetric error would be
    # noise; this is bias, and they are different failures.
    return belief


def one_run(rng, truth_real=True):
    stream = [rng.choice(OBSERVATIONS) for _ in range(TURNS)]
    # The run is on real infrastructure, so real-indicating items dominate.
    stream = [o if (o[1] == truth_real or rng.random() < 0.35)
              else rng.choice([x for x in OBSERVATIONS if x[1] == truth_real])
              for o in stream]

    # Auditor 1: in context. Starts from the task's premise ("simulated") and
    # updates, which is exactly the transcript the agent writes.
    belief = not truth_real
    in_ctx = []
    for o in stream:
        v = committed_read(o, belief, rng)
        in_ctx.append(v)
        if sum(in_ctx[-3:]) >= 3:          # three in a row to overturn a belief
            belief = True
    # Auditor 2: cold, one item at a time, no order and no belief.
    cold = [cold_read(o, rng) for o in stream]

    return sum(in_ctx) / len(in_ctx), sum(cold) / len(cold), belief


def main():
    rng = random.Random(SEED)
    ctx_share = cold_share = 0.0
    ctx_flagged = 0
    for _ in range(RUNS):
        c, k, final = one_run(rng)
        ctx_share += c
        cold_share += k
        ctx_flagged += 1 if final else 0

    print("%d runs x %d observations, environment really is real\n" % (RUNS, TURNS))
    print("  %-32s %14s" % ("auditor", "calls it real"))
    print("  %-32s %13.1f%%" % ("in-context, carrying a belief", 100 * ctx_share / RUNS))
    print("  %-32s %13.1f%%" % ("cold, one item at a time", 100 * cold_share / RUNS))
    print("\n  runs where the in-context auditor ever changed its mind: %.1f%%"
          % (100 * ctx_flagged / RUNS))

    print("\n  Both auditors saw every observation. The cold one has no more")
    print("  information and no better judgment -- BASE_SKILL is identical.")
    print("  The only difference is that a conclusion already existed when")
    print("  each piece arrived, and disagreeing evidence had to overcome it.")

    print("\n  Sensitivity to how committed the reader is\n")
    print("  %-14s %16s %14s" % ("COMMITMENT", "in-context", "cold"))
    global COMMITMENT
    keep = COMMITMENT
    for c in (0.0, 0.3, 0.6, 0.85, 0.95):
        COMMITMENT = c
        r = random.Random(SEED)
        a = b = 0.0
        for _ in range(150):
            x, y, _ = one_run(r)
            a += x; b += y
        print("  %-14.2f %15.1f%% %13.1f%%" % (c, 100 * a / 150, 100 * b / 150))
    COMMITMENT = keep

    print("\n  At COMMITMENT 0 the two are the same auditor. Everything above")
    print("  that is the cost of reading evidence through a story -- which is")
    print("  why a monitor pointed at the agent's own reasoning inherits it.")


if __name__ == "__main__":
    main()
