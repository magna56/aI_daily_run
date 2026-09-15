"""Find authorization bypasses by enumerating what a response can reach.

A permission check guards the object the caller named. The bug class is everything
else that reaches the same data: the table under a different case, its search index,
its statistics, its foreign-key neighbors. Point this at your own schema.

Modeled on the fixes in Datasette 1.0a39 / 0.65.4 (11 September 2026).

Run:  python3 code_example.py
"""

# Flip to True to authorize the resolved target set instead of the typed name.
# That one change is the entire fix, and it closes every bypass found below.
STRICT = False

# A schema with the four shapes that bite: a private table, a search index derived
# from it, engine-internal tables that mirror its contents, and a public table with
# a foreign key pointing into private data.
SCHEMA = {
    "public_notes": {},
    "documents": {"private": True},
    "documents_fts": {"derived_from": "documents"},      # full-text search index
    "sqlite_stat1": {"reflects": ["documents", "members"]},  # row counts, sampled values
    "members": {"private": True},
    "orgs": {"foreign_keys": {"owner_id": "members"}},
}

# What the operator marked private. This is the realistic shape: you deny the tables
# you know hold sensitive rows. Nobody writes a rule for a search index they forgot
# exists, which is exactly the gap.
PRIVATE = {"documents", "members"}


def canonical(schema, name):
    """Resolve a typed name the way the engine does, not the way a string compares.

    SQLite matches table names case-insensitively, so a check on "documents" that
    compares strings exactly is not the check the engine will honor.
    """
    for real in schema:
        if real.casefold() == name.casefold():
            return real
    return None


def reachable(schema, name):
    """Every table whose data can be read through a request for `name`.

    This is the function worth lifting. A permission layer that authorizes the typed
    name is asking about one element of this set and serving all of it.
    """
    target = canonical(schema, name)
    if target is None:
        return set()
    out = {target}
    spec = schema[target]
    if "derived_from" in spec:                 # a search index exposes its source rows
        out |= reachable(schema, spec["derived_from"])
    for src in spec.get("reflects", []):       # stats tables leak counts and samples
        out |= reachable(schema, src)
    for col, dest in spec.get("foreign_keys", {}).items():
        out |= reachable(schema, dest)         # joins and expanded keys follow these
    return out


def can_view(schema, private, name, strict):
    if canonical(schema, name) is None:
        return False
    if not strict:
        return name not in private             # the bug: exact string, typed name
    # Authorize the resolved set: deny if anything this request reaches is private.
    return not (reachable(schema, name) & private)


def audit(schema, private, strict):
    """Enumerate requests that must be denied, and report any the checker allows.

    Nothing here knows about a specific vulnerability. It derives the cases to try
    from the schema, which is why it keeps working as the schema grows.
    """
    findings = []

    def probe(name, why):
        leaked = reachable(schema, name) & private
        if not leaked:
            return                             # nothing private behind this name
        if can_view(schema, private, name, strict):
            findings.append((name, why, sorted(leaked)))

    for table in schema:
        probe(table, "requested directly")
        # Only worth trying a case variant where a deny exists to evade. Probing
        # every casing of every table re-reports the same hole many times over.
        if table in private:
            probe(table.upper(), "same table, different case")

    return findings


def main():
    mode = "STRICT (authorize the resolved set)" if STRICT else "NAIVE (authorize the typed name)"
    print(f"operator marked private: {', '.join(sorted(PRIVATE))}")
    print(f"checker: {mode}\n")

    findings = audit(SCHEMA, PRIVATE, STRICT)
    if not findings:
        print("no bypasses found — every request that reaches private data is denied")
    else:
        print(f"{len(findings)} bypass(es) found:\n")
        for name, why, leaked in findings:
            print(f"  request {name!r} ({why})")
            print(f"    allowed, but reaches: {', '.join(leaked)}")

    # The same audit under the other setting, so the run proves the fix rather than
    # asserting it. This is the assertion to put in your own test suite.
    other = audit(SCHEMA, PRIVATE, not STRICT)
    print(f"\nsame audit with STRICT={not STRICT}: {len(other)} bypass(es)")
    print("\nEvery finding is a permission check that was present and correct about")
    print("the name it was given, and wrong about the data that name reaches.")


if __name__ == "__main__":
    main()
