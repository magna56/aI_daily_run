# How to Find Permission Bugs in Your Code With a Coding Agent

**Category**: AI Engineering Practices
**Tags**: security, coding-agents, reliability
**Date**: 2026-09-15
**Level**: Start here
**For**: Using tools
**Hook**: A permission check can be present, correct, and still hand over the table it was guarding.
**Engineer's view**: This is an over-eager serializer. You once authorized a read of one user and returned their whole organization with it, because the check ran on the record while the response walked the graph. Your permission check is correct about the name it was given and silent about the rows that name reaches.
**TLDR**: Your permission check guards the object the caller named. The bug is everything else that reaches the same rows.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine a library with one shelf you are not allowed to browse. The librarian checks your card at that shelf and turns you away. That part works every time.

But the card catalog in the lobby lists every book on that shelf, with a summary of each. The returns cart holds the books that came off it this morning. And the sign on the shelf spells its name in capital letters, while the librarian's list has it in small letters, so she does not think they are the same shelf.

Nobody unlocked anything. The books got out anyway.

## The Problem

You have shipped this bug, and it had nothing to do with AI. You wrote an endpoint that returns one user. It checks that the caller is allowed to read that user, loads the record, and hands it to the serializer.

The serializer was helpful. It expanded the organization the user belongs to, and the organization came with its member list. The check ran once, against one user ID. The response carried a hundred people.

Nobody had removed the permission check. It was correct about the thing it was asked about.

This is the shape of almost every authorization bug that survives code review. Review reads the check and the check looks right. Tests are written from the same mental picture as the code, so they ask about the same name too. What nobody enumerates is the set of rows a request can actually reach.

Datasette shipped two security releases on 11 September 2026, and the fix list has this shape all the way down. A table the operator had marked private was still reachable under a different capitalization, through its full-text search index, through the database's own statistics tables, and through a foreign key on a public table. Every one of those permission checks existed and passed.

They were found by pointing three coding agents at the project over several rounds. The fix: stop authorizing the name the caller typed, and authorize every table that name can reach.

```figure
{ "kind": "system",
  "title": "The whole argument: one request, two things you could authorize",
  "lanes": [
    { "t": "the caller asks for", "nodes": [
        { "id": "req", "t": "documents_fts" } ] },
    { "t": "you authorize", "nodes": [
        { "id": "typed", "t": "the name they typed", "s": "bad" },
        { "id": "set",   "t": "everything it reaches", "s": "new" } ] },
    { "t": "what comes back", "nodes": [
        { "id": "leak", "t": "private rows, allowed", "s": "bad" },
        { "id": "deny", "t": "denied", "s": "new" } ] }
  ],
  "edges": [
    { "from": "req",   "to": "typed", "t": "not on the deny list", "s": "bad" },
    { "from": "req",   "to": "set",   "s": "new" },
    { "from": "typed", "to": "leak",  "s": "bad" },
    { "from": "set",   "to": "deny",  "s": "new" } ],
  "note": "The search index is a different name for the same rows. Nobody wrote a rule about it." }
```

## The Fix: Authorize What the Request Reaches

Start with the name. A caller asks for `DOCUMENTS`. Your check compares that string against a deny list holding `documents`, finds no match, and allows it. It never reduced the request to its canonical name. SQLite then matches table names without caring about case, and serves the private table.

The check was a string comparison. The lookup was a case-insensitive match. They disagreed, and the disagreement is the vulnerability.

That is one route. There are four, and they are worth memorizing because they recur in every system that lets a caller name a thing.

- **A different spelling of the same name.** Case, trailing whitespace, Unicode forms, URL encoding.
- **A derived table.** A search index, a materialized view, a cache table. It holds the same rows under its own name.
- **An engine-internal object.** SQLite's `sqlite_stat1` through `sqlite_stat4` carry row counts and sampled column values for every table, including the private ones.
- **A relation.** A foreign key, a join, an expanded key. The caller names a public table and the response follows the pointer.

### Why doesn't the existing check catch this?

Because the deny list is written by a person, and a person writes down the tables they know hold sensitive rows. Nobody writes a rule for a search index they forgot exists, or for a statistics table the engine created on its own. The check is not wrong. Its input is incomplete, and it has no way to know that.

So the fix is not more rules. It is one function that turns a requested name into the resolved set — every table that request can read — and a check that runs over all of it.

```figure
{ "kind": "route",
  "title": "Four names, none of them on the deny list, all reaching private rows",
  "source": "one request",
  "parts": [
    { "t": "DOCUMENTS",     "to": 0, "via": "case-insensitive match", "s": "bad" },
    { "t": "documents_fts", "to": 0, "via": "search index",           "s": "bad" },
    { "t": "sqlite_stat1",  "to": 0, "via": "engine statistics",      "s": "bad" },
    { "t": "orgs",          "to": 1, "via": "foreign key",            "s": "bad" }
  ],
  "dests": [
    { "t": "documents (private)", "s": "bad" },
    { "t": "members (private)", "s": "bad" }
  ],
  "note": "The statistics tables reach both. These are the five findings code_example.py reports." }
```

### What do I actually ask the agent?

Not "find security bugs in my code." That returns a list of plausible-sounding findings you then have to disprove one at a time. Ask it to enumerate instead, because enumeration is the part humans skip and the part a model is genuinely good at: list every way a caller can name an object in this codebase, and for each one, list the tables its response can read.

Then you check the list against your permission layer yourself.

## What This Means for You

**When this matters.** You have an endpoint where the caller names something — a table, a file path, a bucket key, a record ID — and you check permission on that name. The more helpful your framework is about expanding relations, the more of this you are carrying.

**How it affects you.** This class of bug is invisible in review, because the reviewer reads the check and the check is correct. It is also invisible to your tests, which were written from the same mental model as the code and ask about the same names. The two defenses you trust most are the two that cannot see it.

**What to do about it.** Start on paper, before you write any code or run any agent. List the object names your API accepts from a caller. For each one, write down what its response can read. Ten minutes and a text file. Most teams find at least one surprise, and no part of this needs the agent yet.

Then write the enumeration as a test, so the answer stops being a document that goes stale. That is the next section. The coding-agent audit comes last, because it is the step that produces findings you have to triage, and it is worth much more once you already have a harness to prove a finding real.

## Implementing It

Three roles touch this: whoever owns the permission layer, whoever owns the tests, and whoever runs the audit. The third one is the least obvious and the easiest to get wrong.

**The permission layer.** Add one function that resolves a requested name into the set of tables the response can read, and check permission over the whole set. The full version, with the schema shapes it walks, is in `code_example.py`.

```python
def reachable(schema, name):
    """Every table whose rows can be read through a request for `name`."""
    target = canonical(schema, name)          # case-fold first: the engine does
    if target is None:
        return set()
    out, spec = {target}, schema[target]
    if "derived_from" in spec:                 # search index, materialized view
        out |= reachable(schema, spec["derived_from"])
    for src in spec.get("reflects", []):       # sqlite_stat1..4 and friends
        out |= reachable(schema, src)
    for dest in spec.get("foreign_keys", {}).values():
        out |= reachable(schema, dest)         # joins and expanded keys
    return out
```

Then the check itself is a one-line change, and it is the whole fix:

```python
# before — correct about the name, silent about the rows
return name not in private

# after — authorize the resolved set
return not (reachable(schema, name) & private)
```

**The tests.** Do not write one test per bug you have heard about. Derive the cases from the schema, so the test keeps working as tables are added:

```python
def test_no_private_table_is_reachable():
    for table in schema:
        for candidate in (table, table.upper()):
            leaked = reachable(schema, candidate) & PRIVATE
            assert not (leaked and can_view(schema, PRIVATE, candidate)), \
                f"{candidate!r} is allowed but reaches {sorted(leaked)}"
```

**The audit.** Run the agent against a checkout, not against a running instance, and never against a system you do not own. Give it the enumeration task, one area at a time, and run several rounds rather than one long session. Datasette's audit used three models from three labs — Claude Fable 5.1, GPT-5.6 Sol and GPT-6 Astra — which matters because different models surface different things and agreement between two of them is a useful signal.

The rule that makes the output trustworthy is a process rule, and it is the one worth copying. On Datasette, Alex Garcia and Simon Willison split every issue: one wrote the automated test that demonstrated the problem, the other wrote the fix. No finding was accepted on the agent's description alone, and two people looked at each one.

**How you know it worked.** The audit function returns zero findings, and the test above is in CI. Before that, the honest signal is per-finding: a finding is real when a test fails without the fix and passes with it, and it is noise until then. Expect to throw away a good share of what the agent reports. If nothing the agent reports can be turned into a failing test, you have a false-positive list rather than an audit, and the usual cause is asking for bugs instead of asking for an enumeration.

One more signal worth watching: if your resolved sets are all of size one, your `reachable` function is not walking the schema, and it will report a clean bill of health on a system full of holes.

## When a Coding-Agent Audit Is the Wrong Tool

It cannot tell you your threat model. Whether a row is sensitive is a product question, and the agent will happily flag a public table as a leak and stay silent about the one that matters. If nobody on the team can say who is supposed to see what, an audit will produce activity rather than safety.

It is also expensive in the currency you have least of. The two-human rule means every finding costs a test and a review, so a long finding list is a long project. Triage is the real work, and the agent does not do it.

Then there is the responsible part. Run this on code you own. Datasette shipped the fixes and deliberately held back some of the automated tests so that people had time to upgrade before the details were public, which is the same discipline in the other direction. If you find something in a dependency, report it and wait.

Three questions before you start:

- Can you name, for each table, who is supposed to see it? If not, fix that first.
- Do you have a way to turn a finding into a failing test in under an hour?
- If the agent produced thirty findings, who is triaging them, and when?

## Glossary

- **permission check** — the code that decides whether this caller may read the thing they asked for.
- **canonical name** — the single spelling an identifier resolves to, after case and encoding are normalized.
- **resolved set** — every table whose rows a single request can read, not just the one named.
- **derived table** — a table built from another, such as a search index, holding the same rows.
- **coding-agent audit** — pointing a coding model at a checkout to enumerate how its data can be reached.
- **threat model** — the written statement of who may see what, which an audit assumes and cannot supply.
