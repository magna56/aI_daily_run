# 02 — How it actually works

This is the mechanism, hop by hop, with the design tradeoff at each hop. Where Hud's own
description is thin, the reasoning is marked as inference.

```
  production process
        │
        │  (1) SDK auto-instruments — no code changes
        ▼
  ┌───────────────┐   function-level telemetry     ┌──────────────┐
  │ Runtime Code  │ ─────────────────────────────▶ │  ClickHouse  │
  │    Sensor     │   counts · sampled durations   │    Cloud     │
  │  (the hook)   │   ALL exceptions + forensics   └──────┬───────┘
  └───────────────┘                                       │
                                                          │ (2) aggregation
                                                          ▼
                                                   ┌──────────────┐
                                                   │    Issues    │
                                                   │  (detected)  │
                                                   └──────┬───────┘
                                                          │ (3) "Prompt to Fix"
                                                          ▼
   ┌──────────────────┐   MCP tool calls          ┌──────────────┐
   │   Hud MCP server │ ◀──────────────────────── │ coding agent │
   │ (production ctx) │ ────────────────────────▶ │ Cursor/Claude│
   └──────────────────┘   runtime ground truth    └──────┬───────┘
                                                          │ (4) GitHub MCP
                                                          ▼
                                                     ┌─────────┐
                                                     │   PR    │
                                                     └─────────┘
```

---

## Hop 1 — the hook ("cheap on the stack")

A **language-specific SDK that auto-instruments your code without modifying it**. **[A]**

What it records: **invocation counts, durations, exceptions, execution flows, dependency
interactions** — and it correlates system-level symptoms with the underlying function-level
cause. **[A]**

The three design decisions that define the product:

### It explicitly does *not* do distributed tracing

This is the most important architectural choice Hud made and the one their own docs call out.
Instead of per-request spans stitched across services, Hud **collects function-level telemetry and
builds an aggregated call graph over time.** **[A]**

*The tradeoff:* you lose the ability to answer "what happened to request `abc123`." You gain the
ability to answer "how does `parseConfig` behave, across every call, in aggregate" — cheaply, with
no sampling decisions made at trace-entry, and with no head-based sampling blind spots. For an
*agent* the second question is strictly more useful than the first: an agent fixing code needs the
behavior of the function it is about to edit, not the narrative of one request.

This is also why the overhead claim is credible. Aggregation is cheap; span propagation is not.

### Incremental sampling on durations, but 100% on exceptions

**All invocation counts and all exceptions are captured. Durations are incrementally sampled** —
timings are recorded on a decreasing fraction of invocations as call volume grows (early calls
measured often, later calls rarely). **[A]** Claimed overhead: **1–2%**. **[A]**

*The tradeoff:* p99 latency on hot paths gets statistically estimated rather than measured. For
the agentic use case that is fine — an agent needs "this function is slow and here is roughly how
slow," not a precise tail figure. But a performance engineer chasing a tail regression will find
this less useful than a real profiler, and Hud should not be sold as a profiler replacement.

**Errors are the asymmetric case and they got it right.** You cannot sample exceptions if the
product's core promise is "forensics captured at the moment of failure." Sampling would mean the
one crash the agent needs is the one you dropped. 100% exception capture is what makes the fix
loop work at all.

### It ignores third-party code

`node_modules`, `site-packages` and equivalents are excluded. **[A]**

*The tradeoff:* this is the single biggest cost-control lever — most stack frames in a real app are
library frames, and dropping them collapses cardinality by an order of magnitude. It is also what
keeps the call graph readable to an agent. But note the tension with the monday.com quote
(*"even for underlying packages"*) — the two claims are in some friction, and the likely resolution
is that library *boundaries* are recorded as dependency interactions while library *internals*
are not. **[C — inference, worth verifying]**

**Languages:** Node.js/TypeScript, Python, Java. **[A]** Notably absent: Go, Ruby, .NET, PHP.
Java's presence signals they are chasing enterprise, not just the startup stack.

---

## Hop 2 — from telemetry to issues

Hud surfaces discrete **"issues"** with types (exception clusters, performance regressions,
anomalous behavior), each carrying the runtime forensics captured when it occurred. **[B]**

The inference worth making: an aggregated call graph plus 100% exception capture gives you a
*fingerprint* — exception type plus the top application frame plus the call path that reached it.
That fingerprint is what lets the system say "this is one issue seen 4,812 times" rather than
"here are 4,812 stack traces," and it is what makes the downstream prompt small enough to fit in
an agent's context. **[C — inference; this is how the prototype implements it]**

---

## Hop 3 — "Prompt to Fix" — this is the actual product surface

Two changelog entries define it: *"Copy Prompt to Fix"* (initial) and *"Prompt to Fix for Every
Issue — From Detection to Fix in One Click"* (the expansion). **[A]**

What it does:

- **Every issue** gets a ready-made prompt you can hand to a coding agent. **[A]**
- **Each issue *type* gets a dedicated prompt** that identifies the problem and tells the agent
  **exactly which Hud MCP tools to call.** **[A]**
- The prompts are **MCP-based rather than context-inlined** — the prompt does not paste the
  forensics in, it instructs the agent to *go fetch* them, "which means your agent gets access to
  the full depth of Hud's production data during investigation." **[A]**
- An **"Open in Cursor"** button (requires Cursor ≥ 1.2.41 with the Hud MCP toggle enabled) fires
  the prompt straight at the agent. **[A]**

### Why "MCP rather than inline" is the smartest decision in the product

Inlining forensics into a prompt caps the investigation at whatever the issue page decided to
include. MCP turns it into a **conversation**: the agent reads the exception, forms a hypothesis,
and calls back for the call graph, the caller's argument distribution, the behavior of the function
before the deploy. It can iterate. An inlined blob cannot be iterated against.

It is also the better *business* decision. Inlined context is a one-shot export — trivially
replicated by any competitor with the same data. An MCP surface that agents call repeatedly during
every investigation becomes the thing the agent's workflow is built around. It is stickier, and it
generates usage telemetry about which context agents actually need, which is a compounding data
advantage nobody else in this category is collecting.

---

## Hop 4 — who opens the PR

**This is the nuance most coverage gets wrong, including some of Hud's own copy.**

Two claims circulate:

1. *"Hud catches production exceptions and **opens a fix PR** grounded in the full execution
   context, ready for an agent to ship."* **[C — homepage copy, not directly verified]**
2. *"Forensics captured at the moment of failure — **ready for an agent to open the fix PR**."*
   **[C — same copy family]**

Those two say different things, and the documented mechanism supports the second. The confirmed
flow is: Hud detects → Hud generates a prompt → prompt names Hud MCP tools → **your agent**
(Cursor, Claude Code, Copilot) investigates → **your agent** writes the patch → **your agent**
opens the PR, in practice through the GitHub MCP server or the agent's native GitHub integration.

So the "one-click PR" is real, but the click starts an agent; it does not start a Hud service that
writes code. **Hud supplies the ground truth. The agent does the engineering. GitHub MCP is the
delivery mechanism, and it belongs to the agent, not to Hud.**

### Why the distinction matters strategically

It cuts both ways.

**In Hud's favor:** not writing the patch is a *deliberate and defensible* choice. It means Hud
never has to be as good at code generation as Anthropic or Cursor — a race it would lose. It means
Hud is complementary to every coding agent rather than competitive with any of them, so it rides
agent adoption instead of fighting it. It means no source-code custody, which shortens enterprise
security review dramatically. And it means their costs are telemetry costs, not inference costs.

**Against Hud:** the layer that owns the PR owns the user relationship, the review surface, and the
billing event. Sentry Seer and Datadog Bits Code both open PRs themselves. If "who opened the PR"
becomes the thing engineering leaders evaluate, Hud is one hop removed from the moment of value and
is structurally positioned as a data source — and data sources get commoditized, bundled, or
replaced by whoever owns the endpoint. Hud's answer has to be that its data is not reproducible
from logs and traces, which is exactly what the no-distributed-tracing, 100%-exceptions,
function-level design is for.

That is the whole bet, stated plainly: **be the context nobody else has, and let everyone else
fight over the patch.**
