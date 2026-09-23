"""More agents finish more work. Do they finish more work per token?

Agensh reports that scaling a leaderless agent organization from 1 worker to
1,024 raises the final test-pass rate from 33.89% to 55.06%. The headline is
that agent count is a new scaling dimension.

The number the paper does not normalize is spend. A thousand workers burn
roughly a thousand times the tokens, so a rising pass rate is only an
ORGANIZATIONAL result if it beats simply giving one worker more attempts.

This implements the claim-and-share loop and reports both curves: raw pass
rate, and pass rate per million tokens. Run: python3 code_example.py
"""

import random

# --- The knob. Change this and watch the conclusion flip. --------------------
# How much a finding shared by one worker helps everyone else. This is the
# whole case for an organization: at 0.0 the workers are just parallel retries
# and agent count buys nothing a bigger attempt budget would not.
SHARE_LIFT = 0.035

SEED, TRIALS, SUBTASKS = 11, 80, 60
BASE_SUCCESS = 0.04          # chance one worker closes one subtask per attempt
TOKENS_PER_ATTEMPT = 9_000   # context gathering plus the attempt itself
CONTENTION = 0.04            # chance a claim collides and the work is redundant


# --- Liftable core: the claim protocol ---------------------------------------

class Workspace:
    """Shared state: proposed, ongoing, completed. No central orchestrator.

    The only thing that must be atomic is the claim. Everything else -- sharing
    findings, merging results -- can be eventually consistent, which is what
    lets this scale past one coordinator's context window.
    """

    def __init__(self, subtasks):
        self.open = set(range(subtasks))
        self.claimed = {}            # subtask -> worker id
        self.done = set()
        self.findings = 0            # shared context every worker reads

    def claim(self, worker, rng):
        """Atomic claim. Returns None when nothing is left to do."""
        free = [t for t in self.open if t not in self.claimed]
        if not free:
            return None
        task = rng.choice(free)
        # A real system uses compare-and-set plus a lease so a dead worker's
        # task returns to the pool. Contention is what that costs you.
        if rng.random() < CONTENTION:
            return None
        self.claimed[task] = worker
        return task

    def complete(self, task, ok):
        self.claimed.pop(task, None)
        if ok:
            self.open.discard(task)
            self.done.add(task)
            self.findings += 1       # the finding is now everyone's

    def success_rate(self):
        # Shared findings lift everyone, with diminishing returns.
        return min(0.95, BASE_SUCCESS + SHARE_LIFT * (self.findings ** 0.5))


def run_organization(n_workers, rounds, rng):
    """One trial: n workers cycling claim -> act -> share -> merge."""
    ws = Workspace(SUBTASKS)
    tokens = 0
    for _ in range(rounds):
        if not ws.open:
            break
        for worker in range(n_workers):
            task = ws.claim(worker, rng)
            if task is None:
                continue
            tokens += TOKENS_PER_ATTEMPT
            ws.complete(task, rng.random() < ws.success_rate())
    return len(ws.done) / SUBTASKS, tokens


def measure(n_workers, rounds, seed):
    rng = random.Random(seed)
    passed = spend = 0.0
    for _ in range(TRIALS):
        p, t = run_organization(n_workers, rounds, rng)
        passed += p
        spend += t
    return passed / TRIALS, spend / TRIALS


def main():
    print(f"{TRIALS} trials, {SUBTASKS} subtasks, share lift {SHARE_LIFT}\n")
    print("Fixed rounds, more workers -- the paper's comparison:\n")
    print(f"{'workers':>8}{'rounds':>8}{'pass rate':>12}{'tokens':>12}{'pass per Mtok':>16}")
    print("-" * 56)
    rows = []
    for n in (1, 2, 4, 8, 16, 32, 64):
        p, t = measure(n, rounds=30, seed=SEED)
        eff = p / (t / 1_000_000) if t else 0
        rows.append((n, p, t, eff))
        print(f"{n:>8}{30:>8}{p:>11.1%}{t:>12,.0f}{eff:>16.2f}")

    print("\nSame token budget instead, spent different ways.")
    print("Rounds are the wall-clock column: 1 worker needs 1,920 to spend what 64 spend in 30.\n")
    print(f"{'workers':>8}{'rounds':>8}{'pass rate':>12}{'tokens':>12}{'pass per Mtok':>16}")
    print("-" * 56)
    equal = []
    for n, rounds in ((1, 1920), (8, 240), (64, 30)):
        p, t = measure(n, rounds=rounds, seed=SEED)
        eff = p / (t / 1_000_000) if t else 0
        equal.append((n, rounds, p, eff))
        print(f"{n:>8}{rounds:>8}{p:>11.1%}{t:>12,.0f}{eff:>16.2f}")

    one, crowd = equal[0], equal[-1]
    print(f"\nAt matched spend the crowd scores {crowd[2] - one[2]:+.1%} against one worker,")
    print(f"and gets there in {one[1] // crowd[1]}x fewer rounds.")
    print("\nThat is the honest shape of the result: agent count buys WALL CLOCK,")
    print("and buys quality only as far as workers share findings. It never buys tokens.")
    print("Set SHARE_LIFT to 0.0 and the quality gap closes entirely.")


if __name__ == "__main__":
    main()
