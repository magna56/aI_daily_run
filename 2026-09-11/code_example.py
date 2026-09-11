"""One protected table, and every name that reaches it.

Builds a small permission layer with the bug Datasette shipped a fix for --
a check keyed on a raw table name -- then runs every alias of every table
through it and reports where the answers disagree.

The last function is the deliverable. It is a property test, not a list of
known bugs, so it keeps failing for names nobody has thought of yet.

Run: python3 code_example.py

Set STRICT = True to switch on the fixed checker and watch the disagreements
go to zero.
"""

STRICT = False        # False = the naive check, True = normalize + resolve + deny-by-default

# The schema as SQLite sees it. Casing here is whatever the CREATE said.
TABLES = ["Customers", "orders", "Secrets", "public_notes"]
# Full-text search creates companion tables that hold the indexed content.
FTS_FOR = {"Secrets": ["Secrets_fts", "Secrets_fts_data", "Secrets_fts_idx"],
           "public_notes": ["public_notes_fts"]}
# Tables SQLite writes for itself. Nobody puts these in a policy.
INTERNAL = ["sqlite_stat1", "sqlite_stat2", "sqlite_stat3", "sqlite_stat4",
            "sqlite_schema"]

# What the operator wrote. A Datasette instance is public with some tables held
# back, so the policy is a DENY list -- and it names each table in one spelling.
PRIVATE = {"anon": {"Secrets", "Customers"}, "staff": {"Secrets"}}


def aliases_of(table):
    """Every identifier that reaches this table's rows."""
    out = {table, table.lower(), table.upper(), table.capitalize()}
    out |= set(FTS_FOR.get(table, []))
    return sorted(out)


# --- the check, before and after -----------------------------------------
def allowed_naive(actor, name):
    """Public unless denied, keyed on the raw string.

    Correct about the name it was given. SQLite resolves any casing to the
    same table, so a spelling the deny list does not contain reaches the rows.
    """
    return name not in PRIVATE[actor]


def source_of(name):
    """An index exists because a table exists; it inherits that table's answer."""
    for suffix in ("_fts_data", "_fts_idx", "_fts"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def allowed_strict(actor, name):
    if name.lower().startswith("sqlite_"):
        return False                                   # internal, never grantable
    want = source_of(name).casefold()                  # an index inherits its source
    return not any(want == denied.casefold() for denied in PRIVATE[actor])


def check(actor, name):
    return allowed_strict(actor, name) if STRICT else allowed_naive(actor, name)


# --- the property worth keeping ------------------------------------------
def disagreements(actor):
    """For each table, do all of its aliases get the same answer?"""
    bad = []
    for t in TABLES:
        answers = {a: check(actor, a) for a in aliases_of(t)}
        if len(set(answers.values())) > 1:
            bad.append((t, answers))
    return bad


def reachable_internals(actor):
    return [n for n in INTERNAL if check(actor, n)]


def main():
    mode = "STRICT (fixed)" if STRICT else "naive (the shipped bug)"
    print("permission check: %s\n" % mode)

    for actor in ("anon", "staff"):
        print("  actor: %s   policy denies %s" % (actor, sorted(PRIVATE[actor])))
        bad = disagreements(actor)
        if not bad:
            print("     every alias agrees")
        for table, answers in bad:
            leak = [n for n, v in answers.items() if v]
            held = [n for n, v in answers.items() if not v]
            print("     %-14s denied as   %s" % (table, held))
            print("     %-14s REACHED via %s" % ("", leak))
        leaked = reachable_internals(actor)
        print("     internal tables reachable: %s\n"
              % (", ".join(leaked) if leaked else "none"))

    print("  The naive check is not wrong about the name it was given. It is wrong")
    print("  about how many names there are. Three shapes, all in the lines above:")
    print("    casing      — the same table, allowed under one spelling and not another")
    print("    _fts tables — content of a denied table, under a name nobody granted")
    print("    sqlite_*    — never in the policy at all, so never denied by it")
    print("\n  Flip STRICT and the first two collapse to agreement and the third to none.")
    print("  The loop in disagreements() is the part to keep: it fails for an alias")
    print("  you have not thought of yet, which is the only kind that matters.")


if __name__ == "__main__":
    main()
