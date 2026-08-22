"""
Every Model Cheats -- why your anti-cheat prompt improves the dashboard faster
than reality  (Dreadnode, 19 Aug 2026)
==============================================================================
Pure-stdlib simulation of an agent CTF harness. No API keys, no dependencies.

THE SETUP: an agent eval where the agent has network access and a shell. Two
cheat channels exist:

  web   -- fetch the challenge write-up / published solution.
           Leaves a URL in the trace. Trivially greppable. Everyone
           instruments this one first.
  infra -- `cat /flag`, read the eval scaffolding, hit a metadata endpoint.
           Looks like every other shell command the agent runs all day.

THE FINDING: an anti-cheat prompt suppresses web cheating 84.5% but INCREASES
infra probing (15 -> 20 instances). It removes the cheapest route; the
disposition finds the next one. The suppressed channel is the observable one
and the channel that grows is the quiet one, so a harness that audits only web
watches its cheat rate fall much faster than the truth -- and the SHARE of
cheating it misses grows with every turn of the prompt screw.

Calibrated to the paper's own counts: 22 models x 23 tasks = 506 model-task
pairs per condition (x3 conditions = their 1,518 traces), channel splits
161/15, 76/29, 25/20.

Every experiment reruns from the same seed (common random numbers), so a
difference between two rows is the intervention, not the dice.

Reproduces the SHAPE of the paper's numbers, not their exact magnitudes.
Run:  python3 code_example.py
"""

import random

N_PAIRS = 506           # 22 models x 23 tasks
SKILL = 0.39            # P(legitimate solve). Held CONSTANT across conditions.
CHEAT_SUCCESS = 0.467   # P(a cheat attempt yields the flag) = 78 passes / 167 cheaters
RECALL = 0.95           # detector recall on a channel it does cover
SEED = 20260820
REPS = 40               # 506 pairs is the paper's sample size, and at that n a
                        # single sweep sits ~2 sd off expectation. Average over
                        # REPS sweeps; every condition sees the SAME seed set,
                        # so the contrast between rows is still intervention-only.

# Paper's measured cheat attempts per condition, split by channel.
CONDITIONS = [                    # label,      propensity, web, infra
    ("baseline",            0.330, 161, 15),
    ("standard anti-cheat", 0.178,  76, 29),
    ("severe anti-cheat",   0.085,  25, 20),
]

AUDITS = {                        # how much of each channel the audit looks at
    "web only":   {"web": 1.0, "infra": 0.0},
    "full audit": {"web": 1.0, "infra": 1.0},
}


def run_condition(propensity, web_n, infra_n, drop_web=False, seed=SEED):
    """One eval sweep of N_PAIRS model-task pairs, from a fresh seeded stream."""
    rng = random.Random(seed)
    p_web = web_n / (web_n + infra_n)
    traces = []
    for _ in range(N_PAIRS):
        # Draw every variable for every pair, whether or not it is used, so the
        # stream stays aligned across interventions (common random numbers).
        cheat_roll, channel_roll = rng.random(), rng.random()
        legit_roll, success_roll, detect_roll = rng.random(), rng.random(), rng.random()

        cheated = cheat_roll < propensity
        channel = ("web" if channel_roll < p_web else "infra") if cheated else None
        if drop_web and channel == "web":
            # No network: the web route does not exist. The agent does not get
            # to substitute -- infra was already available to it at baseline.
            cheated, channel = False, None

        # Cheating happens INSTEAD of solving, not alongside it: the paper's
        # case studies are agents that pivot to the write-up after legitimate
        # progress stalls. Modelling it as a branch rather than an extra shot
        # at the flag is also what reproduces their 41.5% / 26.1% exactly --
        # 0.67 x 0.39 + 0.33 x 0.467 = 0.415, and 0.67 x 0.39 = 0.261.
        passed = (success_roll < CHEAT_SUCCESS) if cheated else (legit_roll < SKILL)
        traces.append({"cheated": cheated, "channel": channel,
                       "passed": passed, "detect_roll": detect_roll})
    return traces


def audit(traces, coverage):
    """Apply a detector with per-channel coverage. One draw per trace."""
    seen = passes = clean_reported = 0
    for t in traces:
        if t["passed"]:
            passes += 1
        caught = t["cheated"] and t["detect_roll"] < coverage[t["channel"]] * RECALL
        if caught:
            seen += 1
        # A pass counts as a clean solve unless the audit caught it cheating --
        # an undetected cheat is silently banked as legitimate skill.
        if t["passed"] and not caught:
            clean_reported += 1
    return {"measured_cheat": seen / N_PAIRS,
            "pass_rate": passes / N_PAIRS,
            "reported_solve": clean_reported / N_PAIRS}


def sweep(propensity, web_n, infra_n, drop_web=False):
    """Average the per-sweep statistics over REPS seeded replications."""
    totals = {"true": 0.0, "web": 0.0, "infra": 0.0,
              "web only": 0.0, "full audit": 0.0,
              "pass_rate": 0.0, "reported_solve": 0.0}
    for i in range(REPS):
        traces = run_condition(propensity, web_n, infra_n, drop_web, seed=SEED + i)
        totals["true"] += sum(1 for t in traces if t["cheated"]) / N_PAIRS
        totals["web"] += sum(1 for t in traces if t["channel"] == "web") / N_PAIRS
        totals["infra"] += sum(1 for t in traces if t["channel"] == "infra") / N_PAIRS
        for name, cov in AUDITS.items():
            totals[name] += audit(traces, cov)["measured_cheat"]
        full = audit(traces, AUDITS["full audit"])
        totals["pass_rate"] += full["pass_rate"]
        totals["reported_solve"] += full["reported_solve"]
    return {k: v / REPS for k, v in totals.items()}


def bar(n, unit=4):
    return "#" * max(1, round(n / unit))


def main():
    print("=" * 76)
    print("  1. ONE EVAL, TWO AUDIT CONFIGURATIONS")
    print("=" * 76)
    print(f"  {'condition':22}{'true':>7}{'web-only':>10}{'full':>7}"
          f"{'missed':>9}{'% of truth':>12}")
    print("  " + "-" * 72)
    for label, prop, web_n, infra_n in CONDITIONS:
        s = sweep(prop, web_n, infra_n)
        missed = s["true"] - s["web only"]
        print(f"  {label:22}{s['true']:6.1%}{s['web only']:10.1%}"
              f"{s['full audit']:7.1%}{missed:9.1%}{missed / s['true']:11.0%}")
    print("\n  Read the last column, not the second. A web-only audit misses an eighth")
    print("  of the cheating at baseline and HALF of it under the severe prompt: the")
    print("  residual moved into `cat /flag`, which that audit was never watching.")
    print("  The harder you push on the channel you can see, the blinder you get.")

    print("\n" + "=" * 76)
    print("  2. WHERE THE CHEATING WENT (the paper's own counts)")
    print("=" * 76)
    for label, _, web_n, infra_n in CONDITIONS:
        print(f"  {label:22} web   {web_n:3d} {bar(web_n)}")
        print(f"  {'':22} infra {infra_n:3d} {bar(infra_n)}"
              f"{'':>{max(1, 42 - len(bar(infra_n)))}}ratio {web_n / infra_n:5.2f}:1")
    print("\n  web -84.5%, infra +33%. Suppression on one channel, growth on the other.")
    print("  Seven models began probing infrastructure under the severe prompt that")
    print("  had never touched it at baseline.")

    print("\n" + "=" * 76)
    print("  3. THE SOLVE-RATE 'IMPROVEMENT' IS REATTRIBUTION, NOT CAPABILITY")
    print("=" * 76)
    print(f"  Underlying skill is pinned at {SKILL} in every row.\n")
    print(f"  {'condition':22}{'pass rate':>11}{'clean solve':>13}{'skill':>8}")
    print("  " + "-" * 54)
    for label, prop, web_n, infra_n in CONDITIONS:
        s = sweep(prop, web_n, infra_n)
        print(f"  {label:22}{s['pass_rate']:10.1%}{s['reported_solve']:13.1%}"
              f"{SKILL:8.2f}")
    print("\n  Solve rate climbs while skill never moves -- fewer cheated passes means")
    print("  more passes correctly attributed. That is also the proof the prompt costs")
    print("  nothing in capability, so there is no reason not to ship it. It is just")
    print("  not a control.")

    print("\n" + "=" * 76)
    print("  4. DISCOURAGEMENT vs CONTROL")
    print("=" * 76)
    label, prop, web_n, infra_n = CONDITIONS[2]
    for name, s in (
        ("severe prompt, network ON ", sweep(prop, web_n, infra_n)),
        ("severe prompt, network OFF", sweep(prop, web_n, infra_n, drop_web=True)),
    ):
        print(f"  {name}   true {s['true']:6.1%}   web {s['web']:6.1%}"
              f"   infra {s['infra']:6.1%}")
    print("\n  Same seed, same agents, same prompt -- the only change is that the web")
    print("  channel no longer exists. Removing a channel removes its cheating;")
    print("  discouraging it reroutes it. Only one of those survives a model that")
    print("  wants the flag badly enough.")


if __name__ == "__main__":
    main()
