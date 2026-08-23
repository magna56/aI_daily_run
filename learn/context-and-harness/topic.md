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

Your friend still has no memory. Every time you want to say one new sentence, you first read the entire conversation back from the start. A sentence from an hour ago gets read again all day. The shortcut: if you re-read the beginning *word for word, unchanged*, they can skim it much faster. Change one word near the start and they have to read the whole thing slowly again. The friend is the model. The person who decides what to re-read, what to skim, and what to throw away is not the friend. That is the harness.

## The Problem

People think the chat is a document the model is "in." It is not. Each API call is a new run. The product rebuilds a prefix — tools, system, messages — and the model scores the next token over that string. If you put a clock or a shuffled tool list at the front, you break the cheap skim (the prompt cache) and pay full price for text you already sent. If you never cut, the window fills and the product summarizes or drops the middle. Both feel like "the model forgot." One is cache invalidation. One is compaction. Neither is a soul.

## For a Software Engineer

This is an accidentally quadratic log plus a cache keyed on a prefix. Appending a message is O(1). Re-sending the whole transcript every turn is O(n²) in tokens×turns. Prompt caching is an exact prefix match — like an HTTP `ETag` over a byte range. Reads of a cached prefix cost ~0.1×. A rewrite of the cache costs ~1.25×. A thrashing cache loses to no cache.

The number worth feeling: in this lesson's toy, a stable 8-turn prefix billed **442** effective tokens; the same turns with a clock in the system prompt billed **2,585**; compaction sat in the middle at **1,437** because it kept rewriting once the ceiling was crossed. The 2026-08-22 lab scales the same idea to 60 turns and published prices: cache thrashing lost to "never cache" ($31.67 vs $25.34).

Monday morning: hunt for anything volatile at the front — `datetime.now()`, a session UUID, a tool list that shuffles. Render order is usually tools → system → messages. Check `cache_read` tokens. If they stay zero on a repeated call, you have a silent invalidator. Do not treat a 1M window as free disk. Claude Code ships a flag whose job is to *shrink* 1M models to 200K.

## What This Means for You

**When this matters**: a long Cursor or Claude Code session that gets expensive, forgetful, or both.

**How it affects you**: old tokens are not "paid for." They are re-paid every turn they stay in the prefix. A timestamp in the system prompt can make you pay 1.25× forever.

**What to do about it**: keep the front of the prompt stable. Put standing rules in a file the harness loads the same way every turn. When a session goes long, start a new one or push exploration into a sub-agent instead of waiting for auto-compact to invent a summary.

## What It Is

The **model** picks the next token over the prefix it was given. The **harness** is everything else: how tools are listed, how files are read, when a sub-agent starts, when the transcript is compacted, whether the prefix is cacheable.

**Prefix** — the bytes from the start of the request through the last message. Cache keys this.

**Compaction** — when the window is full, the harness summarizes or drops, then continues. You get a new prefix. The cache often misses. The summary is lossy. That is why "it forgot the constraint I said at the start" happens after a long session.

Sub-agents exist to keep work *out* of the parent notebook. Progressive tool discovery exists because a hundred schemas sit at the *front* and are re-read every turn. A bigger window does not retire this. It makes a bigger notebook you can overfill.

## Why It Matters

Changelog noise becomes one theme: get work out of the main conversation, keep the prefix stable, treat context as a budget. The 2026-08-22 session is the case study — when a token is inserted changes its lifetime cost by ~5.7×. This page is the vocabulary that lab assumes.

## Key Technical Details

**Background first.** *Harness* = program around the model. *Prefix cache* = exact match from byte 0. *Compaction* = rewrite the notebook so it fits.

- **Stability is a feature.** Sort tool names. No clocks in the system prompt. No per-request UUID at the front.
- **Compaction is a rewrite.** Expect a cache miss and a worse memory of early rules. Re-state invariants after a compact, or start fresh.
- **Sub-agent setup is not free.** The 2026-08-22 sim: offload *loses* on a short session and only pays off when many parent turns remain.
- **1M is not a personality upgrade.** It is a larger buffer. Filling it is what costs money.

## How It Connects to What You Know

Build caches and HTTP ETags: one byte change upstream invalidates everything downstream. Same here.

Previous: [Retrieval](#learn/retrieval). Next: [The agent loop](#learn/the-agent-loop).

Lab: [Context is a budget you re-pay every turn](#2026-08-22).

## Try It Yourself

`code_example.py` bills a tiny session three ways — stable prefix, clock in the system prompt, and a compact — so you can see the 442 / 2,585 / 1,437 shape without an API key.

## Glossary

- **Harness** — the program that builds the prompt, calls tools, caches, and cuts.
- **Prefix** — the leading bytes of the request; the cache key.
- **Prompt cache** — reuse of an exact prefix at a discount.
- **Compaction** — summarizing or dropping so the window fits.
- **Invalidation** — any change in the prefix that forces a full re-read.
