# Why an Idle GPU Is the Wrong Place to Send a Request

**Category**: AI in Production
**Tags**: inference-serving, caching, latency
**Date**: 2026-09-09
**Level**: Building
**For**: Shipping AI
**Hook**: Every load balancer you have written sends work to the least busy machine. On a fleet serving an agent that rule is backwards, because the busy machine is the one already holding your conversation.
**Engineer's view**: You have set a pool to least-connections and watched latency drop. That worked because your workers were interchangeable. A GPU serving an agent is not — it holds the cached prefix of that conversation, so the idle one has to redo work the busy one already did.
**TLDR**: Requests to an LLM server are not interchangeable, because each one is cheap on the machine that already cached its prefix. That breaks two habits at once: balancing by queue depth, and letting any request into the scheduler.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine a row of kitchens, all cooking the same long recipe. One kitchen has already
chopped everything for your dish and is halfway through. Another is empty. Sending your
order to the empty kitchen looks fair, and it is slower, because they have to chop it all
again. The busy kitchen finishes first even with a queue. And if you let one enormous
order into a kitchen, everyone behind it waits, however small their dishes were.

## The Problem

You have solved this before, on machines with no GPU in them. You put a pool behind a load
balancer and set it to least-connections. Latency dropped, and it dropped because your
workers were interchangeable — any box could serve any request at the same cost, so the
emptiest box was always the right answer.

Then someone added a cache to each worker, and least-connections quietly got worse. A
request routed to an idle box missed the cache and did the expensive work again, while the
box that already held the data sat one connection busier and was skipped for being busy.

That is an LLM fleet serving an agent, exactly. Each GPU holds a **prefix cache** — the
computed attention state for the tokens it has already seen. An agent's turns share a
long, identical prefix: the system prompt, the tool definitions, the conversation so far.
On the GPU that served the last turn, that prefix is already computed and the next turn
starts almost free. On an idle GPU it is a fresh **prefill**, which is the expensive half
of serving.

So the habit inverts. **The right target is the machine that already has your conversation,
even when it is busier** — and the same non-interchangeability breaks a second habit, which
is letting any request into the scheduler in the order it arrived.

## The Fix: Route to the Cache, and Cap the Prefill

On 8 September 2026 the vLLM team published serving results with Inferact, measured on
SemiAnalysis's AgentX benchmark. Two of their findings are the two habits above, and both
come from the same root: requests are not interchangeable.

```figure
{ "kind": "system",
  "title": "The whole argument: the same turn, two routing rules",
  "lanes": [
    { "t": "a turn arrives", "nodes": [
        { "id": "req", "t": "turn 7 of a session" } ] },
    { "t": "routed by", "nodes": [
        { "id": "least", "t": "least queue depth", "s": "bad" },
        { "id": "stick", "t": "session stickiness", "s": "ok" } ] },
    { "t": "what it costs", "nodes": [
        { "id": "cold", "t": "prefill the whole prefix", "s": "bad" },
        { "id": "warm", "t": "cache hit, decode only", "s": "ok" } ] }
  ],
  "edges": [
    { "from": "req", "to": "least", "t": "idle GPU", "s": "bad" },
    { "from": "req", "to": "stick", "t": "busier GPU", "s": "ok" },
    { "from": "least", "to": "cold" },
    { "from": "stick", "to": "warm" } ],
  "note": "The idle machine is idle because it has not seen this conversation. That is the cost, not the queue." }
```

### Why does the busier machine win?

Because the queue is short and the prefill is long. Waiting behind two requests costs you
their decode time. Missing the cache costs you a full recomputation of every token in the
prefix, and in an agent that prefix grows with every turn.

The vLLM write-up puts it plainly: load balance does not guarantee better performance, and
cache locality outweighs instantaneous load distribution. The recommendation is
**session-aware sticky routing** — send a session's turns back to the replica that served
the last one — rather than balancing by queue depth.

There is a second half, because a cache that is evicted between turns is no cache at all.
An agent pauses while a tool runs, and a purely reactive cache drops the prefix during that
gap. So retention is made deliberate: keep the prefix across turn boundaries by interval,
and keep prefixes selectively when they are seen repeatedly.

### So what breaks if a long request gets in?

Everything behind it. This is head-of-line blocking, and it is the same failure as one slow
query holding a connection pool.

A prefill is scheduled as a unit of work. A very long one occupies the scheduler while
every short request waits, so the tail latency of small turns is set by the largest prompt
in the fleet. The fix is to stop treating prefill as indivisible:

```figure
{ "kind": "bars",
  "title": "Capping the prefill chunk on DeepSeek V4 Pro",
  "bars": [
    { "label": "Throughput", "v": 93, "d": "+93%", "s": "ok" },
    { "label": "P90 interactivity", "v": 130, "d": "2.3x", "s": "ok" }
  ],
  "note": "From one flag: --long-prefill-token-threshold 512. Measured by vLLM and Inferact on AgentX." }
```

The flag is `--long-prefill-token-threshold`, set to 512 in their example. Above that, a
prefill is split so it cannot monopolize a scheduling step. Their interactivity figure is
reported at the P90, so the gain is measured on the users having the worst time rather than
on the average.

```figure
{ "kind": "route",
  "title": "What the router is actually choosing between",
  "source": "turn 7 of session abc",
  "parts": [
    { "t": "the warm replica", "to": 0, "via": "holds the prefix", "s": "ok" },
    { "t": "an idle replica", "to": 1, "via": "empty queue", "s": "bad" }
  ],
  "dests": [
    { "t": "prefill 400 tokens", "s": "ok" },
    { "t": "prefill 4,380 tokens", "s": "bad" }
  ],
  "note": "Same turn, same model, same output. The only difference is whether the conversation was already there." }
```

## What This Means for You

**When this matters.** You run your own inference — vLLM, SGLang, anything you scale
yourself — and the traffic is conversational. Agents are the extreme case, because the
shared prefix grows every turn and is re-sent every turn. If your traffic is one-shot
requests with no shared prefix, none of this reaches you, and least-connections stays
right.

**How it affects you.** It moves a decision out of the infrastructure layer and into
yours. A generic load balancer cannot make this call, because it cannot see which replica
holds which prefix. Something has to carry the session identity to the routing layer, and
that is application knowledge.

It also changes what you measure. Queue depth and GPU utilization both look healthy while
you are burning the fleet on recomputation, because a cache miss is not idle time — it is
busy time doing work that did not need doing. **Cache hit rate is the number that tells
you**, and most teams are not graphing it.

**What to do about it.**

1. Graph prefix cache hit rate per replica. That is one metric and it usually settles the
   argument before you change any routing.
2. Then make routing sticky by session id. Hash it to a replica rather than asking which
   replica is least busy.
3. Set a prefill chunk cap so one long prompt cannot own a scheduling step.
4. Keep a real fallback: if the sticky target is genuinely saturated, spill. Stickiness that
   never yields turns one hot session into an outage.

## Implementing It

**The change.** Three places, and the third is what stops it becoming an incident.

*The router.* Send a session back where it has been. This is the whole idea, and it is
about eight lines:

```python
import hashlib

def pick(session_id, replicas, load, spill_at=0.9):
    """Sticky by session, with a pressure valve."""
    idx = int(hashlib.blake2b(session_id.encode(), digest_size=8).hexdigest(), 16)
    home = replicas[idx % len(replicas)]
    if load[home] < spill_at:
        return home                       # the warm one, even if it is busier
    # Saturated: spill to the least loaded, and accept the cold prefill.
    return min(replicas, key=lambda r: load[r])
```

Hashing beats a lookup table because it needs no shared state and survives a router
restart. The `spill_at` threshold is the part people leave out: without it, one heavy
session pins a replica and the rest of the fleet watches.

*The server.* Cap the prefill chunk and let the cache survive a tool call:

```bash
vllm serve <model> \
  --enable-prefix-caching \
  --long-prefill-token-threshold 512   # split prefills above this
```

The threshold is a scheduling decision, not a model one. Too low and you add overhead to
every long prompt; too high and one prompt owns the step. 512 is where the published
measurement was taken, and it is a starting point rather than an answer.

*The metric.* Neither change is safe to make blind, and the signal is not in your usual
dashboard:

```python
hit_rate = cached_prefix_tokens / total_prompt_tokens     # per replica, per minute
```

Graph it per replica alongside queue depth. A fleet that looks balanced and has a low hit
rate is the exact failure this fixes, and the two lines together are what make it visible.

**How you know it worked.** Prefix cache hit rate goes up and time-to-first-token goes
down, on the same traffic. Those are one signal, not two: TTFT is dominated by prefill, so
a hit is the mechanism and a faster first token is the result.

Watch the shape of the load chart too. It should get *less* even, and that is the point —
you are trading balance for locality on purpose. What must not happen is a replica pinned
at saturation while others idle, which means your spill threshold is too high.

**When not to.** If prefix cache hit rate is already high, routing is not your problem and
you should leave it alone. Measure before you change anything.

## When Sticky Routing Is the Wrong Tool

Stickiness trades resilience for locality, and sometimes that trade is bad.

The clearest case is short, unrelated requests. A classifier or an embedding endpoint has
no meaningful shared prefix, so there is no locality to preserve and stickiness buys you
nothing while costing you even distribution. Least-connections is correct there and always
was.

Uneven session weight is the real operational risk. Hashing assumes sessions cost roughly
the same. One session running a long agentic job can pin a replica while the fleet idles,
which is why the spill threshold is not optional and why you should alert on it firing
often rather than treating it as normal.

And these numbers came from one benchmark on large hardware — DeepSeek V4 Pro on twelve
GB300s at 256 concurrency. The mechanism is general and the magnitudes are not. Your prefix
is a different length, your turn cadence is different, and the flag value that worked there
is a starting point.

Three questions before you change routing:

- What is my prefix cache hit rate right now, per replica?
- Do my requests actually share a prefix, or have I assumed it?
- If one session goes heavy, what makes it spill, and will I see it happen?

## Glossary

- **Prefix cache** — the attention state a server keeps for tokens it has already
  processed, so a later request sharing that prefix skips recomputing it.
- **Prefill** — the pass over the whole prompt before the first output token. It is the
  expensive half of serving and the half a cache hit skips.
- **Head-of-line blocking** — one large unit of work occupying a scheduler while smaller
  work waits behind it, so the tail latency of small requests follows the biggest one.
- **Sticky routing** — sending a session's later requests to the replica that served its
  earlier ones, in order to land on a warm cache rather than an idle machine.
- **Time-to-first-token** — how long a caller waits before output starts. Dominated by
  prefill, which is why it moves when the cache hit rate moves.
- **Interactivity** — the per-user output rate a server sustains under load, reported here
  at the P90 so it describes the users having the worst time.
