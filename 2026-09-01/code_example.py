"""
A borrowed test suite as an oracle.

Builds a small `retry` implementation with one subtle bug, then checks it two
ways: against tests written from the same misunderstanding that produced the bug,
and against a suite ported from a mature reference implementation.

The self-written suite goes green. The borrowed one does not. That gap is the
whole argument -- tests and code that share an author share a blind spot.

Pure stdlib. Run: python3 code_example.py
"""

import itertools

# Knob: flip to True to "fix" the candidate and watch the borrowed suite go green.
FIXED = False


# --- The reference: a mature implementation we did not write ------------------

def reference_backoff(attempt, base=1.0, cap=30.0):
    """Exponential backoff, the way the established libraries define it.

    Attempt numbering starts at 1, and the FIRST retry waits `base` -- not
    `base * 2`. The cap is applied after doubling, never before."""
    return min(cap, base * (2 ** (attempt - 1)))


# --- The candidate: what the agent wrote --------------------------------------

def candidate_backoff(attempt, base=1.0, cap=30.0):
    """The bug: off by one in the exponent, so every wait is doubled. It is a
    completely reasonable misreading of 'exponential backoff' and produces
    plausible numbers, which is exactly why review misses it."""
    if FIXED:
        return min(cap, base * (2 ** (attempt - 1)))
    return min(cap, base * (2 ** attempt))


# --- The suite the agent wrote for its own code -------------------------------

def agent_written_tests(fn):
    """Written from the same mental model as the implementation. Note that every
    assertion is real, specific, and passes -- it is not a lazy suite. It is a
    confident suite that encodes the same misunderstanding."""
    cases = [
        ("waits grow",        lambda: fn(2) > fn(1)),
        ("first wait is set", lambda: fn(1) == 2.0),      # agrees with the bug
        ("respects the cap",  lambda: fn(99) == 30.0),
        ("cap is a ceiling",  lambda: all(fn(a) <= 30.0 for a in range(1, 50))),
        ("is deterministic",  lambda: fn(3) == fn(3)),
    ]
    return [(name, bool(check())) for name, check in cases]


# --- The suite ported from the reference project ------------------------------

def borrowed_tests(fn, oracle):
    """The port keeps each assertion's MEANING and only changes the call site.
    Nothing here was written with knowledge of our implementation, which is the
    entire property that makes it useful."""
    cases = [
        ("first retry waits base",   lambda: fn(1) == oracle(1)),
        ("second retry doubles",     lambda: fn(2) == oracle(2)),
        ("third retry doubles again", lambda: fn(3) == oracle(3)),
        ("cap applies after doubling",
         lambda: fn(10, base=1.0, cap=30.0) == oracle(10, base=1.0, cap=30.0)),
        ("honours a custom base",    lambda: fn(1, base=0.5) == oracle(1, base=0.5)),
    ]
    return [(name, bool(check())) for name, check in cases]


# --- The liftable core: run both, and report the divergence -------------------

def run_suite(name, results):
    passed = sum(1 for _, ok in results if ok)
    print(f"  {name:<28} {passed}/{len(results)} passed")
    for label, ok in results:
        if not ok:
            print(f"      FAIL  {label}")
    return passed, len(results)


def first_divergence(fn, oracle, attempts=range(1, 8)):
    """Where do the two implementations first disagree? This is the output you
    actually act on -- a failing test name tells you something is wrong, this
    tells you where to look."""
    for a in attempts:
        got, want = fn(a), oracle(a)
        if got != want:
            return a, got, want
    return None


def main():
    print(f"candidate FIXED = {FIXED}\n")

    print("suite written by the same author as the code:")
    self_passed, self_total = run_suite("agent-written", agent_written_tests(candidate_backoff))

    print("\nsuite ported from the reference project:")
    borrowed_passed, borrowed_total = run_suite(
        "borrowed oracle", borrowed_tests(candidate_backoff, reference_backoff))

    div = first_divergence(candidate_backoff, reference_backoff)
    print()
    if div:
        a, got, want = div
        print(f"first divergence at attempt {a}: candidate waits {got}s, reference waits {want}s")
    else:
        print("no divergence across the checked attempts")

    print("\nattempt   candidate   reference")
    for a in itertools.islice(itertools.count(1), 6):
        mark = " " if candidate_backoff(a) == reference_backoff(a) else "  <-- differs"
        print(f"  {a:<8}  {candidate_backoff(a):>7.1f}   {reference_backoff(a):>7.1f}{mark}")

    print(f"\nSelf-written: {self_passed}/{self_total}. Borrowed: {borrowed_passed}/{borrowed_total}.")
    print("Both suites are specific and neither is lazy. Only one was written by")
    print("someone who did not already believe the bug.")
    print()
    print("Now set FIXED = True and run again. The borrowed suite goes 5/5 without a")
    print("single assertion changing -- and the agent-written suite starts FAILING,")
    print("because 'first wait is set' asserted the bug. A suite written alongside the")
    print("code does not merely miss that class of bug; it defends it.")


if __name__ == "__main__":
    main()
