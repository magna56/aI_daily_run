"""How much of a benchmark score belongs to the harness.

The model is held fixed. Only the scaffolding changes: how many past observations
survive to the next step. That alone reproduces both effects in the ARC-AGI-3
results -- a large spread across reasoning-effort settings on one harness and
none on the other, and an effort knob that runs backwards on one of them.

This reproduces the SHAPE of that result, not its percentages. The claim being
demonstrated is that the ranking of your settings can be a property of your
scaffold rather than of the model.

The task is a combination lock. The agent probes one dial at a time and is told
whether it was right, so remembering what it already tried is the whole game.
That is what makes it a task that carries state, which is exactly when the
harness owns a share of the score.

Run: python3 code_example.py

Raise NOTE_BUDGET and watch the two harnesses converge.
"""

from collections import namedtuple

# --- knobs: edit these ---------------------------------------------------
NOTE_BUDGET = 14      # tokens the neutral harness lets the agent carry forward
VALUES = 8            # candidate values per dial before any reasoning
STEP_BUDGET = 32      # probes allowed per episode
EPISODES = 300

# (name, candidates ruled out by reasoning, note tokens written per step).
# Reasoning is sound here: it never prunes away the answer. Its only cost is
# that the notes justifying it compete with observations for the same budget.
EFFORTS = [("none", 0, 0), ("low", 1, 7), ("medium", 3, 8),
           ("high", 5, 9), ("xhigh", 6, 10), ("max", 7, 11)]

Harness = namedtuple("Harness", "name budget carries_reasoning")

NEUTRAL = Harness("neutral", NOTE_BUDGET, False)
PROVIDER = Harness("provider", None, True)


def retained_probes(harness, verbosity):
    """How many past probes the agent can still see. This is the whole mechanism.

    On the neutral harness every step writes one observation plus the model's
    reasoning notes, and both come out of one fixed budget -- so a chattier
    setting remembers fewer probes. The provider harness keeps reasoning state
    outside that budget, so notes never evict observations.
    """
    if harness.carries_reasoning:
        return None                       # unbounded: nothing is forgotten
    return max(1, harness.budget // (1 + verbosity))


def solve(secret, elim, window):
    """Run one episode. True if every dial was opened inside STEP_BUDGET.

    The agent walks its candidate list in order and skips values it can still
    see itself having tried. Anything outside the window is forgotten, so it
    retries values it already ruled out -- and can cycle forever.
    """
    size = max(1, VALUES - elim)          # reasoning narrows the search
    history, steps, dial = [], 0, 0
    while dial < len(secret) and steps < STEP_BUDGET:
        answer = secret[dial] % size
        seen = history if window is None else history[-window:]
        tried = {v for (d, v) in seen if d == dial}
        guess = next((v for v in range(size) if v not in tried), 0)
        history.append((dial, guess))
        steps += 1
        if guess == answer:
            dial += 1
    return dial == len(secret)


def lcg(seed):
    """Seeded generator, so every run of this file prints the same table."""
    state = seed
    def nxt():
        nonlocal state
        state = (state * 1664525 + 1013904223) % (2 ** 32)
        return state
    return nxt


def score(harness, elim, verbosity):
    """Percentage of episodes solved, over one fixed set of locks."""
    window = retained_probes(harness, verbosity)
    rand, solved = lcg(4242), 0
    for _ in range(EPISODES):
        dials = 2 + rand() % 5            # tasks vary in length
        secret = [rand() % VALUES for _ in range(dials)]
        solved += solve(secret, elim, window)
    return 100.0 * solved / EPISODES


def main():
    rows = [(name, score(NEUTRAL, elim, verb), score(PROVIDER, elim, verb),
             retained_probes(NEUTRAL, verb))
            for name, elim, verb in EFFORTS]

    print("One model, one task, two harnesses (note budget = %d tokens)\n" % NOTE_BUDGET)
    print("  %-8s %9s %9s   %s" % ("effort", "neutral", "provider", "probes remembered"))
    for name, a, b, w in rows:
        print("  %-8s %8.1f%% %8.1f%%   %d" % (name, a, b, w))

    neu = [r[1] for r in rows]
    pro = [r[2] for r in rows]
    print("\n  spread across effort settings")
    print("    neutral   %5.1f points   (%.1f%% to %.1f%%)" % (max(neu) - min(neu), min(neu), max(neu)))
    print("    provider  %5.1f points   (%.1f%% to %.1f%%)" % (max(pro) - min(pro), min(pro), max(pro)))

    # A knob that runs backwards is the scaffold talking, not the model.
    def backwards(col):
        return [rows[i + 1][0] + " < " + rows[i][0]
                for i in range(len(rows) - 1) if rows[i + 1][col] < rows[i][col]]
    print("\n  settings that score WORSE than the setting below them")
    print("    neutral   %s" % (", ".join(backwards(1)) or "none"))
    print("    provider  %s" % (", ".join(backwards(2)) or "none"))

    print("\n  Identical weights in every row. On the neutral harness the effort")
    print("  knob looks like the whole story; on the provider harness it is worth")
    print("  nothing. An ablation run on one scaffold does not transfer to the other.")


if __name__ == "__main__":
    main()
