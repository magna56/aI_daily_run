# Friction as a Feature: Blast-Radius Gates for Agent-Driven Architecture Changes

**Category**: AI Engineering Practices
**Date**: 2026-07-17
**Level**: Building
**For**: Building agents
**Hook**: Do not review agent pull requests by diff size. Review them by how far the change reaches.
**Time to read**: ~10 minutes

## What It Is

Armin Ronacher's essay "The Tower Keeps Rising" (July 14, 2026) makes an observation that
matters a lot once agents write most of your diffs: a codebase's real specification isn't
the code — it's a distributed, mostly-undocumented "shared language" the team carries around
in their heads about what concepts mean, where module boundaries sit, which invariants must
hold, and who owns what. Historically, that shared model got *synchronized* as a side effect
of friction: to change a storage layer you had to read someone else's code, ask questions in
review, and coordinate across teams. Some of that slowness was pure waste. But some of it was
the mechanism by which "your understanding became mine" — the point where both parties
discovered whether they still agreed on how the system worked.

Agents remove the friction without replacing the synchronization. An agent can generate a
large, internally coherent, fully-tested diff that crosses three modules and changes a shared
interface in one shot — with no human ever having to read the boundary code to make the
change happen. The code can be correct and the team's shared mental model can silently
diverge anyway, because the step that used to force alignment (a human reading and explaining
the crossing) never happened.

The practical response isn't "add more review" (that's just re-adding the waste). It's to
separate the two things friction used to bundle together — *implementation cost* and
*synchronization value* — and gate only on the second. That means scoring diffs by how much
they cross architectural boundaries (modules, public interfaces, invariants, ownership) and
routing only high-scoring diffs through a mandatory "explain-back" checkpoint, regardless of
who or what wrote the code.

## Why It Matters

Teams running Claude Code / Copilot-style agents at scale are already hitting this: agents
happily produce PRs that touch five files across three owned areas, pass CI, and get rubber-
stamped because reviewing them line-by-line the old way doesn't scale and doesn't match how
the change was actually produced. The failure mode isn't a bug slipping through — tests catch
that. It's slow architectural drift: two teams' mental models of a shared invariant quietly
diverging until a production incident reveals they'd disagreed about it for months.

This reframes "human-in-the-loop" for agentic engineering: instead of gating on *who wrote the
code* (agent vs. human) or *diff size*, gate on *blast radius* — a semantic measure of whether
this specific change crosses a boundary that requires two people (or a person and an agent) to
re-confirm shared understanding. It's the same idea as Claude Code's permission-mode system
(some tool calls are auto-allowed, some need a human), applied one layer up, to architecture
instead of individual actions.

## Key Technical Details

- **Blast radius ≠ diff size.** A 200-line change confined to one module's internals can be
  lower risk than a 5-line change to a shared type's public signature.
- **Signals that matter**: number of distinct modules touched, whether any touched symbol is
  part of a public/exported interface, whether the change crosses a CODEOWNERS boundary, and
  the *fan-in* of touched symbols (how many other modules depend on them) — high fan-in means
  more places whose implicit assumptions could now be wrong.
- **Two-tier gate**: below threshold → agent + CI can merge with no human sync step (this is
  where removing friction is a pure win). At or above threshold → merge is blocked until a
  human produces an "explain-back": a short, structured statement of what invariant changed
  and why, attached to the PR (functionally a micro-ADR).
- **The explain-back is the point**, not the code review. It doesn't require the human to have
  written or even deeply reviewed the diff — it requires them to state, in their own words,
  what boundary moved. That's the cheapest possible re-creation of the old "your understanding
  became mine" moment, and it's auditable later when the invariant is questioned.
- **This composes with existing tooling** (CODEOWNERS, RFC-required paths) rather than
  replacing it — it adds a semantic signal (interface/invariant change) that path-based
  ownership alone can't see.

## How It Connects to What You Know

This is the ReAct/human-in-the-loop pattern applied at the architecture layer instead of the
tool-call layer. Claude Code already does per-action gating (auto-allow safe tools, prompt for
destructive ones); blast-radius gating is the same risk-proportionate-friction idea applied to
*what a diff means* rather than *what a tool does*. It's also a direct answer to the "vibe
coding vs. agentic engineering" tension Simon Willison and others have been writing about:
the fix isn't slowing agents down uniformly, it's building a cheap classifier for the narrow
slice of changes where slowing down actually buys you something.

## Try It Yourself

`code_example.py` builds a tiny synthetic module/ownership/call graph, simulates several
agent-authored diffs, computes a blast-radius score from cross-module reach + public-interface
touches + ownership crossings + symbol fan-in, and applies the two-tier gate — printing which
diffs fast-track and which get routed to a required human explain-back, with the reasons why.
