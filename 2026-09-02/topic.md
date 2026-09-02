# How the Same Model Gives Two Different Answers

**Category**: AI in Production
**Tags**: inference-serving, reliability, training
**Date**: 2026-09-02
**Level**: Building
**For**: Shipping AI
**Hook**: Identical weights, identical input, temperature zero — and two machines disagree. The cause is that addition on a computer depends on the order you do it in.
**Time to read**: ~10 minutes
**Engineer's view**: This is a flaky test under load — a hash that depends on which thread finished first. An exact-string assert across two runtimes fails the day the batch shape changes, not the day your code does.
**TLDR**: Temperature zero is not bitwise across machines. Measure the noise floor on your two runtimes and assert on that, or pin the execution order.

## Explain Like I'm 5

Imagine adding up a long receipt. If you round to the nearest penny after every line, the total you
get depends on the order you added the lines in. Start from the top and you might get £10.02.
Start from the bottom and you might get £10.01.

Nothing was wrong with the arithmetic and nothing was wrong with the receipt. The only thing that
changed was the order. Computers add numbers this way all the time, and a model's answer is a very
long receipt.

## The Problem

You have probably met this and filed it as a mystery. The same prompt, the same model, temperature
set to zero — and the answer on the GPU box is not the answer you got on your laptop. Or an eval
scores two points lower after a serving upgrade that changed nothing about the weights.

The cause is not a bug in either system. **Floating-point addition is non-associative**: `(a + b) +
c` and `a + (b + c)` can give different results, because each step rounds. Every kernel, every
batch shape and every parallelism layout sums its partial results in a different order, so two
runtimes holding byte-identical weights produce genuinely different probabilities. If that sounds
like a hash that depends on which thread finished first, you have the right instinct.

Usually the gap is tiny and nothing happens. Sometimes it is not. The SkyRL team reports a GLM-5.2
reinforcement-learning run where the train–inference disagreement sat around 0.013 — and the
clipping that protects the algorithm discarded roughly **45% of tokens**, after which reward
collapsed entirely.

**The fix is to pin the execution order, not just the weights.** Write down every rounding-relevant
choice — which kernel, which accumulation type, how the reduction is split — and make both sides
honour the same contract. That is what IsoExec does, and it is the part worth understanding even if
you never train anything.

## The Fix: Pin the Execution Order, Not Just the Weights

A checkpoint fixes *what* is computed. It says nothing about *how*, and "how" is where the rounding
lives. IsoExec adds a second artifact alongside the weights: an **execution contract** that both
engines must satisfy, naming the choices that change the last bits.

The pinned items are specific rather than philosophical. The kernel implementation and the
architecture it was built for (`native_fused_sigmoid, version 1, arch: sm90`). The accumulation
dtype (`leaf_dtype: fp32`). The split-K and split-KV partition counts that decide how a reduction
gets chopped up, and which parallelism sizes are known to be bitwise invariant.

Adapters enforce the contract at runtime, and each side publishes a digest, so a mismatch shows up
as a mismatch rather than as a mystery.

### Why would batch size change my answer?

Because a matrix multiply batches your row in with everybody else's, and the accumulation order
follows the batch. A **batch-invariant kernel** is one where "neither the other elements in a batch
nor the batch size should affect the computation for a specific element" — and ordinary kernels are
not batch-invariant. Your request genuinely computes differently depending on who else arrived in
the same millisecond.

That is the uncomfortable one. It means a result you reproduced locally at batch size 1 was never
guaranteed to survive production traffic. Horace He puts it more bluntly: "the primary reason
nearly all LLM inference endpoints are nondeterministic is that the load (and thus batch-size)
nondeterministically varies" — the variable is other people's requests.

### So is temperature zero not deterministic?

It is deterministic given a fixed execution order, and that is a much weaker promise than it
sounds. Temperature zero takes the argmax over the logits; if the top two candidates sit within the
rounding noise, a different reduction order flips which one wins, and the sampler faithfully picks
a different token. Everything downstream then diverges from a difference in the last decimal place.

The measured version: on Qwen3.5-35B-A3B the mean absolute logprob difference between the two
engines was 0.014, and the worst single step was **5.073** — not a rounding artefact by then, an
entirely different distribution.

## What This Means for You

**When this matters.** You compare model outputs across two environments and expect them to match:
an eval that runs locally and in CI, a prod-versus-staging A/B, a regression test asserting on a
model's answer, or a benchmark you are trying to reproduce from someone else's write-up.

**How it affects you.** The gap was small and the consequence was not: a train-inference
disagreement of 0.013 was enough for clipping to discard 45% of tokens, because a threshold sat
downstream of it and thresholds turn small numeric differences into large behavioural ones. Those
comparisons carry a noise floor nobody wrote down, and it is not
uniform — it grows with batch size, parallelism and any change of serving stack. A test asserting
exact output equality across two runtimes is not strict, it is *flaky*, and it will fail on the day
your traffic pattern changes rather than the day your code does. Meanwhile a real regression
smaller than the noise floor is invisible.

**What to do about it.** Today, before changing any infrastructure and without touching a serving
config: measure your own noise floor.
Send the same fifty prompts through both environments, log the top-token logprob for each, and look
at the distribution of differences. That number is the resolution limit of every comparison you
make, and most teams have never looked at it. Keep the whole distribution rather than the average:
the mean is reassuring and the tail is what actually breaks a threshold downstream.

Then write your assertions in terms of that number — compare distributions, not strings — and
record the batch size you measured at, because the floor moves with it.

## Implementing It

**The change.**

*Whoever owns the eval or the regression test.* Stop asserting on exact output. Assert on a
tolerance you measured, and record what the comparison was made under:

```python
def assert_logprobs_close(a, b, tol):
    """tol comes from YOUR measured noise floor, not from a blog post."""
    diffs = [abs(x - y) for x, y in zip(a, b)]
    worst = max(diffs)
    assert worst <= tol, (
        f"max logprob divergence {worst:.4f} exceeds measured floor {tol:.4f} — "
        f"this is a real change, not numerics")
    return worst
```

*Same person, establishing the floor.* It is a one-off script and it is the prerequisite for
everything else. Run identical prompts through both runtimes and keep the distribution, not the
mean — the mean was 0.014 in the paper's run while the worst step was 5.073, and it is the tail
that breaks things:

```python
floor = sorted(abs(local[i] - prod[i]) for i in range(len(local)))
p50, p99, worst = floor[len(floor)//2], floor[int(len(floor)*0.99)], floor[-1]
print(f"p50={p50:.5f}  p99={p99:.5f}  max={worst:.5f}")
```

*Whoever serves the model.* Record the execution conditions next to the result, so a future
disagreement is diagnosable rather than mysterious. This is the cheap half of an execution
contract, and it is worth doing even if you never enforce one:

```python
run_meta = {
    "engine": "vllm-0.11.2", "kernel_backend": "flashinfer",
    "dtype": "bfloat16", "accum_dtype": "fp32",
    "tensor_parallel": 8, "batch_size": batch.size,   # both change the reduction order
}
```

*Whoever is doing RL post-training.* This is where it stops being cosmetic. Log the per-token KL
between rollout and training logprobs, and alert on the clipped-token fraction — the failure
signature is clipping climbing while reward flattens. SkyRL's implementation is Apache-2.0 and
gated behind an environment variable, so it can be switched on for one run without adopting it:

```bash
SKYRL_ISOEXEC=1 python examples/isoexec/run_matched.py   # matched pair vs native execution
```

**How you know it worked.** For the eval path, the signal is that your tolerance test starts
failing for reasons you can name. A tolerance set from a measured floor should be quiet during
normal operation and fire on a real change; if it fires when you merely increase batch size, the
floor was measured at the wrong batch size and the number, not the code, is what to fix. For the RL
path, the numbers to watch are the ones IsoExec moved: mean absolute logprob difference from 0.014
to under 0.001, worst per-step from 5.073 to 0.090, at a cost of 25.3% on the full step. Watch the
clipped-token fraction fall; that is what was destroying the run.

## When Bitwise Reproducibility Is the Wrong Goal

It costs about a quarter of your throughput. IsoExec measured 31.3% slower generation, 18.6% slower
policy training, 25.3% on the full step — and in their own 50-step experiment, eliminating the
mismatch produced **no meaningful reward improvement**. They published that, which is the reason to
trust the rest of it. The mismatch is a plausible cause of instability, not a guaranteed one, and
paying a quarter of your compute against a maybe is a bad trade unless you are already unstable.

For ordinary serving the answer is almost always to measure the noise floor and design around it,
not to eliminate it. Determinism is a debugging tool here: turn it on to isolate a problem, not to
run production.

Three questions before chasing bitwise equality. Do I have evidence of a real failure — clipping,
reward collapse, an eval that moved without a code change — or only an aesthetic discomfort? Would
a measured tolerance solve the same problem for free? And can I afford a quarter of my throughput
against a hypothesis I have not yet tested?

## Glossary

- **non-associative** — `(a+b)+c` and `a+(b+c)` can differ, because each step rounds.
- **Reduction order** — the sequence in which a kernel sums its partial results.
- **Split-K** — chopping one dot product into several partial sums computed in parallel.
- **batch-invariant** — a kernel whose result for your row does not depend on the batch it rode in with.
- **Noise floor** — the spread between two runtimes on identical input; the resolution limit of any comparison.
