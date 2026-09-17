# Campaign slate — Microsoft AI / OpenAI fortnight (2026-09-17 → 2026-10-01)

**A campaign is a dated override of Step 2's topic choice, and nothing else.** Every content
rule, every word band, `node build.js --check` and the `--mix` audience gate apply exactly as
written. A campaign day that cannot clear the content gate is rewritten, never waived — the
slate below was built to sit inside the bands, so a breach means the article drifted, not that
the plan was wrong.

**It expires.** After the last dated row, Step 2 returns to autonomous selection with no further
edit. Do not extend a campaign by adding rows to a slate that has already run out; write a new
file with a new date range, or delete this one.

## Why this slate exists

An outreach fortnight aimed at Microsoft AI leadership. The strategy is not to explain Microsoft
features — their own developer relations does that better and nobody reshares it. It is that
**the scarcest thing a CEO has is credible third-party proof of the argument he is already
making.** Microsoft asserting that its own models are cheap is marketing. An outside engineer
publishing a reproducible harness that measures it, and says plainly where it loses, is an
artifact that can be pointed at.

So most days below take a phrase Satya Nadella uses in public and turn it into something an
engineer can run:

| The public claim | The day that tests it |
| --- | --- |
| "Tokens per dollar per watt" | 5 |
| "Every company must build its own token capital" | 8, 10 |
| MAI Thinking reasoning "at a fraction of the cost" | 6 |
| Maia 200, 1.4x efficiency | 9 |
| Agents are "a new paradigm" that run continuously | 13 |
| AI diffusion and its GDP impact | 14 |
| "No societal permission for an AI future that hollows out entire industries" | 15 |

Days 1-4 are not aimed at that audience at all. They are the technical credibility that earns a
reshare from working engineers, which is the only route by which anything reaches a CEO. Lead
with day 1: `microsoft/vscode-copilot-chat` is MIT-licensed, so its real system prompts and tool
definitions are readable, and almost nobody has written about them carefully.

**Day 15 is load-bearing and must stay honest.** Fifteen flattering articles is a campaign and
reads as one. One well-argued piece on where agents genuinely fail is what makes the other
fourteen quotable, and it is on-narrative rather than against it.

**The standing constraint:** every article has to survive as engineering content on its own
merit, judged by the acceptance test in `SKILL.md` — could a competent engineer ship the change
from this alone. If a campaign day can only be justified by who might read it, cut it and take
the autonomous pick for that date instead.

## The slate

| # | Date | Working title | Category | Tier | Level | For |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | What VS Code's open-source Copilot Chat actually sends the model | Coding Agents & Productivity | A | Start here | Using tools |
| 2 | 2026-09-18 | Building prompts as components with a token budget | Building Agents & MCP | A | Building | Building agents |
| 3 | 2026-09-19 | How VS Code moved agent sessions into their own process | Building Agents & MCP | A | Building | Building agents |
| 4 | 2026-09-20 | Running Codex inside VS Code's agent host | Coding Agents & Productivity | A | Start here | Using tools |
| 5 | 2026-09-21 | Measuring tokens per dollar per watt for real | AI in Production | B | Building | Shipping AI |
| 6 | 2026-09-22 | What a reasoning model costs per task, not per token | New Models & APIs | B | Start here | Using tools |
| 7 | 2026-09-23 | How much of your real work a 15B model can actually close | Applied Research | C | Deeper | How models work |
| 8 | 2026-09-24 | Routing between a small model and a frontier one | AI in Production | B | Building | Building agents |
| 9 | 2026-09-25 | What custom inference silicon changes for you, and what it doesn't | AI Hardware for Engineers | C | Deeper | Shipping AI |
| 10 | 2026-09-26 | The three levers you actually own on inference cost | AI in Production | B | Building | Shipping AI |
| 11 | 2026-09-27 | MCP and A2A across vendors: what actually interoperates | Building Agents & MCP | A | Building | Building agents |
| 12 | 2026-09-28 | Migrating off Semantic Kernel and AutoGen before they stop moving | Building Agents & MCP | A | Building | Building agents |
| 13 | 2026-09-29 | What a continuously-running agent costs over eight hours | AI in Production | B | Building | Shipping AI |
| 14 | 2026-09-30 | How to tell whether AI actually made your team faster | AI Engineering Practices | A | Start here | Using tools |
| 15 | 2026-10-01 | Where agents still fail, and what that means for the work | Evals & Reliability | A | Building | Shipping AI |

Planned mix over the fortnight: **Tier A 8 / B 5 / C 2**, `For` at Using tools 4 / Building
agents 5 / Shipping AI 5 / How models work 1, `Level` at Start here 4 / Building 9 / Deeper 2.
That was chosen to sit inside every band and to correct two drifts live on 2026-09-16: Tier C
and `How models work` were both at zero, and `Building` was running 8 of 10 against a target
of 6.

**Paper budget still binds.** At most one arXiv-led session per 7, so days 7 and 9 are the only
slots that may be built on a paper, and not both inside the same week.

## Per-day notes

Each row below gives the primary source to build on and the claim the day is testing. Sources
still have to clear the admission test in `selection.md`; a vendor blog post announcing a thing
is not a primary source for how the thing works.

1. **Copilot Chat prompts** — `github.com/microsoft/vscode-copilot-chat` (MIT). The `.tsx` prompt
   files, the intent routing, the tool definitions. Read the code, not the announcement. If you
   find something undocumented or wrong, file the issue alongside the article.
2. **prompt-tsx** — `github.com/microsoft/vscode-prompt-tsx`. Priority-based pruning under a
   token budget is the mechanism; component-shaped prompts are the framing.
3. **Agent Host Protocol** — VS Code 1.138 release notes and the AHP docs. Sessions in a
   dedicated process, attachable from multiple windows. Compare with MCP's transport model.
4. **Codex in the agent host** — `chat.agentHost.codexAgent.enabled`,
   `chat.editor.codex.preferAgentHost`, moving one session between the ChatGPT app and VS Code.
5. **Tokens per dollar per watt** — build the harness. Cost *and* energy per completed task, not
   per token. The honest finding is usually that per-token pricing hides task-level cost.
6. **Cost per task** — MAI Thinking against the field on a fixed task set. Name where it loses.
7. **Small-model ceiling** — Phi-4-reasoning-vision-15B and its decision to reason deeper only
   when needed. What fraction of real work closes without a frontier model.
8. **Small/frontier routing** — the router is the deliverable. Escalation policy, and the cost of
   getting escalation wrong in both directions.
9. **Custom silicon** — Maia 200 and the 1.4x claim. Be honest that most of it is not a developer
   lever; the article is about which knobs *are* yours.
10. **Inference cost levers** — caching, batching, context discipline. The "token capital" day.
11. **MCP and A2A** — what actually interoperates across vendors, tested rather than asserted.
12. **Agent Framework migration** — Semantic Kernel and AutoGen are in maintenance mode, so this
    is forced work with a real deadline. Microsoft Learn is the primary source.
13. **Long-running agent economics** — price a session over eight hours. Compaction, state, and
    where the cost curve bends.
14. **Measuring AI's effect on a team** — the hard one. The honest answer is that most
    measurements are confounded, and saying so is the article.
15. **Where agents fail** — failure taxonomy with evidence. No hedging, no apology.
