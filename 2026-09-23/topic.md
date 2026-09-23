# How to Cap What a Reasoning Model Spends on One Request

**Category**: New Models & APIs
**Tags**: cost, latency, caching
**Date**: 2026-09-23
**Level**: Building
**For**: Using tools
**Hook**: Every major provider replaced the thinking-token budget with an effort dial, and an effort dial shifts how much a model thinks without ever bounding it.
**Engineer's view**: This is the difference between ulimit and nice. One is enforced; the other is a hint the scheduler may ignore. You used to set a thinking budget in tokens. Now you set an effort level, and the only enforced ceiling left is the one that kills the request mid-work and bills you anyway.
**TLDR**: An effort level shifts how much a model thinks. It never bounds it, and the only enforced ceiling truncates the request mid-thought while still billing you for the thinking.
**Time to read**: ~11 minutes

## Explain Like I'm 5

You get in a taxi. You can ask the driver to take the scenic route or the quick one, and that changes what the fare will probably be.

It does not change what the fare *could* be.

The only real limit you have is saying "stop when the meter hits twenty dollars." That one is enforced. It is also the one where you sometimes get out on the wrong street, twenty dollars poorer, not having arrived anywhere.

## The Problem

You have shipped this before, and it had nothing to do with AI.

You set a timeout on an HTTP client and believed it. Months later a dependency hung and your service hung with it. The timeout was a *connect* timeout, not a total one, so a server that accepted the connection and then went quiet could hold you for as long as it liked.

The number was real. It governed something other than what you thought.

Reasoning models just did this to everyone at once.

You used to set a thinking budget in tokens. On Claude that was `budget_tokens`, and it is now deprecated on the 4.6 models and rejected outright with a 400 on 4.7 and later. The replacement is an effort setting. Gemini takes a `thinking_level` of minimal, low, medium or high. OpenAI takes a `reasoning.effort` from none through max.

Every one of those is a level, not a number. A level moves the distribution of how much the model thinks. It does not put a ceiling on it, and the providers do not claim it does.

So what is left that is actually enforced? Only `max_output_tokens`. And both Google and OpenAI document what happens when you hit it while the model is still thinking: the response comes back with status `incomplete`, there is no visible output, and you are billed for every reasoning token burned getting there.

So the fix: stop treating the effort level as a cost control, set `max_output_tokens` deliberately, and pick that number from the distribution your own traffic already produces rather than from a round number that looks sensible.

```figure
{ "kind": "system",
  "title": "The whole argument: one of these is enforced, and it is the expensive one",
  "lanes": [
    { "t": "you can set", "nodes": [
        { "id": "eff", "t": "an effort level", "s": "neutral" },
        { "id": "cap", "t": "max output tokens", "s": "neutral" } ] },
    { "t": "which gives you", "nodes": [
        { "id": "shift", "t": "a shifted distribution", "s": "bad" },
        { "id": "hard", "t": "a hard ceiling", "s": "ok" } ] },
    { "t": "and when the tail arrives", "nodes": [
        { "id": "pay", "t": "you pay whatever it thought", "s": "bad" },
        { "id": "trunc", "t": "status incomplete, billed anyway", "s": "bad" } ] }
  ],
  "edges": [
    { "from": "eff", "to": "shift", "s": "bad" },
    { "from": "cap", "to": "hard", "s": "ok" },
    { "from": "shift", "to": "pay", "t": "no ceiling", "s": "bad" },
    { "from": "hard", "to": "trunc", "t": "no answer", "s": "bad" } ],
  "note": "Neither path is free. The decision is which failure you would rather buy, and at what rate." }
```

## The Fix: Pick the Ceiling From Your Own Distribution

The cap is a bet on the tail. You can make that bet deliberately or by accident, and a round number is the accidental version.

### Why isn't the effort level a cost control?

Because it changes the shape of the distribution, not its right edge. In the Code tab's simulation, `high` effort has a median of about 4,000 reasoning tokens and a ninety-ninth percentile above 32,000 — **8x the median**, on identical work.

That ratio is the thing to internalize. One effort level is not one cost. It is a cost distribution, and your bill is decided by the tail, not the middle.

Anthropic's own documentation said as much about the old knob too: the budget was "a target rather than a strict cap," and `max_tokens` was always the real ceiling. The migration did not remove a guarantee. It removed a number that felt like one.

### What actually happens when I hit the ceiling?

You get charged for nothing. OpenAI returns `status: "incomplete"` with `reason: "max_output_tokens"`, and notes this can happen during reasoning before any visible output appears. Google's is the same shape: generation stops with status `incomplete`, output is truncated or empty, and thinking tokens are still billed.

Google adds a detail worth knowing separately: you are billed for the *full* thought tokens the model generates, even though only a summary comes back through the API.

### So how do I choose the number?

From your logs. Take the reasoning-token counts you have already recorded, sort them, and pick the quantile that matches the truncation rate you can live with.

The Code tab does this over 4,000 requests at medium effort. A 2% truncation budget gives a cap of 8,895. The interesting rows are the ones next to it: a cap of 4,096 — which looks like a perfectly reasonable round number — truncates **17.5%** of requests and burns $3.41 on responses that produced nothing. A cap of 2,048 truncates **54.3%**.

Same model, same work. Only the ceiling moved.

## What This Means for You

**When this matters.** Any call to a reasoning model where you care what a single request can cost, and every migration off a thinking budget onto an effort level — which is now forced rather than optional on newer Claude models.

**How it affects you.** If you set a token budget once and moved on, you no longer have the control you think you have, and your per-request ceiling is whatever `max_output_tokens` happens to be. If you never set that, there is no ceiling at all. Your tail requests are unbounded and they are the ones that decide the bill.

**What to do about it.** Start here, and it costs one query: pull the reasoning-token count from your logged responses and print the median, the ninety-fifth and the ninety-ninth percentile. The field is `output_tokens_details.reasoning_tokens` on OpenAI, `usage.output_tokens_details.thinking_tokens` on Claude, and `usage.total_thought_tokens` on Gemini. If the ninety-ninth is several times the median, you have a tail problem and a round-number cap is not handling it.

Then set the cap from that distribution and state the truncation rate you are buying. Write the rate in the code comment next to the number, because the next person to read it will otherwise round it.

## Implementing It

**The change.** Three roles, and the first one is now mandatory rather than optional on recent models.

**Role 1 — whoever makes the call.** The migration is small and the behavior change is not.

```python
# before — a budget that reads like a cap, rejected with 400 on Claude 4.7+
resp = client.messages.create(
    model="claude-sonnet-4-6", max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000}, messages=msgs)

# after — a level, plus the ceiling that is actually enforced
resp = client.messages.create(
    model="claude-sonnet-5", max_tokens=8895,      # from your p98, not a round number
    thinking={"type": "adaptive"},
    output_config={"effort": "high"}, messages=msgs)
```

The behavior differs, not just the syntax. With a fixed budget the model thought on every request. With adaptive thinking it decides per request, and at lower effort it may skip thinking entirely on easy inputs.

**Role 2 — whoever owns the logs.** You cannot choose a cap you have never measured, and the field name differs per provider.

```python
# record this on every response, from day one, whatever provider you are on
usage = {
    "openai":    lambda r: r.usage.output_tokens_details.reasoning_tokens,
    "anthropic": lambda r: r.usage.output_tokens_details.thinking_tokens,
    "gemini":    lambda r: r.usage.total_thought_tokens,
}[provider](resp)
```

Log the effort level and the model beside it. A cap fitted across mixed traffic is fitted to a mixture, and the moment one segment shifts, the rate you thought you bought is gone. Fit per segment if the segments differ.

**Role 3 — whoever handles the response.** A truncated response is not an error your client will raise. You have to look for it.

```python
if getattr(resp, "status", None) == "incomplete":
    # billed, no answer. Retry at a higher cap or degrade — but count it either
    # way, because this rate IS the bet you made when you picked the number.
    metrics.increment("reasoning.truncated")
```

Silently treating that as an empty answer is how a 17% truncation rate survives in production for a quarter.

Decide the retry policy before you need it. Retrying at a higher ceiling pays for the thinking twice, so it is worth it only where the answer is worth more than two attempts. Everywhere else, degrade to a cheaper path and record it.

**How you know it worked.** Two numbers, and you should already be able to name the first.

Your observed truncation rate should land near the rate you chose. If you picked the ninety-eighth percentile and are seeing 10% truncation, your traffic has shifted away from the sample you fitted on, and the cap needs refitting rather than raising.

Second, watch spend on truncated requests as its own line. It is pure waste, it is invisible in an average cost-per-request figure, and in the Code tab a 4,096 cap turns it into $3.41 across 4,000 requests while a fitted cap makes it $0.85.

## When a Reasoning Cap Is the Wrong Tool

If your traffic is uniform, this is machinery for nothing. A cap only ever bounds the tail, so where there is no tail it changes no bill and adds a failure mode you did not have.

It also interacts badly with prompt caching, and this one is easy to miss. Anthropic documents that changing `budget_tokens` between requests invalidates cache breakpoints, because the value is rendered into the prompt — a worked example shows the third request re-creating 1,370 cached tokens after a budget change. Tuning a cap per request is a good way to never get a cache hit.

And a cap does nothing for the requests that do not hit it. If your goal is a lower average bill rather than a bounded worst case, the effort level and the prompt are the levers; the ceiling is not.

Three questions before setting one:

Do I have logged reasoning-token counts, or am I about to fit a cap to a guess?

What truncation rate can this feature actually absorb, stated as a number?

Is a truncated response distinguishable from an empty one in my code today?

## Glossary

- **Effort level** — a setting that shifts how much a model thinks, without bounding it.
- **Reasoning tokens** — tokens the model generates while thinking, billed as output, usually not returned.
- **max_output_tokens** — the enforced ceiling on generated tokens, including reasoning. The real cap.
- **Truncation** — the request stopping at the ceiling mid-thought, returning no answer and still billing.
- **Adaptive thinking** — the replacement for a fixed budget, where the model decides per request whether to think.
- **Tail** — the slowest few percent of requests, which decide the bill that the median hides.
