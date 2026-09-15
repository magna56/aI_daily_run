# 01 — The company

## Identity

| | |
|---|---|
| **Name** | Hud (stylized lowercase; the site is `hud.io`) |
| **Category it claims** | "Runtime Code Sensor" — a category it invented and is trying to own |
| **Tagline** | *Runtime Code Sensor for Production-Safe AI Code* **[B]** |
| **HQ** | Israel **[A]** |
| **Funding** | **$21M**, announced December 2025 **[A]** |
| **Public launch** | December 11, 2025 — "Hud Ships First Runtime Code Sensor to Bring Production Reality to Code Generation" **[A]** |
| **Pricing** | **Not public.** No published tiers, no self-serve price page found. Treat as sales-led. **[A]** |

### Name collision — check this before you search

There are at least three unrelated things called "HUD" in this space, and search engines conflate
all of them:

- **hud.io** — this company. Runtime code sensor.
- **hud.so / hud-evals** — a *different* company doing RL environments and evals for AI agents
  (`github.com/hud-evals/hud-python`). Completely unrelated.
- **Hudu** — an MSP IT-documentation platform with its own MCP server. Pollutes almost every
  query containing "hud" and "MCP".
- **claude-hud**, **hud-mode** — community Claude Code plugins that render a status display.

Any competitive scan that does not filter these out will produce garbage.

## Founders

**[A]** — corroborated across Calcalist, the launch press release and startup databases.

| Name | Role | Background |
|---|---|---|
| **Roee Adler** | CEO, co-founder | Former senior executive at WeWork |
| **May Walter** | CTO, co-founder | Formerly CTO at Santa, Bond and Shookit |
| **Shai Wininger** | Non-executive founder | Co-founder & CEO of Lemonade (NYSE: LMND); previously co-founded Fiverr |

**Why this matters commercially.** Wininger is the signal. He has taken one company public and
co-founded another that became a category name. A non-executive founder of that profile buys three
things a seed-stage devtool normally cannot get: a $21M round without a public product, design-partner
access to serious engineering organizations, and press that treats a category claim ("the first
runtime code sensor") as news rather than as marketing. Do not read the $21M as a signal of unusual
early traction; read it as a signal of founder access.

## What they say the product is

Hud's framing is precise and worth quoting rather than paraphrasing, because the whole positioning
lives in one sentence: AI agents "help engineering teams plan, write, test, and review code, but
their assistance **stops at the merge**." **[C — marketing copy]**

Everything else follows from that. Hud is not claiming to be better observability. It is claiming
there is an unserved leg of the AI software lifecycle — *after* the agent merges — and that agents
cannot close the loop there because they have no representation of runtime behavior.

The product claims, in their words:
- installs in **under a minute, no configuration** **[B]**
- streams **real-time, function-level runtime data** from live systems **into the IDE** **[B]**
- when a regression occurs, "roll back before the blast radius grows" **[C]**
- **"forensics captured at the moment of failure — ready for an agent to open the fix PR"** **[C]**

That last clause is the one to be careful with. See `02-architecture.md` — the agent opens the PR,
not Hud.

## Traction evidence

Named, attributable customers found:

- **monday.com** — Moshik Eilon, Group Tech Lead, on record: *"With Hud we just get all of this
  information for all functions, even for underlying packages."* A second monday.com quote:
  *"In a complex system like ours, Hud eliminated our voodoo incidents — like mysterious CPU spikes
  that required custom profiling tools and days of investigation."* **[B]**
- **Drata** — a published case study. The three stated drivers were (1) context-switching cost,
  with engineers acting as human bridges between disconnected tools, (2) alert fatigue in a complex
  distributed system, and (3) a need to plug into the company's AI strategy. **[B]**
- **VentureBeat** ran a piece headlined on a claim that Hud's sensor **cut triage time from
  3 hours to 10 minutes**. **[B — single source, vendor-supplied metric, page not directly fetchable]**

Infrastructure partner: **ClickHouse Cloud** is the storage layer, confirmed by a ClickHouse
customer blog post. **[A]**

Distribution surfaces confirmed: IDE extensions for **Cursor, VS Code and JetBrains**; an
extension listed on **Open VSX**; SDKs for **Node.js/TypeScript, Python and Java**. **[A]**

### How to read the traction

Two named logos, one of them (monday.com) a large, genuinely complex Israeli engineering org that
is exactly the design-partner profile you would expect a Tel Aviv seed company to land, and one
(Drata) a US compliance SaaS. Both quotes describe the *observability* value — finding voodoo
incidents, killing context switching — **not** the agentic-fix value. That is a meaningful tell:
the proof points that exist are for the sensor, and the agent story is still forward-looking.

## Hiring signal

A listed opening for **"Senior Software Engineer, Runtime Internals"** referencing eBPF and
low-overhead tracing. **[B]** Read this as: the current product is SDK-based auto-instrumentation,
and they are investing in going deeper — likely toward language-agnostic or kernel-level capture
that would remove the per-language SDK tax. That is the right technical bet and it is expensive.
