"""
Bun-in-Rust Engineering Practices — a runnable simulation
=========================================================

Demonstrates the three practices that made ~1M lines of agent-generated Rust
trustworthy enough to ship (Bun rewrite, May 2026):

  1. Conformance suite as an EXTERNAL, deterministic correctness oracle.
  2. Adversarial code review with SPLIT context windows (reviewer sees only
     the diff + "assume it is wrong" — not the author's justification).
  3. "Fix the process, not the code" — failures mutate the LOOP'S RULE SET,
     killing a whole bug *class* rather than patching one diff.

No API keys, no network. The "LLM" agents are deterministic stand-ins so the
economics of each strategy are visible and reproducible.

Run:  python3 code_example.py
"""

from dataclasses import dataclass, field
from typing import Callable

# ---------------------------------------------------------------------------
# The task: "port" N functions. Each generated function may carry a bug from
# one of three classes — the exact classes the real Bun run hit. Each bug
# COMPILES and looks plausible; only behavior (or an adversarial eye) reveals it.
# ---------------------------------------------------------------------------

BUG_CLASSES = ("use_after_free", "sign_error", "eager_eval")


@dataclass
class Function:
    name: str
    bug: str | None          # None == correct
    author_note: str         # the plausible-sounding justification the author emits


def generate_functions(n: int, seed: int) -> list[Function]:
    """Deterministic 'implementer'. ~55% of ports carry a subtle bug."""
    fns = []
    for i in range(n):
        # cheap deterministic PRNG (no Math.random — reproducible)
        r = (seed * 1103515245 + i * 12345) % 100
        if r < 45:
            bug = None
            note = "faithful port; behavior matches original"
        else:
            bug = BUG_CLASSES[r % 3]
            note = {
                "use_after_free": "Box drops at end of match arm; libuv keeps handle — looks fine, compiles",
                "sign_error": "trunc() on the mtime; rounds toward zero, seems reasonable",
                "eager_eval": "unwrap_or(fallback) for the color channel; concise and readable",
            }[bug]
        fns.append(Function(f"fn_{i:02d}", bug, note))
    return fns


# ---------------------------------------------------------------------------
# Reviewers. The whole point: context shapes what a reviewer can catch.
# ---------------------------------------------------------------------------

def naive_reviewer(fn: Function, active_rules: set[str]) -> bool:
    """
    Sees the author's justification too. Tends to RATIONALIZE from intent —
    a plausible author_note lulls it into approving. Misses subtle bugs.
    """
    if fn.bug is None:
        return True
    # A convincing note gets waved through unless a rule explicitly forbids it.
    return fn.bug not in active_rules  # only catches classes it has a rule for... but read-with-intent, so 50/50 even then
        # note: naive path below overrides


def adversarial_reviewer(fn: Function, active_rules: set[str], lens: str) -> bool:
    """
    Sees ONLY the diff + "assume it is wrong." Each reviewer has a lens
    (ownership / arithmetic / evaluation). Catches bugs in its lens, and
    ALWAYS catches any class currently covered by an explicit process rule.

    Returns True == approved (no bug found), False == rejected (bug found).
    """
    lens_catch = {
        "ownership": {"use_after_free"},
        "arithmetic": {"sign_error"},
        "evaluation": {"eager_eval"},
    }[lens]
    if fn.bug is None:
        return True
    if fn.bug in active_rules:      # process rule makes it systematically catchable
        return False
    if fn.bug in lens_catch:        # this reviewer's specialty
        return False
    return True                      # outside lens & no rule -> slips past THIS reviewer


# ---------------------------------------------------------------------------
# Conformance suite: the external oracle. Deterministic. Catches ANY bug that
# reaches it — but running the full suite is "expensive", so we count invocations.
# ---------------------------------------------------------------------------

@dataclass
class Stats:
    reviewed: int = 0
    merged_buggy: int = 0
    caught_in_review: int = 0
    caught_by_suite: int = 0
    suite_runs: int = 0


def merge_loop(fns: list[Function], strategy: str, active_rules: set[str]) -> Stats:
    s = Stats()
    for fn in fns:
        s.reviewed += 1
        approved = True

        if strategy == "no_review":
            approved = True
        elif strategy == "single_naive":
            # one reviewer, reads WITH author intent -> misses ~half of subtle bugs
            approved = fn.bug is None or (fn.bug in active_rules)
        elif strategy == "adversarial":
            # two adversarial reviewers, diff-only, complementary lenses
            r1 = adversarial_reviewer(fn, active_rules, "ownership")
            r2 = adversarial_reviewer(fn, active_rules, "arithmetic")
            r3 = adversarial_reviewer(fn, active_rules, "evaluation")
            approved = r1 and r2 and r3   # rejected if ANY reviewer flags it

        if not approved:
            s.caught_in_review += 1
            continue  # fixer would repair; excluded from merge

        # Conformance gate runs on everything that passed review (external oracle).
        s.suite_runs += 1
        if fn.bug is not None:
            s.caught_by_suite += 1        # oracle never lies
        # If it truly reaches production buggy, that's an escape:
        # (in this model the suite catches all, so escapes only happen if we skip it)
    return s


def run_no_suite(fns: list[Function], strategy: str, active_rules: set[str]) -> Stats:
    """Variant WITHOUT the conformance oracle — shows what review alone lets through."""
    s = Stats()
    for fn in fns:
        s.reviewed += 1
        if strategy == "single_naive":
            # A process rule CATCHES its bug class; anything with no rule slips
            # past the naive reviewer. Inverting this made each added rule ship
            # more bugs, i.e. the exact opposite of the point being made.
            approved = fn.bug is None or (fn.bug not in active_rules)
        else:  # adversarial
            approved = all(
                adversarial_reviewer(fn, active_rules, l)
                for l in ("ownership", "arithmetic", "evaluation")
            )
        if not approved:
            s.caught_in_review += 1
        elif fn.bug is not None:
            s.merged_buggy += 1           # ESCAPE: buggy code shipped
    return s


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def pct(n, d): return f"{100*n/d:5.1f}%" if d else "  n/a"


def main():
    N = 200
    fns = generate_functions(N, seed=7)
    n_buggy = sum(1 for f in fns if f.bug)
    print("=" * 70)
    print(f"Simulated port: {N} functions, {n_buggy} carry a subtle (compiling) bug")
    print("=" * 70)

    # --- Practice 2: review economics, NO oracle (review is the only defense) ---
    print("\n[Review alone — no conformance suite] escapes to production:")
    for strat in ("single_naive", "adversarial"):
        s = run_no_suite(fns, strat, active_rules=set())
        print(f"  {strat:14s}: caught {s.caught_in_review:3d}/{n_buggy}  "
              f"| SHIPPED BUGGY {s.merged_buggy:3d}  ({pct(s.merged_buggy, n_buggy)} escape)")

    # --- Practice 1: add the external oracle. Adversarial review + suite ---
    print("\n[Adversarial review + conformance oracle] defense in depth:")
    s = merge_loop(fns, "adversarial", active_rules=set())
    print(f"  caught in review: {s.caught_in_review:3d}   "
          f"caught by suite: {s.caught_by_suite:3d}   suite runs: {s.suite_runs}")
    print(f"  -> total buggy stopped: {s.caught_in_review + s.caught_by_suite}/{n_buggy}  "
          f"({pct(s.caught_in_review + s.caught_by_suite, n_buggy)})")
    print("     (the oracle is the backstop the reviewers can't hallucinate past)")

    # --- Practice 3: "fix the process, not the code" ---
    # Observe the dominant escaping bug class under single-naive review, then
    # add a PROCESS RULE for it. Watch that whole class vanish next iteration.
    print("\n[Fix the process, not the code] mutate the loop's rule set:")
    rules: set[str] = set()
    for iteration in range(1, 4):
        s = run_no_suite(fns, "single_naive", active_rules=rules)
        # find worst remaining escaping class
        escapes: dict[str, int] = {}
        for f in fns:
            if f.bug and f.bug not in rules:
                approved = True  # single_naive with intent misses it
                if approved:
                    escapes[f.bug] = escapes.get(f.bug, 0) + 1
        worst = max(escapes, key=escapes.get) if escapes else None
        # Render the rule set before padding it: ":<40" applied to the
        # `sorted(...) or '[]'` expression hits list.__format__ as soon as the
        # set is non-empty, which is every iteration after the first.
        rules_txt = ", ".join(sorted(rules)) or "[]"
        print(f"  iter {iteration}: rules={rules_txt:<40} "
              f"shipped_buggy={s.merged_buggy:3d}")
        if worst is None:
            print("           all bug classes covered by process rules — loop is clean")
            break
        rules.add(worst)  # edit the LOOP, not the diff
        print(f"           worst class = '{worst}'  ->  add process rule, resume")

    print("\nTakeaway: patching diffs is O(bugs); patching the loop is O(bug-classes).")
    print("Bun fixed ~16k compiler errors + subtle logic bugs across 64 agents this way.")


if __name__ == "__main__":
    main()
