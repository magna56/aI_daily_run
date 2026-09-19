# What Actually Makes a Coding Agent Better: Planning, Tools, or Context?

**Category**: Applied Research
**Tags**: benchmarks, cost, paper
**Date**: 2026-09-19
**Level**: Deeper
**For**: Building agents
**Hook**: The same harness change that rescues a weaker model only costs a stronger one money. Which knob to turn depends on which model is behind it.
**Engineer's view**: This is the wrapper you built so the team could not get SQL wrong. Juniors got faster. Seniors routed around it, because raw SQL was shorter, and you maintained both for a year. A rich tool API is that wrapper: it rescues a model with weak shell skills and taxes one that never needed it.
**TLDR**: Three harness components were measured separately, and they do different jobs. Only one makes an agent more accurate, and it is not the one people tune.
**Time to read**: ~11 minutes

## Explain Like I'm 5

Think of teaching someone to cook in your kitchen. You can write the steps out for them, hand them special gadgets, or keep tidying the counter so there is room to work.

For a beginner, the written steps help most. The gadgets help too, because they cannot chop well yet.

For a chef, the steps just slow them down, and the gadgets are worse than a knife they already know. Tidying the counter still helps both, because when the counter fills up everything stops.

## The Problem

You have shipped this one. You built a wrapper so nobody on the team could get the database call wrong: a small API, safe defaults, no raw SQL. The juniors got noticeably faster.

The seniors routed around it within a month, because the raw query was four lines and yours was a lookup in your docs. You maintained both for a year.

Harness design has the same shape, and almost all published advice ignores it. A coding agent is a model plus the scaffolding around it: how work is planned, which actions it can take, how the transcript is kept under control. That scaffolding gets evaluated as one lump. A harness wins on a benchmark, people copy the whole thing, and nobody knows which part did the work.

So the advice travels as though it were universal. Give the agent rich tools. Make it plan first. Summarize aggressively. Each of those is genuinely good advice for some model, and dead weight for another, and the write-up rarely says which.

A paper published on 17 September takes the lump apart. Fan, Zhang, Ma and five co-authors hold the execution loop fixed and vary exactly three things: planning, action space, and context management. That runs across four models, two benchmarks, and 176 matched settings. The finding is not that one design wins. It is that the three components do **three different jobs**, and only one of them is really about accuracy.

```figure
{ "kind": "system",
  "title": "The whole argument: three knobs, three different effects",
  "lanes": [
    { "t": "you can change", "nodes": [
        { "id": "ctx", "t": "context management", "s": "ok" },
        { "id": "plan", "t": "planning", "s": "new" },
        { "id": "act", "t": "action space", "s": "new" } ] },
    { "t": "and it changes", "nodes": [
        { "id": "far", "t": "how far the run gets", "s": "ok" },
        { "id": "stop", "t": "where the run stops", "s": "new" },
        { "id": "grain", "t": "how code gets written", "s": "new" } ] },
    { "t": "which mostly buys", "nodes": [
        { "id": "acc", "t": "fewer failed runs", "s": "ok" },
        { "id": "cost", "t": "lower cost, same accuracy", "s": "neutral" } ] }
  ],
  "edges": [
    { "from": "ctx", "to": "far", "s": "ok" },
    { "from": "plan", "to": "stop", "s": "new" },
    { "from": "act", "to": "grain", "s": "new" },
    { "from": "far", "to": "acc", "t": "stops overflow", "s": "ok" },
    { "from": "stop", "to": "cost", "s": "neutral" },
    { "from": "grain", "to": "cost", "s": "neutral" } ],
  "note": "Two of the three knobs move money, not correctness. Tuning them for accuracy is tuning the wrong thing." }
```

## The Fix: Vary One Component at a Time, Against Your Own Model

The setup is the contribution. One harness, one fixed loop, and only three things allowed to move.

Matched is the word doing the work. Every setting differs from its neighbor in one component, so a difference in the result belongs to that component.

### Why does context management help at all?

Not for the reason usually given. Its value rises as the context-window budget tightens, and **most of the benefit comes from preventing context-overflow failures**. It is not making the agent smarter with better-curated context. It is stopping the run from dying.

That reframes it. Context management is reliability engineering, not prompt engineering. Its payoff sits entirely in the runs that would otherwise have crashed.

### What order should the context pipeline run in?

Rule-based elision first, LLM summarization second. Staging them in that order gave the strongest overall efficiency of the five strategies tested. Cheap deterministic cuts remove the bulk, and the expensive model call only handles what is left.

The negative result next to it is the more useful one. **Making elided content recoverable — letting the agent ask for what was cut — added machinery the models rarely used, and produced no accuracy gain.** That is an afternoon of work most harness authors would happily spend. The paper says do not.

### When does planning stop paying for accuracy?

When the model gets good enough. Planning **shifts from an accuracy scaffold for weaker models to a cost saver for stronger ones**, with little change in accuracy either way.

The trajectory analysis says why: planning changes *where trajectories stop*. A strong model with a plan stops sooner, because it wanders less before deciding it is done. Same answer, fewer turns.

### Should I give the model fewer tools?

Possibly, and this is the one that inverts. **Predefined tools improve performance for models with weaker bash proficiency. Bash-capable models operate effectively with a bash-only interface and reach substantially lower cost**, especially on command-line-centric tasks.

A rich tool API is scaffolding. It rescues a model that cannot drive a shell. It charges one that can, in schema tokens on every turn and in a coarser unit of work.

## What This Means for You

**When this matters.** It matters whenever you copy a harness design from someone whose model is not yours. The advice that a rich tool layer or a planning step is good practice was true of the setup it was measured on, and the paper's point is that the sign of the effect changes with model strength.

**How it affects you.** Two of the three knobs mostly move cost rather than correctness. Tune planning or your tool layer hoping for accuracy and the expected gain is near zero on a strong model. You will read the noise as signal, because agent runs are expensive and you will not do enough of them.

**What to do about it.** Start with the one measurement that needs no redesign. Count how many of your agent's runs end because the context filled up, rather than because the task finished or failed honestly:

```bash
# overflow deaths vs honest endings, from your own agent logs
grep -c "context.*limit\|max_tokens\|context_length_exceeded" agent-runs.log
```

If that number is more than a few percent of runs, context management is your highest-value change and the other two knobs are a distraction. If it is near zero, you have already solved the accuracy half, and planning and tools are cost decisions you should evaluate on the bill rather than the score.

## Implementing It

**The change.** Three roles, and the first one covers most readers.

*Role 1: whoever owns the context pipeline.* Put the cheap deterministic pass before the model call, not after, and do not build the recovery affordance:

```python
def compact(transcript, budget, summarize):
    """Rule-based elision first, LLM summarization second. The ordering is the
    finding: deterministic cuts remove the bulk for free, so the expensive call
    only sees what survived."""
    kept = [m for m in transcript if not elidable(m)]          # stage 1: free
    if tokens(kept) <= budget:
        return kept
    head, tail = kept[:2], kept[-6:]                            # never summarize these
    middle = summarize(kept[2:-6], budget - tokens(head + tail))  # stage 2: paid
    return head + [middle] + tail

def elidable(m):
    # the deterministic rules: superseded file reads, duplicate tool output,
    # stack traces already acted on. No model judgment required.
    return m.get("role") == "tool" and m.get("superseded_by") is not None
```

Skip the "expand what was cut" tool. The paper tested exactly that and found models rarely reached for it and accuracy did not move, so it is machinery to maintain for no return.

*Role 2: whoever picks the action space.* Decide it per model, not once. The test is whether your model can actually drive a shell, and that is measurable in an afternoon:

```python
ACTION_SPACE = "bash_only" if model.bash_fluent else "predefined_tools"
# bash_fluent: run 30 command-line-centric tasks with a bash-only harness and
# compare pass rate against the predefined-tool harness. If it holds, keep
# bash-only — the schema tokens for a rich tool layer are charged every turn.
```

*Role 3: whoever runs the evaluation.* Change one component per run and hold the loop fixed. That is the design that makes any of this readable. A sweep varying planning and the tool layer together cannot tell you which one moved the number, and that is the state most internal harness evaluations are in.

The four models and two benchmarks are what let the paper say the effects change sign with model strength. You do not need that breadth. You need two configurations of your own model and enough runs that the difference clears the noise, which on agent tasks is usually more runs than anyone budgets for.

**How you know it worked.** Split your metric in two before you change anything, because the whole point is that these knobs act on different things. Track **overflow failures** and **cost per solved task** separately from pass rate.

A context change should cut overflow failures and leave pass rate roughly alone. A planning or action-space change on a strong model should cut cost per solved task and leave pass rate alone. If you only watch pass rate, all three changes look like noise, and you will conclude the harness does not matter when what actually happened is that you measured the one quantity none of them moves.

## When Component-Level Harness Tuning Is the Wrong Tool

It is the wrong tool when your agent is not failing on long tasks. All of this is about long-horizon work where transcripts grow and runs die of their own length. If your agent answers in three turns, none of these knobs has anything to act on.

It is also a lot of evaluation for the size of the prize. Matched settings mean many runs, and agent runs are slow and expensive. Before committing to a sweep, check that the gap between your best and worst current configuration is even worth the compute you would spend measuring it.

And the result is bounded in ways worth respecting. Four models, two benchmarks, one fixed execution loop. The loop being fixed is what makes the components comparable. It also means nothing here tells you whether a different loop would beat all 176 settings. The abstract also reports these as directions rather than deltas, so treat the signs as transferable and the magnitudes as belonging to that setup.

Three questions before you start:

- What fraction of my runs die of context overflow rather than finishing?
- Can my model drive a shell, or am I paying for tools that compensate for one that cannot?
- Am I tuning for accuracy on a knob that the paper says only moves cost?

## Glossary

- **harness** — everything around the model: the loop, the tools, the planning step, the transcript management
- **action space** — the set of actions the agent may take, from a rich tool API down to bash only
- **context management** — keeping the transcript under the budget so a long run does not die of its own length
- **elision** — cutting content by deterministic rule rather than asking a model to summarize it
- **matched settings** — evaluation runs that differ in exactly one component, so a difference is attributable
- **long-horizon** — a task taking many turns, where the transcript grows enough to become the binding constraint
