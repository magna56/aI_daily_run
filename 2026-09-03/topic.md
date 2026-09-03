# How a Coding Agent Decides to Re-Read Your Whole Conversation

**Category**: Coding Agents & Productivity
**Tags**: caching, cost, context-engineering
**Date**: 2026-09-03
**Level**: Start here
**For**: Using tools
**Hook**: A few ordinary things you do mid-session make your coding agent pay full price to read the entire conversation again, and they are not the things you would guess.
**Time to read**: ~10 minutes
**Engineer's view**: This is a Docker layer cache. Your agent resends the whole conversation every turn, and the server replays it only while the front of that request stays byte-identical. Change one thing near the front and you pay full price to process all of it again, exactly like a bad COPY line.
**TLDR**: Your coding agent reuses the conversation it already sent, which is why most turns are cheap. A short list of ordinary actions throws that away, and the next turn re-reads everything at twenty times the price.

## Explain Like I'm 5

Imagine reading a long story out loud to a friend who forgets everything overnight. Every evening
you start again at page one.

To save your voice, your friend records the opening chapters and plays them back instead. That only
works if you read those pages exactly the same way each time. Change one word near the front and
the recording no longer matches, so you read the whole thing aloud again.

Your coding agent works like this. It sends the entire conversation to the model every single turn,
and the far end replays the part that did not change.

## The Problem

You have shipped this bug before, in a Dockerfile. The image took four minutes to build every time,
even when you had only fixed a typo in the README. You stared at it for a while and then saw it.
`COPY . .` sat above `RUN npm install`. Docker reuses a cached layer only while every layer above it
is unchanged, so one byte in any file broke the match and the install ran again from scratch. You
moved the package manifest up, and the build dropped to twenty seconds.

Your coding agent has that same cache. You are still writing the Dockerfile wrong, and this time you
cannot see the layers.

Every turn, the agent resends the whole conversation. The system prompt, your project files, every
message and tool result so far, all of it. The model remembers nothing between calls. So the server
matches the front of that request against what it processed last time, and replays it instead of
reading it again. The match is exact, and it starts at the very beginning.

Here is what the two paths cost. Take a session sitting at 300,000 tokens on Opus 5. Replaying that
prefix costs about fifteen cents. Rebuilding it costs about three dollars. Same conversation, same
answer, twenty times the money.

The only thing that decides which one you get is whether you touched the front.

**The fix is to learn the short list of actions that rewrite the front of the request, and stop
doing them in the middle of a task.** There are nine of them, they are documented, and most are
avoidable once you know they cost something.

## The Fix: Keep the Front of the Request Byte-Identical

### What counts as "the front"?

The agent orders each request so the stablest content goes first:

| Layer | What is in it | Rewritten when |
| --- | --- | --- |
| System prompt | Instructions, tool definitions, output style | Tool definitions change, or you upgrade |
| Project context | CLAUDE.md, auto memory, unscoped rules | Session start, `/clear`, or `/compact` |
| Conversation | Your messages, Claude's replies, tool results | Every turn |

A change in the conversation layer leaves the two above it cached. A change in the system prompt
invalidates everything below it.

Two more things belong to the cache key without appearing in the prompt. **The model** and the
**effort level** each have their own cache, so changing either re-reads identical content.

### So what actually breaks it?

Nine actions, in four groups. The first is the expensive one, because you choose it.

- **You picked it.** Switching models with `/model`. Changing effort with `/effort`. Turning on fast
  mode, which adds a header to the key.
- **The tool list moved.** Connecting or disconnecting a server whose tools load into the front, or
  toggling a plugin that provides one. A bare deny rule like `Bash` does it too, by dropping the
  tool from context. Deferred tools and a scoped `Bash(rm *)` are both safe.
- **The history got rewritten.** Compaction, and dropping old images once a request hits the image
  limit.
- **The binary changed.** Upgrading, which is why the first turn after a restart is slow.

### Why is /rewind free when /compact is not?

Both shorten the conversation, and they land on opposite sides of the rule. `/compact` replaces your
history with a summary, so the next request shares no front with the old one. `/rewind` truncates
back to an earlier turn, whose history is exactly what the cache was built from. Compacting builds a
new entry. Rewinding lands on one that already exists and is still warm.

One more surprise falls out of the same rule. Editing CLAUDE.md mid-session does not break the
cache, because it does not take effect either. Project files load once at session start and hold
until the next `/clear`.

## What This Means for You

**When this matters.** Cost here scales with how much context is sitting behind the change. If you
clear between every small task, none of this reaches your bill. If you run four-hour sessions, one
careless `/model` is the most expensive thing you will do all day.

**How it affects you.** The habit that costs most is deciding your model or effort level after you
are deep into the work. It feels free. In a forty-turn session it costs about a dollar fifty, and it
gets worse the longer you leave it.

**What to do about it.**

1. Pick your model and effort at the top of a session, before you type the first prompt. No settings
   file, no flags, five seconds. That is most of the win for most people.
2. Run `/usage` and read the `Prompt cache (main)` line. If your hit rate is low or the miss count
   keeps climbing, the settings in `Implementing It` are where you fix it.
3. Move `/compact` to a natural break between tasks instead of letting it fire mid-task. When you
   want to abandon a path entirely, `/rewind` instead — it truncates back onto a warm entry.
4. If you sign in with an API key or through a cloud provider, your cache expires after five minutes
   of idle time rather than an hour. Set the TTL yourself. That is the next section.

## Implementing It

**The change.** This touches four surfaces, and only the first one needs no configuration at all.

*Your own session.* Order it. Model and effort first, work second, `/compact` at task boundaries.
Nothing to install, and it is the change with the best return.

*Your settings file.* Two controls, one per bucket. Each accepts `5m` or `1h`, and any other value
is ignored silently:

```json
{
  "promptCacheTtl": "1h",
  "subagentPromptCacheTtl": "1h"
}
```

`promptCacheTtl` covers the main conversation: your interactive turns, `-p` runs, and Agent SDK
turns. `subagentPromptCacheTtl` covers everything else — subagents, workflows, teammates, forks,
compaction, session titles. On a Claude subscription inside your plan's usage the main conversation
already gets an hour, so the first line changes nothing and the second one does the work. On an API
key or a cloud provider both buckets default to five minutes and both lines matter. Requires
v2.1.242 or later.

*One subagent.* Override a single agent without touching global settings:

```yaml
---
name: test-runner
experimental:
  cacheTtl: 1h
---
```

Requires v2.1.248 or later, and it is ignored while a subscription is drawing on usage credits.

*Your fleet.* Ship it through the `env` block in managed settings:

```json
{
  "env": {
    "CLAUDE_CODE_PROMPT_CACHE_TTL": "1h",
    "CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL": "1h"
  }
}
```

First match wins: `FORCE_PROMPT_CACHING_5M=1`, then the bucket's environment variable, then the
bucket's setting, then a subagent's frontmatter, then `ENABLE_PROMPT_CACHING_1H=1`, then the
default. So a developer's own settings file cannot quietly undercut the fleet value, while
`FORCE_PROMPT_CACHING_5M=1` in their shell still wins — which is what you want when they are
debugging.

**How you know it worked.** Run `/usage` and read one line (v2.1.251 or later):

```text
Prompt cache (main):   14 requests · 91% of input tokens from cache ·
  2 misses (last 6m 10s ago, 310.2k tokens re-cached) · warm (1h TTL, last activity 40s ago)
```

The TTL named in the `warm` clause is the one your setting actually produced. If it still says `5m`
after you wrote `1h`, something higher in that precedence list won. The miss count is trustworthy: a
request counts as a miss only when it re-processed more than 5% and at least 2,000 tokens it could
have read instead.

For a scriptable check, ask for the raw numbers:

```bash
claude -p "hello" --output-format json | jq '.usage.cache_creation'
```

One-hour writes land in `ephemeral_1h_input_tokens` and five-minute writes in
`ephemeral_5m_input_tokens`. A zero in the field you expected means the setting is not in effect.
Across a healthy session, `cache_read_input_tokens` grows turn over turn while
`cache_creation_input_tokens` stays small. Creation near the full conversation size on every turn
means something is rewriting your front.

## When Pinning the Cache Is the Wrong Tool

The hour is not free. A cache read costs about a tenth of the normal input rate. A five-minute
cache write costs 1.25 times that rate, and a one-hour one costs 2 times. If your turns start less
than five minutes apart, every request already refreshes the short entry, and the hour buys you
nothing but the doubled write price. Break-even on the short TTL is two requests; on the hour it is
three.

Watch the clock carefully, because the lifetime runs from the *start* of the request that writes or
reads the entry. A four-minute generation leaves roughly one minute for the next request to begin.

A warm cache is also not the same as a cheap one. That 300,000-token context you are keeping alive
still costs about fifteen cents to replay on every single turn. If half of it is a debugging detour
you finished an hour ago, `/clear` beats any TTL setting.

And the cache is scoped to one machine and one directory, because the working directory is baked
into the system prompt. Two worktrees of the same repository build different fronts and cannot share
an entry. No setting fixes that.

Three questions before you change anything:

1. How far apart do my turns actually start? Under five minutes, the short TTL is strictly cheaper.
2. Am I on a subscription inside my plan's usage? Then my main conversation already has the hour.
3. Is the context I am keeping warm still context I need?

## Glossary

- **prefix** — the front of the request the server matches against what it processed last time; the match is exact
- **cache write** — processing content and storing it, billed above the normal input rate
- **cache read** — replaying stored content, billed at roughly a tenth of the normal input rate
- **TTL** — time to live: how long an idle cached prefix survives before it expires
- **compaction** — replacing conversation history with a summary, which builds a new prefix
- **effort level** — how much reasoning the model spends per turn; part of the cache key
