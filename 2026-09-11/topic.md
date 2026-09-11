# How an AI Audit Found Three Names for One Protected Table

**Category**: Coding Agents & Productivity
**Tags**: coding-agents, security, reliability
**Date**: 2026-09-11
**Level**: Building
**For**: Using tools
**Hook**: A permission check that guards a table by its name guards exactly one spelling of that name. Three frontier models were pointed at one codebase and came back with the other spellings nobody had enumerated.
**Engineer's view**: You have written an access check keyed on a string, then watched someone reach the same resource by another route — a different case on a case-insensitive filesystem, an alias, a view. The check never fired, because it only knew one spelling of the thing it was protecting.
**TLDR**: An audit of Datasette by three frontier models found permission bugs that were all one bug: the guarded resource had other names. Models are good at that search because it is exhaustive and boring.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine a guest list at a door. The list says one name, and the guard checks it letter by
letter. Someone arrives with the same name spelled with a capital letter, and the guard
does not match it. Someone else arrives using a nickname. A third person is not on the list
at all, because nobody thought to write down that they existed. The rule was fine. The
list of names it knew was short.

## The Problem

You have shipped this, and no model was involved. You wrote an access check keyed on a
string — a path, a bucket, a table. It worked. Then someone reached the same resource
through a second route: a different case on a case-insensitive filesystem, a symlink, an
alias, a view over the same rows. The check did not fire, because the resource had two
names and your check knew one.

This is not a logic error you can spot by reading the check. The check is correct. What is
wrong is the assumption underneath it, that the string you were handed is the only way to
refer to the thing you are guarding. That assumption is invisible in the code, so review
does not catch it, and tests do not catch it because you write tests for names you thought
of.

Finding the rest is a search problem, not a reasoning problem. It means asking "what else
is this called?" for every guarded resource, and following each answer far enough to know
whether the check still applies. It is exhaustive, it is repetitive, and a person doing it
for the four hundredth table is not doing it as carefully as they did the first.

**The fix is to hand that search to something that does not get bored** — and to keep a
protocol that stops you trusting what it hands back.

## The Fix: Give the Boring Search to a Model, Keep the Proof for a Human

Datasette shipped two security releases on 10 September 2026 whose fixes are almost all in
permission checks. Alex Garcia and Simon Willison ran the audit with three models, then
spent close to a week reviewing what came back. Three of the fixes are one bug wearing
different clothes.

```figure
{ "kind": "route",
  "title": "One protected table, three names the check did not know",
  "source": "a table you denied access to",
  "parts": [
    { "t": "a different casing", "to": 0, "via": "SQLite folds case", "s": "bad" },
    { "t": "its search index", "to": 0, "via": "separate table", "s": "bad" },
    { "t": "sqlite_stat1..4", "to": 0, "via": "never enumerated", "s": "bad" }
  ],
  "dests": [
    { "t": "reached the data anyway", "s": "bad" }
  ],
  "note": "Three routes, one cause: the resource had names the check was never given." }
```

**Casing.** SQLite treats table and view names case-insensitively. The permission check
compared them case-sensitively. So `Secrets` and `secrets` were the same table to the
database and two different strings to the guard. The fix applies the same case folding the
database applies.

**The search index.** A full-text search index is a separate table holding the content of
the table it indexes. Denying the source table said nothing about the index, which is a
different name. Viewing an index now requires permission on the table it draws from.

**The statistics tables.** The SQLite statistics tables, `sqlite_stat1` through
`sqlite_stat4`, hold query-planner data
about your tables. They are not tables anyone wrote a rule for, because nobody thinks of
them as tables that exist. They are denied by default now.

### Why did models find these and review did not?

Because the work is enumeration rather than insight. A reviewer reads a permission check and
asks whether it is correct. It is correct. The question that finds the bug is a different
one — "what else refers to this table?" — and it has to be asked hundreds of times.

That is what a model is genuinely good at, and the reason is worth being precise about: not
better reasoning, but the four-hundredth repetition getting the attention of the first.

### So do you just take what it reports?

No, and this is the part worth copying. Two people reviewed every item, and they split the
work so that neither could wave something through:

> one of us would create the automated tests highlighting the issue, then the other would
> implement the fix

A finding does not become real until a test fails because of it. That test is written by a
person who is not the person fixing it, so the fix has to satisfy an independent statement
of the problem rather than the model's description of it.

```figure
{ "kind": "system",
  "title": "The whole argument: where the check and the database disagree",
  "lanes": [
    { "t": "the request names", "nodes": [
        { "id": "req", "t": "\u201csecrets\u201d" } ] },
    { "t": "resolved by", "nodes": [
        { "id": "guard", "t": "the permission check", "s": "bad" },
        { "id": "db",    "t": "SQLite", "s": "neutral" } ] },
    { "t": "which finds", "nodes": [
        { "id": "none",  "t": "no rule for that string", "s": "bad" },
        { "id": "table", "t": "the Secrets table", "s": "new" } ] }
  ],
  "edges": [
    { "from": "req",   "to": "guard", "t": "exact match", "s": "bad" },
    { "from": "req",   "to": "db",    "t": "case folded", "s": "ok" },
    { "from": "guard", "to": "none",  "s": "bad" },
    { "from": "db",    "to": "table" } ],
  "note": "Two resolvers, two answers. The guard says allow because it found nothing to deny." }
```

## What This Means for You

**When this matters.** You have an authorization layer that names resources, and more than
one way to reach them. Datasette is the sharp case because SQLite hands you aliases for
free, but the pattern is everywhere: object storage with prefixes, a filesystem that folds
case, an ORM with views, any API where an id and a slug both resolve.

**How it affects you.** It gives you a job to delegate that is well matched to what these
tools actually do. Most attempts to use a model on a codebase ask it for judgment, and the
results are mixed because judgment is the thing it is least reliable at. This asks it for
an exhaustive list, which is the thing it does not tire of.

It also sets a bar for the output. The audit's value came from the review protocol, not the
model. Without the failing test written by a second person, you have a list of plausible
findings and no way to tell which ones are real — and a plausible security finding is worse
than none, because it costs a day to disprove.

**What to do about it.**

1. Write down every way a caller can name a resource in your system. That list is the
   input, and most teams have never written it.
2. Run the audit against that list rather than asking for "security problems". A narrow
   question gets a checkable answer.
3. Make every finding produce a failing test before anyone writes a fix, and have a
   different person write each.
4. Then re-run it on the aliases you discovered while fixing, because that list grows once
   you start looking.

## Implementing It

**The change.** Three places, and the third is what makes the first two safe.

*The question you ask.* This is a step, not a preamble, and it is where most of these
attempts go wrong. Do not ask for security problems. Ask for an enumeration you can check:

> For every table in this schema, list every other identifier that reaches the same rows —
> different casing, views, generated index tables, internal tables that describe it. For
> each one, name the function that decides access and say whether it is reached.

A request shaped like that returns a list you can diff against your own. A request shaped
like "audit this for vulnerabilities" returns prose at a uniform confidence, which is the
failure mode in the counter-case below.

*Normalize at the boundary.* Compare names the way the underlying system compares them,
once, where the request enters:

```python
def canonical(name: str) -> str:
    """One spelling per resource, decided here and nowhere else."""
    return name.strip().casefold()          # SQLite folds ASCII case; so do we

def allowed(actor, table: str) -> bool:
    return canonical(table) in {canonical(t) for t in policy_tables(actor)}
```

`casefold()` rather than `lower()` because it handles non-ASCII forms that `lower()` leaves
distinct. The rule is that no code past this point compares a raw name.

*Resolve derived resources to their source.* A name that exists because another table
exists must inherit that table's answer:

```python
DERIVED = (("_fts", ""), ("_fts_data", ""), ("_fts_idx", ""))

def source_of(table: str) -> str:
    """An index is not a separate thing to be granted separately."""
    for suffix, repl in DERIVED:
        if table.endswith(suffix):
            return table[: -len(suffix)] + repl
    return table

def allowed_resolved(actor, table: str) -> bool:
    return allowed(actor, source_of(table))
```

*Deny by default, and enumerate the exceptions.* The statistics tables were reachable
because the policy listed what was forbidden rather than what was permitted:

```python
INTERNAL_PREFIXES = ("sqlite_",)            # sqlite_stat1..4, sqlite_schema, and friends

def visible(actor, table: str) -> bool:
    if table.lower().startswith(INTERNAL_PREFIXES):
        return False                         # not enumerable, not grantable
    return allowed_resolved(actor, table)
```

**How you know it worked.** Write the test before the fix, and have someone else write it.
The test should assert on the property rather than the instance: for every table in the
database, every alias of that table returns the same authorization answer.

```python
for t in all_tables(db):
    answers = {allowed_resolved(actor, alias) for alias in aliases_of(t)}
    assert len(answers) == 1, f"{t}: aliases disagree — {answers}"
```

That loop is the real deliverable. It fails today for a name nobody has thought of yet, and
it is the only part of this work that keeps paying after the audit is over.

**When not to.** If your resources have exactly one name and no derived objects, this is
machinery you do not need. Check by listing the aliases first — if the list is short and
static, a review is cheaper than a harness.

## When an AI Audit Is the Wrong Tool

The audit worked here because the question was narrow and the answers were checkable. Where
either stops being true, it stops being a good trade.

An open-ended request for "security issues" is the clearest failure. It returns a long list
at a uniform tone of confidence, and separating the real ones costs more than the finding
was worth. The value came from asking about aliases of guarded names, not from asking
whether the code was safe.

It is also wrong where a finding cannot be turned into a failing test. If the issue is a
design judgment — this token lives too long, this default is too permissive — there is
nothing for the second person to write, and the protocol that made the output trustworthy
does not apply. Those are worth discussing, and they are not audit findings.

And the cost is real. Two experienced maintainers spent close to a week reviewing one
codebase, on a project one of them wrote. The models made the search tractable; they did not
make it cheap.

Three questions before you run one:

- Can I state the question as "list every X", rather than "find problems"?
- Can each finding be expressed as a test that fails now?
- Do I have a second person to write those tests, and a week for someone to review them?

## Glossary

- **Permission check** — the code that decides whether an actor may see a resource. Usually
  keyed on the resource's name, which is the assumption this session is about.
- **Case folding** — normalizing letter case before comparison. SQLite folds ASCII case in
  table names, so a check that does not fold sees two tables where the database sees one.
- **Full-text search index** — a separate table holding a searchable copy of another table's
  content. It has its own name, so it needs its own answer inherited from its source.
- **SQLite statistics tables** — the internal tables SQLite writes to hold query-planner
  statistics. They describe your data and are easy to omit from a policy that lists tables.
- **Deny by default** — writing the policy as what is permitted rather than what is
  forbidden, so a resource nobody enumerated is unreachable instead of open.
- **Alias** — any second name that reaches the same underlying resource: different casing,
  a view, a derived index, a slug alongside an id.
