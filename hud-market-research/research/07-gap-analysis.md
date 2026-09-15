# 07 — Gap analysis: what is actually still open

Six candidate gaps, each tested against the question *"has someone already built this?"* rather
than asserted. Two turned out to be closed. That matters more than the four that are open —
a gap analysis that survives contact with the competition is the only kind worth acting on.

| # | Gap | Hud | Sentry | Datadog | Others | Verdict |
|---|---|---|---|---|---|---|
| 1 | Handled / logged errors | No | **Yes** | Yes | — | Open vs Hud only |
| 2 | **Value-level silent regressions** | No | No | No | Daikon (academic) | **WIDE OPEN** |
| 3 | Write-time push context to the *agent* | Partial | No | No | — | Open, narrower than it looks |
| 4 | Provenance × runtime outcome join | No | No | No | Provenance-only vendors | **Open at the join** |
| 5 | Language coverage | 3 langs | Many | Many | — | Open but it's a capex race |
| 6 | Deploy-to-verify loop | **Yes** | Yes | Yes | — | **CLOSED — do not build** |

---

## 1. Handled and logged errors — open vs Hud, closed vs Sentry

Hud does not ingest logs and targets unhandled exceptions, so caught-and-logged failures are
invisible to it. But **Sentry already covers this**: `captureException()` for handled errors, plus
a structured Logs product. **[A]**

So this is not an industry gap — it is a Hud gap, and the customer's answer is "also run Sentry,"
which most teams already do.

**What remains open:** Sentry's handled-error capture requires *manual instrumentation* — someone
has to have written the `captureException` call. The zero-config, auto-instrumented version of
handled-error capture does not exist. That is a real but modest wedge: table stakes for a product,
not a company.

## 2. Value-level silent regressions — the real gap

Nobody in the commercial market captures what *flows through* a function in the normal path. Hud
says so explicitly. Sentry is error-shaped, Datadog is trace-and-infra-shaped. All three detect
**crashes, slowness and 5XX** — which is how *human* bugs fail.

**AI-generated code does not fail that way.** It is plausible by construction: it returns the wrong
number, drops the edge case, writes to the right table with the wrong tenant id. No exception, no
latency change, no 5XX, same branch taken. The category sells "production-safe AI code" while
instrumenting exclusively for the failure mode AI code does not have.

**Is it feasible?** Yes, and the research is settled. **Daikon** has done dynamic invariant
detection — observe values across executions, infer the properties that held — since the early
2000s, and is still actively released (v5.9.1, September 2026). It is open source, academic, offline
and heavyweight: instrument, dump traces, analyze. **[A]**

**What nobody has done is make it continuous, cheap, and agent-facing.** The buildable version
never stores a raw value, which is what makes it privacy-viable for the same reason Hud avoided
values in the first place:

> Per function, keep the **shape** of what passes through — type distribution, null rate, numeric
> range, cardinality, enum membership — using sketches (t-digest, HyperLogLog) rather than stored
> values. Learn the envelope from production. A deploy that moves the distribution is a regression,
> detectable with no exception, no latency change, and no value ever persisted.

That is the one gap on this list where the science is proven, the commercial slot is empty, and it
sits exactly where AI code breaks.

## 3. Write-time push context — open, but narrower than first assessed

The original framing was "nobody puts runtime context in front of an agent before it writes." That
overstated it. Hud's IDE extension renders **"Hudders" — inline runtime performance and error
signals above every function** — plus Live Call Graphs. Write-time runtime context exists.

**But it is rendered for a human to read, not pushed into the agent's context window.** The
agent-facing path is Hud's MCP server, which is **pull**: the agent must choose to call it, and
the realistic trigger is a human starting from a Hud issue page.

What is open is the delivery mechanism: a `PreToolUse` hook that fires when the agent is about to
edit a function and injects that function's production reality **unrequested**. Claude Code has
supported this since v2.1.9 (`additionalContext`, January 2026) and a guardrail ecosystem exists
around it — but **every published hook is static**: block dangerous commands, enforce conventions,
run a formatter. Not one wires production telemetry into it. **[A]**

Push beats pull because agents under-ask, and an MCP tool that is never called is worth zero.

## 4. Provenance × runtime — open at the join only

The original claim, "nobody tracks which AI-authored code causes production failures," was **wrong
on the first half**. An AI-code-provenance category exists and is growing, driven by the EU AI Act
and California AB 2013: **Crash Override** (AI code traceability), **Exceeds Ink** (line-level
authorship written as a Git Note per commit), commit trailers recording whether a change was
autocomplete, generated block, or agent-authored. **[B]**

What none of them have is the **other half — the join to runtime outcome.** They record who wrote
it; nobody correlates that against what failed. One vendor states the problem without solving it:
*"without this you cannot correlate anything, and correlation is the whole point."*

This is better news than the original claim. The expensive half (capturing authorship, surviving
rebases and merges) is being standardized by others, and the join is cheap to build on top.

Supporting evidence for demand: Amazon's early-2026 incident where AI-generated code contributed
to an outage costing roughly **120,000 lost orders**. **[C — single source, verify before quoting]**

## 5. Language coverage — open, but not a wedge

Hud ships three languages; Go, .NET, Ruby and PHP are uncovered. This is a real constraint on Hud's
TAM (see `04-market.md`) but it is a capital-expenditure race against a funded team that is already
hiring for it. Do not compete here.

## 6. Deploy-to-verify — closed

Hud's Heads-Up Alerts do post-deploy error *and* performance regression detection with version
attribution, root-cause function highlighting, and new-versus-increased discrimination. Earlier
drafts of this repo said this was missing. **It is not. Do not build it.**

---

## Recommendation

**One data asset, two surfaces.**

The asset is **#2** — continuous value-shape capture, sketch-based, no raw values retained. It is
the only gap here with proven science, an empty commercial slot, and direct alignment with how AI
code actually fails.

Surface it two ways:
- **To the agent, at write-time, via #3** — a `PreToolUse` hook that pushes the function's value
  envelope into context before the edit, unrequested.
- **To the engineering leader, via #4** — join the value-shape regressions against the provenance
  metadata others are already emitting, and answer "which AI-authored changes are degrading
  production."

Treat **#1** as table stakes inside the sensor, not as the pitch. Ignore **#5** and **#6**.

**The strategic reason this shape works:** it does not require out-building Hud's sensor. Value
shapes can be derived from a thin hook of your own, or federated from what a team already runs.
A small team cannot win a multi-language low-overhead instrumentation race against $21M. It does
not have to.

**The honest risk:** value-shape capture is meaningfully more expensive per call than counting, and
high-cardinality arguments are the hard case. Sampling plus sketches make it tractable, but "1–2%
overhead" is a claim that would have to be earned, not assumed. That, and not the market, is what
would kill this.
