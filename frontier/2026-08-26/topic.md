# How a Coding-Agent Harness Learns to Patch Itself

**Category**: Building Agents & MCP
**Tags**: agents, reliability, paper, production
**Date**: 2026-08-26
**Level**: Deeper
**For**: Building agents
**Hook**: A research harness rewrites its own prompts and tools after every batch of failures — but the single biggest reason it works is the step that throws most of those rewrites away.
**Time to read**: ~12 minutes

## Explain Like I'm 5

A coach watches game tape after every match and tries a new play based on what went wrong. A bad coach starts running the new play in the very next real game. A good coach tries it in practice first, against a different set of drills than the one that inspired it, and only keeps it if it still works there. Most of coaching is not inventing plays. It is refusing to trust a play that only looked good once.

## The Problem

Teams that hand-tune a coding agent's prompts and tools do it the bad-coach way: something breaks, someone edits the system prompt or the tool description to fix that specific failure, and the patch ships straight into the next session. It usually works on the case that prompted it. Whether it also breaks something that used to work is rarely checked, because checking means building and running a second set of tasks the patch was never written for — extra work most teams skip under deadline.

A Microsoft Research team measured exactly how much that skipped step costs. In their harness-patching pipeline, removing the held-out validation check — keeping every patch that merely looked better on the failures that motivated it — dropped their agent's accuracy on GAIA2 from 62.0% to 50.6% Pass@1. Eleven and a half points, from one missing gate. That is a bigger swing than the two other techniques in the paper combined.

## How the Harness Learns From Its Own Failures

AutoSaddler treats improving a coding-agent harness as an offline learning loop, not a series of one-off edits. Each round: run the current harness on a small batch of tasks, look hard at what failed, propose one change, and only keep that change if it clears two separate bars.

### The Loop, One Round at a Time

Given harness `H_n`, a round does five things. **Evaluate** — run `H_n` on a mini-batch `B_n` of tasks, recording full execution traces for both successes and failures. **Diagnose** — an LLM agent with file-system access reads those traces, the harness's own source, and "progressively retrieve[s] relevant trace details" to find "the suspected root cause," not just the surface symptom. **Patch** — the diagnosis agent proposes one structured change and produces `H'_n`. **Gate** — check whether the patch actually helps, twice (below). **Remember** — whichever way the gate went, log what happened so the next round's diagnosis has that history to draw on.

### The Three Patch Types

A patch is not a free-form edit — it is typed, which is what makes it inspectable and reversible. The paper's own taxonomy: **prompt patches** — "add or modify behavioral rules in the system prompt," "modify tool docstrings to avoid tool misuse"; **tool patches** — "add a new tool when no existing tool supports the required action," "fix bugs or extend internal tool functionality"; **middleware patches** — "inject a just-in-time reminder before a specific tool call," "modify agent configuration, iteration budget, or environment settings." Each further splits into **Capability** (an executable code change) or **Steering** (a textual edit) — a distinction that matters because Capability patches, despite being harder to generate, land far more often: 67–83% acceptance versus the bulk of unconstrained edits concentrating on the easier, weaker Steering type.

### Two Acceptance Gates, Not One

This is the mechanism the whole session hangs on. A patch is accepted only if **both** hold:

1. **Mini-batch improvement** — `J(H'_n)` on `B_n` beats `J(H_n)` on the same batch. Cheap to check, and the bar every naive patch-and-ship workflow already clears, because the patch was written *for* this batch.
2. **Development-set generalization** — the same patched harness is then run on a held-out set, `D_dev`, that had nothing to do with the failure that motivated the patch. Only a patch that clears *this* bar too gets kept.

Gate 1 alone answers "did this fix the thing I was looking at." Gate 2 answers the question that actually matters: "did fixing that break something else, or does the improvement hold up on tasks I wasn't thinking about."

### What the Ablations Prove

Three components, tested by removing each one and re-measuring GAIA2 Pass@1 against the full system's 62.0%: skip the deep, file-reading diagnosis and use a single shallow reflection instead — **57.8%**. Skip the structured prompt/tool/middleware taxonomy and let the agent edit anything unconstrained — **56.9%**. Skip the development-set gate and keep any patch that improved its own mini-batch — **50.6%**, the largest drop of the three, and the regression rate across rounds flips sign: it *decreases* roughly 0.24 points per iteration with the gate in place, and *increases* about 0.16 points per iteration without it. The gate is not tuning the system. It is the difference between the system converging and the system drifting.

## For a Software Engineer

This is a held-out test set applied to prompt engineering instead of code. You already refuse to ship a bug fix that only passes the one regression test that reproduced the bug — you run the whole suite, because a fix scoped to one failure can break something the failing test never touched. Nothing here is a new idea; it is that same discipline, pointed at the file most teams still edit by feel.

**Monday morning:** if you or your team hand-edit your agent's system prompt, tool descriptions, or middleware based on the last failure someone reported, you almost certainly have gate 1 (does the fix look right) and almost certainly do not have gate 2 (does it hold on tasks unrelated to the failure). Building even a five-task held-out set you check every prompt change against, by hand, before merging it, buys most of the 11-point gap this paper measured — before you automate a single line of the diagnosis or patch-generation.

## What This Means for You

**When this matters:** your coding agent's prompt, tool set, or middleware keeps getting patched in response to the latest complaint, and every few weeks something that used to work quietly stops.

**How it affects you:** each ungated patch is a coin flip whose downside you cannot see until later, and they compound — a harness patched ten times without a generalization check is not ten times better, because some of those ten patches are actively fighting each other.

**What to do about it:** carve out a small, fixed set of tasks that represent your harness's normal operating range — not the failure you're currently chasing — and run every prompt, tool, or middleware change against it before merging, the same way you would not merge code without running the test suite. If your team already automates any part of this, look at the `optimization` section of a config-driven version — [AutoSaddler's own config](https://github.com/microsoft/AutoSaddler) splits "task selection, acceptance, development gate, ranking, budget, retries" into one place precisely so the gate is a setting, not a step someone has to remember.

## Implementing It

**The change.** Two roles, because a real deployment of this idea needs both a loop that proposes patches and a rule that decides whether to keep them — and the rule is the part worth getting right first, per the ablation above.

*Patch reviewer — the two-gate acceptance rule itself.* This is the entire mechanism that separated 62.0% from 50.6% in the paper, and it is small enough to write down completely:

```python
def should_accept(score_before, score_after, batch_delta_ok, dev_delta_ok):
    """Both gates must hold. Either alone reproduces the paper's weaker
    ablations -- batch-only overfits the failure that motivated the patch."""
    return batch_delta_ok(score_before, score_after) and dev_delta_ok
```

If you build nothing else from this session, build the version of this that runs by hand: keep your held-out set, re-run it after every prompt change, and require both "the failure I was chasing is fixed" and "the held-out set didn't regress" before you merge.

*Loop author — where the gate sits in the round.* `code_example.py` implements the full five-stage loop from `How the Harness Learns From Its Own Failures` above as a toy: a tiny synthetic harness with prompt/tool/middleware knobs, a mini-batch and a disjoint dev-set of tasks, a diagnosis step that proposes one of the three patch types, and `should_accept` gating each proposal exactly as described. It is not the paper's LLM-based diagnosis agent — that needs a real model and a real codebase to read — it is the *control loop* around that agent, which is the part you can validate without one.

**How you know it worked.** Run `code_example.py` and watch two patches go through the same gate. The shallow patch — it memorizes the exact task IDs that failed instead of learning what they needed — passes gate 1 (`batch_ok=True`) in **every** round and fails gate 2 (`dev_ok=False`) in every round too, printed as `REJECTED (overfits mini-batch)` four times in a row; its dev-set score never moves off its starting **20%**. The deep-diagnosis patch clears both gates on round 0 and the harness's dev-set score jumps to **100%** and stays there. The final held-out-test comparison — tasks neither loop ever saw — makes the gap impossible to miss: **0% for the memorized patch, 100% for the one that generalized**. If your own patch-review process cannot produce that same before/after number on a set of tasks nobody wrote the patch for, you have gate 1 only — the weaker half of this mechanism.

## When This Is the Wrong Tool

Do not build the automated diagnosis-and-patch-generation half of this before you have the gate. Automating patch *proposal* without a development-set check just proposes overfit patches faster — you would be automating the exact failure mode the paper's own ablation shows costs the most. Get the two-gate discipline working by hand first, even manually, before spending engineering effort on the agent that writes patches for you.

This is also expensive relative to just editing a prompt: a full round costs a mini-batch of task runs, an LLM diagnosis call with codebase access, a candidate patch run on the same mini-batch, and — the gate that matters most — another run on a held-out set. For a small team maintaining one internal agent, that is a lot of infrastructure to stand up for what might be a once-a-month prompt tweak. The paper's own numbers argue for the *discipline* — two gates, not one — long before they argue for the *automation*.

Three questions before you build any of this: **Do you have a held-out task set that is genuinely disjoint from whatever surfaced your last failure**, or does your "regression check" quietly reuse the same cases you were already looking at? **Is your patch typed** — prompt, tool, or middleware, capability or steering — or is it an unconstrained edit that makes the *next* diagnosis harder to reason about, the way the paper's own ablation shows unconstrained editing costs 5 points on its own? **Are you tracking whether your regression rate is trending down over time**, or only reacting to whichever failure was reported most recently?
