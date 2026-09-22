# How Jev Answers Five Questions in One Round Trip

**Category**: New Models & APIs
**Tags**: agents, latency, context-engineering
**Date**: 2026-09-22
**Level**: Building
**For**: Building agents
**Hook**: Jev returns typed values instead of text, and because it scores every question in parallel against one shared state, asking it five things costs about what asking one thing costs.
**Engineer's view**: This is the N+1 query you already fixed once. You replaced a loop of small fetches with one over-fetching join, because a round trip cost more than the extra rows. Same trade here, in the opposite direction from how you chain model calls: ask everything, discard most of it.
**TLDR**: Chaining model calls re-sends your whole context on every round trip. A model that scores questions in parallel lets you ask the entire decision in one call and throw away the branches you did not need.
**Time to read**: ~11 minutes

## Explain Like I'm 5

Imagine asking a waiter about the menu. You ask one question, wait while he walks to the kitchen and back, then ask the next. Five questions, five walks.

Or you ask all five at once. He makes one walk and returns with every answer — including answers that turned out not to matter, because you asked about the soup and then ordered pasta.

The walk is the expensive part. The questions are nearly free. So you ask everything while he is standing there listening.

## The Problem

You have shipped this bug before, and it had nothing to do with AI.

You fetched a list of orders, then looped over it and fetched each order's customer. It was fine against a hundred rows on your laptop. In production it made a thousand round trips and the endpoint timed out.

You fixed it with one query that joined more than you strictly needed.

That is the whole lesson, and you already know it. When the round trip is expensive and the payload is cheap, over-fetch and throw the extra away.

Now look at how a decision gets built on top of a model.

Classify the ticket. If it is a bug, ask how severe. If it is severe, ask whether there are reproduction steps. Every step is another call, and every call re-sends the ticket, the thread, and whatever context you assembled around them. Latency is the sum of the steps. You pay for the same state on each one.

You have rebuilt N+1, somewhere a round trip costs seconds rather than milliseconds.

TypeSafe's Jev is built so the trade flips back. It scores every question in parallel and in isolation against one shared state, so a request carrying five questions takes about as long as a request carrying one.

So the fix: stop chaining. Put every question the decision could need into a single call — category, frustration, refund requested, bug severity, reproduction steps — and discard the answers whichever branch you took does not use.

```figure
{ "kind": "system",
  "title": "The whole argument: the questions are cheap, the context is not",
  "lanes": [
    { "t": "the decision needs", "nodes": [
        { "id": "q", "t": "five typed questions", "s": "neutral" } ] },
    { "t": "chained, you pay", "nodes": [
        { "id": "many", "t": "a round trip per branch", "s": "bad" } ] },
    { "t": "fanned out, you pay", "nodes": [
        { "id": "one", "t": "one round trip, state sent once", "s": "ok" } ] },
    { "t": "per ticket", "nodes": [
        { "id": "slow", "t": "906 tokens · 172 ms", "s": "bad" },
        { "id": "fast", "t": "600 tokens · 114 ms", "s": "ok" } ] }
  ],
  "edges": [
    { "from": "q", "to": "many", "t": "state re-sent each trip", "s": "bad" },
    { "from": "q", "to": "one", "t": "asks one more question", "s": "ok" },
    { "from": "many", "to": "slow", "s": "bad" },
    { "from": "one", "to": "fast", "s": "ok" } ],
  "note": "Fan-out asks MORE and discards a fifth of it, and still costs less. The state is what was expensive." }
```

## The Fix: Put Every Question in One Call and Discard What You Do Not Use

The request carries two things that are deliberately separate: a **state**, which is the content being judged, and a map of **questions**, which are the judgments you want about it.

### Why doesn't asking more questions cost more?

Because the questions do not see each other. Each one is scored independently against the same state, so a tenth question cannot crowd the first and does not lengthen anything the others read. The docs put it plainly: adding more questions usually has little effect on response time.

That is what makes the speculative version worth it. Ask `bug_severity` even when the ticket probably is not a bug. If it is, you saved a round trip. If it is not, you throw the answer away and paid almost nothing.

Run the Code tab for the arithmetic. Over 400 tickets, fanning out asks about one extra question each and discards 20% of everything it asks — and still uses **1.45x fewer tokens** and **1.51x less latency** than chaining. The saving is not in the questions. It is that a 600-token state gets sent once instead of once per trip.

### What goes in the state and what goes in a question?

State is the facts; questions are the judgments. State takes a string, a JSON object, or an array of text values, and the docs recommend an object for most requests so each part has a name. Text only — images, audio and video are not supported.

The split matters more than it looks. Anything you put in the question text is repeated per question; anything in the state is shared across all of them.

### What do the three primitives actually return?

`Choice` returns the picked key, a probability for every option you defined, and a confidence. `Score` returns a position along your levels — it can land between two of them — plus a legend, probabilities and confidence. `Noul` returns a single number from 0 to 1, where near 1 is a strong yes and 0.5 is maximum uncertainty, and it has no separate confidence field because the value already is one.

## What This Means for You

**When this matters.** Any decision your code makes by asking a model more than one thing: ticket triage, intent routing, moderation, extraction, or a guardrail that runs before a tool call.

**How it affects you.** If you built that decision as a chain, your latency is the sum of the steps and your token bill scales with the depth of the tree rather than the size of the question. That cost is invisible in a per-call dashboard, because every individual call looks cheap and fast.

**What to do about it.** Start here, and it needs no new vendor: count the model round trips in your worst decision path, and multiply by the tokens of context each one re-sends. That product is what chaining is costing you, and most teams have never written it down. If it is one round trip, stop — this article is not about you.

Then, if you are going to try a structured-decision model, port one decision rather than the system. Pick the highest-volume, smallest-judgment one you have — the classifier in front of everything else is usually right — and run it in shadow against whatever you use now before you route real traffic through it.

## Implementing It

**The change.** Three roles touch this, and the second one is where the work actually moves.

**Role 1 — whoever defines the decision.** Questions become data, not prose. Each gets a type and its own criteria.

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

response = TypeSafeClient().system_one(
    state={"message": ticket.body, "order_id": ticket.order_id},
    questions={
        "category": Choice(instructions="Which team should handle this",
                           criteria={"billing": "Payment or subscription issues",
                                     "technical": "Bugs or integration problems",
                                     "sales": "Pricing or account questions"}),
        "frustration": Score(instructions="How frustrated the customer appears",
                             criteria=["Calm, just stating facts",
                                       "Frustrated but civil",
                                       "Very angry, strong language"]),
        "is_urgent": Noul(instructions="The message conveys time-sensitivity"),
    },
)
dept = response.answers["category"].choice     # a key you defined, not a string to parse
```

Over HTTP it is one `POST https://api.typesafe.ai/v1/systemone` with `model: "jev-latest"`, and the response carries `answers` keyed by your question ids plus a `usage` block with input and output token counts.

**Role 2 — whoever assembles the state.** This is the role nobody assigns, and skipping it is how the whole thing fails. Jev knows only what you hand it and cannot look anything up, so every lookup a chained prompt used to do implicitly is now yours to do first.

```python
# the retrieval you used to hide inside a prompt is now an explicit step
state = {
    "message": ticket.body,
    "plan": billing.plan_for(ticket.account_id),     # you fetch it
    "recent_incidents": status.incidents(hours=24),  # you fetch it
}
```

Get this wrong and the model answers honestly about a state that was missing the deciding fact. That failure looks like a bad model and is actually a bad request.

Keep the state to facts the judgment needs. Everything you put in it is read by every question in the request, so padding it does not cost you once. It costs you on all of them.

**Role 3 — whoever wires the branch.** Ask everything, then filter. The speculative answers cost a round trip only when you need them.

```python
a = response.answers
if a["category"].choice == "bug_report":
    route_bug(severity=a["bug_severity"].score, repro=a["has_repro"].noul)
else:
    route_general(a["category"].choice)     # bug_severity and has_repro discarded
```

**How you know it worked.** Three signals, all countable.

First, round trips per decision should fall to exactly 1. If your logs still show two, a question is reading another question's answer, and that dependency has to move into your code.

Second, latency should stay flat as you add questions. Time the same state with three questions and with eight. If the second is materially slower, you are not getting parallel evaluation and the fan-out argument does not hold for your workload.

Third, input tokens per decision should stop scaling with tree depth. That is the real saving, and it is the one a per-call cost dashboard will never show you, because it only ever gets cheaper by making a call disappear.

## When Jev Is the Wrong Tool

It chooses; it does not write. Chat, code generation, summaries, and any output a human reads as prose are all outside what a structured-decision model does. It also cannot explain itself — you get a distribution, not a reason — so if an auditor needs to know *why* a claim was rejected, a typed answer with a probability beside it is not an answer to that question.

It cannot look anything up either. Every fact the decision depends on has to be in the state you assembled, which moves real work to Role 2 above and makes retrieval bugs look like model bugs.

Treat the comparison figures carefully, including the ones here. The benchmarks are vendor-run, TypeSafe's own team wrote the workflows, and the reference answers are an average of two frontier models rather than human labels — so the reported accuracy measures agreement with an expensive model, not correctness. The company also says it cannot prove the pricing is unsubsidized. The latency and token arithmetic in the Code tab is structural and does not depend on any of that, but the accuracy claims do.

Three questions before adopting it:

Does my decision have a fixed set of answers, or does something downstream need prose?

Can I assemble every fact the judgment needs before the call?

Is this decision frequent enough that one round trip instead of three actually shows up anywhere?

## Glossary

- **State** — the content being judged, sent once and shared by every question in the request.
- **Fan-out** — asking every question the decision could need in one call, then discarding the unused answers.
- **Noul** — a question answered as a number from 0 to 1, where near 1 is a strong yes.
- **Choice** — a question answered by picking one key from criteria you defined.
- **Score** — a question answered as a position along ordered levels you defined, possibly between two.
- **Round trip** — one request and response between your code and the model, the unit this article is minimizing.
