# How to Catch the Broken Step Your Agent's Tests Miss

**Category**: Evals & Reliability
**Tags**: reliability, benchmarks, agents, paper
**Date**: 2026-08-27
**Level**: Building
**For**: Shipping AI
**Hook**: An AI agent's overall pass rate can barely move while one whole step inside it stops working completely — unless you test that step on its own.
**Time to read**: ~8 minutes

## Explain Like I'm 5

Imagine your school gave you one overall grade for the semester instead of a grade per class. Ace four classes, completely fail the fifth, and your overall grade barely moves — the report card still looks fine. Nobody glancing at that one number would guess you failed an entire subject. The only way to catch it is to look at each class on its own. That's the whole idea, applied to software instead of students.

## The Problem

A team running an AI ordering agent watches one number after every release: the percentage of end-to-end test conversations that finish correctly. It holds steady for weeks. Then a support ticket lands — the agent stopped escalating high-value orders for human review a fortnight ago, and has been quietly auto-approving them ever since.

The regression was in the eval suite the whole time. It just never moved the number anyone was watching. A single pass rate averages every kind of conversation a customer might have, and escalation only fires on a narrow slice of them — orders over a spend limit, orders flagged for fraud. Break it completely and most test conversations never touch that path, so the score that broke doesn't look broken.

An average is very good at hiding something that only happens sometimes.

## How Layer-Isolated Testing Catches What the Average Hides

A June 2026 paper (arXiv:2606.11686) measures this on a deployed ordering agent. The fix: stop grading the agent once, and grade each step separately.

### One Slice Per Layer

The paper splits its agent into eight layers. Three matter here: **escalation** decides when an order needs a human — the one that broke above; **ontology** turns a customer's words into a canonical product ID; the **out-of-distribution gate** rejects inputs the agent was never built for.

Each gets an **assertion slice**: test cases run in **pure mode** — the layer's own logic, called directly, LLM stubbed out entirely.

```python
def ontology_resolve(sku: str, broken: bool) -> str | None:
    return None if broken else CANON.get(sku)

# case: input "sku-42", expected output "CANON-COLA-42"
assert ontology_resolve("sku-42", broken=False) == "CANON-COLA-42"
```

"No LLM is invoked; a slice failure is a real contract violation," in the paper's words. Nothing to argue about, unlike an LLM judge scoring a free-form answer.

### The Locked Baseline

Each slice's pass rate is frozen into a **locked baseline** — a JSON record of `(total, passed, rate, failed_ids)`. The paper's is 238 cases across 23 slices, all at 100%, running in 2.39 seconds — fast enough for every pull request. CI diffs against it, and **any per-slice drop blocks the merge.** It also enforces **coverage honesty**: a slice with zero cases reports `null`, never `1.0`, so an untested layer can't look tested.

### The Masking Effect

To validate this, the authors broke one layer at a time — monkeypatching a single entry point. Across the seven non-safety layers:

| Layer regressed | Aggregate score moved | The matching slice moved |
| --- | --- | --- |
| OOD gate | −1.68 pp | −36.36 pp |
| Intent signals | −4.20 pp | −25.00 pp |
| Escalation | −4.62 pp | −50.00 pp |
| Defense scan | −5.04 pp | −63.16 pp |
| Reformulator | −5.88 pp | −80.00 pp |
| Decomposer | −5.88 pp | −90.91 pp |
| Ontology (foundational) | −26.47 pp | −95.24 pp |

Six of seven barely dent the aggregate — a wobble any team would read as noise — while the matching slice falls off a cliff. The outlier, ontology, is **foundational**: everything downstream needs a resolved product ID, so breaking it cascades and the average notices. A layer's *position* in the pipeline, not its importance, decides whether the average can hide it.

## For a Software Engineer

This is the per-endpoint alert argument. If `/checkout` throws 500s on every request but it's one endpoint of forty behind a single "overall API error rate," that metric moves by a fraction most on-call rotations would page right past. Nobody would monitor a multi-service API that way — yet it's exactly how most teams evaluate an agent: one task-success number standing in for eight layers of very different logic.

**The number worth feeling:** six of seven layer-breaking bugs moved the aggregate under six points while destroying 25 to 91 points of the slice that owned the bug. Ask whether your own dashboard could show a six-point wobble while something underneath it is dead.

## What This Means for You

**When this matters:** you run an agent or multi-step LLM pipeline, you watch one end-to-end success rate as your health signal, and it's been stable a while — which you've read as "nothing changed."

**How it affects you:** a stable aggregate is not proof the parts underneath still work. A rarely-exercised path — an escalation rule, a safety check, a malformed-input fallback — can regress completely without moving it. You find out from a support ticket, not CI.

**What to do about it:**
1. List the distinct steps your agent takes — "resolve entity," "decide tool," "validate output," "escalate or not." Most agents already have 4-8, named or not.
2. For each, write a few deterministic assertions calling that step directly, LLM bypassed. Shape is below.
3. Freeze today's per-step rates as your baseline, and gate CI on any step dropping — not just the aggregate.

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

It only works on layers with a clean, callable boundary you can invoke without a live model — so it assumes your code is already factored that way. A pipeline built as one long prompt has to be refactored first, and that refactor is a real project, not a testing add-on.

It also tests the **scaffold**, not reasoning quality. A layer can pass every pure-mode assertion while the LLM feeding it drifts to worse answers. That stays a job for LLM-judged evals or human review, run alongside this — never replaced by it.

Three questions first: **Does your code separate into callable steps**, or would isolating one require a rewrite? **What covers the reasoning quality this can't see?** And **who owns the baseline** when a layer's correct behavior legitimately changes — an unowned baseline goes stale or gets bypassed the first time it's inconvenient.
