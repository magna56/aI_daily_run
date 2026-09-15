"""Triage what a coding-agent audit reports, instead of reading it.

Three models audit one schema. This scores what came back: which claims are real,
which are noise, which are not testable, and which real bugs nobody found. The
oracle is independent of the findings, so the numbers mean something. The bug
class itself is the 2026-09-11 session; this is the pipeline around it.

Run:  python3 code_example.py
"""

# Rounds of auditing to simulate. Each round a model repeats what it already found
# and adds one claim. Going 2 -> 3 rounds takes raw findings from 15 to 25 and
# precision from 67% to 57%: the bill grows faster than the truth does.
ROUNDS = 3

SCHEMA = {
    "public_notes": {},
    "documents": {"private": True},
    "members": {"private": True},
    "documents_fts": {"derived_from": "documents"},
    "sqlite_stat1": {"reflects": ["documents", "members"]},
    "orgs": {"foreign_keys": {"owner_id": "members"}},
}
PRIVATE = {"documents", "members"}


def canonical(name):
    """The table a typed name resolves to, the way the engine resolves it."""
    return next((t for t in SCHEMA if t.casefold() == name.casefold()), None)


def reachable(schema, name, seen=None):
    """Every table whose rows a request for `name` can read."""
    target = canonical(name)
    if target is None:
        return set()
    seen = seen or set()
    if target in seen:
        return seen
    seen.add(target)
    spec = schema[target]
    nxt = ([spec["derived_from"]] if "derived_from" in spec else []) \
        + list(spec.get("reflects", [])) + list(spec.get("foreign_keys", {}).values())
    for n in nxt:
        reachable(schema, n, seen)
    return seen


def leaks(name):
    # Does the naive check allow this name while it reaches private rows?
    allowed = name not in PRIVATE           # the bug: exact string, typed name
    return allowed and bool(reachable(SCHEMA, name) & PRIVATE)


def oracle_bypasses():
    # Keyed on the table reached, not the string typed: counting strings scores
    # `DOCUMENTS_FTS` as a miss separate from `documents_fts` and overstates it.
    out = set()
    for t in SCHEMA:
        for candidate in (t, t.upper()):
            if leaks(candidate):
                out.add(canonical(candidate))
    return out


# What came back. Hand-written to carry the error modes a real transcript does:
# correct claims, a confident claim about a table that does not leak, a claim
# about a table that does not exist, and prose with no testable target in it.
FINDINGS = {                        # (the name it names, what it claims)
    "model-A": [("documents_fts", "search index exposes source rows"),
                ("sqlite_stat1", "statistics tables leak sampled values"),
                ("public_notes", "notes table looks over-permissive"),
                (None, "the permission logic may be inconsistent in places")],
    "model-B": [("documents_fts", "fts shadow table is not permission-checked"),
                ("DOCUMENTS", "name comparison is case-sensitive, SQLite is not"),
                ("documents_backup", "backup table is world-readable")],
    "model-C": [("sqlite_stat1", "internal tables were never enumerated"),
                ("orgs", "foreign key reaches members"),
                ("DOCUMENTS", "case folding mismatch")],
}


def verify(finding):
    """real | noise | untestable -- the only judgment a machine can make here."""
    name = finding["request"]
    if not name:
        return "untestable"                 # no target: a human has to read it
    if not reachable(SCHEMA, name):
        return "noise"                      # a table that does not exist
    return "real" if leaks(name) else "noise"


def run_audit(rounds):
    # Collect across rounds. Repeats are most of what actually arrives.
    collected = []
    for r in range(rounds):
        for model, items in FINDINGS.items():
            # Round 1 reports two claims; each later round repeats them and adds one.
            for request, claim in items[:min(len(items), r + 2)]:
                collected.append({"request": request, "claim": claim,
                                  "model": model, "round": r + 1})
    return collected


def triage(collected):
    # Group by target; count how many distinct models reported each one.
    groups = {}
    for f in collected:
        key = f["request"] or f["claim"]
        g = groups.setdefault(key, {"verdict": verify(f), "models": set(), "n": 0})
        g["models"].add(f["model"])
        g["n"] += 1
    return groups


def main():
    collected = run_audit(ROUNDS)
    groups = triage(collected)
    truth = oracle_bypasses()

    print(f"{len(collected)} raw findings across {ROUNDS} rounds and "
          f"{len(FINDINGS)} models -> {len(groups)} distinct claims\n")

    MARK = {"real": "REAL ", "noise": "noise", "untestable": "?????"}
    for key, g in sorted(groups.items(), key=lambda kv: (-len(kv[1]["models"]), kv[0])):
        print(f"  {MARK[g['verdict']]}  {len(g['models'])} model(s)  {str(key)[:52]}")

    real = {canonical(k) for k, g in groups.items() if g["verdict"] == "real"}
    n_real = sum(1 for g in groups.values() if g["verdict"] == "real")
    print(f"\nverified real: {n_real} of {len(groups)} distinct claims "
          f"({100 * n_real / len(groups):.0f}% precision)")

    # Agreement is the only triage signal available before you write any tests.
    for label, keep in (("reported by one model", lambda n: n == 1),
                        ("reported by two or more", lambda n: n >= 2)):
        bucket = [g for g in groups.values() if keep(len(g["models"]))]
        hit = sum(1 for g in bucket if g["verdict"] == "real")
        print(f"  {label}: {hit}/{len(bucket)} real")

    missed = truth - real
    print(f"\noracle finds {len(truth)} reachable private tables; "
          f"the models named {len(real)}.")
    if missed:
        print(f"nobody reported: {', '.join(sorted(missed))}")
    print("\nThe models told you which shapes to enumerate. The oracle gives you")
    print("coverage, and it keeps working on tables added next month.")


if __name__ == "__main__":
    main()
