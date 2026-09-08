# How Spotify Stops a Large File From Entering Claude's Context

**Category**: Coding Agents & Productivity
**Tags**: coding-agents, context-engineering, cost
**Date**: 2026-09-08
**Level**: Building
**For**: Using tools
**Hook**: A hook can refuse a file read before it happens, and hand the model a sentence explaining what to do instead. The file never enters the context, so you are not trimming the bill afterwards — you are preventing it.
**Engineer's view**: You have written middleware that rejects an oversized upload with a 413 before the parser allocates anything. The saving was not the error code. It was that the expensive work never started. A PreToolUse hook is that middleware, and the resource it protects is the context window.
**TLDR**: A hook runs before a tool call and can deny it, telling the model why in a sentence the model then reads. That turns your context window into something you enforce rather than something you hope about.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine an assistant who reads every document you hand over, and charges by the page. You
could let them read a 900-page manual and then ask your question. Or you could stop them at
the door and say: do not read that one, ask the summarizer down the hall instead. The
second way costs almost nothing, because the pages were never read. The important part is
that you also told them where to go, so they do not simply stand there.

## The Problem

You have written this before, and no model was involved. Your service accepted uploads.
Someone posted a 50MB file, your parser allocated all of it, and the box fell over. You
fixed it with middleware that checks `Content-Length` and returns a 413 before the body is
ever read. The fix was not the status code. It was that the expensive work never started.

An agent has the same shape and no such middleware by default. When Claude Code calls
`Read` on a 4,000-line file, the whole file lands in the context window. It is charged on
that turn, and then charged again on every turn afterwards, because the transcript is
re-sent each time. A single careless read is not one bill. It is a bill with a subscription.

The usual advice is to manage this after the fact — compact the conversation, summarize,
start a new session. All of that is cleanup. It runs after the tokens have been spent, and
the file is in the transcript by then.

**The fix is to refuse the read before it happens**, and to use the refusal to tell the
model where to go instead.

## The Fix: Deny the Tool Call, and Say Why

Claude Code fires a `PreToolUse` hook before it runs any tool. The hook is a program. It
gets the pending call as JSON on stdin — `tool_name`, `tool_input`, `cwd`, `tool_use_id` —
and it decides whether the call happens at all.

```figure
{ "kind": "system",
  "title": "The whole argument: the same Read call, with and without a hook",
  "lanes": [
    { "t": "the model asks", "nodes": [
        { "id": "read", "t": "Read a 4,000-line file" } ] },
    { "t": "what happens", "nodes": [
        { "id": "none", "t": "no hook: the tool runs", "s": "bad" },
        { "id": "hook", "t": "PreToolUse denies it", "s": "ok" } ] },
    { "t": "the context holds", "nodes": [
        { "id": "all", "t": "the whole file, every turn", "s": "bad" },
        { "id": "line", "t": "one sentence", "s": "ok" } ] }
  ],
  "edges": [
    { "from": "read", "to": "none" },
    { "from": "read", "to": "hook", "t": "before it runs", "s": "ok" },
    { "from": "none", "to": "all",  "t": "re-sent each turn", "s": "bad" },
    { "from": "hook", "to": "line", "t": "the deny reason", "s": "ok" } ],
  "note": "Nothing is trimmed afterwards. The file is never read, so it is never in the transcript." }
```

### How does a hook actually refuse something?

Two ways, and the difference matters. Exiting with code 2 blocks the call unconditionally.
Or exit 0 and print a decision on stdout:

```figure
{ "kind": "anatomy",
  "title": "What the hook prints to refuse a call",
  "lines": [
    "{",
    "  \"hookSpecificOutput\": {",
    "    \"hookEventName\": \"PreToolUse\",",
    "    \"permissionDecision\": \"deny\",",
    "    \"permissionDecisionReason\":",
    "      \"File is 4,012 lines. Use /bulk-reader\"",
    "  }",
    "}"
  ],
  "callouts": [
    { "line": 3, "t": "deny stops the call. allow lets it through. Omit the field and normal permissions decide.", "s": "new" },
    { "line": 4, "t": "Shown to the model. It is the only part of the file that costs tokens.", "s": "ok" },
    { "line": 5, "t": "Say where to go, not just no. A bare refusal leaves the model stuck or retrying.", "s": "ok" }
  ],
  "note": "Exit 2 also blocks, and beats this JSON: a deny is a deny even if the JSON says allow." }
```

The second field is the one people miss. `permissionDecisionReason` is not a log line. It
is shown to the model, which then continues the conversation and can act on it. So the hook
is not only a gate. It is a one-sentence channel into the context, and one sentence is
roughly four orders of magnitude cheaper than the file.

### Which reads should get through?

Not all of them, or the agent stops working. The rule Spotify's plugin uses is size plus
intent.

```figure
{ "kind": "route",
  "title": "What the hook lets past",
  "source": "a pending Read or Bash call",
  "parts": [
    { "t": "a small file", "to": 0, "via": "under 350 lines", "s": "ok" },
    { "t": "a targeted read", "to": 0, "via": "offset + limit", "s": "ok" },
    { "t": "the whole big file", "to": 1, "via": "no bounds", "s": "bad" }
  ],
  "dests": [
    { "t": "runs normally", "s": "ok" },
    { "t": "denied, with somewhere to go", "s": "new" }
  ],
  "note": "A read with offset and limit is already bounded, so it is not the problem this solves." }
```

A read of 40 lines is fine. A read with `offset` and `limit` is already bounded, so it
passes too. What gets denied is the unbounded read of something large, plus the same thing
done through Bash — `cat`, `head`, `tail`, `less`, `more` — because otherwise the model
routes around the hook the moment it is blocked.

## What This Means for You

**Where this comes from.** Spotify Engineering published a post on 3 September 2026,
[Portal by Spotify cut my Claude Code token usage by 90%](https://engineering.atspotify.com/2026/9/portal-by-spotify-cut-my-claude-code-token-usage-by-90),
by Dimitri Mazmanov. Their plugin, `shunt`, is public and its README reports 82 to 94%
savings on large reads. Read that number carefully: it was measured on one Java monorepo
across four scenarios, with no published data, and the blog and the README do not quite
agree with each other. Treat it as a direction, not a figure to forecast with.

The other half of their design does not transfer. Denied reads are routed to Portal, which
is Spotify's Backstage platform, and you do not have it. **The hook is the part that is
yours** — it is a documented Claude Code feature, and it works pointed at anything.

**How it affects you.** It moves context from something you clean up to something you
enforce. That is a different job with a different owner: the same person who set your
service's body-size limit should be setting this, and for the same reason.

**What to do about it.**

1. Grep your last week of transcripts for your largest single tool result. Most people have
   never looked, and the number usually settles the argument.
2. Write the hook with a high threshold and have it only warn. Watch what it would have
   blocked for a day before it blocks anything.
3. Then turn on the deny, and make the reason line name a real alternative.
4. Point that alternative wherever you like — a subagent, a script, a cheap model. The hook
   does not care, which is why it outlives whatever you point it at.

## Implementing It

**The change.** Two files, and the second is what stops the model routing around the first.

*The hook script.* It reads the pending call on stdin and prints a decision:

```python
#!/usr/bin/env python3
import json, sys, os

MIN_LINES = int(os.environ.get("HOOK_MIN_LINES", "350"))
ev = json.load(sys.stdin)
ti = ev.get("tool_input", {})
path = ti.get("file_path", "")

# A bounded read is already the good behavior. Never punish it.
if ti.get("offset") is not None or ti.get("limit") is not None:
    sys.exit(0)

try:
    n = sum(1 for _ in open(path, "rb"))
except OSError:
    sys.exit(0)                      # not our business; let normal flow handle it

if n > MIN_LINES:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason":
            f"{path} is {n} lines. Summarize it with /bulk-reader, "
            f"or re-read with offset and limit if you need one region.",
    }}))
sys.exit(0)
```

Exit 0 throughout, and note the script prints nothing at all when the file is small — an
absent `permissionDecision` falls through to the normal permission flow, which is what you
want for the reads that were never the problem. Exiting 2 would also block, but then the
reason has to travel on stderr and you lose the structured field.

*The registration.* In `.claude/settings.json`, with a matcher so the script only runs for
the tools you care about:

```json
{ "hooks": { "PreToolUse": [
  { "matcher": "Read",
    "hooks": [ { "type": "command",
                 "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/big-read.py",
                 "timeout": 10 } ] },
  { "matcher": "Bash",
    "if": "Bash(cat *)",
    "hooks": [ { "type": "command",
                 "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/big-read.py",
                 "timeout": 10 } ] } ] } }
```

The second entry is not optional. A model told it cannot `Read` a file will try `cat` on it
within one turn, and that path bypasses a `Read`-only matcher entirely. Cover `head`,
`tail`, `less` and `more` the same way, and let piped commands through — `cat f | grep x`
is already a targeted read.

**How you know it worked.** Two signals, and you need both.

The immediate one is that the hook fires. Run `claude --debug`, open a large file, and
confirm you see the deny and that the reason text appears in the transcript. If the model
never mentions it, your matcher is wrong.

The slower one is the number that matters: your largest single tool result over a week
should drop to roughly the threshold. Watch for the failure mode too — if the model starts
saying it cannot complete tasks, your reason line is not naming a real alternative, and a
hook that only says no makes the agent worse.

**When not to.** Do not ship it denying on day one. Run it printing to stderr for a day
first, because a threshold that is too low turns a working agent into one that argues with
its own tooling.

## When Blocking a Read Is the Wrong Tool

This is a budget control, and budget controls are wrong wherever the spend was justified.

If the agent genuinely needs the whole file, blocking the read does not save you anything.
It moves the reading to a summarizer, and a summary of a file you needed in full is a lossy
copy that costs a round trip. Refactoring across a large module is the clearest case: there
is no summary of a file you are about to edit line by line.

Small repositories do not need it either. The saving scales with the size of what you would
have read, so a codebase of 200-line files has nothing here. Check your largest tool result
before you build anything.

And a hook is a blunt instrument by design. It sees a path and a size, not a purpose. It
cannot tell a file the model must quote exactly from one it only needs the shape of, which
is why the threshold is a guess and why the escape hatch — offset and limit — has to stay
open.

Three questions before you add one:

- What is my largest single tool result today, and is it actually a problem?
- Does the reason line name something the model can really do instead?
- Have I covered Bash as well as Read, or have I just moved the read somewhere I cannot see?

## Glossary

- **Context window** — everything the model can see on a turn, including the whole
  transcript. A file read into it is re-sent on every later turn, not just the one.
- **PreToolUse** — the hook event that fires after the model asks for a tool and before the
  tool runs. It is the only point where a call can be stopped without its output existing.
- **Hook** — a program Claude Code runs at a defined event. It gets JSON on stdin and its
  stdout, or its exit code, decides what happens next.
- **permissionDecision** — the field that decides: `deny` stops the call, `allow` lets it
  through, and omitting it falls back to normal permissions.
- **permissionDecisionReason** — the sentence shown to the model when a call is denied. It
  is how the hook says where to go instead of only saying no.
- **Matcher** — the tool-name filter on a hook registration. A matcher of `Read` never sees
  a `cat`, which is why a read blocker needs a Bash entry too.
