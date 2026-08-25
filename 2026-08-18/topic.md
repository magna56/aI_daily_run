# How vLLM Chooses a Prefill Token Budget

**Category**: AI in Production
**Tags**: inference-serving, latency, production
**Date**: 2026-08-18
**Level**: Deeper
**For**: Shipping AI
**Hook**: There is no single right batch size. The winner flips when the GPU gets busy.
**Time to read**: ~10 minutes

## What It Is

Every vLLM deployment has one knob that dominates its latency profile: `max_num_batched_tokens`
(MBT), the per-iteration token budget the scheduler is allowed to spend. The vLLM docs give the
conventional advice — "smaller values (e.g. 2048) achieve better ITL... higher values achieve
better TTFT" — and every serving team picks a number, writes it into a Helm chart, and moves on.

P-PAS (Timo Sämann, arXiv:2608.15171, submitted Aug 15 2026) shows that number is a load-dependent
optimum, not a constant. The paper's core empirical claim: large prefill chunks improve execution
efficiency **under low scheduling pressure**, and that advantage inverts as demand rises. There is
no static MBT that is simultaneously right for your 3am traffic and your 10am traffic. P-PAS
replaces the constant with a controller that reads concurrent prefill and decode state at schedule
time and expands or constricts the budget accordingly.

The mechanism is a second-order effect of chunked prefill. Since Sarathi-Serve (arXiv:2403.02310)
introduced stall-free batching, the standard scheduler runs decodes first, then spends leftover
budget on prefill chunks. That fixed prefill-decode interference at the level of "a giant prompt
no longer blocks the batch entirely" — but it did not remove the coupling. Every sequence currently
decoding pays the **full iteration wall-clock** for each token it emits. An 8192-token iteration
takes roughly 170ms on an A100-class step; a 2048-token one takes ~50ms. With two sequences in
flight, that difference is noise. With forty, you have just multiplied everyone's inter-token
latency by 3.4x to make one request's prefill finish sooner.

## Why It Matters

This is the long-context RAG and agentic regime specifically — tens of thousands of input tokens
producing short outputs — where end-to-end latency, not throughput, is the objective. That
describes most production LLM traffic that isn't chat.

The practical consequence is that the standard tuning ritual is subtly broken. Teams benchmark MBT
against a synthetic load generator at one fixed rate, find an optimum, and ship it. The benchmark
picked the right answer *for that rate*. Production load is diurnal, so the config is provably
wrong for part of every day, and the failure mode is invisible: no errors, no saturation alarm,
just p99 latency that is 20-30% worse than it needed to be during whichever half of the cycle you
did not tune for.

It also reframes what "tuning" means for serving infra. MBT is not a capacity constant like
`max_num_seqs` or GPU memory utilization; it is a **control variable**. The right artifact to ship
is a policy, not a number. That is a different mental model than most inference deploys use today.

## Key Technical Details

- **The knob**: MBT caps total tokens per engine step, summing decode tokens (1 per running seq)
  and prefill chunk tokens. Decodes get priority; prefill fills the remainder.
- **Iteration cost is affine in batched tokens**: `T ≈ T_base + k · tokens`. Fixed overhead means
  small budgets cost throughput; the linear term means large budgets cost per-iteration latency.
- **The asymmetry that drives the inversion**: prefill cost is paid once per request; iteration
  latency is paid by *every decoding sequence, every token*. So the cost of a large budget scales
  with decode population while its benefit does not.
- **P-PAS signal**: concurrent prefill backlog + decode population. Budget expands toward the max
  when pressure is low, constricts toward a floor as pressure rises.
- **Lineage**: Sarathi-Serve (chunked prefill, stall-free batching; 2.6x-5.6x capacity over vLLM)
  made the budget meaningful. P-PAS makes it dynamic. Llumnix multi-tier SLA work
  (arXiv:2608.16336, Aug 17 2026) attacks the adjacent problem — the same scheduler needs to
  express more than two priority classes, and finds ~4 tiers is the cost-effectiveness sweet spot.
- **Caveat worth holding**: the paper reports maintaining low latency across load regimes but the
  public abstract is thin on head-to-head TTFT/TPOT/SLO numbers against Sarathi-Serve. Treat the
  mechanism as well-founded and the magnitude as unverified until you read the artifact.

## How It Connects to What You Know

You already think about admission control and head-of-line blocking in request routers. This is
the same problem one layer down, with an unusual twist: the "requests" in the batch are *phases* of
different jobs with opposite cost profiles. Prefill is compute-bound and embarrassingly parallel;
decode is memory-bandwidth-bound and serial. Continuous batching mixes them into one queue, so the
scheduler is doing multi-class scheduling of workloads with different bottleneck resources — a
classic queueing-theory setup where the static-parameter answer is usually wrong.

It also rhymes with the cascade work from the 2026-08-03 session. There the lesson was that the
routing gate's calibration is the whole moat; here the lesson is that the scheduler's pressure
signal is the whole moat. Both are cases where the expensive component (the model) is fixed and
all remaining leverage sits in a cheap control decision made with live state.

And it connects to the AIMD/backpressure patterns you'd recognize from network and ticker-plant
flow control: measure queue pressure, shrink the window, let the drain catch up. P-PAS is
essentially congestion control for a token budget.

## Try It Yourself

`code_example.py` is a pure-stdlib discrete-event simulator of a vLLM-style continuous-batching
scheduler with chunked prefill, decode-priority, and an affine iteration cost model. It runs 200
long-context requests (4k-16k prompts, 32-256 outputs) through three load regimes against three
static budgets and P-PAS.

It reproduces the inversion: **MBT=8192 wins at 1 and 4 req/s, MBT=2048 wins at 8 req/s.** Then it
scores worst-case regret across all regimes, where the honest result shows up — P-PAS never wins a
single regime outright (a perfectly tuned static budget always beats it there) but has the lowest
worst-case regret at +5.9%, versus +9.3% for MBT=8192 and +32.4% for MBT=1024. That is the actual
argument for adaptive scheduling: not peak performance, but never being badly wrong.

Worth doing: change `T_BASE_MS` and `K_TOK_MS` to match your own hardware's measured step time and
see whether the crossover rate moves. That crossover is the number your deploy config should
actually be keyed to.
