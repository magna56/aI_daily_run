# How to Test an AI Agent So a Broken Layer Can't Hide

**Category**: Evals & Reliability
**Tags**: reliability, benchmarks, agents, paper
**Date**: 2026-08-27
**Level**: Building
**For**: Shipping AI
**Hook**: An AI agent's overall pass rate can barely move while one whole step inside it stops working completely — unless you test that step on its own.
**Time to read**: ~11 minutes

## Explain Like I'm 5

Imagine a school gave you one overall grade for the semester instead of a grade per class. If you get a perfect score in four classes and completely fail the fifth, your overall grade only drops a little — the report card still looks basically fine. Nobody glancing at that one number would ever guess you failed an entire class. The only way to catch it is to also look at each class's grade on its own, not just the average across all of them. That is the whole idea here, just applied to testing a piece of software instead of a student.

## The Problem

A team running an AI ordering agent in production watches one number after every release: the percentage of end-to-end test conversations that finish correctly. It holds steady release after release, so nobody looks any further — until a support ticket surfaces that the agent stopped escalating suspicious high-value orders for human review two weeks ago, and has been silently auto-approving them ever since. The regression was sitting in the eval suite the whole time; it just never moved the number anyone was watching. A single pass-rate score is an average across every kind of conversation a customer might have, and escalation only ever fires on a narrow slice of those — orders over a spend limit, orders with a mismatched shipping address, orders flagged for fraud. Break escalation completely and most test conversations never touch that code path at all, so the score that actually broke does not look broken. It is the same failure mode as a dashboard that only tracks median latency: a page that is unusably slow for one in twenty users can sit invisible under a healthy median indefinitely.

## How Layer-Isolated Testing Catches What the Average Hides

A new paper (arXiv:2606.11686, Zhang, Wang & Lei, June 2026) names this precisely and measures it on a real, deployed ordering agent. Their fix is to stop grading the agent once and start grading each step of it separately.

### The Layers of an Ordering Agent

The paper decomposes the agent into eight named layers, each the unit that gets its own test suite: **ontology** (turning a customer's words into a canonical product ID), **intent** (a signal vector describing what the customer wants), **routing** (which tool or handler gets invoked), **decomposition** (splitting one request into ordered sub-goals), **escalation** (deciding when an order must go to a human), **safety** (price, SKU and allergen checks that can reject an order outright), **memory** (recalling prior session context), and a cross-cutting **envelope/defense** band (out-of-distribution rejection, input reformulation, locale handling).

### A Pure-Mode Assertion Slice

Each layer gets an **assertion slice**: a small set of test cases run in **pure mode** — the layer's own deterministic logic, called directly, with the LLM stubbed out of the picture entirely. An ontology slice looks like this:

```python
def ontology_resolve(sku: str, broken: bool) -> str | None:
    return None if broken else CANON.get(sku)

# case: input "sku-42", expected output "CANON-COLA-42"
assert ontology_resolve("sku-42", broken=False) == "CANON-COLA-42"
```

"No LLM is invoked; a slice failure is a real contract violation," in the paper's own words — there is no ambiguity to argue about, unlike an LLM-judge scoring a free-form answer.

### The Locked Baseline

Every slice's pass rate is frozen into a **locked baseline** — a JSON record of `(total, passed, rate, failed_ids)` per slice. The paper's production baseline is 238 cases across 23 slices, all at 100%, and the whole pure suite runs in 2.39 seconds — about 10 milliseconds per case, fast enough for every pull request. CI diffs the current run against that baseline: **any per-slice rate drop blocks the merge.** The gate also enforces **coverage honesty**: a slice with zero cases reports its rate as `null` ("uncovered"), never a false `1.0` — an untested layer can't silently look tested.

### The Masking Effect, By the Numbers

The paper validates this by breaking one layer at a time — monkeypatching a single entry point (ontology resolver → null, escalation → never escalate, defense scan → allow everything). Across the seven non-safety layers, here is what they measured:

| Layer regressed | Aggregate score moved | The matching slice moved |
| --- | --- | --- |
| OOD gate | −1.68 pp | −36.36 pp |
| Intent signals | −4.20 pp | −25.00 pp |
| Escalation | −4.62 pp | −50.00 pp |
| Defense scan | −5.04 pp | −63.16 pp |
| Reformulator | −5.88 pp | −80.00 pp |
| Decomposer | −5.88 pp | −90.91 pp |
| Ontology (foundational) | −26.47 pp | −95.24 pp |

Six of the seven regressions barely dent the aggregate — a 2-to-6-point wobble a team would read as noise — while the slice built to test exactly that layer falls off a cliff. The one outlier, ontology, is **foundational**: every other layer depends on a correctly resolved product ID, so breaking it cascades downstream and the aggregate score notices. A layer's position in the pipeline, not its importance, determines whether the average can hide it.

## For a Software Engineer

This is the same lesson as replacing one aggregate error-rate alert with a per-endpoint alert. If `/checkout` starts throwing 500s on every request but it is one endpoint out of forty behind a single "overall API error rate" metric, that metric moves by a fraction most on-call rotations would page right past. Nobody would seriously monitor a multi-service API with one combined error rate instead of one per endpoint — yet that is exactly how most teams evaluate an agent today: one end-to-end task-success number standing in for eight layers of very different logic.

**The number worth feeling:** in the paper's own regression tests, six of seven layer-breaking bugs moved the aggregate score by less than six percentage points while destroying 25 to 91 percentage points of the one slice that actually owned the bug. Whatever dashboard you currently watch for your own agent, ask whether it could show the same six-point wobble while something underneath it is completely dead.

## What This Means for You

**When this matters:** you have an agent (or any multi-step LLM pipeline) in production, you watch one end-to-end success rate as your main health signal, and that rate has been stable for a while — which you have been reading as "nothing changed."

**How it affects you:** stability in an aggregate score is not proof that every part underneath it still works. If your agent has a rarely-exercised path — an escalation rule, a safety check, a fallback for malformed input — that path can regress completely and your one dashboard number will not tell you. You find out from a support ticket, not from CI.

**What to do about it:**
1. List the distinct logical steps your agent actually takes (not files — steps: something like "resolve entity," "decide tool," "validate output," "escalate or not"). This is your layer taxonomy, and most agents already have 4-8 of them whether or not anyone named them.
2. For each step, write a handful of deterministic assertions that call that step's code directly with the LLM call stubbed out or bypassed — see `Implementing It` below for the exact shape.
3. Freeze the current pass rate per step as your baseline, and gate CI on any step's rate dropping — not just the aggregate.

## Implementing It

**The change.** This moves work onto whoever owns the agent's test suite, and separately onto whoever wires CI — most teams only build the first half.

*Eval-harness author — the slice, isolated from the LLM.* Structure a layer so its logic can be called without a model in the loop, and give it a small table of input/expected-output pairs:

```python
def escalate(order: dict, broken: bool = False) -> bool:
    if broken:
        return False  # injected fault: "never escalate"
    return order["total_cents"] > 50_000 or order["flagged"]

ESCALATION_SLICE = [
    ({"total_cents": 12_000, "flagged": False}, False),
    ({"total_cents": 80_000, "flagged": False}, True),
    ({"total_cents": 5_000,  "flagged": True},  True),
]

def run_slice(fn, cases, broken=False):
    passed = sum(int(fn(c, broken=broken) == exp) for c, exp in cases)
    return passed, len(cases)
```

`run_slice` is the reusable core — it works for any layer whose function takes an input and a `broken` flag and returns something comparable. The full version, plus a second real layer (safety repricing) and the masking-table comparison across seven layers, is in `code_example.py`.

*CI engineer — wire the gate's *output* into the merge check*, not just the function that computes it (that part, `gate_ci`, is in `code_example.py`). The step itself is small precisely because the decision already happened in Python:

```yaml
- name: layer-isolated eval gate
  run: python3 eval/gate_ci.py --baseline eval/baseline_layers.json
  # exits 1 and prints the blocked layer names; a required check, not advisory
```

Point `--baseline` at a `baseline_layers.json` checked into the repo next to the tests, and make this a **required** status check, not one people learn to ignore. A slice that regresses blocks the merge; a slice with zero cases (`total: 0`) blocks it too, by design — an untested layer should never pass silently just because nobody wrote its cases yet.

**How you know it worked.** Run `code_example.py`. It breaks each of seven layers one at a time and prints both scores side by side: the aggregate suite drops by 1.6 to 26.4 percentage points depending on the layer, while the matching slice drops by 25 to 100 percentage points every time — the same masking shape the paper measured, reproduced with its own smaller synthetic suite rather than the paper's literal ordering agent. The `gate_ci` demo then breaks escalation specifically and shows `blocked slices: ['escalation', 'memory']` — the regression is named, not just detected, and the untested `memory` layer is flagged as uncovered rather than passing by default.

## When Layer-Isolated Testing Is the Wrong Tool

This costs real setup: it only works on layers with a clean, callable boundary you can invoke without a live model, which means it assumes your agent's code is already factored that way. A pipeline built as one long prompt with no isolable steps has to be refactored before this technique applies at all — and that refactor is itself a real project, not a testing add-on.

It also tests the **scaffold**, not the model's reasoning quality. A layer can pass every pure-mode assertion while the LLM call feeding it drifts to worse answers in ways no deterministic case captures — that is still a job for LLM-judged evals or human review, run alongside this, not replaced by it. And it adds a maintenance surface: every new layer needs its own slice and its own baseline entry, or it silently becomes the "memory" row in this article's own CI example — present in the taxonomy, uncovered in the tests.

Three questions before you build this: **Does your agent's code actually separate into callable steps**, or would isolating one require a rewrite? **Do you have a mechanism (LLM-judge evals, human review, production monitoring) covering the reasoning quality this technique cannot see?** And **who owns updating the baseline** when a layer's correct behavior legitimately changes — an unowned baseline either goes stale or gets bypassed the first time it's inconvenient.
