# Hud — market research + pipeline prototype

A teardown of **[Hud](https://www.hud.io/)**, the Israeli startup that calls its product the
*"Runtime Code Sensor"*: a low-overhead hook you install in production that captures
function-level behavior and exception forensics, then hands that context to a coding agent
so the agent can open a fix PR.

This repo is two things:

1. **`research/`** — a market teardown: the company, how the product actually works, who it
   competes with, how big the market is, and where the thesis is fragile.
2. **`prototype/`** — a dependency-free Python implementation of the whole pipeline the
   research describes: auto-instrumentation hook → aggregated call graph + crash forensics →
   issue detection → MCP server → generated "prompt to fix" → agent opens the PR via GitHub MCP.
   It is ~700 lines of stdlib Python and runs in one command.

## The one-paragraph version

Coding agents now write a large share of production code, but they write it blind: they see the
repo and the tests, never how the function behaves under real traffic. Hud sells the missing
input. A language SDK auto-instruments the app with claimed 1–2% overhead, deliberately skipping
distributed tracing in favor of aggregated function-level telemetry, and captures full forensics
at the moment an exception is thrown. When something breaks, Hud does not write the patch itself —
it generates a **prompt** that tells your agent which Hud MCP tools to call, and your agent pulls
the production context and opens the PR. The product is a *context supplier to agents*, not an
observability dashboard, and that framing is the entire bet.

## Read in this order

| Doc | What it answers |
|---|---|
| [`research/01-company.md`](research/01-company.md) | Who Hud is, funding, founders, traction, positioning |
| [`research/02-architecture.md`](research/02-architecture.md) | How the sensor, issue detection, MCP and PR handoff actually work |
| [`research/03-competition.md`](research/03-competition.md) | Sentry Seer, Datadog Bits Code, Lightrun, the AI-SRE tier, the code-review tier |
| [`research/04-market.md`](research/04-market.md) | Market size, the "why now" data, adoption evidence |
| [`research/05-assessment.md`](research/05-assessment.md) | Where the moat is real, where it is not, and what would kill this |
| [`research/sources.md`](research/sources.md) | Every source, with a confidence rating per claim |
| [`prototype/README.md`](prototype/README.md) | Run the pipeline yourself |
| [`prototype/fix_flow.md`](prototype/fix_flow.md) | The one-click PR hop by hop, and who owns each hop |

## Run the prototype

```bash
make demo    # replay traffic through the sensor, then print what an agent would see
make test    # 18 self-checks, including a full MCP handshake
```

`make demo` runs a checkout service 250 times. One tenant out of six was configured through a
legacy admin panel that writes a config value as a string instead of an int — 5% of traffic, no
failing test, nothing wrong-looking in the repo. The sensor catches all 21 crashes, collapses them
into one issue, and prints the local variable values captured at the moment of failure:

```
TypeError: unsupported operand type(s) for //: 'str' and 'int'  (seen 21 times)
  demo_app.py:43  in demo_app.py:apply_discount
    discount = price_cents * config["discount_bps"] // 10000
      price_cents    = 53452
      config         = {'tenant': 'initech', 'currency': 'USD', 'discount_bps': '150'}
```

`'150'` in quotes is the entire product. An agent reading the repo cannot know that value is
sometimes a string. An agent reading this fixes it in one pass.

## Evidence quality — read this before quoting anything

The network this research was performed on **blocks egress to `hud.io`, `docs.hud.io`,
`venturebeat.com`, `clickhouse.com` and `prnewswire.com`.** No first-party Hud page was fetched
directly. Everything here comes from search-engine summaries of those pages plus secondary
coverage. Claims are tagged:

- **[A]** — corroborated by two or more independent sources
- **[B]** — single source, but a credible one (press release, named-customer quote, vendor docs)
- **[C]** — inference or marketing copy taken at face value; verify before acting on it

Pricing, headcount, ARR and customer count are **not public** and are not guessed at anywhere in
this repo.
