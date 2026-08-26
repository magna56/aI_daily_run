# How the Agent Loop Works

**Category**: Building Agents & MCP
**Tags**: agents, mcp
**Date**: 2026-08-23
**Level**: Start here
**For**: Building agents
**Hook**: An agent is a loop that looks, decides, and calls a named tool. The name is the API.
**Kind**: Learn
**Time to read**: ~16 minutes

> **You'll be able to:** place any agentic system on a five-level ladder from a single call to multi-agent, pick the cheapest pattern that solves your actual task, and know why a tool's name is part of its contract, not a label you can freely change.

## Explain Like I'm 5

A helper who can only act by filling out forms: "read this file," "change these lines." The loop is simple — look, decide, fill a form, look again. If they were trained on *your company's* form and you hand them a different one, they keep writing the old field names. The work looks done. The form is invalid.

## The Problem

Anyone can write the observe-think-act loop in an afternoon. Teams then invent a nicer tool schema than the one the model was trained on, and newer models get *worse* at calling it. The failure is silent: extra fields, parse errors, retries that look like flakiness. People upgrade the model and the tools break.

## For a Software Engineer

An agent is a `while` loop with a cap. Observe (prefix + last tool result). Think (the model emits a thought or a tool call). Act (your code runs the named function and appends the result). Stop when it says it is done or you hit `max_iters`.

The tool list is not documentation. It is the surface area of the API the model can call. Names matter the way route paths matter. Models that were reinforced on a vendor's coding agent emit `edit_file(path, old_string, new_string)` or `apply_patch` with a unified diff. If your schema uses `mutate_buffer` with a different shape, the model is worse at filling it — and may invent fields from the schema it was trained on.

The number worth feeling: the 2026-07-05 lab is that failure in the wild — newer Claude models injected extra keys into a third-party edit array because Claude Code's schema had leaked into their reflexes. The loop was fine. The labels on the kitchen drawers were not.

Monday morning: keep the loop in one function you can print. Name tools after the verbs models already emit, or write a thin adapter. Use MCP to *expose* tools, not to replace the loop.

## What This Means for You

**When this matters**: you are wiring tools into an LLM, or a "better" model started failing your schema.

**How it affects you**: this is lock-in at the *behavior* layer, not the HTTP layer. Matching `path` / `old_string` / `new_string` is closer to matching a public contract the other side already implements than to taste.

**What to do about it**: log every observe / think / act line. When someone asks "why did it call `execute_command` twice?", the answer should be a log line, not a framework callback maze. Prefer trained names; adapt if you cannot.

## What It Is

**Observe** — build the prefix: system, tools, messages, last result.

**Think** — one model call. The output is either text (stop) or a structured tool call (name + arguments).

**Act** — dispatch on the name. Validate arguments in *your* code. Return a string the model will see next turn.

**MCP** (Model Context Protocol) is a standard way to list tools and call them over a process boundary — JSON-RPC, a server that says "I have `search_docs`." The host (Cursor, Claude Code) is the loop. MCP is the plugin bus. It does not think. It does not replace observe/think/act.

A tool schema is a JSON Schema (or equivalent) the model sees in the prefix. That is why a hundred tools are expensive (lesson 7): they sit at the front and are re-read every turn.

## Why It Matters

Frameworks hide the cycle and then you cannot debug it. The 2026-07-05 `llm-coding-agent` write-up is ~500 lines because the authors refused to hide it. Once the loop is visible, the remaining hard part is the contract — names, required fields, what happens on a bad call. Lesson 9 is when "think longer" is a different product. This lesson is the kitchen.

## Key Technical Details

**Background first.** *Tool calling* means the model emits a structured call instead of (or before) user-facing text. *MCP* is a host/server protocol for exposing those tools. *Schema trap* means the model's likely arguments match a vendor's tools, not yours.

- **Cap the loop.** `max_iters` is a fuse. Infinite observe/act is a bill.
- **Validate in code.** Shape checks belong in the act step. Lesson-adjacent: 2026-07-09 puts policy gates in front of the call.
- **One result, one observation.** Do not swallow errors. The model cannot fix what it cannot see.
- **MCP is transport.** If you do not have a loop, a server does nothing.

## Five Levels of Agency

Every system built on a model sits somewhere on this ladder, and the ladder is also a cost curve:

| Level | What it is | Who controls the flow |
|---|---|---|
| **1 — Single call** | One prompt, one response | You. Entirely. |
| **2 — Workflows** | Multiple calls wired together with code you wrote | You. The model fills in steps. |
| **3 — Tool use** | The model can call functions and read the results | Shared. You define the tools. |
| **4 — Agents** | The model loops, deciding each next action itself | The model, within your limits. |
| **5 — Multi-agent** | Several agents delegating to each other | Emergent. Hardest to predict. |

**The boundary that matters is between 2 and 4.** At level 2 the control flow is in your source code — readable, testable, and its worst-case cost is boundable. At level 4 the control flow *is* a model output, so none of that holds. That is a genuine engineering trade-off, not a maturity ladder to climb — plenty of excellent production systems are deliberately level 2 and stay there on purpose.

## Workflow Patterns — Level 2, Control Flow in Your Code

Five shapes cover nearly everything at this level:

- **Prompt chaining** — a fixed sequence, each step feeding the next. Reliable because nothing can deviate from the path you wrote. Slow.
- **Routing** — classify the input, dispatch to a specialist handler. Cheap (2 calls), but a silent misclassification sends the whole request down the wrong branch.
- **Parallelization** — fan out independent subtasks and join. Either *sectioning* (different subtasks, combine the pieces) or *voting* (the same task N times, take the majority).
- **Evaluator-optimizer** — generate, grade against criteria, regenerate if it falls short. Only works when the evaluation criteria are crisp; a vague grader just adds cost and latency.
- **Orchestrator-workers** — a coordinator decomposes the task, workers handle the pieces, the coordinator synthesizes. Right when you don't know the task shape up front — but a bad decomposition can't be rescued downstream.

## Agent Patterns — Level 4, the Loop Decides

Where the observe/think/act loop this lesson opened with actually lives, and how much each variant commits to up front:

- **ReAct** — the loop above, run to completion: reason, act, observe, repeat until done. Handles open-ended tasks well. Expensive, and **can loop forever** without a hard turn cap.
- **Reflexion** — attempt, evaluate (ideally automatically — run the tests), write down what went wrong, retry with that reflection in context. Excellent for code generation where correctness is machine-checkable; weak without a real evaluator.
- **ReWOO** (Reasoning Without Observation) — plan the *entire* sequence of tool calls up front, execute them all, synthesize once. Two model calls total, regardless of step count — far cheaper than ReAct because nothing re-invokes the model between steps. The trade: it cannot adapt mid-execution, so every step must be genuinely independent of the others' results.
- **Tree search** — explore multiple action paths, score, prune, expand the promising ones. The most expensive pattern here by a wide margin. Reserve it for problems where a wrong early step is unrecoverable and worth paying to avoid.

## Pattern Comparison

| Pattern | Calls | Best for | Trade-off |
|---|---|---|---|
| Prompt chaining | N | Known multi-step tasks | Slow but reliable |
| Routing | 2 | Distinct categories | Misclassification risk |
| Parallelization | N | Independent subtasks | Can't share state |
| Evaluator-optimizer | 2–6 | Refinable outputs | Needs a crisp evaluator |
| Orchestrator-workers | N+2 | Unknown task shape | Plan quality is the bottleneck |
| ReAct | N | Open-ended tasks | Expensive, can loop forever |
| Reflexion | 2–3/attempt | Testable output | Needs automated evaluation |
| ReWOO | 2 total | Independent steps | Can't adapt mid-execution |
| Tree search | N × branches | Hard, high-stakes problems | Most expensive |

## Multi-Agent — Level 5

**Handoffs** transfer control from one agent to another: mechanically, a tool call that happens to return another agent, which demystifies it — a handoff is just a function that returns an `Agent`. **A2A** standardizes discovery and communication between agents from different systems the way MCP standardizes agent-to-tool.

Multi-agent buys parallelism and context isolation — each agent works in its own window, so bulky intermediate work does not pollute the others. It costs coordination: overlapping findings, contradictory conclusions, and the burden of reconciling them at the end. Lesson 9 covers the same trade for research agents specifically.

## The Decision Hierarchy

Work down this list and stop at the first "yes" — the default failure mode in this whole space is starting near the bottom:

```
Can one good prompt do it?              → do that. Most tasks stop here.
Do you know the steps in advance?       → workflow pattern. Control flow in your code.
Are the steps knowable but independent? → ReWOO. Plan once, execute, synthesize.
Is the output machine-checkable?        → Reflexion. Let the tests be the evaluator.
Is the task genuinely open-ended?       → ReAct, with a hard turn cap.
Big enough to decompose and parallelize?→ orchestrator-workers or multi-agent,
                                           and budget for the synthesis cost.
```

## Quick Reference

| Term | Plain English |
|---|---|
| Agent loop | Observe → think → act → observe, with a stop condition. |
| Tool | A named function the model can request; your code executes it. |
| Schema | The argument contract for a tool. Part of its API, not documentation. |
| MCP | A protocol for listing and calling tools over a process boundary. |
| ReAct | Reason, act, observe, repeat until done. The canonical agent loop. |
| ReWOO | Plan the whole tool-call sequence up front; two model calls total. |
| Reflexion | Attempt, evaluate, retry with the evaluation in context. |
| Orchestrator-workers | A coordinator decomposes; workers execute; coordinator synthesizes. |
| Handoff | A tool call that returns another agent. |

## Do It Today

**Step 1 — watch a renamed tool break the loop, 2 minutes.**

```bash
python3 learn/the-agent-loop/code_example.py
```

It runs the same observe/think/act loop three ways: matching tool name, a renamed tool, and MCP's `tools/list` + `tools/call` still using the matched name. **You know it worked** when the matching-name run and the MCP run both succeed and produce `debug = True → debug = False`, while the renamed-tool run fails with `schema miss: 'edit_file' not in [mutate_buffer]` — the loop itself never changed between runs; only the name did.

**Step 2 — place one system you use or are building on the five-level ladder.** Say out loud whether the control flow is in your code (level ≤ 2) or in a model's decision (level 4+), and whether that's a deliberate choice or an accident of which framework you picked first.

**Step 3 — run your own task through the decision hierarchy**, top to bottom, and stop at the first "yes." If you land on ReAct, write down the turn cap before you write anything else — it is the one line that turns "can loop forever" into a bounded cost.

## Gotchas

- **A tool's name is part of its contract, not a label.** A model reinforced on a vendor's coding agent emits that vendor's verbs; renaming your tool to something cleaner can make a *better* model worse at calling it.
- **ReAct without a turn cap is not a loop, it's a liability.** `max_iters` is a fuse, not an optimization.
- **A vague evaluator in evaluator-optimizer just adds cost.** If you cannot state the grading criteria crisply, this pattern will loop and still not converge on quality.
- **ReWOO's cheapness has a condition attached.** It only works when steps are genuinely independent of each other's results — the moment step 3 needs to see step 2's output before it can be planned, ReWOO cannot express that.
- **Multi-agent is not a free upgrade from single-agent.** It buys isolation and parallelism, and it costs a synthesis step that has to reconcile agents that may disagree.

## How It Connects to What You Know

A worker that reads a queue, calls a service by name, writes the result — the name *is* the API, the way a route path is. MCP is microservices for tools; the loop is the worker. The five-level ladder is the same shape as the classic build vs buy vs delegate decision: more autonomy is not automatically better, it is a trade you make on purpose or by accident.

Previous: [How the Chat Is Re-Read Every Turn](#learn/context-and-harness). Next: [How Reasoning Models Work](#learn/reasoning-models).

Lab: [Building coding agents from scratch — and the tool schema trap](#2026-07-05).
