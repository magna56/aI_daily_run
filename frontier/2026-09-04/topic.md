# How to Compile a Prompt Into a Function You Can Ship

**Category**: Hands-on Techniques
**Tags**: distillation, fine-tuning, cost, paper
**Date**: 2026-09-04
**Level**: Building
**For**: Shipping AI
**Hook**: Some of the prompts you send on every request are not really prompts. They are fixed functions, and you can build one into a small model you own.
**Time to read**: ~10 minutes
**Engineer's view**: This is interpreted versus compiled. Your prompt is a script you re-send to a remote interpreter on every request, paying its price and its latency each time. Compiling turns that same instruction into a small adapter you version, ship, and run yourself. One artifact, instead of one call per request.
**TLDR**: A fixed instruction you send to a big model on every request can instead be built once into a small model you own. It takes about a minute to produce, and afterwards nothing remote sits in the request path.

## Explain Like I'm 5

Imagine you run a shop, and every order has to be written out in the same tidy format. Right now you
phone a translator, read them the order, and wait while they write it back. You do that for every
single customer, and you pay every time.

One day you notice you have been asking for the same thing all along. So you sit with the translator
once, work through a few hundred examples together, and make yourself a card that handles it.

After that you use the card. The translator only helped you make it.

## The Problem

You have shipped this bug before, and it was a regular expression. The pattern never changed, but
the compile call sat inside the request handler. So every request rebuilt the same matcher from the
same string before looking at a single character of input. It worked. It just did the same work
forever. You moved one line up to module scope and the endpoint got faster for free.

A prompt in production is that bug with a much bigger bill.

Most prompts are not conversations. They are fixed instructions. Turn this messy address into these
five fields. Rewrite this in our house tone. Sort this ticket into one of six buckets. The
instruction never changes, and only the input does. But the instruction is re-sent to a large remote
model on every request, and the model works out what to do from scratch each time, from the same
words as last time.

That costs three things. Money on every call. Latency you cannot tune. And a dependency on someone
else's model staying available, and staying the same, next quarter.

**The fix is to compile: turn the instruction into a small model artifact once, then run that
instead.** The big model still does the work. It just does it at build time rather than on the
request path.

## The Fix: Move the Instruction From Run Time to Build Time

Yuntian Deng and Pengyu Nie at the University of Waterloo, with Stuart Shieber at Harvard, built
this as a working compiler. You hand it a sentence describing a text function. It hands you back an
artifact you can run.

### What actually gets built?

Not a fine-tuned model per task, which is the expensive thing people assume. Every compiled program
shares **one frozen Qwen3-0.6B** as its interpreter. What differs per function is small:

| Piece | What it is |
| --- | --- |
| Adapter | One LoRA adapter, rank 64, alpha 16 |
| Scaffold | A prompt template the compiler generates |
| Package | A `.paw` file holding the adapter, the scaffold, the original spec, and interpreter metadata |

That split is what makes it a compiler rather than a training project. One runtime, many small
artifacts, each versioned like any other build output.

### Where does training data come from if I only wrote a sentence?

The big models generate it. Teacher models read the spec and synthesize task-specific examples, the
adapter trains on those, and the teachers are then gone from the picture.

Two things about that supervision are worth copying. More examples help, with clear
diminishing returns: 1,440 pairs scored 0.821, 2,400 scored 0.836, and 7,200 scored 0.866. And the
*mix* of teachers matters more than raw volume. A 2:1 blend of a cheap teacher and a strong one
scored 0.851, against 0.746 for the cheap teacher alone.

### Is the compiled thing actually any good?

The test set is stacked against it on purpose. FuzzyBench-Hard holds exactly those specs where the
fast compilation path scored zero exact matches. On that set the compiled functions average **0.836**
against **0.224** for the fast path.

The score is semantic, not literal. A judge model decides whether the output correctly applies the
spec to the input, forgiving cosmetic formatting and rejecting real errors.

What it costs is time you spend once. The fast path compiles in 3.5 seconds; training takes 50.9
seconds on a datacenter card, 68.2 on the previous generation, and 99.2 on a consumer card. Call it
a minute, once, per function.

## What This Means for You

**When this matters.** The moment a prompt is on a hot path and its instruction half never changes.
Classification, extraction, normalization, reformatting, tone rewriting — anything where you would
have written a function if only you could have specified it precisely enough.

**How it affects you.** It changes what a prompt *is* in your architecture. Today it is
configuration that gets interpreted remotely on every request. This makes it a build input, which
means it gets a version, a test, and a diff, and it stops being able to change under you.

**What to do about it.**

1. Go read your own logs and find the prompt whose instruction never varies. That is a grep, it
   takes ten minutes, and most teams find at least one running on every request.
2. Count what that one costs per month, in money and in the latency it adds. You need that number
   before anything else, because it is what the build pipeline has to beat.
3. Capture a few hundred real input and output pairs from what you already send. That is your test
   set, and you can build it before you commit to any of this.
4. Then compile one, keep the remote call as a fallback, and compare. `Implementing It` has the
   pipeline and the guard.

## Implementing It

**The change.** Four surfaces, and the fourth is the one people skip.

*The spec author.* The spec is source code now, so it lives in the repo next to a held-out set you
did not train on:

```
functions/address_split/
  spec.md          # the instruction, in one paragraph
  golden.jsonl     # 200 real input/output pairs, never used for training
  build.lock       # teacher models and counts that produced the shipped artifact
```

*The build step.* Synthesize, train, package. This is a continuous integration job, not something
anyone runs by hand:

```python
pairs = []
for teacher, n in [("cheap-teacher", 1600), ("strong-teacher", 800)]:   # the 2:1 mix
    pairs += synthesize(spec, teacher, n)
pairs = [p for p in pairs if validates(p, spec)]     # drop what the teacher got wrong
adapter = train_lora(BASE, pairs, rank=64, alpha=16)
package(adapter, scaffold, spec, base=BASE, out="address_split.paw")
```

*The serving side.* One base model in memory, many adapters swapped per call. This is the whole
economic argument, so do not accidentally load a separate base per function:

```python
BASE = load_once("Qwen3-0.6B")           # shared, frozen
FUNCS = {name: load_adapter(p) for name, p in packages.items()}

def run(name, text):
    return BASE.with_adapter(FUNCS[name]).generate(scaffold(name, text))
```

That sharing is where the savings live. Ten compiled functions cost you one small base model in
memory plus ten adapters, not ten models. Load a separate base per function and you have rebuilt the
expensive thing you were trying to escape.

*The fallback.* A compiled function is right most of the time, not always, so the call site needs a
path for when it is not:

```python
out = run("address_split", text)
if not validates(out, schema):
    out = remote_model(spec, text)       # the old path, still there
    metrics.increment("compiled.fallback", tags=[name])
```

Tag that metric by function name. Without the tag you learn that something is drifting, but not
which thing.

**How you know it worked.** Three signals, in the order they arrive.

Score the artifact on `golden.jsonl` before it is allowed to ship, using a judge that checks meaning
rather than string equality. Set a floor and fail the build below it. A compiled function that is
never scored against held-out data is a rewrite you are hoping about.

Then watch the fallback counter in production. It is the number that tells you the truth, and it
should be low and flat. A rising fallback rate means your inputs have drifted away from what the
teachers imagined, which is the signal to recompile with fresh pairs.

Finally, compare the bill and the latency against the number you wrote down in step two. If the
remote call is still in the hot path for most requests, the compile bought you nothing and you
should say so rather than keep the pipeline.

## When Compiling a Prompt Is the Wrong Tool

The artifact is frozen at build time, so anything needing fresh facts or world knowledge is out.
A function that classifies a ticket is a good candidate. One that answers questions about your
product catalog is not, because the catalog changes and the adapter will not.

The authors are direct about the correctness ceiling: synthetic supervision inherits the teacher's
mistakes, and applications that need guaranteed correctness should validate outputs or keep
deterministic paths. Read 0.836 on the hard set as roughly one in six wrong on the cases chosen to
be hardest. Design for that number rather than around it.

Watch the ownership cost too. Compiling means you now run a build pipeline, a retrain cadence, a
held-out set that has to stay honest, and a fallback path that has to stay tested. For a prompt that
changes every week that is worse than the remote call you were making.

And a conversation is not a function. If the interaction has state, or the instruction depends on
what the user said three turns ago, there is nothing fixed to compile.

Three questions before you build one:

1. Has this prompt's instruction changed in the last three months?
2. Do I have a few hundred real input and output pairs, or would I be inventing my test set?
3. What happens on the request where the compiled function is wrong?

## Glossary

- **compile** — to turn an instruction into a runnable artifact once, ahead of time, instead of interpreting it per request
- **adapter** — a small set of trained weights that specializes a shared frozen base model
- **scaffold** — the prompt template the compiler generates to drive its own artifact
- **teacher** — the large model that writes training examples from a spec and is then out of the loop
- **held-out set** — real pairs never used in training, kept to score the artifact honestly
- **fallback** — the original remote call, kept for the requests the compiled function gets wrong
