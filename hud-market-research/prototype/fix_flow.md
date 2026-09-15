# The one-click PR, hop by hop

What actually happens between "production throws" and "a pull request exists" — and which
component owns each hop. The ownership column is the strategically interesting one.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 1. PRODUCTION            apply_discount() raises TypeError                      │
│                          owner: your app                                        │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │ the hook is already attached — nothing to turn on
┌───────────────────────────────▼─────────────────────────────────────────────────┐
│ 2. SENSOR                capture every frame + every LOCAL VALUE                 │
│                          100% of exceptions, never sampled                       │
│                          owner: HUD                                              │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │ fingerprint = exc type + innermost app frame
┌───────────────────────────────▼─────────────────────────────────────────────────┐
│ 3. AGGREGATE             21 crashes collapse into ONE issue: EXC-78aafbd4        │
│                          alongside call counts, durations, the call graph         │
│                          owner: HUD                                              │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────────────┐
│ 4. PROMPT TO FIX         a prompt that NAMES TOOLS rather than pasting context   │
│                          "call get_issue, then get_function_stats, then..."       │
│                          owner: HUD          <-- this is the click               │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │ "Open in Cursor" / paste into Claude Code
┌───────────────────────────────▼─────────────────────────────────────────────────┐
│ 5. AGENT INVESTIGATES    pulls production context through HUD MCP, iteratively    │
│                          owner: YOUR AGENT (Cursor / Claude Code / Copilot)      │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────────────┐
│ 6. AGENT WRITES THE FIX  reads the repo, edits the code, runs the tests          │
│                          owner: YOUR AGENT           <-- HUD is not here         │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────────────┐
│ 7. GITHUB MCP            create_branch -> push_files -> create_pull_request       │
│                          owner: GITHUB MCP SERVER    <-- HUD is not here either  │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────────────┐
│ 8. HUMAN REVIEWS         the PR body cites what the sensor observed               │
│                          owner: you                                              │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │ merge + deploy
┌───────────────────────────────▼─────────────────────────────────────────────────┐
│ 9. SENSOR CONFIRMS       the fingerprint stops appearing -> issue closes itself   │
│                          owner: HUD          <-- the loop closes                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Read the ownership column

HUD owns hops 2, 3, 4 and 9. It does **not** own 5, 6 or 7 — the investigation, the patch, or the
pull request. Marketing copy that says "Hud opens a fix PR" is compressing hops 4–7 into one
sentence and giving HUD credit for three hops it deliberately does not own.

**Hop 9 is the underrated one.** Because the sensor is still running after the merge, it can
confirm the fix worked without anyone checking — the fingerprint either reappears or it does not.
No other component in this chain can close that loop, and it is the strongest argument for why the
context supplier should be a *continuous sensor* rather than a one-time export. An agent that opens
a PR and walks away has no idea whether it helped. This one finds out.

## Why not owning hops 5–7 is deliberate

- HUD never competes with Anthropic, Cursor or GitHub at code generation — a race it would lose.
- HUD never takes custody of customer source code, which materially shortens security review.
- HUD's costs are telemetry costs, not inference costs.
- Every improvement in agent quality makes HUD more valuable at zero engineering cost to HUD.

## And why it is still a risk

The PR is where the buyer sees value and where the billing event naturally lands. Sentry's Seer
and Datadog's Bits Code both own hops 5–7 themselves. If engineering leaders come to evaluate this
category by "what opened the PR," HUD is structurally one hop upstream — and upstream of the
visible value is where products get bundled, undercut, or acquired.

HUD's defense is hop 2: the local variable values at the moment of failure, plus the behavior of
every call that *did not* fail. That data genuinely cannot be reconstructed from logs, traces or
source. As long as that stays true, being upstream is a position rather than a problem.
