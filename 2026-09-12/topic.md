# Why a Model Fixes the Gap It Cannot Find

**Category**: Evals & Reliability
**Tags**: benchmarks, reliability, coding-agents
**Date**: 2026-09-12
**Level**: Building
**For**: Shipping AI
**Hook**: Asked to find what is missing from a specification, the best model finds about one gap in ten. Handed the same gap, it resolves four out of five. Noticing and fixing are not the same skill, and only one of them is weak.
**Engineer's view**: You have handed someone a ticket and got back the wrong thing — not because they could not build it, but because they never noticed it was ambiguous and filled the hole with a guess. Ask if anything is unclear and they say no. Point at the line and they ask the right question immediately.
**TLDR**: A model given an underspecified task rarely notices, but resolves the ambiguity well once it is pointed at. So the step worth building is the one that finds gaps, not the one that fills them.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine handing someone a recipe that never says what temperature to use. If you ask
"is anything missing here?", most people skim it and say it looks fine. If you point at the
line and ask "what temperature?", almost everyone says the right thing — check the recipe,
ask the author, use the usual number for this kind of cake. They could always answer. They
just never spotted that there was a question.

## The Problem

You have shipped this and no model was involved. You wrote a ticket, someone competent
picked it up, and what came back was wrong. Not badly built — built to a reading of the
ticket you had not considered. They hit the ambiguity, made a reasonable assumption, and
moved on. You asked afterwards whether anything had been unclear and they said no, because
by then it was not unclear to them.

Handing work to an agent has the same failure and a worse feedback loop. The agent does not
stall on a vague ticket. It picks a reading and produces confident, plausible output, and
the assumption it made is not written down anywhere you will look.

That is underspecification, and it is expensive precisely because it resolves silently. The
instinct is to fix it with a better model, or by asking it to flag anything unclear before
it starts. Researchers at Yale measured what that instinct is worth. They built a
benchmark of 660 specification gaps — 163 real ones pulled from reproducibility reports and
GitHub issues, plus 497 injected into otherwise complete references — and ran 13 models at
it.

**The fix is to stop asking the model to notice**, and to build the noticing step yourself.

## The Fix: Separate Finding the Gap From Filling It

The benchmark splits the job into two tasks that are usually run as one, and the results
come apart completely.

```figure
{ "kind": "bars",
  "title": "Two halves of the same job, measured separately",
  "bars": [
    { "label": "Find the gap", "v": 9.6, "d": "9.6%", "s": "bad" },
    { "label": "Fix it, once shown", "v": 80.6, "d": "80.6%", "s": "ok" }
  ],
  "note": "Best of 13 models, on the real-world half of the benchmark. Same model, same specs." }
```

**Defect localization** gives the model the specification alone and asks what is missing.
The best model recovers 9.6% of the real gaps. **Clarification action generation** gives it
the specification *and* the location of the gap, and asks what to do about it. The same
model succeeds 80.6% of the time.

That is not a small difference in one skill. It is two different skills, and only one of
them is weak.

### Does fixing the gaps actually help?

Yes, and by more than the numbers above suggest. The authors ran an oracle study: hand the model the correct resolution for every
specification gap and measure whether the text is now implementable without guessing.

```figure
{ "kind": "system",
  "title": "The whole argument: where the value is, and where it is not",
  "lanes": [
    { "t": "a spec as written", "nodes": [
        { "id": "spec", "t": "14% implementable" } ] },
    { "t": "ask the model to", "nodes": [
        { "id": "find", "t": "find its own gaps", "s": "bad" },
        { "id": "fix",  "t": "fix a gap you found", "s": "ok" } ] },
    { "t": "and you get", "nodes": [
        { "id": "little", "t": "9.6% of them", "s": "bad" },
        { "id": "lots",   "t": "98% implementable", "s": "new" } ] }
  ],
  "edges": [
    { "from": "spec", "to": "find" },
    { "from": "spec", "to": "fix", "t": "you localize", "s": "ok" },
    { "from": "find", "to": "little", "s": "bad" },
    { "from": "fix",  "to": "lots",   "s": "new" } ],
  "note": "The model is the wrong tool for one of these and close to sufficient for the other." }
```

Codification readiness goes from **14% to 98%**. So the gaps are the whole problem, the
resolutions are cheap once located, and the expensive step is the one nobody builds.

### Why is noticing so much harder than answering?

Because noticing requires holding a model of what *should* be there and comparing it against
what is. Answering only requires reasoning about a question already in front of you.

A specification that omits a learning rate does not contain a hole. It contains prose that
reads smoothly and happens not to mention one. Nothing in the text draws attention to the
absence, which is exactly why a reader skims past it — and why "is anything unclear?" is a
question that reliably returns no.

## What This Means for You

**When this matters.** You hand tasks to an agent as prose — a ticket, an issue, a design
note — and the agent produces work rather than questions. The more capable the agent, the
worse this gets, because a weaker model stalls visibly where a stronger one writes something
plausible.

**How it affects you.** It moves the effort somewhere unintuitive. The instinct is to
improve the prompt or the model; the measurement says the return is in the *detection* step,
which is the one part you can build without a model at all. A checklist of fields your
domain always needs will outperform asking a frontier model to introspect, because a
checklist compares against what should be there and the model does not.

It also tells you what to keep the model for. Once you can point at a gap, the model is
genuinely good — 80.6% — at proposing the right clarification. That is a real capability and
it is worth wiring up, just not the one you were about to rely on.

**What to do about it.**

1. Take your last ten agent tasks and check which ones the agent completed without asking
   anything. That number is usually all of them, and it is the problem.
2. Write down the fields a task in your domain cannot be done without. That list is short
   and you already know it.
3. Run the check structurally — absence of a field, not a model's opinion — and only then
   hand each gap to the model to phrase the question.
4. Log which gaps fire most often, and fix the template that keeps producing them.

## Implementing It

**The change.** Three pieces, and the first is deliberately not a model call.

*The detector.* Structural, cheap, and the part that carries the result:

```python
REQUIRED = {                      # what a task in your domain cannot be done without
    "bugfix":  ["repro", "expected", "scope"],
    "feature": ["motivation", "acceptance", "out_of_scope"],
}
CUES = {                          # how each field usually shows up in prose
    "repro":      ("steps to reproduce", "repro:", "to reproduce"),
    "expected":   ("expected", "should ", "when this is fixed"),
    "scope":      ("only", "do not touch", "limited to"),
    "motivation": ("because", "so that", "we need"),
    "acceptance": ("done when", "acceptance", "success looks like"),
    "out_of_scope": ("out of scope", "not in scope", "explicitly not"),
}

def gaps(task_text: str, kind: str) -> list[str]:
    body = task_text.lower()
    return [f for f in REQUIRED[kind]
            if not any(cue in body for cue in CUES[f])]
```

No model runs here, and that is the point: the detector compares against a list of what
should be present, which is the comparison the model cannot make. Keep `REQUIRED` short.
Every field you add fires on tasks that did not need it, and a detector that cries wolf is
one somebody turns off — which costs you more than the gaps it would have caught.

*The clarifier.* Now use the model, on the task it is good at — one gap at a time:

```python
PROMPT = """Task:
{task}

A required element is missing: {field}.
Write one question to the author that would resolve it. Ask only about {field}."""

def questions(task_text, kind, ask):
    return [ask(PROMPT.format(task=task_text, field=f)) for f in gaps(task_text, kind)]
```

One gap per call, named explicitly. Handing the model the whole task and asking "what is
unclear?" is the 9.6% path; handing it a located gap is the 80.6% path, and the difference
is entirely in what you put in the prompt.

*The gate.* Decide what happens when gaps exist, and make it visible:

```python
def start(task_text, kind, ask, block=False):
    missing = gaps(task_text, kind)
    if not missing:
        return "go"
    for q in questions(task_text, kind, ask):
        post_comment(q)                 # the questions a human would have asked
    return "blocked" if block else "go-with-assumptions"
```

Start with `block=False`. A detector that stops work on day one gets switched off by
lunchtime; one that posts the questions and lets the task proceed earns its place, and you
can tighten it once you see which gaps are real.

**How you know it worked.** Count the tasks where the agent asked something before starting.
That number is near zero today, and it going up is the whole result — you are converting
silent assumptions into visible questions.

The slower signal is rework. Compare how often agent output gets sent back for "not what I
meant" before and after. That is the failure this addresses, and it is the only measure that
says whether the questions were the right ones.

**When not to.** If your tasks already arrive on a template that enforces these fields, the
detector will fire on nothing and you have already solved this. Check before you build it.

## When Gap Detection Is the Wrong Thing to Build

A detector is a cost on every task, and it is worth being honest about where it does not pay.

Exploratory work is the clearest case. If the task is genuinely open — try something, see
what happens — there is no missing field, because there is no finished state to specify. A
checklist there produces noise, and noise on every task is how a check gets disabled.

It is also wrong when the answer is cheaper than the question. For a small, reversible
change, letting the agent assume and correcting it afterwards costs less than a round trip
to a human. Detection is worth most where the work is long or the mistake is expensive.

And the numbers come from research-method specifications, not your issue tracker. The
asymmetry between finding and fixing is the transferable part; 9.6% is not a figure to
forecast your own backlog with, and the synthetic half of the benchmark is injected gaps
rather than ones people really left.

Three questions before building one:

- Do my tasks have required fields I could actually name?
- Would I rather see a question before the work or a correction after it?
- Is the agent currently asking me anything at all, ever?

## Glossary

- **Specification gap** — something an implementer needs that the text does not say. It is
  an absence, which is why it does not attract attention when read.
- **Defect localization** — finding where a specification is underspecified, given only the
  specification. The weak half: 9.6% on real-world gaps.
- **Clarification action** — the question or resolution that closes a located gap. The
  strong half: 80.6% once the location is given.
- **Codification readiness** — whether a specification carries enough for a competent
  implementer to build the intended thing without unsupported assumptions.
- **Oracle study** — an experiment that hands the system the correct answers to isolate
  where the value sits. Here it moved readiness from 14% to 98%.
- **Underspecification** — a task that admits more than one correct implementation. The
  agent picks one silently, which is what makes it expensive.
