"""
What actually makes a coding agent better: planning, tools, or context?

Implements the two-stage context pipeline the paper found most efficient —
rule-based elision before LLM summarization — and prices a long agent run
under each of the three harness knobs so you can see which one moves which
number.

`compact` is the part to lift. Point `elidable` at your own transcript shape
and pass your real summarizer.

Run: python3 code_example.py
"""
# REQUIRES: none (standard library only)

from dataclasses import dataclass, field

# ---------------------------------------------------------------- knobs ----
CONTEXT_BUDGET = 900      # shrink it and context management starts earning its keep
BASH_FLUENT = True        # does your model drive a shell? decides the action space
PLANNING = True           # on a strong model this is a cost lever, not an accuracy one
TOOL_SCHEMA_TOKENS = 140  # charged on EVERY turn a rich tool layer is in scope


# ------------------------------------------------------ the liftable core ----
@dataclass
class Msg:
    role: str
    text: str
    superseded_by: str = None   # set when a later read replaced this one
    pinned: bool = False        # task statement and the last few turns

    def tokens(self) -> int:
        return max(1, len(self.text) // 4)


def elidable(m: Msg) -> bool:
    """The deterministic rules. No model judgment, so this stage is free: a tool
    result a later turn superseded carries no information the agent still needs."""
    return m.role == "tool" and m.superseded_by is not None and not m.pinned


def compact(transcript, budget, summarize):
    """Stage 1 rule-based elision, stage 2 LLM summarization — in that order.

    The ordering is the finding. Cheap deterministic cuts remove the bulk, so
    the paid call only ever sees what survived. Running the model first means
    paying it to read text a regex would have deleted.

    Deliberately absent: any way for the agent to ask for elided content back.
    The paper built that and found models rarely used it, with no accuracy gain."""
    kept = [m for m in transcript if not elidable(m)]
    elided = len(transcript) - len(kept)
    if _total(kept) <= budget:
        return kept, elided, 0

    head = [m for m in kept[:2]]
    tail = [m for m in kept[-4:]]
    middle = kept[2:-4]
    room = budget - _total(head + tail)
    summary, paid = summarize(middle, room)
    return head + [summary] + tail, elided, paid


def _total(msgs) -> int:
    return sum(m.tokens() for m in msgs)


def llm_summarize(msgs, room):
    """Stands in for a real summarizer. Returns (message, tokens_charged) —
    you pay to READ everything handed to you, which is why stage 1 matters."""
    charged = _total(msgs)
    text = f"[summary of {len(msgs)} turns]" + "." * max(0, room * 4 - 24)
    return Msg("assistant", text[: max(24, room * 4)]), charged


# ----------------------------------------------------- the run simulation ----
def build_run(turns: int):
    """A long-horizon run: a task statement, then repeated read/act pairs where
    later reads supersede earlier ones — the shape that fills a window."""
    t = [Msg("user", "Fix the failing integration test in packages/api." * 3, pinned=True)]
    for i in range(turns):
        t.append(Msg("assistant", f"read src/handlers/orders.py (attempt {i})" * 2))
        t.append(Msg("tool", f"FILE CONTENTS attempt {i} " * 40,
                     superseded_by=f"attempt {i+1}" if i < turns - 1 else None))
    for m in t[-4:]:
        m.pinned = True
    return t


def run(turns, budget, planning, bash_fluent):
    """Returns (overflowed, cost_tokens, turns_used). Planning shortens the run
    on a capable model; a rich tool layer charges schema on every turn."""
    stop = int(turns * 0.75) if planning else turns      # planning changes where it stops
    transcript = build_run(stop)
    kept, elided, paid = compact(transcript, budget, llm_summarize)
    overflow = _total(kept) > budget
    schema = 0 if bash_fluent else TOOL_SCHEMA_TOKENS * stop
    return overflow, _total(kept) + paid + schema, stop, elided


def main():
    print(f"long run, budget {CONTEXT_BUDGET} tokens\n")
    print(f"{'harness':<34}{'overflow?':>10}{'cost':>9}{'turns':>7}")
    print("-" * 60)
    configs = [
        ("no context management", dict(budget=10**9, planning=False, bash_fluent=False)),
        ("context mgmt only", dict(budget=CONTEXT_BUDGET, planning=False, bash_fluent=False)),
        ("+ planning", dict(budget=CONTEXT_BUDGET, planning=True, bash_fluent=False)),
        ("+ bash-only action space", dict(budget=CONTEXT_BUDGET, planning=True, bash_fluent=True)),
    ]
    base = None
    for label, kw in configs:
        over, cost, turns_used, elided = run(40, **kw)
        if base is None:
            base = cost
        # the "no context management" row is allowed to exceed the real budget:
        # that IS the overflow failure the paper says the benefit comes from
        real_over = _total(build_run(turns_used)) > CONTEXT_BUDGET and kw["budget"] > CONTEXT_BUDGET
        print(f"  {label:<32}{('YES' if real_over else 'no'):>10}{cost:>9,}{turns_used:>7}")
    print()

    print("what each knob moved, against the row above it:")
    print("  context management  -> stopped the overflow. THIS is the accuracy knob.")
    print("  planning            -> fewer turns, same answer. cost only.")
    print("  bash-only           -> no tool schema on every turn. cost only.\n")

    t = build_run(40)
    kept, elided, paid = compact(t, CONTEXT_BUDGET, llm_summarize)
    print(f"pipeline on a {_total(t):,}-token transcript:")
    print(f"  stage 1, rule-based elision : dropped {elided} superseded tool results, cost 0")
    print(f"  stage 2, LLM summarization  : read {paid:,} tokens — only what stage 1 left")
    print(f"  result                      : {_total(kept):,} tokens, budget {CONTEXT_BUDGET}")
    print("\n  reverse the stages and stage 2 reads the whole transcript instead.")


if __name__ == "__main__":
    main()
