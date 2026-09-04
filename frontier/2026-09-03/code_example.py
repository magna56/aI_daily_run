"""The gate that decides whether a skill is allowed into an agent's library.

Implements the two mechanisms from Repo-To-Skill (arXiv:2609.02749) that matter to
anyone authoring skills by hand: admission by execution, and progressive disclosure.
A candidate claims some commands and carries assertion cases lifted from its source,
and the gate runs both against a fixture before the skill is shelved. A failure gets
one repair pass; if it still fails it stays out, and the reason is recorded.

Run: python3 code_example.py -- flip VERIFY to False and watch a skill with a dead
command reach the library and fail at run time instead, which is where it fails today.
"""

from collections import namedtuple

# --- knobs: edit these ---------------------------------------------------
VERIFY = True             # False = shelve every candidate unchecked
ROUTER_TOKENS = 18        # what one skill costs in the router index
LIBRARY_FILLER = 200      # extra skills, to show what the context does at scale

Skill = namedtuple("Skill", "name area family use commands cases body_tokens")

# The fixture: what actually exists in the environment the checks run against.
FIXTURE_COMMANDS = {"python3", "pytest", "pip", "faiss-build"}
FIXTURE_STATE = {"dim": 768, "metric": "ip", "rows": 10_000}

# A skill naming a command removed upstream is the README bug, verbatim. Only some
# have a known replacement; the rest are the ones a gate has to refuse outright.
RENAMES = {"faiss-make-index": "faiss-build"}


def run(cmd, env):
    """Stand-in for a subprocess call. Returns (returncode, message)."""
    program = cmd.split()[0]
    if program not in env:
        return 127, "command not found"
    return 0, "ok"


def evaluate(expr, state):
    """Assertion cases carried over from the source repository's own examples."""
    try:
        return eval(expr, {"__builtins__": {}}, dict(state))
    except Exception as exc:                      # a case that cannot run IS a gap
        return "error: " + type(exc).__name__


def verify(skill, env, state):
    """Return (ok, gaps). A skill only ships when ok is True."""
    gaps = []
    for cmd in skill.commands:
        rc, msg = run(cmd, env)
        if rc != 0:
            gaps.append("`" + cmd + "` exited " + str(rc) + ": " + msg)
    for expr, expected in skill.cases:
        got = evaluate(expr, state)
        if got != expected:
            gaps.append("`" + expr + "` gave " + repr(got) + ", expected " + repr(expected))
    return (not gaps), gaps


def repair(skill, gaps):
    """One local repair pass: the rename that the source moved to."""
    fixed = []
    for cmd in skill.commands:
        program = cmd.split()[0]
        fixed.append(cmd.replace(program, RENAMES[program], 1) if program in RENAMES else cmd)
    return skill._replace(commands=fixed)


def admit(candidates, env, state, gate=True):
    """The pipeline's last stage. Returns (library, construction_records)."""
    library, records = [], []
    for skill in candidates:
        ok, gaps = verify(skill, env, state) if gate else (True, [])
        repaired = False
        if not ok:
            skill = repair(skill, gaps)
            ok, gaps = verify(skill, env, state)
            repaired = True
        records.append({"name": skill.name, "checks": len(skill.commands) + len(skill.cases),
                        "repaired": repaired, "gaps": gaps, "admitted": ok})
        if ok:
            library.append(skill)
    return library, records


def load_for_task(task_words, library):
    """Progressive disclosure: the router is always read, bodies only on a match."""
    router_cost = ROUTER_TOKENS * len(library)
    opened = [s for s in library if any(w in s.use.lower() for w in task_words)]
    return opened, router_cost + sum(s.body_tokens for s in opened)


CANDIDATES = [
    Skill("faiss-index", "retrieval", "vector-search",
          "Build and query a vector index for approximate nearest neighbors.",
          ["faiss-make-index --dim 768"], [("dim == 768", True)], 4200),
    Skill("pytest-harness", "engineering", "testing",
          "Run a repository's test suite and read the failures.",
          ["pytest -q"], [("rows > 1000", True)], 3100),
    Skill("env-bootstrap", "engineering", "setup",
          "Set up a clean environment before running anything else.",
          ["make bootstrap"], [], 2400),
    Skill("metric-choice", "retrieval", "vector-search",
          "Choose an index metric for nearest neighbor search.",
          ["python3 -c pass"], [("metric == 'cosine'", True)], 2800),
    Skill("shard-planner", "serving", "scaling",
          "Plan shard counts for a large index that will not fit in memory.",
          ["python3 -c pass"], [("rows // 1000", 10)], 3600),
]


def main():
    filler = [Skill("filler-%d" % i, "misc", "misc", "unrelated capability number %d" % i,
                    [], [], 3000) for i in range(LIBRARY_FILLER)]
    candidates = CANDIDATES + filler

    library, records = admit(candidates, FIXTURE_COMMANDS, FIXTURE_STATE, gate=VERIFY)

    print("Admission gate (VERIFY = %s)\n" % VERIFY)
    for r in records[:len(CANDIDATES)]:
        mark = "admitted" if r["admitted"] else "REJECTED"
        note = " (repaired)" if r["repaired"] and r["admitted"] else ""
        print("  %-16s %-9s %d check(s)%s" % (r["name"], mark, r["checks"], note))
        for g in r["gaps"]:
            print("      gap: " + g)

    kept = sum(1 for r in records if r["admitted"])
    print("\n  %d of %d shelved, %d rejected with the reason recorded."
          % (kept, len(records), len(records) - kept))
    print("\nProgressive disclosure on one task: \"index these vectors\"")
    opened, cost = load_for_task(["vector", "index"], library)
    whole = sum(s.body_tokens for s in library)
    print("  library holds            %6d skills / %8d tokens" % (len(library), whole))
    print("  opened for this task     %6d skills / %8d tokens" % (len(opened), cost))
    print("  share of the library read %5.1f%%" % (100.0 * cost / whole))
    print("  ->", ", ".join(s.name for s in opened) or "nothing matched")

    if VERIFY:
        ungated, _ = admit(candidates, FIXTURE_COMMANDS, FIXTURE_STATE, gate=False)
        picked, _ = load_for_task(["vector", "index"], ungated)
        bad = [s for s in picked if not verify(s, FIXTURE_COMMANDS, FIXTURE_STATE)[0]]
        print("\nWith the gate off, the same task opens %d skill(s), %d of which fail"
              % (len(picked), len(bad)))
        print("  at run time instead of at admission: %s"
              % (", ".join(s.name for s in bad) or "none"))


if __name__ == "__main__":
    main()
