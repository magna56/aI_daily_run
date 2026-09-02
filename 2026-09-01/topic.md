# How to Check AI-Written Code Against Someone Else's Test Suite

**Category**: AI Engineering Practices
**Tags**: coding-agents, reliability, production
**Date**: 2026-09-01
**Level**: Building
**For**: Using tools
**Hook**: Tests your agent wrote for code your agent wrote share the same blind spot. Borrowing a mature project's tests gives you a check it could not have faked.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine hiring a translator you have never worked with. You could read their translation and look
for mistakes, but you do not speak the language — that is why you hired them.

So you do something else. You hand them a book that a translator you trust has already done, and
compare the two versions line by line. You still cannot read the language. But now every place the
two disagree is a place worth asking about, and you did not have to trust anybody to find them.

## The Problem

An agent will now write a thousand tests as happily as it writes ten. The bottleneck moved: it is
no longer producing the code, it is knowing whether the code is right.

Reviewing it line by line does not scale, and asking the agent for more tests does not fix it
either. Tests written by the same author as the code inherit the same misunderstanding — if it
misread the spec, it writes a test that agrees with the misreading, and the suite goes green. If
that sounds like the reason nobody accepts a developer's own "works on my machine" as evidence,
hold that thought.

Graham Dumpleton, who wrote `wrapt` and `mod_wsgi`, spent the second half of August shipping a new
Python library this way. **wrapture** reached 1.0.0a12 in about two weeks, with over a thousand
tests and 150-plus pages of documentation, and by his own description "the AI wrote the code, the
tests and the prose. I set the direction, made the design calls, reviewed what came back, and sent
plenty of it back."

The interesting part is not that it worked, but the check he used to know it had. **Borrow your
oracle: take the test suite of a mature project that does something similar, have the agent port
those tests onto your API, and treat every failure as a question to answer.** Dumpleton did this
with packages that lean on `unittest.mock`. The assertions came from outside — written by other
people, for other code, before his project existed, and so beyond anything his agent could have
bent to match its own mistakes.

## The Fix: Borrow a Mature Project's Test Suite

The technique has a name: **differential testing**. Run the same inputs through two independent
implementations and treat any disagreement as a defect to explain. It is standard practice for
compilers, JVMs and database engines, where nobody can write the correct output down by hand.

What is new is where the second implementation comes from. You are not writing one — you borrow a
mature library that already does roughly what yours does, and its tests with it.

### Why not just ask the agent for more tests?

Because more tests from the same author buy you coverage, not independence. A test is an
*assertion about intent*, and the agent's intent is exactly what is in question. Run a thousand of
its tests against its own code and you learn that it is self-consistent, which was never in doubt.

The borrowed suite is different in kind. Those assertions were written by other people, for other
code, before your project existed. Nothing in them can have been shaped to match your agent's
misreading.

### So does every failure mean I have a bug?

No, and this is where the judgement lives. A ported test fails for one of three reasons: your code
is wrong, the port is wrong, or your API deliberately differs.

The first is the bug you were hunting. The second is noise, and it is common — the agent doing the
porting can misread the original as easily as it misread your spec. The third is the valuable one:
a deliberate difference you now have to write down, because the failing test is proof that
somebody with a reasonable mental model expected the other behaviour.

The rule that keeps this honest is that a failing test is never *adjusted* until it passes. It is
explained, then either fixed or documented.

### Documentation that cannot drift

The other half of Dumpleton's stack is smaller and worth stealing outright: every example in the
documentation runs as a doctest against the real implementation. Prose written by an agent is the
easiest thing in the repository to get subtly wrong, and the hardest to review at 150 pages. If
the examples execute, they cannot quietly stop being true.

## For a Software Engineer

This is a shadow deployment, and you have run one.

When you replace a service, you do not read the new implementation and pronounce it correct. You
run it beside the old one on the same traffic, diff the responses, and investigate every
divergence before you cut over. The old service is not a specification — it is just a second
opinion that was not written this morning by whoever wrote the new one.

A borrowed test suite is that, moved earlier and made cheap. The traffic is someone else's test
cases, the diff is pass/fail, and the "old service" is a library that has survived years of real
users finding its edges.

The number worth holding onto: **over a thousand tests, written in two weeks, by the same author
as the code.** That figure is impressive and it is not evidence. The borrowed suite is the part
that is.

## What This Means for You

**When this matters.** You have let an agent write something substantial — a library, a client, a
parser, a migration — and you cannot personally review every line of what came back. That is now
most people, most weeks, and it is just as true of a well-directed agent as a careless one.

**How it affects you.** Your green suite is weaker evidence than it looks, because the tests and
the code share an author and therefore share a blind spot. `code_example.py` makes this concrete:
fix its planted bug and the agent-written suite starts *failing*, because one assertion had
encoded the bug as a requirement. A suite written alongside the code does not merely miss that
class of defect — it defends it. This does not show up as flaky tests
or obvious breakage. It shows up months later as a behaviour nobody specified and nobody caught,
in code that had a thousand passing tests the whole time.

**What to do about it.** Today, without changing anything: name the mature project closest to what
you just built, and ask whether you could run its tests against your code. If yes, that is your
oracle and the rest of this article is a weekend. If no — if nothing comparable exists — that
itself is the finding, and it means every assertion protecting this code was written by its
author. Say so in the README, and weight your review accordingly. Either way you now know which
of the two situations you are in, which is more than a passing test suite was telling you.

## Implementing It

**The change.**

*Whoever is directing the agent.* Pick the target and pin it, so the port is reproducible rather
than a moving reference:

```toml
# oracle.toml — the borrowed suite is a dependency; treat it like one
[oracle]
package  = "wrapt"
version  = "1.17.2"          # pinned: an upstream test change must be a visible diff
tests    = "tests/test_function_wrappers.py"
port_to  = "tests/ported/test_function_wrappers_ported.py"
```

*Same person, driving the port.* The instruction matters more than the model. Ask for a
translation, not a reimplementation, and forbid the agent from touching the assertions:

```text
Port tests/test_function_wrappers.py to our API. Rules:
  - Keep every assertion's meaning identical. Do not weaken, skip, or reorder them.
  - Only the setup and the call site change; the expected values do not.
  - Where our API has no equivalent, leave the test in place and mark it
    @pytest.mark.xfail(reason="no equivalent: <what is missing>") — do not delete it.
```

That `xfail` rule is the one people drop, and it is the one that pays. A deleted test is a gap you
will never see again; an `xfail` with a reason is a list of everything your API cannot do, written
by someone else. Read that list before your next design decision — it is the cheapest external
review you will get.

Resist the temptation to let the agent "make the ported tests pass." The port and the fix are two
separate jobs, and doing them in one pass is how an assertion quietly becomes weaker.

*Whoever triages the results.* Every failure gets a label before anything is edited, and the label
decides who fixes it:

```python
# triage.py — a failure is never "adjusted until green"
VERDICTS = {
    "impl":  "our code is wrong        -> fix the implementation",
    "port":  "the port is wrong        -> fix the test, cite the original line",
    "spec":  "we differ deliberately   -> xfail + document, never silently pass",
}
```

The label goes in the commit that resolves the failure, so the split stays queryable later. When
someone asks why your API behaves unlike the library everyone knows, `git log --grep=spec` is the
answer, and it was written at the moment the difference was discovered rather than reconstructed
afterwards.

*Whoever writes the docs.* Make the examples execute, so agent-written prose cannot drift from
agent-written code. Two lines of configuration turn every fenced example in your Markdown and
every docstring into a test:

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--doctest-glob=*.md --doctest-modules"
```

Run it in CI, not locally only. The failure mode this catches is not a broken example — it is a
correct example that silently stopped matching the implementation three commits ago, which is
exactly the kind of drift nobody notices in 150 pages of prose.

**How you know it worked.** The number to watch is not the pass rate, it is the **count of ported
tests that failed on the first run and the verdict split across them**. A port where everything
passes immediately is a port that was weakened — go and read ten of the assertions against the
originals before you believe it. A healthy first run has failures in all three buckets, and the
`spec` bucket is the deliverable: that list is your API's deliberate differences, discovered rather
than assumed, and it belongs in the documentation before release. Re-run it on every upstream
version bump; a newly failing ported test means the reference learned something you have not.

## When Borrowing a Test Suite Is the Wrong Tool

It needs a neighbour. If you are building something genuinely novel, there is no mature project
whose tests mean anything against yours, and forcing the comparison produces a port so loose it
asserts nothing. Fall back to property-based testing, where the oracle is an invariant rather than
another implementation.

**Check the licence before you port anything.** A test suite is source code, and a port is a
derivative work. wrapt is BSD-licensed and Dumpleton was porting tests from packages into his own
project, which is a different position from vendoring GPL tests into a proprietary codebase. This
is a five-minute check that is very awkward to undo after release.

It is also the wrong tool where the two APIs differ so much that every test needs real
reinterpretation. At that point the port is not a translation, it is new test authoring by the same
agent, and you are back where you started with extra steps.

Three questions before reaching for it. Is there a project close enough that its assertions still
mean something against my code? Does its licence let me carry its tests? And when a ported test
fails, do I have the discipline to explain it rather than edit it until it goes green?
