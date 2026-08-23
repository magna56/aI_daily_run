# The Chat Is Re-Read Every Turn; the Harness Is the Program Around the Model

**Category**: Coding Agents & Productivity
**Tags**: context-engineering, caching, coding-agents
**Date**: 2026-08-23
**Level**: Start here
**For**: Using tools
**Hook**: The model forgets everything between turns. The program around it rebuilds the chat and decides what gets cached or cut.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5
Imagine a friend who forgets the whole conversation the moment they finish a sentence. Every time you want to add one new thought, you must read the entire chat back to them from the start. A helper sits beside you with the notebook. The helper decides what to re-read, when to use a shortcut if the beginning has not changed, and when the notebook is so fat that they write a short summary and throw the old pages away. Your friend only ever sees whatever the helper puts in front of them. The friend is the model. The helper is the harness.

## The Problem
Chat products trained everyone to believe the model "remembers." It does not. Each API call is a fresh request. The transcript, the tool list, the system prompt, the cache, the summary of last Tuesday — those are assembled by a program you did not write (Claude Code, Cursor, Codex) or one you did (your agent). When a long session gets stupid, or expensive, or suddenly forgets a decision you approved, people blame the model. Often the harness rebuilt the notebook badly.

## For a Software Engineer
This is a **stateless server plus a stateful client**. The model is the server: it receives a request body and returns tokens. It keeps no session. The harness is the client *and* the middleware: it stores messages, renders a *prefix* (tools, then system prompt, then history), optionally asks the provider to cache that prefix, runs tools, and when the window is full, *compacts* — rewrites old history into a summary and starts a new prefix.

Prompt caching is an **exact prefix match**, like an HTTP `ETag` over a byte range. If the first N tokens are byte-identical to a previous call, the provider can skip the expensive re-read and charge ~0.1×. Change one character near the front — a `datetime.now()` in the system prompt, a tool list that shuffled — and everything after that position misses. Rebuilding the cache costs ~1.25×, so a thrashing cache is worse than no cache. The daily session on 2026-08-22 prices that: cache thrashing lost to "never cache" ($31.67 vs $25.34 in the simulation).

Monday-morning action: treat the agent as two processes. Ask "what did the model generate?" and separately "what did the harness put in the prefix?" If you are debugging a long Cursor or Claude Code session, you are almost always debugging the second.

## What This Means for You
**When this matters**: a coding-agent session gets slower and sloppier as it grows, a cache read counter stays at zero, or you are trying to decide whether a problem is "the model" or "the tool."

**How it affects you**: you pay for every old message on every new turn. A volatile prefix burns the cache. Compaction buys room and can drop state (an approval, a file you were editing). Blaming the model for a harness bug wastes a day.

**What to do about it**: keep the front of the prompt stable (no timestamps, no per-request UUIDs in the system prompt). Put standing instructions in a file the harness loads the same way every turn. When a session goes long, start a new one or push exploration into a sub-agent instead of waiting for auto-compact to invent a summary. For the full cost model, read 2026-08-22 (*Context Is a Budget You Re-Pay Every Turn*).

## What It Is
A **model** is a function: tokens in, tokens out. It does not have your files, your git status, or yesterday's chat unless those bytes are in *this* request.

A **harness** is the program that makes that function look like a chat with tools. On every turn it:

1. Builds the prefix in a fixed order — tool schemas, system prompt, messages.
2. Sends the request, maybe marking a cache breakpoint.
3. Reads the model's output — plain text, or a structured tool call.
4. Executes tools (read a file, run a test) and appends the results.
5. Loops until the model stops calling tools or a limit hits.
6. When the transcript is too large, compacts: replace old messages with a summary and continue.

Claude Code, Cursor, Codex, and the agent you write in fifty lines are all harnesses. They differ in permissions, MCP, hooks, and how aggressively they compact — not in the fact that the model is re-reading a notebook the harness bound.

## Why It Matters
Once you split model from harness, a lot of changelog noise becomes one theme. Sub-agents exist to keep work *out* of the parent notebook. Progressive MCP discovery exists because a hundred tool schemas sit at the *front* of the prefix and are re-read every turn. Auto-compact exists because the window is finite and the loop is not. A "1M context" model does not retire this; it makes a bigger notebook you can overfill. The 2026-08-22 session's most telling detail is a flag whose job is to *shrink* a 1M window to 200K.

If you only change prompts and never change harness behavior, you are tuning the essay and ignoring the compiler.

A practical split when something goes wrong: if the model *asked* to do the right thing and the file did not change, the harness denied or failed the tool. If the model asked for the wrong thing, look at the prefix — which tools it could see, which instructions were still in the notebook, whether compaction had already replaced the decision you thought was still there. Those are different tickets. Mixing them is how a team spends a week "trying another model."

## Key Technical Details
**Background first.** The *prefix* is everything sent before the model generates, in render order: tools, then system, then messages. A *prompt cache* stores that prefix server-side when the bytes match. *Compaction* is the harness deleting or summarizing old messages to free tokens — which changes the prefix, so it is also a cache write. *Context engineering* is the job of choosing those bytes on purpose.

- **Every turn is a full re-read.** There is no hidden memory. The API is stateless. Session persistence is your (or the product's) disk, not the model.
- **Prefix order decides blast radius.** Edit a tool schema and you invalidate tools, system, and messages. Edit the system prompt and you invalidate system and messages; tools can stay cached. Append a user message and only the tail misses. This is why a clock in the system prompt is a footgun and a clock in the latest user message is not.
- **The cache is a prefix match, not a semantic one.** Same words, different JSON key order: miss. Same tools, different model: usually a miss. The diagnostic on Anthropic's API is `cache_read_input_tokens`. Zero on repeated identical-looking calls means something in the prefix is changing.
- **Compaction is a cliff.** You get a smaller window and a new prefix on the same turn. The next request pays a cache write. Summaries drop details — including "the user approved this command" — which is why compacted sessions sometimes re-ask or re-deny. It is a log rotation, not a gradual fade.
- **The harness owns tools, permissions, and retries.** The model can only *ask* to call `read_file`. The harness decides whether that runs, what the result looks like, and whether the result is kept or released. "The model deleted a file" is almost always "the harness executed a tool call."
- **You are already using a harness.** Slash commands, rules files, hooks, and MCP servers are harness features. They change the prefix or the loop. They do not change the model's weights.
- **This session's toy numbers are the shape, not the bill.** A stable 8-turn prefix billed **442** effective tokens; the same turns with a clock in the system prompt billed **2,585**; compaction sat in the middle at **1,437** because it kept rewriting once the ceiling was crossed. Real sessions are longer and the multipliers are the same. The 2026-08-22 lab scales the same harness idea to 60 turns and published Opus 5 rates.
- **New chat is a harness move.** When a session has compacted twice and the model is arguing with a summary of a summary, the cheapest fix is not a better prompt. It is a new transcript with a short handoff you wrote. That is you doing the harness's job on purpose.

## How It Connects to What You Know
Think of an HTTP API with a CDN in front. The origin (the model) is stateless. The edge (the harness) holds cookies, assembles headers, and caches GET bodies by exact key. Compaction is vacuuming the session store and replacing it with a snapshot.

The daily lab on 2026-08-22 is the budget and cache-invalidation deep dive — when a token is inserted changes its lifetime cost by ~5.7×, and a bad cache costs more than no cache. This page is the vocabulary that lab assumes: prefix, cache, compaction, model vs harness. If you have used Cursor for a week and thought the chat was the model, start here.

## Try It Yourself
`code_example.py` is a toy harness. It stores messages, builds a `tools | system | messages` prefix every turn, applies a prefix-hash cache (0.1× hit, 1.25× write), and compacts at a token ceiling. It prints who did what — harness vs model — and shows a stable prefix hitting cache, a timestamp breaking it, and a compaction rewriting the notebook. Pure Python, no API key.

## Glossary
- **Model** — the function that turns an input token sequence into output tokens. No files, no memory, no tools unless the harness provides them in this request.
- **Harness** — the program around the model: prompt assembly, tool execution, cache markers, compaction, permissions.
- **Prefix** — the bytes sent before generation, in order: tool schemas, system prompt, messages.
- **Prompt cache** — a provider feature that reuses work for an exact matching prefix. Hits are cheap; writes are slightly expensive; misses are full price.
- **Cache invalidation** — a prefix byte changed, so everything from that point on must be re-processed.
- **Compaction** — the harness summarizing or dropping old messages to free the context window. New prefix, new cache entry, possible lost state.
- **Context window** — the maximum tokens one request can hold. A ceiling, not a gift.
- **Context engineering** — choosing what occupies that window on each turn.
- **Token** — the billing and context unit; roughly three-quarters of an English word.
