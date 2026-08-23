# Your Coding-Agent Benchmark Score Might Just Be a Bigger VM

**Category**: Evals & Reliability
**Tags**: benchmarks, coding-agents, production
**Date**: 2026-08-23
**Time to read**: ~10 minutes

## Explain Like I'm 5
Imagine two students take the same timed exam, but one of them is given a desk that
occasionally, at random, gets yanked out from under them mid-answer — not because their answer
was wrong, just because the room briefly ran out of desks. If you only look at the final scores,
the desk-yanking looks like that student "isn't as capable." It isn't about ability at all. That's
what happens when you time AI coding agents inside memory-limited sandboxes: sometimes the work
gets forcibly killed not because the code was wrong, but because it briefly used more memory than
allowed — and the score alone can't tell you which happened.

## The Problem
Top coding-agent leaderboards (SWE-bench, Terminal-Bench) routinely separate competing frontier
models by just 1-3 percentage points, and teams treat those gaps as a real capability ranking.
Nobody publishes, or holds constant, the memory limits their evaluation containers ran under.
Anthropic measured what that omission is worth: switching only the container's memory headroom —
same model, same harness, same tasks — swung the score by 6 points, more than the gap the
leaderboard was supposedly measuring.

## For a Software Engineer
This is a resource-provisioning problem wearing a benchmark-methodology costume — the same shape
as a CI test that fails under load and passes in isolation, except here the "flakiness" gets
baked into a permanent-looking leaderboard number instead of getting re-run and shrugged off.
Container runtimes enforce two separate memory numbers: a soft guaranteed allocation and a hard
kill threshold (Kubernetes calls these `requests`/`limits`; cgroups calls them `memory.high` /
`memory.max`). When a team sets both to the same tight value "to match the task spec," a perfectly
normal transient spike — installing a package, buffering a build — crosses the hard-kill line and
the whole run dies. That gets counted as the agent failing, even though its approach might have
worked fine with 20% more headroom.

The number worth feeling: going from strict per-task memory limits to 3x headroom cut Anthropic's
infrastructure-caused failure rate from 5.8% to 2.1% — while the actual success rate didn't move
outside statistical noise (p=0.40). Every one of those rescued runs was never a capability
question; it was a container question. Monday-morning action: if you run an eval CI loop, check
whether your sandbox's memory limits are documented anywhere — an undocumented resource change is
exactly as dangerous a confound as an undocumented prompt change, and far more common.

## What This Means for You
**When this matters**: you run or read any leaderboard/benchmark ranking coding agents or LLMs, or
you maintain your own eval CI where pass/fail sometimes flips between runs with no code change.

**How it affects you**: a model choice, a "which agent framework is better" call, or your own CI's
red/green signal might be tracking container memory headroom instead of actual capability — you
could be chasing, or trusting, pure noise dressed up as a score.

**What to do about it**: document your eval's guaranteed and hard-kill memory values as a
first-class parameter, the same way you'd document prompt version or sampling temperature. If
you're comparing two setups, calibrate headroom so scores at the low and high end of resource
allocation land within statistical noise of each other before trusting the comparison. Treat any
leaderboard gap under ~3 points as unproven until both sides' eval configs are documented and
matched.

## What It Is
"Quantifying infrastructure noise in agentic coding evals" (Anthropic Engineering, Feb 2026) is a
systematic study of how much a coding-agent benchmark score depends on the resource envelope its
container runs in, not just the model inside it. Agentic evals are different from static
single-shot benchmarks: the model writes code, installs dependencies, runs tests, and iterates —
so the runtime environment is an active participant in the score, not a passive backdrop. Anthropic
ran Terminal-Bench 2.0 across six resource configurations on Google Kubernetes Engine, from strict
per-task enforcement up to fully uncapped, holding the model, harness, and task set fixed, and
watched both the infrastructure error rate and the success score move.

## Why It Matters
RAG pipelines get audited for hidden constants; prompts get versioned; but the container a coding
agent runs inside almost never gets treated as an experimental variable at all — it's "just infra."
This work shows that's backwards for agentic evals specifically, because the agent's own behavior
(what it installs, how much it iterates, how large a test suite it runs) determines its own memory
footprint, unlike a static benchmark where the runtime is inert. Two providers who differ only in
how generously they provision their eval sandboxes will produce two different leaderboard
positions for the identical model — and there's currently no standard forcing them to disclose
that difference.

## Key Technical Details

**Background first.** A container's resource limits usually come in two numbers: a *guaranteed
allocation* (what it's promised) and a *hard kill threshold* (the ceiling above which the
container's process gets forcibly terminated — the Linux out-of-memory killer, or an equivalent).
An agentic coding eval isn't a single inference call; it's a loop where the agent writes files,
installs packages, and runs its own tests inside that container, so its memory use is bursty and
task-dependent rather than flat.

- **The experiment held everything else fixed.** Same Claude model, same harness, same task set,
  across six resource configurations on GKE — the only variable was how much memory headroom the
  container was given, from 1x each task's per-task spec up to fully uncapped.
- **Infrastructure error rate dropped monotonically as headroom grew**: 5.8% at strict enforcement
  down to 0.5% uncapped.
- **1x to 3x headroom is the "false failure" zone.** Infra errors fell from 5.8% to 2.1%
  (p<0.001), but the success score stayed within statistical noise (p=0.40) — the extra memory was
  rescuing runs that were already capable, not making the agent smarter.
- **3x to uncapped is a different zone.** Infra errors dropped a further 1.6 points, but this time
  success jumped ~4 percentage points for real — above 3x, extra memory starts *enabling a
  different strategy*, not just preventing crashes.
- **The `bn-fit-modify` task makes the mechanism concrete.** Some models' first move is installing
  the full data-science stack (pandas, networkx, scikit-learn) to fit a Bayesian network — under a
  tight limit that install itself fails before any solution code runs. Other models implement the
  math from scratch with only the standard library. Which strategy "wins" is decided by the
  container's memory ceiling, not by which model is more capable.
- **The effect scales with how memory-hungry the benchmark's tasks are.** A parallel check on 227
  SWE-bench problems (10 samples each, up to 5x baseline RAM) found a real but much smaller
  1.54-point lift — SWE-bench's typical task just doesn't touch memory as heavily as
  Terminal-Bench's.
- **Anthropic's own recommendation**: publish both memory numbers per task, not one pinned value;
  calibrate the headroom band so scores at the floor and ceiling of resource allocation land within
  noise of each other; and treat any public leaderboard gap under 3 points with active skepticism
  until eval configuration is documented and matched.

## How It Connects to What You Know
This is the flaky-CI problem wearing an eval-methodology costume: a test that fails under
contention and passes in isolation isn't testing your code, it's testing your CI runner's
headroom — the fix there (fixed, generous, documented resource allocation for test runners) is
the exact fix recommended here. It's also the same instinct behind controlling for confounders in
any A/B test: you can't attribute a lift to your change if you also silently changed the
environment. And it rhymes with the P-PAS scheduling session from 2026-08-18 — there too, a number
that looked like a fixed setting (`max_num_batched_tokens`) turned out to be load-dependent, and
the "obviously correct" fixed choice was quietly wrong across regimes.

## Try It Yourself
`code_example.py` simulates the same two-phase pattern with synthetic tasks: most need very little
memory, a small "heavy-footprint" minority genuinely need ~2.7x the base allocation, and a
separate, better-performing strategy only becomes available once headroom clears 3x. Sweeping five
resource multipliers reproduces both halves of the story in one run: below the 3x threshold, the
infrastructure failure rate drops sharply while the success rate among completed runs stays flat
(overlapping 95% confidence intervals) — the rescued runs bought nothing extra. Crossing the
threshold, success jumps for real (diverging confidence intervals) even though nothing about the
model changed.

## Glossary
- **SWE-bench / Terminal-Bench** — public benchmarks that score coding agents by having them solve
  real GitHub issues or terminal tasks end-to-end inside a sandboxed environment.
- **Agentic eval** — an evaluation where the model actively writes code, installs dependencies,
  and runs its own tests inside a live environment, as opposed to a single-shot prompt/response
  benchmark where the runtime is passive.
- **Container resource limits** — the memory (and CPU) ceilings a container orchestrator enforces
  on a running process; in Kubernetes, `requests` (guaranteed) and `limits` (hard ceiling); in
  Linux cgroups, `memory.high` (soft throttle point) and `memory.max` (hard kill point).
- **OOM kill** (Out-Of-Memory kill) — the Linux kernel forcibly terminating a process that has
  exceeded its allowed memory, regardless of whether that process's logic was correct.
- **Headroom** — how much spare capacity (here, memory) sits between what a task typically needs
  and the hard limit it's running under.
- **Statistical noise / p-value** — a p-value below a threshold (commonly 0.05) signals a
  difference is unlikely to be due to random chance alone; a high p-value (like the 0.40 seen
  between 1x and 3x success scores) means the observed gap is consistent with pure chance, i.e.
  not a real effect.
- **Confound** — a variable that changes alongside the one you meant to test, making it impossible
  to tell which one caused the result you observed; here, memory headroom is a confound for "model
  capability" in benchmark comparisons.
- **GKE** (Google Kubernetes Engine) — Google Cloud's managed Kubernetes service; the platform
  Anthropic ran these container experiments on.
