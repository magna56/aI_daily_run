# Why Your Tool's Output Format Only Hurts the Cheap Model

**Category**: Building Agents & MCP
**Tags**: agents, mcp, cost, context-engineering
**Date**: 2026-09-07
**Level**: Building
**For**: Building agents
**Hook**: Stripping the field names out of what a tool returns saves about 40% of the tokens. The best models barely notice, the cheap ones lose several points, and in a real agent it is the cheap one reading the result.
**Engineer's view**: You once shipped an API that returned rows as bare arrays to save bandwidth. Your own client was fine. A partner's simpler client silently mapped column three onto column four for weeks. The saving was real and the cost landed on the weakest consumer, which is this, exactly.
**TLDR**: Compact tool output saves real tokens and the accuracy it costs is not spread evenly. A frontier model shrugs it off; the small model you gave the grunt work to does not.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine handing someone a table of numbers. You can write the heading above each
column, or you can save paper and leave the headings off. Someone who already knows the
table can read it either way. Someone new has to count across the row and remember which
position means what. Most of the time they get it right. Sometimes they land one column
over, and the answer still looks like a number, so nobody notices it is wrong.

## The Problem

You have shipped this, and no model was involved. You had an endpoint returning rows of
data, and you changed it from objects to bare arrays to cut the payload. Your own client
was fine, because you wrote it and it had tests. Months later a partner reported bad
figures. Their simpler client had been reading column three as column four since the
change. The values were all numbers, so nothing threw, and the bug lived in a report
instead of a stack trace.

Agent tools are back at that decision. A tool that returns rows can label every field, or
it can send the values and a header once. The compact form is genuinely cheaper — the TOON
project measures around 40% fewer tokens than JSON on the same data, and close to 60% on
flat tables. Tokens are latency and money, so the saving is not imaginary.

What is easy to miss is who pays for it. You test the format against the best model you
have, it handles either one, and you ship the cheaper one. But in an agent the model
reading that tool result is often not your best model. It is the small, fast one you gave
the grunt work to, and that is the one the format was never tested on.

**The fix is to pick the format per reader, not per tool** — and to measure it on the model
that will actually read it.

## The Fix: Match the Format to the Model That Reads It

The TOON project published a benchmark across six formats and 244 questions, and the useful
part is not the winner. It is the spread between the best and worst format for each model.

```figure
{ "kind": "bars",
  "title": "How much the format changes accuracy, per model",
  "bars": [
    { "label": "Grok-4.5", "v": 1.6, "d": "1.6 pts", "s": "ok" },
    { "label": "Gemini 3.6 Flash", "v": 5.8, "d": "5.8 pts", "s": "neutral" },
    { "label": "Claude Haiku", "v": 3.7, "d": "3.7 pts", "s": "neutral" },
    { "label": "GPT-5.4 Nano", "v": 4.9, "d": "4.9 pts", "s": "bad" }
  ],
  "note": "Best format minus worst format, same 244 questions. The strongest model is nearly format-blind." }
```

Grok-4.5 scores 97.1% on its best format and 95.5% on its worst. Test there and you would
conclude the serialization format does not matter. GPT-5.4 Nano swings 4.9 points, and its
best format is not the one that wins overall. The saving is charged against the reader's
spare capacity, and a small model has less of it.

### Does it matter what the tool is being asked?

More than the format does. Splitting the same questions by type turns a small effect into
a large one.

| Question type | Best format | Worst format |
| --- | --- | --- |
| Field retrieval | 100% | 97.8% |
| Structure awareness | 90.3% | 78.5% |
| Aggregation | 48.4% | 32.8% |
| Structural validation | 100% | 45.0% |

Looking one value up is safe in every format. Nothing you choose will break it. But asking
the model to sum a column, or to confirm the shape of what it received, is where the
formats separate — and structural validation runs from 45% to 100% on the same data.

So the question is not which format is best. It is what your agent does with the rows. A
tool feeding a lookup can be as compact as you like; one whose output gets summed or
validated is where the labels earn their tokens.

### Why do the labels help at all?

Because without them, position is the only thing carrying meaning.

```figure
{ "kind": "anatomy",
  "title": "The same three rows, with the names taken out",
  "lines": [
    "cols: id,region,units,revenue",
    "rows:",
    "  17,EU,412,288000",
    "  18,NA,377,301500",
    "  19,APAC,590,204000"
  ],
  "callouts": [
    { "line": 0, "t": "Said once, at the top. Every row below depends on the reader still holding this.", "s": "new" },
    { "line": 2, "t": "Nothing here says which number is units and which is revenue. Position is the only clue.", "s": "bad" },
    { "line": 4, "t": "By row three the header is far away, and a miscount still returns a plausible number.", "s": "bad" }
  ],
  "note": "This is the same failure as an API that returns bare arrays: it works until the reader is weaker than you assumed." }
```

The header is stated once and every row depends on it. That is a memory task, and memory
is what separates a large model from a small one. It also fails quietly: a model that
reads the wrong column returns a number, not an error.

This is why the datasette-mcp plugin went the other way in version 0.2. It changed
`execute_sql` to return an array of objects rather than arrays of arrays, deliberately
making replies bigger, so that weaker models stop losing track of which position maps to
which column.

```figure
{ "kind": "system",
  "title": "The whole argument: one result, two readers",
  "lanes": [
    { "t": "one tool result", "nodes": [
        { "id": "rows", "t": "80 rows of SQL" } ] },
    { "t": "serialized as", "nodes": [
        { "id": "compact", "t": "values, header once", "s": "new" },
        { "id": "labeled", "t": "a name on every field", "s": "ok" } ] },
    { "t": "read by", "nodes": [
        { "id": "big", "t": "a frontier model", "s": "ok" },
        { "id": "small", "t": "your subagent", "s": "bad" } ] }
  ],
  "edges": [
    { "from": "rows", "to": "compact", "t": "-40% tokens", "s": "new" },
    { "from": "rows", "to": "labeled" },
    { "from": "compact", "to": "big",   "t": "no real cost", "s": "ok" },
    { "from": "compact", "to": "small", "t": "pays for it", "s": "bad" } ],
  "note": "The saving is charged to whoever reads the result, and that is rarely your best model." }
```

## What This Means for You

**When this matters.** You have a tool returning rows, and something other than your top
model reads them. That covers most agent designs, because delegating bulk work to a cheap
model is the point of having a subagent. It matters most when the reader has to aggregate
or validate rather than look one value up.

**How it affects you.** It turns a formatting choice into a routing choice. The right
question stops being "what should this tool return" and becomes "who is reading this, and
what are they doing with it". Those can have different answers inside one agent, which is
why Anthropic's own tool-writing guidance suggests letting the caller ask for a detailed or
a concise response rather than picking one forever.

It also means your format benchmark is probably invalid. If you evaluated on your strongest
model, you measured the case where the effect does not exist.

**What to do about it.**

1. Write down which model reads each tool's output. Most teams have never made that list,
   and it takes ten minutes.
2. For any tool whose reader is a small model, re-run your accuracy check on that model
   rather than the one you developed against.
3. Split the check by what the agent does with the rows. Lookups will pass anything;
   aggregation and validation are where you will see the difference.
4. Then give the tool a response-format parameter so the caller chooses, instead of
   deciding once for every caller.

## Implementing It

**The change.** Three places, and the third is what keeps it honest.

*The tool itself.* Return the shape the caller asks for, and default to the safe one:

```python
def rows_payload(cols, rows, fmt="labeled"):
    """Serialize a result set. `compact` is cheaper; `labeled` is safer."""
    if fmt == "compact":
        # header once, then values. Cheapest, and position carries the meaning.
        return {"cols": cols, "rows": [list(r) for r in rows]}
    # a name on every field. Bigger, and nothing depends on the reader counting.
    return {"rows": [dict(zip(cols, r)) for r in rows]}
```

Default to `labeled`. A tool that defaults to compact is optimizing a cost the caller can
see for an error the caller cannot.

*The caller.* Choose on behalf of the model that will read the result, not on behalf of
the tool:

```python
COMPACT_OK = {"lookup", "filter"}     # position is enough
NEEDS_NAMES = {"aggregate", "validate", "join"}

def choose_format(reader_model, intent):
    if intent in NEEDS_NAMES:
        return "labeled"
    if reader_model in SMALL_MODELS and intent not in COMPACT_OK:
        return "labeled"
    return "compact"
```

The intent is usually already in your code — it is whatever made you call the tool. If it
is not, that is worth knowing on its own.

*The check that catches a regression.* The failure is silent, so the test has to compare
against a known answer rather than assert the call succeeded:

```python
def format_delta(model, rows, question, truth):
    """Points lost by going compact, for one model on one question type."""
    got = {f: ask(model, rows_payload(COLS, rows, f), question) for f in ("labeled", "compact")}
    return {f: (v == truth) for f, v in got.items()}
```

Run it over a few dozen questions per intent, per reader model. That is a small eval and it
is the only thing standing between you and a wrong column in a report. Keep the questions
in the repo next to the tool, because the answer changes whenever you change the reader —
a model swap is a format decision even though nothing about the tool moved.

**How you know it worked.** Accuracy on aggregation and validation questions is unchanged
when you switch a tool to compact, measured on the model that actually reads it — not on
your development model. If it moves, you have found the tools that need their labels back,
and you have found them before a user did.

The second signal is a token count that went down without the first number moving. Both
matter. A saving with no accuracy check is not a result, and an accuracy check with no
saving means you did the work for nothing.

**When not to.** If one model reads everything and it is a frontier model, this is a
rounding error. Measure once, take the tokens, and move on.

## When Compact Tool Output Is the Wrong Tool

The compact form is right more often than this article's framing suggests, and it is worth
saying where.

Field retrieval barely moves. Every format scored between 97.8% and 100% on looking one
value up, so a tool that exists to answer "what is the status of order 4471" can be as
terse as you like, on any model. Forcing labels there spends tokens on a problem you do not
have.

Small results do not matter either. The saving scales with row count, so three rows of
output are not worth a decision. This is a question about tools that return tables, not
tools that return an object.

And the numbers here are one benchmark, on 244 questions, with a format author running it.
The per-model spread is the part worth trusting, because it is a comparison within each
model rather than a claim about which format wins.

Three questions before you change anything:

- Which model actually reads this tool's output in production?
- Does the agent look values up, or does it aggregate and validate?
- Is my accuracy check running on the reader, or on the model I develop against?

## Glossary

- **Tool result** — what a tool hands back to the model that called it. In MCP this is a
  list of content blocks, and for a query tool it is usually rows of data.
- **Serialization format** — how those rows are written down. The choice here is whether
  each value carries its field name or whether the names are stated once at the top.
- **Subagent** — a second, usually cheaper model that a main agent delegates work to. It is
  frequently the thing reading tool output, which is the point of this article.
- **Aggregation** — asking the model to compute over the rows, such as summing a column,
  rather than reading one value out. This is where formats separate.
- **Structural validation** — asking the model to confirm the shape of what it received.
  Scores here ranged from 45% to 100% across formats on the same data.
- **TOON** — a compact tabular format that states field names once per table. Used here as
  the source of the benchmark, not as a recommendation.
