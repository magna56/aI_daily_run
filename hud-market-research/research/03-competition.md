# 03 — Competitive landscape

Hud sits at the intersection of four markets that are actively collapsing into each other. The
useful way to map it is by **who owns the runtime data** and **who opens the PR**, because those
are the two chokepoints.

| Player | Owns runtime data? | Opens the PR itself? | Threat level to Hud |
|---|---|---|---|
| **Sentry (Seer)** | Yes — errors | **Yes**, and hands off to agents too | **Highest** |
| **Datadog (Bits Code)** | Yes — everything | **Yes** | **Highest** |
| **Lightrun** | Yes — dynamic instrumentation | No — MCP to agents | **Direct** |
| **AI-SRE tier** (Resolve, Traversal) | No — federates yours | Partially | Adjacent |
| **AI code review** (CodeRabbit, Greptile, Bugbot) | No | Yes (review, not fix) | Adjacent |
| **Hud** | Yes — function-level | No — MCP to agents | — |

---

## Tier 1: the incumbents who already have the data

### Sentry — Seer

The most direct threat, because Sentry already owns exception data at enormous scale and has built
exactly the loop Hud is describing.

- **Seer is the full loop:** Sentry detects an error, Seer finds the root cause, **Autofix opens a
  PR**, and if CI or code review flags something, **Seer iterates on the fix**. **[A]**
- Seer also does the handoff play: it **packages the evidence into a case file and hands it to
  Cursor cloud agents, Claude Code, or GitHub Copilot**, which implement, run checks and open the
  PR. **[A]** That is *Hud's exact motion*, shipped, by a company with an installed base.
- Expanded to **local development and code review** — catching bugs in PRs before production. **[A]**
- **Pricing: $40 per active contributor per month, unlimited usage**, simplified in January 2026. **[A]**

**Read:** Sentry has both halves. It opens the PR *and* it feeds agents. Its weakness is the data
shape — Sentry sees errors and traces, not the continuous function-level behavior of code that is
working fine. Hud's honest differentiator against Sentry is **"we see the 99% of executions that
did not throw"**, which is what you need for performance regressions, behavioral drift, and
blast-radius reasoning. Whether engineering leaders will pay for a second agent-context tool when
Seer is $40/contributor and already in the stack is the central commercial question.

### Datadog — Bits Code / Bits Investigation / Bits Agent Builder

The strategic threat, because Datadog is converting a monitoring platform into an agentic platform.

- **Bits Code** is positioned as an *"always-on developer teammate"* that turns production
  observability signals into **validated code fixes ready for human review**, and it **opens PRs
  on your behalf** according to preferences you define. **[A]**
- **Bits Investigation** integrates with Bits Code, connecting to your source provider to
  **create, update and iterate on production-ready PRs**. **[A]**
- **Bits Code for Code Security** auto-generates vulnerability fixes and opens PRs. **[A]**
- 2026 updates: new agent harness, **MCP-powered tool integration**, investigations completing in
  **3–4 minutes**, expanded to RUM, Database Monitoring and Network Path Analysis. **[A]**
- Enterprise controls: per-repo/service/team access scoping, **zero data retention** with
  third-party AI providers. **[A]**

**Read:** Datadog is the bundling risk, not the product risk. Its agentic fixes will be worse than
a specialist's for a while, but it is already in the account, already has the security review
passed, and holds ~24% APM vendor share. **[A]** The question every Hud deal will hit is "why not
just turn on Bits?" — and the answer has to be a data-shape answer, because it cannot be a price
answer.

### Lightrun

The closest philosophical competitor — same thesis, different capture mechanism.

- Launched an **MCP solution in December 2025** (same month as Hud's launch) billed as the
  *"industry's first fully integrated Runtime Context for AI coding agents."* **[A]** Note both
  companies claim a "first" in the same month; treat both category claims as marketing.
- Gives Cursor and Copilot visibility into post-deployment behavior; the MCP acts as a secure
  bridge letting agents **add logs and traces in real time, capture snapshots, investigate issues
  safely, and suggest fixes.** **[A]**

**Read:** Lightrun's model is *dynamic, on-demand* instrumentation — the agent asks a question and
Lightrun goes and instruments to answer it. Hud's is *always-on aggregate* capture — the answer is
already recorded. Lightrun is more powerful for a novel question; Hud is better for "what was
happening when it broke," because Lightrun has to be told to look *before* the crash and Hud
recorded it unconditionally. **Hud's 100%-exception-capture is the sharpest edge it has against
Lightrun and it should lead with it.**

---

## Tier 2: the AI-SRE layer

These attack from the incident side rather than the code side. They mostly *federate* data from
tools you already own, which is why they are adjacent rather than head-on — but they compete for
the same budget line and the same "agent fixes production" narrative.

- **Resolve AI** — **$125M Series A at a $1B valuation, February 2026**; **$150M+ total** including
  a $35M Greylock-led seed. Autonomous agents investigate in parallel across existing monitoring,
  cloud APIs and internal docs. **[A]**
- **Traversal** — **$48M raised**. Founded by Anish Agarwal (CEO), Raaz Dwivedi (Cornell Tech),
  Raj Agarwal, Ahmed Lone. Builds a **Production World Model** (a live map of services, infra and
  networking) plus a **Causal Search Engine** that walks 10+ hops to a root cause. **[A]**
- Others in the scan: Causely, DrDroid, Rootly AI SRE, Sherlocks.ai, Dash0's Agent0. **[B]**

**Read:** $173M into two companies in this tier versus Hud's $21M. But note what they *do not*
have: their own sensor. They reason over data someone else collected, which means their ceiling is
set by the quality of that data. Hud's $21M buys a data asset; Resolve's $150M buys a reasoning
layer on top of commodity data. **Those are complementary, not competing — the most likely
outcome is that a company like Resolve or Traversal would rather integrate Hud than rebuild it,
which is also the most likely acquisition path.**

## Tier 3: the AI code-review layer

Shifted left of Hud entirely — they catch bugs at the PR, before production. Relevant because they
are competing for the same "AI makes code unsafe, buy this" budget, and because they are the
category that has already proven engineering leaders will pay.

- **CodeRabbit** — **$88M raised** ($16M Series A led by CRV, Aug 2024; $60M Series B).
  **~140K paid users**, largest GitHub install base. **[A]**
- **Cursor Bugbot** — **2M+ PRs reviewed monthly** after Cursor **acquired Graphite in
  December 2025**. **[A]**
- **Greptile** — **$25M Series A**, 2,000+ customers including Brex and Substack. **[A]**
- Category scale: **~$420M in 2026 ARR across all vendors**, with **44% of teams** using an AI code
  reviewer on at least some PRs. **[B]**

**Read:** This tier proves demand exists but it also *caps* Hud's story. Every bug caught at review
is a bug Hud never gets to sell the runtime forensics for. Hud's counter is the class of bug review
cannot see — load-dependent, data-dependent, environment-dependent failures — which is a real and
permanent class, but a smaller one than "all bugs."

---

## Where Hud is genuinely differentiated

1. **Function-level continuous behavior, not just failures.** Sentry sees throws. Hud sees the
   behavior of every function all the time, which is the only way to reason about regressions that
   do not throw.
2. **100% exception capture with forensics.** No sampling on the thing that matters. This is the
   direct answer to Lightrun.
3. **Aggregated call graph instead of distributed tracing.** Cheaper, and the shape an agent
   actually wants. Nobody else made this specific tradeoff.
4. **60-second, zero-config install.** In a category where instrumentation projects die in
   procurement, time-to-first-value is a real moat at the bottom of the funnel.
5. **No source-code custody.** Because the agent does the fixing, Hud never holds the repo. That is
   a materially shorter enterprise security review than Datadog's or Sentry's.

## Where it is not

1. **It does not own the PR** — the moment the buyer actually sees value.
2. **Three languages.** No Go, .NET, Ruby, PHP. Half the enterprise estate is out of scope.
3. **A "second tool" sale.** The buyer already has Sentry or Datadog. Hud is additive spend,
   not replacement spend, and additive spend is the first thing cut.
4. **The category name is contested.** Lightrun claimed the same "first runtime context for agents"
   crown the same month.
