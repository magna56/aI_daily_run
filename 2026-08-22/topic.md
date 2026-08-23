# Context Is a Budget You Re-Pay Every Turn

**Category**: Coding Agents & Productivity
**Tags**: coding-agents, cost, caching, context-engineering
**Date**: 2026-08-22
**Level**: Start here
**For**: Using tools
**Hook**: Every old message is reread on every turn. A bad cache can cost more than no cache at all.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine you and a friend are building something together, but your friend has no
memory. Every time you want to say one new sentence, you first have to read the
*entire* conversation back to them from the beginning. So a sentence you said an
hour ago doesn't get read once — it gets read again, and again, and again, all
day. The longer you work, the more of your day is spent re-reading rather than
building. The trick everyone uses is a shortcut: if you re-read the beginning
*word for word, unchanged*, your friend can skim it ten times faster. But change
one single word near the start, and they have to read the whole thing slowly
again.

## For a Software Engineer

This is an **accidentally quadratic** problem, and you already know the shape of
it. An agent transcript is an append-only log that is fully re-read on every
turn. Appending is O(1); the session is O(n²). The cost of a token is not its
size — it is **its size times the number of turns that come after it**. A 6,000
token file dump at turn 5 of a 60-turn session is not a 6,000 token expense; it
is roughly 40,000, because it gets re-sent 55 more times.

Prompt caching is the fix, and it is a **prefix match** — exactly like an HTTP
`ETag` over a byte range, or a build cache keyed on everything upstream. Reads
of the cached prefix cost 0.1x. But any byte that changes anywhere in the prefix
invalidates everything after it, and re-writing the cache costs **1.25x**. So
this is fundamentally a **cache invalidation problem**, with the classic
property that a badly-invalidating cache is *worse than no cache at all*: 1.25x
paid every turn loses to 1.0x paid every turn. In the simulation, cache
thrashing costs **$31.67 against $25.34 for never caching** — you did the work
of adding caching and made it 25% more expensive.

Three things to actually do Monday morning. **One:** check whether anything
volatile sits at the front of your prompt — a `datetime.now()`, a session UUID,
a tool list that varies per user. Render order is `tools` → `system` →
`messages`, so a timestamp in your system prompt invalidates the entire
conversation behind it. Verify with `usage.cache_read_input_tokens`; if it is
zero across repeated calls, you have a silent invalidator. **Two:** stop
treating a 1M-token window as an upgrade. It is a bigger buffer to overfill, and
filling it is what costs money. Claude Code ships
`CLAUDE_CODE_DISABLE_1M_CONTEXT` specifically to hold 1M-native models down to
200K — a knob whose entire purpose is to make your context *smaller*. **Three:**
push reading-heavy work into subagents so its output never lands in the parent
transcript — but know the crossover, because it is not free.

The honest number from the simulation: subagent offload **loses 11% on a
20-turn session** and only breaks even somewhere between turn 30 and turn 40.
A subagent has to re-establish its own system prompt and tools, and you pay for
that immediately. What you buy is that the 6,000 tokens it read are never
re-read by the parent — a benefit proportional to how many turns remain. By 200
turns it saves 55%. This is the same reasoning as deciding whether to fork a
process: the setup cost is fixed and known, the savings are proportional to the
work avoided, and below some threshold you should just do it inline.

## What It Is

Over roughly the last three weeks, Claude Code and Cursor shipped a set of
changes that look unrelated in a changelog and are obviously one theme once you
line them up: **get work out of the main conversation.**

Claude Code 2.1.218 changed `/code-review` to run as a background subagent,
with the stated reason that "review work no longer fills your conversation."
2.1.212 added a per-session cap on subagent spawns (default 200, override with
`CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`) and a session-wide cap on WebSearch
calls. 2.1.232 turned on subagent forking by default, so a `subagent_type:
'fork'` subagent inherits the full conversation. 2.1.236 fixed unbounded memory
growth in long sessions by releasing subagent tool results "once they leave the
recent display window." 2.1.237 added a built-in "Concise" output style that
"leads with results and skips preamble." Cursor's 19 August release added
subagents on isolated VMs, a `/goal` command for long-lived objectives, and
mid-task steering.

The Model Context Protocol roadmap, published the same day as this session,
makes the identical argument one layer down at the protocol level: "connecting
to a server with a hundred tools means the model pays for that entire surface
before the user has asked a single question." Its answer is progressive
discovery — expose a small initial interface and reveal more as the
conversation narrows.

## Why It Matters

The thing that makes this newly urgent is that the context window got *bigger*.
Claude Opus 5 (`claude-opus-5`) ships with a 1M-token context window as both the
default and the maximum, at $5 per million input tokens. Intuitively that should
have retired the whole problem. It did the opposite: a window you can fill with
a million tokens is a window where an append-only log can run up a bill nobody
budgeted for, because the per-turn re-read scales with how full it is.

That is why the most telling entry in the whole changelog is 2.1.223, which
changed `CLAUDE_CODE_DISABLE_1M_CONTEXT` to hold *every* model with a native 1M
window down to 200K via auto-compaction. Someone shipped a switch whose only
function is to give you less of the headline feature. That only makes sense once
you price the re-read.

The second-order effect is that **context management stopped being a model
capability and became a harness responsibility**. Nothing about Opus 5 changes
the arithmetic above. What changes it is where the tokens go: which ones enter
the parent transcript, which ones go to a fork, which ones get released, and
whether anything is quietly invalidating your prefix. Those are all decisions
made by the tool, not the model — which is why they show up in changelogs and
config keys rather than model cards.

## Key Technical Details

**Background first.** Four primitives carry the rest of this section. The
*prefix* is everything the model reads before generating: tool schemas first,
then the system prompt, then the message history, in that fixed order. A *cache
breakpoint* marks a position in that prefix; content before it can be served
from cache on later calls. A *cache read* is billed at 0.1x the normal input
rate and a *cache write* at 1.25x, so caching is a bet that you will read more
often than you write. *Compaction* is the harness summarising old history to
free room — which necessarily rewrites the prefix.

- **A token's cost is size x remaining turns.** This is the whole model, and
  everything below is a consequence. In a 60-turn session, a 6,000-token read at
  turn 1 bills 7.15x its size; the same read at turn 60 bills 1.25x. Identical
  bytes, **5.7x the cost**, decided entirely by when it arrived.

- **Caching is a prefix match, so invalidation is positional.** Any byte change
  anywhere in the prefix invalidates everything after it. The cache is keyed on
  the exact rendered bytes up to each breakpoint — which means non-deterministic
  JSON serialisation, an unsorted dict, or a set iteration order is enough to
  miss. The diagnostic is `usage.cache_read_input_tokens`: zero across repeated
  identical-prefix calls means something upstream is changing.

- **Invalidation is tiered, not all-or-nothing.** Changing tool definitions or
  switching models invalidates tools, system, *and* messages. Changing the
  system prompt invalidates system and messages but leaves the tools cache.
  Changing message content invalidates only messages. Practical consequence:
  `tool_choice` and toggling thinking are cheap to vary per request; adding one
  tool mid-session is not.

- **There is an escape hatch for mid-session instructions.** Appending a
  `{"role": "system", ...}` entry to `messages` — supported on Claude Opus 5 and
  Opus 4.8, no beta header — adds an operator instruction *after* the cached
  history instead of editing the top-level system prompt ahead of it. Same
  effect on behaviour, none of the invalidation.

- **The cache only looks back 20 content blocks.** Each breakpoint walks
  backward at most 20 blocks to find a prior entry. An agentic turn that emits
  more than 20 tool_use/tool_result pairs pushes the previous breakpoint out of
  range, and the next request silently misses — no error, just a full-price
  turn. Place an intermediate breakpoint every ~15 blocks in long turns.

- **Parallel requests cannot share a cache they are all still writing.** An
  entry becomes readable only once the first response *begins streaming*. Fan
  out ten identical-prefix requests at once and all ten pay full price. Send
  one, await first token, then fire the rest.

- **The minimum cacheable prefix is not monotonic across models.** It is 512
  tokens on Claude Opus 5, 1024 on Opus 4.8, and 4096 on Opus 4.6 and Haiku 4.5.
  A 3,000-token prompt caches on Opus 5 and silently does not on Opus 4.6 —
  `cache_creation_input_tokens: 0`, no error.

- **Compaction is a cliff, not a slope.** It shrinks the window and spikes the
  bill on the same turn, because the rewritten prefix is a full cache write. In
  the simulation the turn immediately after compaction costs 3.1x the turn
  before it, despite the context being a quarter the size. The related 2.1.234
  fix — auto mode "repeatedly re-checking and denying sandboxed commands'
  network access after conversation had been compacted" — is the correctness
  half of the same event: compaction dropped the state that recorded the earlier
  approval.

## How It Connects to What You Know

If the words prefix, cache, and harness are still new, start at AI basics → [Context and the harness](#learn/context-and-harness). This post is the changelog case study.

The FrugalGPT cascade from the 2026-08-03 session optimised *which model* answers.
This optimises *how much conversation* each answer has to carry, and the two
compose: a cascade over a bloated transcript still re-reads the transcript at
every tier.

The closer relative is the 2026-08-18 session on vLLM's `max_num_batched_tokens`.
That argued prefill cost is paid once per request while per-iteration cost is
paid by every decoding sequence on every token — so the right batch size is
load-dependent and you should ship a policy, not a constant. This is the same
asymmetry one layer up: cache write is paid once, cache read is paid by every
remaining turn, and the right offload threshold depends on session length rather
than being a fixed rule. Both sessions end at "the optimum is a function of
load, so stop hard-coding a number."

It also sharpens the MCP picture from 2026-08-05 (Stateless MCP). Statelessness
solved horizontal scaling of the *server*; the roadmap's progressive discovery
addresses the *client's* context bill from that server's tool surface. A server
can be perfectly stateless and still cost you 9,000 tokens on every single turn
because its schemas sit at position 0 of the prefix.

## Try It Yourself

`code_example.py` prices a 60-turn agent session four ways using published Opus 5
rates and the documented cache multipliers. It reproduces the result that cache
thrashing beats no caching at all in the wrong direction ($31.67 vs $25.34), the
5.7x swing from *when* a file read lands, the session-length sweep where subagent
offload loses 11% at 20 turns and saves 55% at 200, and the compaction cliff.
Pure stdlib, no API key.

The parameters at the top are the interesting part — set `TOOLS` to your actual
MCP tool surface and `TURNS` to how long your sessions really run, and the
crossover moves.

## Glossary

- **Token** — the unit a model reads and bills in; roughly ¾ of an English word.
  Both what you send and what you get back are counted, at different rates.
- **Context window** — the maximum number of tokens the model can consider at
  once. Claude Opus 5's is 1M. It is a ceiling, not an allowance: filling it is
  what costs money.
- **Prefix** — everything sent to the model before it generates, in fixed render
  order: tool schemas, then system prompt, then message history. Position in the
  prefix determines blast radius when something changes.
- **Prompt caching** — reusing server-side work for a prefix you have sent
  before. Matches on exact bytes, so it is all-or-nothing from the first
  differing byte onward.
- **Cache read / cache write** — reading a cached prefix costs 0.1x the normal
  input rate; writing a new cache entry costs 1.25x (5-minute lifetime). Caching
  pays off from the second read; a cache that never reads is pure 25% overhead.
- **Cache breakpoint** — the marker saying "cache everything up to here." Max 4
  per request. Placing it after volatile content is the most common way to cache
  nothing while believing you cache everything.
- **Invalidation** — a cache entry becoming unusable because the bytes it was
  keyed on changed. Here it cascades forward: invalidate at position N and
  everything after N goes with it.
- **Subagent / fork** — a separate model conversation spawned to do a scoped
  piece of work and report back a summary. The parent pays for the summary, not
  for everything the subagent read. A `fork` specifically inherits the parent's
  full conversation.
- **Compaction** — automatically summarising old history to reclaim context
  room. Buys space, costs a full cache write, and can drop state the session was
  relying on.
- **MCP (Model Context Protocol)** — a standard for connecting external tools to
  a model. Relevant here because every connected server's tool schemas sit at the
  very front of the prefix and are re-read on every turn.
- **Progressive discovery** — the MCP roadmap's answer to that: expose a small
  set of tools initially and reveal more as the conversation narrows, instead of
  loading a hundred schemas before the user has typed anything.
