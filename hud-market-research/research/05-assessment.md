# 05 — Assessment: where the thesis holds and where it breaks

## The bet, stated in one line

> Coding agents are blind after the merge; own the sensor that gives them sight, and let every
> agent vendor fight over who writes the patch.

It is a good bet. It is also a *narrow* one, and the narrowness is deliberate — Hud has chosen a
position that is defensible against the agent vendors (it never competes with them) and fragile
against the observability vendors (who already have a version of its data).

## What is genuinely strong

**1. The data-shape argument is real, not marketing.**
Continuous function-level aggregation with 100% exception capture is a materially different asset
from error-shaped data (Sentry) or trace-shaped data (Datadog). An agent asking "how does this
function normally behave, and what was different when it broke" is answerable from Hud's data and
is *not* cleanly answerable from the others. That is the moat, and it is a technical one.

**2. Refusing to write the patch is strategically correct.**
It means Hud never has to beat Anthropic or Cursor at code generation, never holds customer source
code, rides agent adoption instead of competing with it, and has telemetry-shaped costs rather than
inference-shaped costs. Most companies in this space made the opposite choice and will regret it.

**3. MCP-not-inline was the right call and is underrated.**
It converts a one-shot context export into an iterative investigation surface. It is stickier, it
scales with agent capability instead of being capped by a template, and it generates a proprietary
signal — *which context agents actually request* — that nobody else in the category is collecting.
If Hud builds anything durable beyond the sensor, it will be built on that signal.

**4. 60-second install.**
Unglamorous and probably the highest-ROI thing they have. Instrumentation products die in
procurement and in "we'll get to it next sprint." Removing configuration removes the death.

## What is fragile

**1. Not owning the PR is a real structural risk.**
The PR is where the buyer sees value, where the review happens, and where the billing event
naturally sits. Sentry and Datadog both own it. If the market's mental model settles on "the thing
that opens the fix PR," Hud is one hop upstream and gets described as a data source — and data
sources get bundled, undercut, or acquired. Hud's only defense is that its data cannot be
reconstructed from logs and traces. That defense is currently true. It needs to *stay* true.

**2. The proof points are for the sensor, not for the agent loop.**
Both public monday.com quotes describe classic observability wins — voodoo incidents, CPU spikes,
context switching. The VentureBeat metric is *triage time*, 3 hours to 10 minutes: a human-triage
number, not an agent-fix number. **There is currently no public evidence of the agentic fix loop
working at a named customer.** The company is being sold on an agentic thesis and validated on an
observability outcome. That gap is the single most important thing to watch.

**3. It is an additive purchase.**
Nobody rips out Sentry to install Hud. Every deal is incremental budget next to a tool the team
already pays for, at a moment when Sentry charges $40/contributor for a loop that overlaps and
Datadog gives Bits Code away inside an existing contract. Additive spend is what gets cut first.

**4. Three languages.**
Node/TS, Python, Java. The SDK-per-language model means each new runtime is a real engineering
project, and the estate they cannot see is large. The runtime-internals/eBPF hiring is the right
answer and it is a hard, slow one.

**5. Category-naming risk.**
"Runtime Code Sensor" is a strong name and they are spending heavily to own it — but Lightrun
claimed essentially the same crown in the same month, and if the category ends up called something
else by someone bigger, the naming investment is stranded.

**6. Pricing opacity.**
No public pricing at all. That signals sales-led enterprise motion, which is coherent with the
Java support and the design-partner logos, but it sits badly with a 60-second self-serve install.
The install is built for product-led growth and the pricing is not, and one of those will have to
move.

## What would kill this

In rough order of likelihood:

1. **Sentry ships continuous function-level capture.** Seer already has the loop and the install
   base; the only thing missing is Hud's data shape. This is the existential one.
2. **Datadog bundles it to zero.** Not better — just included. Enough to end the additive-budget
   conversation in most accounts.
3. **Agents get good enough not to need it.** If a coding agent can read the repo, reproduce
   locally, and reason its way to the same conclusion, the runtime context becomes a nice-to-have.
   Less likely than it sounds — load- and data-dependent bugs are genuinely not reproducible from
   source — but it is the bear case.
4. **The pain never becomes acute.** DORA's own stability degradation is single-digit percent. If
   AI coding stays strongly net-positive, "production-safe AI code" stays a should-have.

## What would prove it out

- **A named customer on the agentic loop**, with a merged-PR count — not a triage-time number.
- **A fourth and fifth language**, ideally via the eBPF path rather than another SDK.
- **Self-serve pricing**, which would mean the 60-second install is actually converting.
- **An agent vendor embedding Hud by default** — the outcome that makes the "context supplier"
  position permanent rather than transitional.

## Bottom line

A technically sharp company with a correct read on where agents are blind, a genuinely
differentiated data asset, and a deliberate refusal to compete with the agent vendors — sitting in
a position that is one incumbent feature release away from being uncomfortable. The $21M and the
Wininger name bought them access and time; what they do with the next four languages and the first
public agentic-fix case study decides whether this is a category or a feature.

**Most likely outcome:** acquisition by an observability incumbent or an AI-SRE company that wants
a proprietary sensor rather than federated data. **Least likely outcome:** Hud becomes the
standalone system of record for runtime context across the industry — that requires beating Datadog
at distribution, and $21M does not buy that.
