"""What one AI task costs in dollars and watts.

Implements the task-scoped meter from the article: a meter that wraps a user
task rather than a model call, counts every attempt including the failures,
and refuses to add watt-hours measured at two different system boundaries.

The claim it proves: the per-call number and the per-task number are different
figures, and the energy figure moves again depending only on where the
boundary is drawn. Google publishes both of its own numbers for the same
prompt -- 0.10 Wh at the accelerator, 0.24 Wh for the whole serving system.

Run: python3 code_example.py
"""

import random
from dataclasses import dataclass

# --- The knob. Change this and watch the whole conclusion move. ---------------
# Fraction of model calls that fail and get retried. Set it to 0.0 and the
# per-call and per-task numbers collapse into one -- which is exactly the case
# where this whole apparatus is not worth building.
RETRY_RATE = 0.22

SEED = 7           # deterministic, so the printed numbers are reproducible
TASKS = 500        # user tasks to simulate


# --- Liftable core: paste these two into your own repo ------------------------

@dataclass(frozen=True)
class Rate:
    """A price is a number plus where it came from.

    `boundary` and `instrument` are required on purpose. A bare float in a
    dict is how a narrow vendor figure ends up in a capacity plan wearing a
    comprehensive label.
    """
    usd_in: float          # dollars per prompt (input) token
    usd_out: float         # dollars per output token
    wh_per_token: float    # watt-hours per token, AT THE STATED BOUNDARY
    boundary: str
    instrument: str
    source: str


class TaskMeter:
    """Measures one finished unit of user work, not one model call."""

    def __init__(self, task_id, rates):
        self.task_id, self.rates = task_id, rates
        self.attempts = []

    def record(self, model, prompt_tokens, output_tokens, ok):
        # Failed attempts burned real tokens on real hardware. Dropping them
        # is the original bug this file exists to show.
        self.attempts.append((model, prompt_tokens, output_tokens, ok))

    def totals(self):
        boundaries = {self.rates[m].boundary for m, *_ in self.attempts}
        # Adding watt-hours across two boundaries produces a number that looks
        # fine and means nothing. Crash instead of reporting it.
        assert len(boundaries) <= 1, f"mixed boundaries: {boundaries}"
        usd = wh = 0.0
        for model, pt, ot, _ok in self.attempts:
            r = self.rates[model]
            usd += pt * r.usd_in + ot * r.usd_out
            wh += (pt + ot) * r.wh_per_token
        return usd, wh, len(self.attempts)


# --- The demonstration --------------------------------------------------------

# Two rate tables for the SAME model and the SAME prompt. Only the boundary
# differs. Google's published pair: 0.10 Wh at the accelerator, 0.24 Wh once
# idle capacity, host CPU/RAM and cooling are inside the line.
# 0.24 Wh for a ~700-token median prompt is ~3.4e-4 Wh/token.
NARROW = {"flash": Rate(3.0e-8, 1.2e-7, 1.43e-4, "accelerator only",
                        "vendor published table",
                        "cloud.google.com/blog/.../measuring-the-environmental-impact-of-ai-inference")}
WHOLE = {"flash": Rate(3.0e-8, 1.2e-7, 3.43e-4, "whole serving system",
                       "vendor published table",
                       "cloud.google.com/blog/.../measuring-the-environmental-impact-of-ai-inference")}


def run_task(task_id, rates, rng):
    """One user task: a plan call, two tool-answer calls, retries on failure.

    This is the shape that makes per-call accounting wrong -- fan-out plus
    retry. A single-call feature would not diverge at all.
    """
    meter = TaskMeter(task_id, rates)
    for prompt_tokens, output_tokens in ((900, 120), (1400, 300), (1400, 260)):
        while True:
            ok = rng.random() >= RETRY_RATE
            meter.record("flash", prompt_tokens, output_tokens, ok)
            if ok:
                break          # the retry re-sends the prompt: tokens paid twice
    return meter


def measure(rates):
    rng = random.Random(SEED)
    usd = wh = calls = 0.0
    for i in range(TASKS):
        u, w, c = run_task(i, rates, rng).totals()
        usd, wh, calls = usd + u, wh + w, calls + c
    return usd, wh, calls


def main():
    usd_w, wh_w, calls = measure(WHOLE)
    _usd_n, wh_n, _ = measure(NARROW)

    assumed = TASKS * 3             # 3 calls per task, what the planning doc assumed
    print(f"{TASKS} user tasks, retry rate {RETRY_RATE:.0%}, seed {SEED}\n")

    print("1. The unit you pick changes the dollar figure")
    print(f"   attempts actually made : {calls:.0f}")
    print(f"   attempts the doc assumed : {assumed}")
    print(f"   cost per ATTEMPT         : ${usd_w / calls:.6f}")
    print(f"   cost per FINISHED TASK   : ${usd_w / TASKS:.6f}")
    print(f"   naive per-call estimate  : ${usd_w / calls * 3:.6f}  <- what the planning doc said")
    print(f"   understated by           : {(usd_w / TASKS) / (usd_w / calls * 3):.2f}x\n")

    print("2. The boundary changes the energy figure, with nothing else changed")
    print(f"   accelerator only     : {wh_n / TASKS:.4f} Wh per task")
    print(f"   whole serving system : {wh_w / TASKS:.4f} Wh per task")
    print(f"   same workload, ratio : {wh_w / wh_n:.2f}x\n")

    print("3. Both figures are true. Neither is a measurement without this line:")
    r = WHOLE["flash"]
    print(f"   boundary={r.boundary} | instrument={r.instrument}")
    print(f"   task=one user request including every retried attempt")
    print(f"   source={r.source}")


if __name__ == "__main__":
    main()
