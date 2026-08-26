# How the Chat Is Re-Read Every Turn

**Category**: Coding Agents & Productivity
**Tags**: context-engineering, caching, coding-agents
**Date**: 2026-08-23
**Level**: Start here
**For**: Using tools
**Hook**: The model forgets everything between turns. The program around it rebuilds the chat and decides what gets cached or cut.
**Kind**: Learn
**Time to read**: ~14 minutes

> **You'll be able to:** explain why old tokens are repaid every turn instead of paid once, read the four cache-weight tiers a session actually bills at, and find the specific things bloating a context window instead of vaguely blaming "a long conversation."

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

## How the Bill Is Actually Weighted

Cost is not proportional to raw token count. It is proportional to token *type*:

| Token type | Weight | Notes |
|---|---|---|
| Output tokens | 1.0× | Most expensive — every word the model writes |
| Cache write | 0.417× | First time a piece of static context loads |
| Input tokens | 0.333× | Conversation history, tool results — not cached |
| Cache read | 0.033× | Static context on the 2nd+ message — **30× cheaper** |

**The asymmetry that matters:** your *static* context — system prompt, project briefing, tool schemas — gets cached after the first message and costs 0.033× from then on. Your *tool results* are not cached; they cost 0.333× on every single message they persist in the transcript. A 4K-token briefing file and a 4K-token search result are the same size and roughly a **tenfold** difference in ongoing cost, purely because of where each one sits in the caching model.

This is also most of why an expensive model burns quota faster than the fact "it thinks more" explains: more compute per token, extended-thinking tokens billed at the 1.0× output rate, and generally longer responses — also at 1.0×.

## Where the Bloat Actually Hides

Ranked by typical impact, biggest first:

1. **An instruction that triggers an expensive tool automatically.** "Search the knowledge base for any question about X" fires a multi-thousand-token result that then persists for *every remaining message* — cost is `size × remaining turns`, not `size`. Three such searches early in a 30-message session can be a quarter of a million tokens for three lookups. Fix: make the trigger explicit ("search only when asked, or when context cannot answer it").
2. **Accumulated one-off permissions.** Months of individually-approved commands in a local settings file can reach hundreds of entries, all loaded on every message. Replacing them with a handful of wildcards (`Bash(git:*)` instead of forty specific git invocations) is a ten-minute fix that pays out for the rest of the session's life.
3. **Unused tool schemas.** Every registered integration loads its full schema into the system prompt whether you call it or not — including ones that are silently disconnected and loading dead weight for nothing.
4. **A briefing file nobody prunes.** Tables restating what the tool schemas already say, JSON "how to call this" examples, directory trees — all resent on every turn regardless of relevance.
5. **A volatile prefix.** Covered above, and worth repeating here because it compounds with all four of the above: a clock or a shuffling list at the front of the prompt turns every one of these into a full-price rewrite instead of a 0.033× cache read.

## Quick Reference

| Term | Plain English |
|---|---|
| Harness | The program that builds the prompt, calls tools, caches, and cuts. |
| Prefix | The leading bytes of the request; what the cache keys on. |
| Prompt cache | Reuse of an exact, unchanged prefix at a steep discount. |
| Cache write / cache read | First load (0.417×) vs a repeated hit on unchanged prefix (0.033×). |
| Compaction | Summarizing or dropping older turns so the window fits. |
| Invalidation | Any change to the prefix that forces a full, expensive re-read. |
| Static context | System prompt, briefing file, tool schemas — cacheable. |
| Tool result | Retrieved or generated content — not cached, repaid every turn it persists. |

## Do It Today

**Step 1 — see the same 8 turns billed three ways, 2 minutes.**

```bash
python3 learn/context-and-harness/code_example.py
```

It runs a toy session with a stable prefix, then the same session with a timestamp in the system prompt, then one that hits a compaction ceiling. **You know it worked** when the stable run bills **442 effective tokens**, the volatile one (a clock at the front, invalidating the cache every turn) bills **2,585**, and the compacted one lands at **1,437** — smaller notebook, but a fresh prefix means a fresh cache write. Same eight turns, nearly 6× apart, purely from what sits at the front of the prompt.

**Step 2 — hunt for a volatile prefix in your own setup.** Anything rendered fresh every call — a timestamp, a session ID, a tool list whose order isn't fixed — sits at the front and invalidates the cache for everything behind it. Sort what can be sorted; move anything genuinely dynamic to the end of the prefix instead of the start.

**Step 3 — check what's actually loaded.** List your registered integrations and remove ones you have not used this month. Check the size of your project briefing file — if it is restating what a tool schema already says, cut it; that content loads twice for no benefit.

## Gotchas

- **Old tokens are not "paid for."** They are re-paid every turn they remain in the prefix. A timestamp in the system prompt can cost you the write rate forever, not once.
- **Compaction is a rewrite, not a memory trick.** Expect a cache miss and a lossier memory of early instructions after one. Re-state invariants after a compact rather than trusting the summary kept them.
- **A bigger context window is not a free upgrade.** It is a bigger buffer. Filling it is what costs money — Claude Code itself ships a flag whose entire job is to *shrink* a 1M-token model back to 200K by default.
- **Offloading to a subagent is not free either.** Spinning one up costs its own setup tokens; it only pays off when enough parent turns remain to amortize that cost.
- **A dead, disconnected integration still loads its schema.** It costs the same as a working one and returns nothing.

## How It Connects to What You Know

Build caches and HTTP ETags: one byte change upstream invalidates everything downstream. The weighted-token table above is the same shape as a CDN's cache-hit-vs-origin-fetch cost difference, just applied to a conversation instead of a static asset.

Previous: [How Retrieval Works](#learn/retrieval). Next: [How the Agent Loop Works](#learn/the-agent-loop).

Lab: [Context is a budget you re-pay every turn](#2026-08-22).
