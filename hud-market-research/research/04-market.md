# 04 — Market size and the "why now"

## The wedge: AI writes more code and breaks more production

Hud's entire market depends on one claim being true — that AI-generated code has raised the
production failure rate enough that teams will pay to close the loop. The data mostly supports it,
but the numbers in circulation vary wildly in quality, so they are graded here.

| Claim | Figure | Source quality |
|---|---|---|
| Share of enterprise code written by AI | **~41%** (Feb 2026) | **[C]** — "Zylos Research," cited second-hand; could not verify the primary. Directionally consistent with everything else, but do not quote this number in a deck. |
| Delivery stability | **−7.2%** | **[B]** — Google DORA |
| Incidents per pull request | **+23.5%** | **[B]** — industry aggregate |
| Incidents per pull request | **+242.7%** | **[C]** — single vendor blog. An order of magnitude away from the DORA-adjacent figure above. **Almost certainly measuring something different or badly.** Included only so you recognize it when a pitch deck quotes it. |
| Teams with rework rate under 2% | **only 7.3%** | **[C]** |
| Individual output: tasks completed | **+21%** | **[B]** — Faros AI Engineering Report 2026 |
| Individual output: PRs merged | **+98%** | **[B]** — same |
| Epics completed per developer | **+66.2%** | **[B]** — same |

**The honest synthesis:** throughput gains from AI coding are large and real. Stability degradation
is real but *modest* — single-digit percent on DORA's own measure, not the 3x some vendors claim.
AI-generated code churns faster because it produces plausible-looking code that needs later
refinement. **[B]**

**What this means for Hud's TAM.** The pitch writes itself — "AI merged 98% more PRs and your
stability went down, buy the safety net." But the gap between +98% throughput and −7.2% stability
is the thing to watch: for most teams, AI coding is still strongly net-positive, which means the
pain is real but **not yet acute enough to be a budget emergency.** Hud is selling into a problem
that is growing, not one that is already on fire. That is a fine place to be at $21M and a
difficult one at Series B, because it makes the sale a "should" rather than a "must."

## Market sizing

| Market | 2026 size | Growth | Source |
|---|---|---|---|
| **APM** | **$21B** | 12.8% CAGR; Datadog ~24% share | **[B]** |
| **Observability tooling** | **$4.35B** → $16.97B by 2035 | 16.5% CAGR | **[B]** |
| **AI code review** | **~$420M ARR** across vendors | ~$2B (2023) → ~$5B (2028) category | **[B]** |
| **AI code reviewer adoption** | **44%** of teams, at least some PRs | — | **[B]** |

The two observability figures disagree by 5x because they are measuring different things (full APM
including infrastructure vs. the observability-tooling slice). Use **$21B APM** as the ceiling of
the budget Hud is reaching into and **$420M AI-code-review ARR** as the realistic comparable for
how fast a genuinely new AI-devtool category monetizes.

### Sizing Hud's actual near-term market — bottom-up

Hud's reachable market today is narrower than any of those headline numbers, and the constraints
are concrete:

- Must run **Node/TS, Python or Java** — excludes Go, .NET, Ruby, PHP shops
- Must already use a **coding agent** (Cursor, Claude Code, Copilot) in the fix loop
- Must have **production complexity** worth a sensor — the monday.com "voodoo incidents" profile
- Must be willing to add a **second** runtime tool alongside Sentry or Datadog

That is a specific buyer: a mid-to-large engineering org, agent-forward, on a supported stack, with
distributed-system pain. It is a real segment and it is the right beachhead, but it is thousands of
companies, not tens of thousands. At a plausible enterprise ACV this supports a strong Series B
narrative only if the language coverage expands — which is exactly what the eBPF/runtime-internals
hiring signal suggests they know.

## Why the timing is genuinely good

Three things converged in late 2025 and Hud launched into all three:

1. **MCP became the default integration surface.** A year earlier, "give agents your runtime data"
   would have meant building bespoke plugins for every IDE. MCP made the distribution problem
   disappear — one server, every agent. Hud's whole go-to-market is only cheap because MCP exists.
2. **Agents crossed from autocomplete into merging code.** The "stops at the merge" framing only
   became a real gap once agents were actually reaching the merge.
3. **The incumbents' data shape is wrong for agents and they cannot easily change it.** Sentry is
   error-shaped, Datadog is infrastructure-and-trace-shaped. Rebuilding around continuous
   function-level aggregation is not a feature they can ship in a quarter.

**The counter-timing risk:** Lightrun shipped the same idea the same month, and Sentry shipped the
agent-handoff before either. Hud is not early to the thesis. It is betting on being *better at the
data layer*, which is a build-quality bet rather than a timing bet — and build-quality bets are
won by execution, not by the $21M.
