# How 1,024 Agents Split One Task Without a Coordinator

**Category**: Applied Research
**Tags**: agents, benchmarks, paper
**Date**: 2026-09-23
**Level**: Building
**For**: Building agents
**Hook**: Microsoft Research ran a thousand agents on one codebase with nothing assigning the work, and the interesting question is not whether the score went up but what you bought with the tokens.
**Engineer's view**: This is the dispatcher you deleted. You had one process handing work to a pool, it became the bottleneck and the single point of failure, and you replaced it with workers claiming from a shared queue. An orchestrator model is that dispatcher, and its context window is the queue depth you cannot raise.
**TLDR**: A leaderless agent organization scales further than an orchestrated one, because nothing has to hold the whole plan. What the scaling curve buys you is wall-clock time, not cheaper work.
**Time to read**: ~11 minutes

## Explain Like I'm 5

Picture a warehouse with one supervisor who tells everybody what to do next.

Add more staff and for a while it gets faster. Then it stops, because everyone has to wait for the supervisor to look up and speak. The supervisor is now the slowest part of the building.

The fix is a board on the wall. People take a card, do the job, put up what they learned, and take another. Nobody waits to be told.

More people still finish sooner. It does not make each job cheaper.

## The Problem

You have shipped this before, and it had nothing to do with AI.

You built a job system with one dispatcher process handing tasks to a pool of workers. It was easy to reason about and it worked. Then the pool grew, and the dispatcher became the thing everyone queued behind — and the single point whose crash stopped all of it.

You replaced it with a shared queue and an atomic claim. Workers took their own work.

That is the same move that agent systems are now making, for the same reason but with a harder limit. An orchestrating model has to hold the plan, the assignments and the progress in its context. That context is finite, so the orchestrator is not merely a bottleneck; it is a bottleneck you cannot buy your way out of by giving it a bigger machine.

Microsoft Research's **Agensh** removes it entirely and runs up to 1,024 workers with nothing in the middle. Scaling from one worker to 1,024 on the pandoc codebase takes the final test-pass rate from 33.89% to 55.06%.

That number is real and it is also the thing to be careful about. A thousand workers burn roughly a thousand times the tokens, and the paper does not normalize for spend.

So the fix, and the way to read it: let workers claim their own subtasks from a shared workspace, keep only the claim atomic, and judge the result at **matched token spend** rather than at matched rounds. Do that and the shape of what you gained changes.

```figure
{ "kind": "system",
  "title": "The whole argument: what a thousand workers actually buy",
  "lanes": [
    { "t": "you scale to", "nodes": [
        { "id": "many", "t": "1,024 workers", "s": "neutral" } ] },
    { "t": "judged at", "nodes": [
        { "id": "rounds", "t": "fixed rounds", "s": "bad" },
        { "id": "spend", "t": "fixed token spend", "s": "ok" } ] },
    { "t": "the gain reads as", "nodes": [
        { "id": "qual", "t": "much better quality", "s": "bad" },
        { "id": "clock", "t": "same quality, far less waiting", "s": "ok" } ] }
  ],
  "edges": [
    { "from": "many", "to": "rounds", "t": "1000x the tokens", "s": "bad" },
    { "from": "many", "to": "spend", "s": "ok" },
    { "from": "rounds", "to": "qual", "s": "bad" },
    { "from": "spend", "to": "clock", "t": "64x fewer rounds", "s": "ok" } ],
  "note": "Both readings come from the same runs. Only the thing held constant changed." }
```

## The Fix: Let Workers Claim Their Own Work, and Judge It at Matched Spend

Three pieces of shared state, and only one of them needs to be strongly consistent.

### Why does a central orchestrator stop scaling?

Because the plan lives in its context. Every assignment, every result and every revision has to fit, and the window does not grow with the size of the job. Past some worker count the orchestrator spends more of its budget restating the state of the world than deciding anything about it.

Agensh replaces it with a shared workspace holding proposed, ongoing and completed work, a message interface between workers, and a shared context of findings. A worker gathers context, claims a subtask, acts, publishes what it learned, verifies, and merges — asynchronously, with nobody waiting to be told.

### What has to be atomic, and what doesn't?

The claim, and almost nothing else. Two workers doing the same subtask is waste; two workers reading a slightly stale finding is fine, because the finding is a hint rather than a fact they must agree on.

That asymmetry is the whole reason this scales. Strong consistency is needed at exactly one point, and everything expensive — sharing, verifying, merging — is allowed to be eventually consistent.

### Does more agents actually mean better, or just more?

This is where you have to do work the paper leaves undone. Run the Code tab: at a fixed 30 rounds, the pass rate climbs from **2.7%** with one worker to **100%** by sixteen, which is the paper's shape.

Then hold tokens constant instead and give one worker the attempts the crowd would have spent. All three configurations land on the same pass rate and the same cost — and the crowd reaches it in **64x fewer rounds**.

So the honest reading is that agent count buys wall-clock time, and buys quality only as far as workers genuinely share findings. Set the sharing lift to zero in the simulation and the quality difference disappears entirely, leaving parallel retries.

## What This Means for You

**When this matters.** Any time you were about to add an orchestrator model to coordinate sub-agents, and any time somebody quotes a multi-agent scaling number at you.

**How it affects you.** If your agent system has a planner holding the whole task, its context is your scaling limit and no model upgrade removes it. And if you are evaluating whether to fan out, the number that decides it is wall-clock under a spend cap, not pass rate at a fixed number of turns.

**What to do about it.** Start here, and it needs no new framework: take your existing multi-step agent run and write down the token spend and the elapsed time separately. Most teams have one number that blends them. If you cannot say what a run cost and how long it took as two figures, you cannot tell whether parallelism helped or just cost more.

Then, if you do fan out, measure it the way the section above does — match the spend, vary the shape, and compare. A fan-out that wins at fixed rounds and ties at fixed spend is a latency optimization, which is a perfectly good thing to buy as long as you know that is what you bought.

## Implementing It

**The change.** Three roles, and the first one carries the only hard correctness requirement.

**Role 1 — whoever owns the workspace.** The claim must be atomic and it must expire, or a crashed worker takes a subtask to the grave.

```python
def claim(self, worker, now):
    # compare-and-set in whatever you already run: Redis, Postgres, a file lock.
    # The lease is what makes a dead worker recoverable without a supervisor.
    for task in self.open - set(self.claimed):
        prev = self.claimed.get(task)
        if prev is None or prev.expires < now:
            self.claimed[task] = Lease(worker, expires=now + LEASE_SECONDS)
            return task
    return None
```

Pick the lease duration from your slowest attempt, not your average one. Too short and a working agent has its subtask stolen mid-thought, which you pay for twice; too long and a crashed one parks that subtask until the timer runs out. This is the same number you have tuned on a job queue before, and it behaves the same way here.

Everything else in the workspace can be eventually consistent. Findings, messages and progress are hints, and a worker reading a stale one wastes an attempt rather than corrupting a result.

**Role 2 — whoever writes the worker loop.** One cycle, repeated, with no instruction from anywhere.

```python
while workspace.open:
    task = workspace.claim(me, time.time())
    if task is None:
        continue                      # contention or nothing left; do not block
    context = workspace.findings()    # what everyone has learned so far
    result = attempt(task, context)
    workspace.publish(result.finding) # share BEFORE verifying, so peers move
    workspace.complete(task, ok=verify(result))
```

Publishing the finding before verification is deliberate. A peer acting on a hint that later fails has lost one attempt; a peer that waited for verification has lost the round.

**Role 3 — whoever reports the result.** Record spend and elapsed rounds as separate columns, always.

```python
metrics.emit(workers=n, rounds=r, tokens=total_tokens, passed=pass_rate)
# a single "cost" figure here is how a latency win gets reported as a quality win
```

**How you know it worked.** Two signals, and the second is the one that keeps you honest.

First, contention should stay low as workers grow. Count failed claims as a fraction of attempts. If it climbs with worker count, your claim is a bottleneck and you have rebuilt the dispatcher inside the lock.

Second, plot pass rate per million tokens, not pass rate. In the Code tab that number rises from 0.10 to 0.34 and then flattens — it stops improving well before the raw pass rate does, and the gap between those two points is the part of the win that is spend rather than organization.

## When a Leaderless Agent Organization Is the Wrong Tool

It needs work that genuinely divides. Subtasks with a strict order give a thousand workers nothing to claim, and the cooperation loop becomes a thousand agents reading the same board and waiting.

The economics deserve suspicion too. At matched spend the simulation shows the crowd tying on quality, and the paper reports no compute normalization at all, so the headline curve conflates agent count with token budget. That does not make the result wrong — the wall-clock win is real and the paper frames it for time-constrained work — but "agent count is a new scaling dimension" is a stronger sentence than the evidence shown supports.

And a thousand concurrent workers is a real operational surface: rate limits, a thousand leases to expire, and a cost that arrives all at once rather than over an afternoon.

Three questions before adopting it:

Does my task actually decompose, or does step two need step one's answer?

Can I state my budget as a spend cap rather than a turn count?

Would I still fan out if the quality came out identical and only the clock moved?

## Glossary

- **Orchestrator** — a model that holds the plan and assigns work, and whose context window becomes the ceiling.
- **Claim** — a worker taking a subtask for itself; the one operation that must be atomic.
- **Lease** — an expiry on a claim, so a crashed worker's task returns to the pool without a supervisor.
- **Shared context** — findings published by workers for other workers to read, consistent only eventually.
- **Contention** — two workers reaching for the same subtask, wasting an attempt.
- **Matched spend** — comparing configurations at equal token cost rather than equal rounds.
