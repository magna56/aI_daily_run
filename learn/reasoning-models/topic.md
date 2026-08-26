# How Reasoning Models Work

**Category**: New Models & APIs
**Tags**: training, cost
**Date**: 2026-08-23
**Level**: Building
**For**: How models work
**Hook**: A reasoning model is the same weights spending extra tokens before it answers — you buy quality with time and money.
**Kind**: Learn
**Time to read**: ~18 minutes

> **You'll be able to:** name which inference-time and training-time technique is actually doing the work when a product says "thinking," explain the shape of how DeepSeek-R1 was built, and know when more samples stop helping.

## Explain Like I'm 5

Sometimes you ask a friend a hard question and they sit quietly scribbling on scratch paper before they speak. They did not become a different person. They spent more time. The scratch paper still counts as talking — you wait, and you pay for the paper. "Think harder" in these products is that extra scribbling, not a new brain in the box.

## The Problem

Vendors ship a "reasoning" or "thinking" SKU next to a fast one. Teams treat the thinking SKU as strictly smarter and route everything to it. Bills jump. Latency jumps. Easy tickets get a three-page inner monologue. Hard tickets still fail if the prefix is missing the file. You did not buy a new capability class. You bought test-time compute — more tokens before the user-visible answer — and you applied it with a blunt default.

## For a Software Engineer

This is the same trade as turning on `-O3` or running a fuzzer longer: extra work at *request* time, same program. A reasoning model is usually the same (or sibling) weights with a training recipe that makes long scratchpad tokens likely, plus a product that hides those tokens or bills them on a different meter.

The number worth feeling: if the hidden chain is 2,000 tokens and the answer is 200, you paid for ~10× the generation of a direct reply — every time, including "rename this variable." That can be worth it on a gnarly proof or a multi-file root cause. It is waste on a format conversion.

Monday morning: split your traffic. Fast model / no thinking for tool routing, classify, commit messages, "what does this error mean?" Thinking SKU for tasks you would be willing to wait 30–60 seconds on and review. Cap thinking tokens if the API has a knob. Do not A/B "smarter" without measuring both quality *and* p95 latency.

## What This Means for You

**When this matters**: you are picking a default model in Cursor or an API router, and one option says it "thinks."

**How it affects you**: quality per dollar is a product choice. A reasoning default on a high-QPS agent will dominate the bill and still not read a file you never fetched (lesson 4).

**What to do about it**: make thinking an explicit mode, like "run the slow tests." Log thinking tokens separately. If the vendor hides the scratchpad, you still pay for it — read the usage fields.

## What It Is

At runtime it is still next-token prediction (lesson 1). The difference is *what tokens come first*. A reasoning model is trained (often with reinforcement on graded tasks) so that a long intermediate trace is a likely continuation. The product may stream that trace, hide it, or summarize it.

Test-time compute means: spend more inference to get a better answer from the same weights — sample longer, search, vote, or think. Training-time compute is a bigger or longer-trained model. They are not interchangeable. A small model thinking longer can beat a large model answering immediately on some math and code benches. It will not invent your private API.

"Extended thinking" sliders are usually a token budget on that scratchpad. They are temperature's cousin: a knob with a real cost, not a personality.

## Why It Matters

If you do not name the trade, someone will set the org default to the thinking SKU because the eval chart went up. Eval charts rarely include your p95 or your tool-call format. Reasoning is a different *product* — slower, pricier, sometimes better on hard items. Treat it like reserved instances vs on-demand, not like "the smart one."

## Key Technical Details

**Background first.** *Test-time compute* is extra inference per request. *Chain of thought* is intermediate tokens. *Reasoning model* is a checkpoint + product behavior that makes those tokens likely and (often) hidden.

- **Hidden tokens still bill.** Check `output_tokens` / thinking-specific fields, not just the visible reply.
- **Thinking does not replace tools.** A long scratchpad about a missing file is still a missing file.
- **Stop sequences and JSON mode still apply.** A reasoning model that rambles before `{` will break your parser unless you constrain it (lesson 2).
- **Caps exist for a reason.** Unlimited thinking is an unbounded loop with a nicer name.

## Inference-Time Techniques

Ways to spend more compute *per request* on already-trained weights, cheapest first:

- **Chain of thought** — write the reasoning out before the final answer, rather than jumping straight there. Measurably improves accuracy on multi-step problems, because the model cannot skip a step it has to write down.
- **Self-consistency** — sample several independent reasoning chains at non-zero temperature so they genuinely differ, then take the majority answer. Independent errors rarely agree with each other, so voting cancels most of them out even though no single sample got more reliable. This lesson's code example implements exactly this.
- **Tree of Thoughts** — instead of one linear chain, search a tree of partial thoughts: generate several candidate continuations, score which look promising, expand only those. Catches dead ends earlier than self-consistency, at the cost of far more calls per question.
- **Sequential revision** — generate an answer, then ask the model to critique and revise it in a following turn. Cheap, and it works — but an uncalibrated revision step can turn a *correct* answer wrong just as easily as it fixes a bad one.

## Training-Time Techniques

Ways the reasoning capability got *built into the weights* in the first place:

- **STaR (Self-Taught Reasoner)** — bootstraps reasoning without human-written rationales. The model generates a chain of thought for each training question; rationales that reach the correct final answer are kept and used to fine-tune it; the loop repeats. You never label *how* to reason, only whether the final answer was right.
- **Reward models — ORM vs PRM.** An Outcome Reward Model scores only the final answer. A Process Reward Model scores each intermediate step, catching a flawed step even when the model stumbles onto the right final answer anyway — denser signal, but step-level labels are far more expensive to collect.
- **Self-correction (SCoRe)** — trains a model, via RL on its own generated data, to genuinely improve an answer when given a chance to revise it. The objective specifically rewards a wrong-to-right correction, which is what prevents the failure mode of an unhelpful right-to-wrong flip that plain revision fine-tuning can produce.

## Case Study: How DeepSeek-R1 Was Built

The pipeline shape is the part worth remembering, more than any one stage:

1. **Cold-start fine-tuning** on a small set of human-readable chain-of-thought examples — this exists because the version *without* it reasoned well but produced language-mixed, poorly formatted output. A small warm start fixes readability before the big RL stage begins.
2. **Large-scale RL using GRPO** (Group Relative Policy Optimization). Its practical advantage over standard PPO: no separate learned critic model. For each prompt it samples a *group* of outputs, scores each with a rule-based reward, and trains on each output's reward relative to its group's average — roughly halving the memory and complexity of the RL loop. Most of the actual reasoning capability comes from this stage.
3. **Rejection sampling plus supervised fine-tuning** — the RL model generates a large volume of reasoning data, only the correct and well-formatted samples are kept, combined with general data, and used for another SFT round to broaden the model past pure math/code/logic.
4. **A final RL pass** aligning for helpfulness and harmlessness, so the released model is not narrowly a reasoning specialist.

**The emergent part worth knowing:** during stage 2, average response length for hard problems *increased over training* without anyone targeting length directly — the model learned that spending more tokens on harder problems paid off in reward. Behaviours resembling self-reflection and backtracking appeared the same way, from the reward signal alone. A pure rule-based reward (correctness plus format) was used deliberately rather than a learned one, because a learned reward model is itself exploitable — a policy can learn to game a learned reward in ways a simple correctness check cannot be gamed.

The reasoning traces from the RL-trained model were also used to fine-tune much smaller dense models, which recovered a large fraction of the improvement at a fraction of the size — reasoning ability transfers through distillation more cheaply than it can be trained from scratch in something small.

## Train Bigger, or Think Longer?

For a fixed compute budget you can spend it upfront (a larger model, more pretraining) or per-query (more inference-time sampling on a smaller one), and the right split depends on the question's difficulty:

- **Easy to medium:** a smaller model given room to sample multiple attempts and vote frequently matches or beats a much larger model that only answers once — there is a real chance of hitting the right answer on repeated tries.
- **Genuinely hard:** no amount of extra sampling rescues a model that cannot solve the problem at all — every sample is wrong for the same underlying reason, so voting over wrong answers does not produce a right one. Here the larger or better-trained model wins outright.

This is measurable, not philosophical — it is exactly what this lesson's code example shows: the routing table below finds the point where more samples stop helping and the fast model wins on cost with no accuracy left on the table.

"Deep research" products apply this same machinery inside an external loop — search, read, decide if you know enough, repeat — and the orchestrator-workers pattern from [How the Agent Loop Works](#learn/the-agent-loop) is exactly the multi-agent version of it: a lead agent splits the question into independent sub-questions, spawns one focused sub-agent per slice, and synthesizes their condensed briefs rather than reading everyone's raw search results itself.

## Quick Reference

| Term | Plain English |
|---|---|
| Test-time compute | Extra inference spent on one request, on the same weights. |
| Training-time compute | A bigger or longer-trained model. Not interchangeable with the above. |
| Chain of thought | Intermediate reasoning tokens written before the final answer. |
| Self-consistency | Sample several reasoning chains, take the majority answer. |
| Tree of Thoughts | Search a tree of partial thoughts instead of one linear chain. |
| ORM / PRM | Reward the final answer only, vs reward every intermediate step. |
| GRPO | Group-relative RL that scores a batch of outputs against their own average — no critic model needed. |
| Distillation | Training a small model on a large model's reasoning traces. |
| Thinking budget | A cap on how many scratchpad tokens a request may spend. |

## Do It Today

**Step 1 — see the routing table pick the cheap model correctly, 2 minutes.**

```bash
python3 learn/reasoning-models/code_example.py
```

**You know it worked** when the easy-task row hits **100% at 4 steps for $0.0054**, the same hard task at **0 steps hits only 0.0244%** (the fast model, on the wrong tool), and 12 steps recovers **100% for $0.0150 at 25 seconds**. That is the whole trade-off in three rows: the fast model fails a hard task outright, not partially, and thinking is what buys the fix.

**Step 2 — find one place in your own workflow that reaches for the thinking SKU by default.** Ask whether the task is genuinely open-ended (worth it) or a format conversion / classification (waste). Split that traffic explicitly.

**Step 3 — if your API exposes a thinking-token field, log it separately from output tokens for one week.** Hidden reasoning tokens still bill; you cannot manage a cost you are not measuring.

## Gotchas

- **Hidden tokens still bill.** Check `output_tokens` or the thinking-specific usage field, not just the visible reply length.
- **Thinking does not replace tools.** A long scratchpad about a missing file is still a missing file — reasoning cannot invent data it was never given.
- **Stop sequences and JSON mode still apply.** A model that rambles before `{` breaks your parser unless the output is constrained (lesson 2).
- **Self-consistency needs genuine variance.** Sampling at temperature 0 for "several independent chains" just gets you the same chain N times — the voting buys nothing.
- **A learned reward model is exploitable.** That is why R1's RL stage deliberately used rule-based rewards instead — a policy can learn to game a learned judge in ways a simple correctness check cannot be gamed.
- **Caps exist for a reason.** Unlimited thinking is an unbounded loop with a nicer name.

## How It Connects to What You Know

You already buy latency with more CPU on a request — this is that, billed per token. GRPO's group-relative scoring is the same idea as A/B testing against a control that moves with you instead of a fixed baseline. Speculative decoding and cascades (cheaper model first, escalate on failure) are the other side of the same budget: spend inference where it is likely to pay off, not everywhere.

Previous: [How the Agent Loop Works](#learn/the-agent-loop). Next: [How the Forward Pass Runs](#learn/how-the-forward-pass-runs).
