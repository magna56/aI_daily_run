# Why a Prompt Cache Miss Costs More Than No Cache at All

**Category**: New Models & APIs
**Tags**: caching, cost, production
**Date**: 2026-09-13
**Level**: Building
**For**: Shipping AI
**Hook**: Writing a prompt cache entry costs 1.25 times the normal rate and reading one costs a tenth. So a prefix that gets written and never reused is not a wasted optimization, it is a 25% surcharge you chose.
**Engineer's view**: You have put a cache in front of something slow, watched the hit rate sit near zero, and had no way to see which header was busting it. This is that, with one difference that changes the arithmetic: here a miss is not free, because writing the entry costs more than not caching.
**TLDR**: A prompt cache write costs more than an uncached call and a read costs almost nothing, so the hit rate decides whether caching saves money or adds a surcharge. There is now an API that tells you why a miss happened.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine paying a small fee to put a book on a shelf so you can grab it cheaply later. If
you come back and read it ten times, the fee was nothing. If you put it on the shelf and
never come back, you paid the fee for nothing — you would have been better off just reading
it once where you stood. Now imagine the shelf quietly refuses your book whenever you
change your coat, and nobody tells you which coat.

## The Problem

You have shipped this without a model involved. You put a cache in front of something slow.
The hit rate sat near zero. You knew *that* it was missing and had no way to see *why* — some
header varied, some query parameter reordered, and the cache key changed on every request.
You found it eventually by diffing two requests by hand.

Prompt caching has that shape and one extra twist that changes the arithmetic. On GPT-5.6 and
later a cache read costs 0.1 times the normal input rate. A cache write costs 1.25 times. So a miss is not a missed saving, it is a surcharge: you paid a quarter more
than an uncached call would have cost, to store a prefix nobody read.

That only pays back with reuse, and the bar is low — a single reuse already puts you ahead.
The trouble is that misses are easy to cause and, until recently, invisible. The prefix has
to match exactly, it has to reach 1,024 tokens before anything is cached at all, and the
entry expires 30 minutes after it was last touched.

**The fix is to ask the API why it missed**, rather than diffing two requests by hand.

## The Fix: Make the API Name the Thing That Changed

On 8 September 2026 prompt cache diagnostics went generally available in the Responses API.
You pass the id of a baseline response and the API compares the two.

```python
prompt_cache_options={"comparison_response_id": baseline.id}
```

The reply carries a `prompt_cache_diagnostics` object:

```json
{ "type": "cache_miss", "reason": "tools_changed",
  "comparison_reusable_tokens": 5629, "cache_missed_tokens": 5629 }
```

`reason` is the part worth having. It is one of nine values, and each names a specific thing
you changed.

```figure
{ "kind": "anatomy",
  "title": "The nine reasons a prefix stops matching",
  "lines": [
    "model_changed",
    "prompt_cache_key_changed",
    "service_tier_changed",
    "tools_changed",
    "text_format_changed",
    "reasoning_effort_changed",
    "verbosity_changed",
    "context_compacted",
    "input_changed"
  ],
  "callouts": [
    { "line": 3, "t": "Tools added, removed, reordered, or their definitions edited. Reordering alone is enough.", "s": "bad" },
    { "line": 5, "t": "Settings nobody thinks of as prompt content. Raising effort for one hard request evicts the prefix.", "s": "bad" },
    { "line": 7, "t": "Compaction replaced earlier turns — your own context management invalidating your own cache.", "s": "new" }
  ],
  "note": "Only the last reason is about the words you sent. The other eight are configuration." }
```

### Why is the prefix so easy to break?

Because cache reuse requires the **entire rendered prefix** to match, and the rendered prefix
includes settings you would not call prompt text. Changing `tools`, `text.format`,
`reasoning.effort`, `text.verbosity`, `parallel_tool_calls` or `context_management` all
invalidate it.

That last one is the sharp edge. Compaction is the feature that shortens a long conversation
for you, and it works by replacing earlier content — which is exactly what the cache keys on.
Your context management and your prompt cache are fighting over the same bytes.

### So when does caching actually pay?

Sooner than the write premium suggests, but not automatically.

```figure
{ "kind": "bars",
  "title": "Cost of one prefix, relative to never caching",
  "bars": [
    { "label": "written, never reused", "v": 125, "d": "1.25x", "s": "bad" },
    { "label": "written, reused once", "v": 68, "d": "0.68x", "s": "ok" },
    { "label": "written, reused 10 times", "v": 21, "d": "0.21x", "s": "ok" }
  ],
  "note": "Write 1.25x, read 0.1x, averaged over the calls that share the prefix." }
```

One reuse is enough to come out ahead. The failure mode is not thin margins, it is prefixes
that are written and never read — a 30-minute window that nobody returns inside, or a
setting that quietly changes between the write and the read.

## What This Means for You

**When this matters.** You send a long, repeated prefix — a system prompt, a tool list, a
document — and you are paying for it. Below 1,024 visible input tokens nothing is cached at
all, so short prompts are outside this entirely.

**How it affects you.** It turns a guess into a measurement. Before this the honest answer
to "is our caching working" was an inferred hit rate and a hypothesis; now the API names the
field that changed. That is the difference between a hypothesis and a bug report.

It also reframes what to protect. The instinct is to keep the prompt text stable, and the
list above says text is one reason out of nine. **Eight of the nine are configuration** —
tool order, reasoning effort, output format. Those are the things a team changes without
thinking of them as prompt edits, which is exactly why they go unnoticed.

**What to do about it.**

1. Capture one response id as a baseline and re-run a representative request against it. One
   call tells you whether you have a problem.
2. If it misses, read the `reason` before changing anything. Eight of nine point at a config
   field, not at your prompt.
3. Freeze tool order. Serializing a dict or a set will reorder it eventually, and
   `tools_changed` does not distinguish reordering from editing.
4. Then check the 30-minute window against your real traffic pattern. A prefix nobody
   revisits inside half an hour is a write you are paying 1.25 times for.

## Implementing It

**The change.** Three places, and the third is what stops it regressing.

*The probe.* One request, against a baseline you already have:

```python
baseline = client.responses.create(model="gpt-5.6", input=PROMPT, tools=TOOLS)

probe = client.responses.create(
    model="gpt-5.6", input=PROMPT, tools=TOOLS,
    prompt_cache_options={"comparison_response_id": baseline.id},
)
d = probe.prompt_cache_diagnostics
print(d.type, getattr(d, "reason", ""), d.comparison_reusable_tokens, d.cache_missed_tokens)
```

Run it against a request you believe *should* hit. A miss here is the whole finding, and
`cache_missed_tokens` prices it: those tokens were billed at 1.25 times instead of 0.1.

Note what the probe is not. It compares one response against one baseline, so it answers
"did this reuse that" rather than "what is my hit rate". Run it on the handful of request
shapes you actually care about; it is a debugger, not a dashboard.

*The stable prefix.* Most misses are ordering, not content. Pin it:

```python
TOOLS = sorted(TOOL_DEFS, key=lambda t: t["name"])   # never a dict/set iteration order

def call(user_turn, effort="medium"):
    # Everything before the user's turn is the cacheable prefix, so nothing in
    # it may vary per request. Effort is deliberately a parameter, not a knob
    # tuned per call: raising it for one hard request evicts the prefix for all
    # the easy ones that follow.
    return client.responses.create(
        model=MODEL, tools=TOOLS, reasoning={"effort": effort},
        text={"format": OUTPUT_FORMAT, "verbosity": "medium"},
        input=SYSTEM_BLOCKS + [{"role": "user", "content": user_turn}],
    )
```

*The regression check.* The prefix breaks when someone edits a tool, so assert on it in CI:

```python
import hashlib, json

def prefix_fingerprint():
    """Everything that is part of the rendered prefix, in a stable order."""
    return hashlib.sha256(json.dumps({
        "model": MODEL, "tools": TOOLS, "format": OUTPUT_FORMAT,
        "system": SYSTEM_BLOCKS, "effort": "medium", "verbosity": "medium",
    }, sort_keys=True).encode()).hexdigest()[:12]

def test_prefix_is_stable():
    assert prefix_fingerprint() == PINNED, (
        "the cacheable prefix changed — update PINNED deliberately, and expect "
        "every warm cache entry to be rewritten at 1.25x once this ships")
```

That test fails on a tool rename the same way it fails on a deliberate change, which is the
point: it makes the cost visible at review time rather than on the bill. Print the reason for
the change in the failure message and a reviewer can decide whether it was worth it, which is
a conversation nobody has today because nothing surfaces it.

**How you know it worked.** The diagnostic returns something other than `cache_miss` for a
request you expected to hit. That is the direct signal and it takes one call.

The slower one is the bill. Cached input tokens should rise as a share of total input tokens,
and the number to watch is not the hit rate on its own — it is hits against writes. Many
writes and few reads is the shape that costs you money while looking like caching.

**When not to.** Do not add the CI check before you have run the probe once. If your prefix
is already stable the fingerprint test is pure friction, and you will find that out in a
single call.

## When Prompt Caching Is the Wrong Thing to Optimize

Caching rewards repetition, and plenty of workloads do not repeat.

Short prompts are the clearest case. Below 1,024 visible input tokens nothing is cached at
all, so a service sending brief, varied requests has nothing to tune here and should look at
model choice or output length instead.

Genuinely unique prefixes are the other. If every request carries a different document, the
prefix is new every time and every call pays the 1.25 write premium for an entry nobody will
read. That is worse than not caching, and it is the one case where the right move is to keep
the varying content *out* of the cacheable region rather than to chase a higher hit rate.

Traffic shape matters too, though less sharply than it looks. Widening the gap between calls
erodes the saving rather than reversing it, because real traffic arrives in bursts and plenty
of calls still land inside the 30-minute window. Uniqueness is what flips the sign; latency
only flattens it.

Three questions before spending time here:

- Is my prefix over 1,024 tokens, and does the same one recur?
- Do repeat requests land inside 30 minutes of each other?
- When I probe a request that should hit, what does `reason` actually say?

## Glossary

- **Prompt cache** — reuse of the computed state for a prompt prefix the model has already
  processed, so a repeated prefix is billed at a fraction of the normal input rate.
- **Cache write** — storing a new prefix. On GPT-5.6 and later it costs 1.25 times the
  uncached input rate, which is why a miss is a surcharge and not merely a lost saving.
- **Cache read** — reusing a stored prefix, at 0.1 times the uncached rate.
- **Rendered prefix** — everything the model sees before the varying part, including tools,
  output format and reasoning settings. Reuse requires all of it to match exactly.
- **Compaction** — automatic shortening of a long conversation. It rewrites earlier content,
  which invalidates the prefix built on it.
- **Baseline response** — the earlier response you expected this one to reuse. Passing its
  id is what turns diagnostics on.
