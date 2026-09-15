# 06 — What Hud actually provides

A capability inventory, separated from marketing. Written after three rounds of research that each
expanded what Hud turned out to cover — the honest summary is that **Hud is broader than a first
pass suggests**, and two earlier conclusions in this repo were wrong in Hud's favor.

Confidence keys as in `sources.md`. Everything here is from search summaries of `docs.hud.io`,
still egress-blocked from this network.

---

## Captured at the sensor

| Signal | Captured? | Detail |
|---|---|---|
| Invocation counts | **Yes — all** | No sampling **[A]** |
| Exceptions | **Yes — all, unsampled** | Explicitly "all exceptions"; unhandled exceptions named **[A]** |
| Durations | **Yes — sampled** | Incremental sampling, decreasing fraction as volume rises **[A]** |
| Execution paths | **Yes** | **[B]** |
| Branch decisions | **Yes** | **[B]** — understated in earlier drafts of this repo |
| Dependency interactions | Yes | **[A]** |
| Call graph | **Yes — aggregated** | Built over time; explicitly *not* distributed tracing **[A]** |
| **Raw variable values** | **No — by design** | *"does not capture full state or raw variable values"* **[B]** |
| Parameters at failure | **Yes — Forensic Engine** | On errors, spikes and degradations only: execution path, parameters, dependencies, machine state; scrubbed **[B]** |
| **Logs** | **No — by design** | Tracks behavior *"without requiring logs"*; does **not** replace your logging system **[B]** |
| Third-party internals | No | `node_modules` / `site-packages` excluded **[A]** |

**Overhead:** 1–2% claimed. **Languages:** Node/TS, Python, Java. **Storage:** ClickHouse Cloud. **[A]**

## Detection — "Heads-Up Alerts"

More built out than this repo originally credited. All run on production data with no
configuration. **[B]**

- **Post-deploy error regressions** — new or sharply increased errors immediately after each
  deploy; correlates each issue to the **deployed version**; highlights likely root-cause
  functions; **distinguishes new errors from increased existing ones**, across endpoints *and*
  queues.
- **Post-deploy performance regressions** — monitors new/updated functions and compares
  performance across 2-minute, 10-minute, 30-minute and hourly intervals, up to 24 hours
  after deploy.
- **HTTP 5XX correlation** — links 5XX responses back to the backend exception, naming the
  endpoint and the function likely responsible.
- **Delivery:** Slack, web app, and inside the IDE.

## Surfaces

- **IDE extensions** — Cursor, VS Code, JetBrains (also on Open VSX). Features named:
  **"Hudders"** (inline runtime performance and error signals rendered *above every function*),
  **Live Call Graphs**, and Heads-Up Alerts in-editor. **[B]**
- **MCP server** — the agent-facing surface. Cursor ≥ 1.2.41. **[A]**
- **Prompt to Fix** — per-issue-type prompts naming which Hud MCP tools to call; MCP-referencing
  rather than context-inlining; "Open in Cursor". **[A]**
- **Web app** — issue pages. **[B]**

## Three corrections to earlier conclusions in this repo

**1. Hud is not performance-focused.** Exceptions are first-class and unsampled, 5XX correlation
exists, and Hud publishes error-tracking content marketing positioning against Sentry. The
*evidence* skews performance (monday.com's CPU spikes, the triage-time metric) but the *product*
does not. `04-market.md`'s framing of the beachhead should be read with that in mind.

**2. Hud records execution paths and branch decisions**, not merely counts, durations and
exceptions as `02-architecture.md` implies. That is a genuine functional signal and it narrows
the "silent bug" gap — though it does not close it (see below).

**3. Hud does close the deploy-to-verify loop.** `05-assessment.md` and `fix_flow.md` both imply
nobody productizes post-merge verification. Heads-Up Alerts does exactly that, with version
attribution and separate error and performance regression detectors. That gap is **closed** and
should not be built against.

## What Hud genuinely does not cover

Three things, and they are the real inventory for a gap analysis:

**Handled and logged errors.** Hud does not ingest logs and names *unhandled* exceptions. The
single most common failure report in a mature service — `try/except` → `logger.error(...)` →
return an error response — is invisible to Hud unless it escapes uncaught or surfaces as a 5XX.

**Values in the normal path.** Hud explicitly does not capture raw variable values; it keeps
"constrained behavioral signals." Values appear only in the Forensic Engine, only once something
has already been flagged as an error, spike or degradation. So Hud sees **which branch ran**, never
**what flowed through it** while things looked fine.

**Silent functional bugs.** Follows from the above. A bug that returns `0` instead of `150`, or
writes the right shape to the wrong tenant, throws nothing, is not slow, produces no 5XX, and takes
the same branch. Nothing in the Heads-Up Alert set fires. This is the hole.
