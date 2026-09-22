"""Ask the whole decision tree in one call, then throw most of it away.

A structured-decision model evaluates every question in parallel and in
isolation against one shared state. That changes the arithmetic you learned
from chaining LLM calls: an extra question costs almost no latency, and the
state is sent once instead of once per round trip.

So the cheap design is the wasteful-looking one -- ask everything up front,
including the questions you probably will not need, and discard the branches
that turn out to be irrelevant.

This models both shapes over the same ticket workload and prints what each
costs. Run: python3 code_example.py
"""

import random

# --- The knob. Change this and watch the conclusion move. --------------------
# Tokens in the shared state (the ticket, the thread, the app context).
# Chaining re-sends this on EVERY round trip. Fan-out sends it once, which is
# why asking more questions can cost fewer input tokens.
STATE_TOKENS = 600

SEED, TICKETS = 5, 400
LATENCY_PER_CALL_S = 0.114     # one structured-decision call, any question count
ANSWER_TOKENS = 12             # a typed answer is tiny next to prose


# --- Liftable core: a decision tree as data ----------------------------------

class Question:
    """One typed question. `needs` makes it speculative: it is only USED when
    the predicate holds, but under fan-out it is still ASKED regardless."""

    def __init__(self, qid, kind, needs=None):
        self.qid, self.kind, self.needs = qid, kind, needs

    def used(self, answers):
        return self.needs is None or self.needs(answers)


TRIAGE = [
    Question("category", "choice"),
    Question("frustration", "score"),
    Question("refund_requested", "noul"),
    # speculative: only meaningful once category is known to be a bug
    Question("bug_severity", "score", needs=lambda a: a["category"] == "bug_report"),
    Question("has_repro", "noul", needs=lambda a: a["category"] == "bug_report"),
]


def waves(questions):
    """Split into dependency waves. Each wave is one round trip when chaining.

    Anything with `needs` cannot be asked until the answers it reads exist, so
    chaining pays a round trip per wave. Fan-out collapses every wave into one.
    """
    first = [q for q in questions if q.needs is None]
    later = [q for q in questions if q.needs is not None]
    return [first, later] if later else [first]


def ask_chained(questions, answer_fn):
    """One round trip per wave, re-sending the state each time."""
    answers, trips, asked, in_tokens = {}, 0, 0, 0
    for wave in waves(questions):
        live = [q for q in wave if q.used(answers)] if answers else wave
        if not live:
            continue
        trips += 1
        in_tokens += STATE_TOKENS          # the state goes again, every trip
        for q in live:
            answers[q.qid] = answer_fn(q)
            asked += 1
    return answers, trips, asked, in_tokens


def ask_fanout(questions, answer_fn):
    """One round trip, every question, state sent once. Filter afterwards."""
    answers = {q.qid: answer_fn(q) for q in questions}
    used = {q.qid: answers[q.qid] for q in questions if q.used(answers)}
    return used, 1, len(questions), STATE_TOKENS


# --- The demonstration --------------------------------------------------------

def make_model(rng):
    """A deterministic stand-in for the model. Returns typed values, the shape
    the real API returns: a choice, a score, or a noul between 0 and 1."""
    def answer(q):
        if q.kind == "choice":
            return rng.choice(["bug_report", "billing", "how_to", "bug_report"])
        if q.kind == "score":
            return round(rng.uniform(0, 3), 2)
        return round(rng.random(), 2)
    return answer


def run(strategy, label):
    rng = random.Random(SEED)
    model = make_model(rng)
    trips = asked = used = in_tok = 0
    for _ in range(TICKETS):
        answers, t, a, i = strategy(TRIAGE, model)
        trips, asked, used, in_tok = trips + t, asked + a, used + len(answers), in_tok + i
    out_tok = asked * ANSWER_TOKENS
    latency = trips / TICKETS * LATENCY_PER_CALL_S
    print(f"\n{label}")
    print(f"  round trips per ticket : {trips / TICKETS:.2f}")
    print(f"  latency per ticket     : {latency * 1000:.0f} ms")
    print(f"  questions asked / used : {asked / TICKETS:.2f} / {used / TICKETS:.2f}")
    print(f"  input tokens per ticket: {in_tok / TICKETS:.0f}   (state re-sent per trip)")
    print(f"  output tokens per ticket: {out_tok / TICKETS:.0f}")
    return trips / TICKETS, latency, (in_tok + out_tok) / TICKETS, asked / TICKETS, used / TICKETS


def main():
    print(f"{TICKETS} tickets, state = {STATE_TOKENS} tokens, "
          f"{LATENCY_PER_CALL_S * 1000:.0f} ms per call")

    c_trips, c_lat, c_tok, c_ask, c_use = run(ask_chained, "Chained: ask, branch, ask again")
    f_trips, f_lat, f_tok, f_ask, f_use = run(ask_fanout, "Fan-out: ask everything, discard the rest")

    print("\n--- what the wasteful-looking design actually costs ---")
    print(f"  fan-out asks {f_ask - c_ask:+.2f} more questions per ticket")
    print(f"  and discards {f_ask - f_use:.2f} of them as irrelevant "
          f"({(f_ask - f_use) / f_ask:.0%} of everything it asked)")
    print(f"  yet uses {c_tok / f_tok:.2f}x FEWER tokens, because the state is sent once")
    print(f"  and {c_lat / f_lat:.2f}x less latency, because it is one round trip")

    print("\n  Chaining re-sends the state on every trip. That is the whole")
    print("  asymmetry: the questions are cheap, the context is not.")


if __name__ == "__main__":
    main()
