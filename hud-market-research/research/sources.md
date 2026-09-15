# Sources

## Methodology and its limits — read first

Research date: **2026-09-15**.

The network used for this research **blocks outbound egress to several key domains**, including
every first-party Hud property. The following could **not** be fetched directly:

- `hud.io` — blocked
- `docs.hud.io` — blocked (docs, changelog, MCP install guide, FAQ)
- `venturebeat.com` — blocked
- `clickhouse.com` — blocked
- `prnewswire.com` — blocked

Everything attributed to those domains below comes from **search-engine summaries of their
content**, not from reading the pages. Direct quotes sourced this way are marked. Before using any
specific figure externally, re-verify it against the primary page from an unrestricted network.

**Not found at all, and therefore absent from this research rather than estimated:** Hud's pricing,
headcount, ARR, customer count, exact investor names, and any third-party technical benchmark of
the 1–2% overhead claim.

## Confidence key

- **[A]** corroborated by two or more independent sources
- **[B]** single credible source
- **[C]** inference, or vendor marketing copy taken at face value

---

## First-party Hud (all via search summaries — not directly fetched)

- Homepage — https://www.hud.io/
  *Positioning, "stops at the merge", forensics/PR copy, customer quotes.* **[C]** for copy claims.
- Docs, Welcome — https://docs.hud.io/docs/welcome
- Docs, FAQ — https://docs.hud.io/docs/faq
  *Source of the sensor mechanics: no distributed tracing, aggregated call graph, 1–2% overhead,
  incremental duration sampling, 100% exception capture, third-party code excluded.* **[A]**
- Docs, What You Can Do with Hud — https://docs.hud.io/docs/what-you-can-do-with-hud
- Hud MCP Server overview — https://docs.hud.io/docs/hud-mcp-server
- Install MCP — https://docs.hud.io/docs/install-mcp
  *Cursor ≥ 1.2.41, Tools & MCP toggle.* **[A]**
- Changelog index — https://docs.hud.io/changelog
- Changelog, "Copy Prompt to Fix" — https://docs.hud.io/changelog/introducing-prompt-to-fix
- Changelog, "Prompt to Fix for Every Issue — From Detection to Fix in One Click" —
  https://docs.hud.io/changelog/prompt-to-fix-for-every-issue-from-detection-to-fix-in-one-click
  *The key source on the fix flow: per-issue-type prompts, MCP-not-inline, "Open in Cursor".* **[A]**
- Glossary, code instrumentation — https://www.hud.io/glossary/code-instrumentation/
- Legacy marketing site — https://hud-bkp.webflow.io/

## Company, funding, founders

- **Calcalist / Ctech**, "Hud quietly raises $21 million for sensor built for the AI coding era" —
  https://www.calcalistech.com/ctechnews/article/rygzfgomwe **[A]**
- **PR Newswire**, "Hud Ships First Runtime Code Sensor to Bring Production Reality to Code
  Generation" (2025-12-11) —
  https://www.prnewswire.com/news-releases/hud-ships-first-runtime-code-sensor-to-bring-production-reality-to-code-generation-302637854.html **[A]**
- Yahoo Finance syndication of the above —
  https://finance.yahoo.com/news/hud-ships-first-runtime-code-140000747.html
- New-Tech Europe syndication —
  https://www.new-techeurope.com/2025/12/11/hud-ships-first-runtime-code-sensor-to-bring-production-reality-to-code-generation/
- **Crunchbase** — https://www.crunchbase.com/organization/hud-0892
- **Startup Nation Finder** — https://finder.startupnationcentral.org/company_page/hud
- israel.com, "Israeli Startup Hud Launches Tool to Make AI-Generated Code Safer" —
  https://israel.com/breaking-only/israeli-startup-hud-launches-tool-to-make-ai-generated-code-safer/

## Technical and traction

- **ClickHouse**, "How Hud is building the first runtime code sensor with ClickHouse Cloud" —
  https://clickhouse.com/blog/hud-runtime-code-sensor **[A]** for the ClickHouse dependency.
- **VentureBeat**, "How Hud's runtime sensor cut triage time from 3 hours to 10 minutes" —
  https://venturebeat.com/ai/how-huds-runtime-sensor-cut-triage-time-from-3-hours-to-10-minutes
  **[B]** — vendor-supplied metric, page not directly read.
- Open VSX extension listing — https://open-vsx.org/extension/hud/hud **[A]**
- G2 seller page — https://www.g2.com/sellers/hud
- Snowman Labs partner page — https://snowmanlabs.com/partners/hud-runtime-intelligence
- DEV Community writeup — https://dev.to/anthonymax/hud-runtime-code-sensor-for-production-safe-ai-code-1kbo
- Job listing, "Senior Software Engineer, Runtime Internals" —
  https://freehire.me/jobs/senior-software-engineer-runtime-internals-hud-odqecf3t **[B]**

## Competitors

**Sentry / Seer** — all **[A]**
- https://sentry.io/changelog/seer-sentrys-ai-debugger-is-generally-available
- https://sentry.io/about/press-releases/sentry-expands-seer-ai-debugging-agent
- https://sentry.io/cookbook/self-healing-workflow-seer/
- https://sentry.io/cookbook/ai-code-review-seer/
- https://sentry.io/cookbook/seer-agent-use-cases/
- https://blog.sentry.io/automated-debugging-workflow-sentry/
- https://docs.sentry.io/ai/
- https://theaiengineer.substack.com/p/how-sentry-built-seer

**Datadog / Bits** — all **[A]**
- https://www.datadoghq.com/product/ai/bits-code/
- https://www.datadoghq.com/blog/bits-code/
- https://www.datadoghq.com/blog/bitsai-dev-agent-code-security/
- https://docs.datadoghq.com/bits_ai/bits_code/
- https://docs.datadoghq.com/bits_ai/bits_remediation/
- https://stack-archive.com/blog/datadog-dash-2026-bits-ai-agent-platform-2026/ **[B]**

**Lightrun** — **[A]**
- https://finance.yahoo.com/news/lightrun-runtime-context-empowers-ai-130000632.html

**AI-SRE tier**
- https://www.traversal.com/ and https://startupintros.com/orgs/traversal **[A]**
- https://rootly.com/ai-sre, https://www.dash0.com/comparisons/best-ai-sre-tools **[B]**
- https://github.com/agamm/awesome-ai-sre **[B]**
- https://www.anyshift.io/blog/top-10-ai-sre-tools-2026-comparison **[C]**

**AI code review tier**
- https://cursor.com/en-US/changelog/1-0 **[A]**
- https://levelop.dev/blog/best-ai-code-review-tools-2026-coderabbit-greptile-qodo-compared **[B]**
- https://www.ideaplan.io/blog/ai-code-review-tools-market-share-2026 **[B]**
- https://tech-insider.org/coderabbit-vs-greptile-vs-qodo-2026/ **[C]**

## Market data

- **DORA 2025/2026** via https://www.faros.ai/blog/key-takeaways-from-the-dora-report-2025 **[B]**
- Faros AI Engineering Report 2026 (throughput figures) **[B]**
- https://justanalytics.app/blog/apm-market-statistics-and-trends-2026 — APM $21B **[B]**
- https://www.businessresearchinsights.com/market-reports/observability-tool-market-122304 **[B]**
- https://www.pagerly.io/blog/ai-generated-code-incidents-2026-data-2026-08-30 — source of the
  **+242.7% incidents per PR** figure. **[C] — treat as unreliable**, an order of magnitude from
  every other estimate.
- https://www.practicallogix.com/the-2026-vibe-coding-reckoning-what-dora-actually-found **[C]**

## Explicitly NOT Hud — name collisions

- `hud-evals` / hud.so — RL environments and agent evals. https://github.com/hud-evals/hud-python
- **Hudu** — MSP IT documentation. Dominates "hud MCP" search results.
- `jarrodwatts/claude-hud`, `adrida/hud-mode` — Claude Code status-display plugins.
