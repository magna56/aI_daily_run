"""
Debate Training Reduces Reward Hacking in RLAIF  (arXiv:2608.17776, DeepMind, Aug 2026)
=======================================================================================
Pure-stdlib simulation of the paper's core dynamic. No API keys, no dependencies.

SETUP: a WEAK frozen judge scores Alice's solution. It has three exploitable biases
(verbosity / authority / impersonation) and poor discrimination on correctness. Alice
hill-climbs on judge reward; persuasion traits improve ~3x faster than genuine skill
AND divert capacity from it, so hacking is the cheaper gradient direction. Result:
reward goes UP while accuracy and judge quality go DOWN.

FIX: Bob, a critic rewarded 1-r. Two mechanisms -- a substantive critique raises the
judge's discrimination and crowds out surface cues, and a competent critic actively
EXPOSES naked rhetoric, making hacks net-negative. But Bob has cheap hacks of his own,
so word limits are what force him onto the substantive route.

Reproduces the shape of the paper's Figures 1/3 and two ablations, not its magnitudes.
Run:  python3 code_example.py
"""
import math, random

STEPS, N_EVAL, SIGMA = 80, 400, 0.25
SLOW = 0.32                # real capability improves ~3x slower than persuasion
DIVERT = 0.16              # persuasion diverts capacity from actual reasoning
JUDGE_DISCRIM = 0.95       # weak judge: barely separates correct from incorrect
HACK_EXPOSURE = 0.55       # how hard a competent critic punishes naked rhetoric
BIASES = {"verbosity": 0.80, "authority": 1.00, "impersonation": 1.40}
HACKS = tuple(BIASES)

sig = lambda x: 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, x))))
eff_skill = lambda a: a["skill"] - DIVERT * sum(a[k] for k in HACKS)


def critique(correct, alice, bob, word_limit):
    """Bob attacks. Returns (push against Alice, SUBSTANCE). Which of his three
    levers the optimizer picks is the whole ablation:
      detection -- real flaws + exposes Alice's "unjustified claims and
                   assumptions" (paper 4.1). Creates substance. Slow to learn.
      bluff     -- cheap, but backfires on correct solutions.
      verbosity -- pure judge-exploitation. Cheap, fast, unbounded unless a word
                   limit clamps it. This is the lever that ate the paper's
                   preliminary runs, where Bob won on almost every prompt."""
    if bob is None:
        return 0.0, 0.0
    d, words = bob["detection"], min(bob["verbosity"], word_limit)
    push = d * (1.2 if not correct else 0.30)
    push += d * HACK_EXPOSURE * sum(alice[k] for k in HACKS)
    push += bob["bluff"] * (0.5 if not correct else -0.7)
    push += BIASES["verbosity"] * words
    push -= 1.1 * max(0.0, bob["verbosity"] - word_limit)      # soft overflow penalty
    return push, 1.2 * d / (0.9 + d)                           # substance saturates


def judge_vote_share(correct, alice, bob, word_limit, rng):
    """Judge sampled 8x independently; reward is the mean vote share (paper 3.4).
    Substance sharpens the judge and dilutes Alice's cues; rhetoric only shoves the
    verdict, which is how an unconstrained Bob turns the judge into a constant."""
    push, substance = critique(correct, alice, bob, word_limit)
    logit = JUDGE_DISCRIM * (1.0 + substance) * (1.0 if correct else -1.0)
    logit += sum(w * alice[k] for k, w in BIASES.items()) / (1.0 + substance)
    return sum(rng.random() < sig(logit - push) for _ in range(8)) / 8.0


def rollout(alice, bob, word_limit, rng, n=N_EVAL, rlvr=False):
    """Returns (mean reward, accuracy, judge MCC vs ground truth)."""
    tot_r = correct_n = tp = fp = tn = fn = 0
    for _ in range(n):
        correct = rng.random() < sig(eff_skill(alice) - rng.gauss(0.55, 0.85))
        r = float(correct) if rlvr else judge_vote_share(correct, alice, bob, word_limit, rng)
        tot_r += r
        correct_n += correct
        said = r > 0.5
        if correct and said:  tp += 1
        elif correct:         fn += 1
        elif said:            fp += 1
        else:                 tn += 1
    den = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) or 1.0
    return tot_r / n, correct_n / n, (tp * tn - fp * fn) / den


def mutate(traits, rng, cap=3.0):
    """(1+1)-ES step. Skill/detection move slowly; persuasion moves freely up to cap."""
    slow = ("skill", "detection")
    return {k: max(-2.0 if k in slow else 0.0, min(4.0 if k in slow else cap,
                   v + (SLOW if k in slow else 1.0) * rng.gauss(0, SIGMA)))
            for k, v in traits.items()}


def train(use_critic, cotrain, word_limit, rlvr=False, seed=11):
    rng = random.Random(seed)
    alice = {"skill": 0.30, "verbosity": 0.02, "authority": 0.02, "impersonation": 0.02}
    bob = {"detection": 0.30, "bluff": 0.02, "verbosity": 0.02} if use_critic else None

    def ev(a, b, s):
        """Common random numbers: candidate and incumbent face the SAME problems and
        judge coin-flips. Without this, eval noise swamps the gradient and nothing --
        not even RLVR -- learns."""
        return rollout(a, b, word_limit, random.Random(s), 150, rlvr)[0]

    hist = []
    for _ in range(STEPS):
        s = rng.randrange(1 << 30)
        cand = mutate(alice, rng)                       # Alice maximizes r
        if ev(cand, bob, s) > ev(alice, bob, s):
            alice = cand
        if bob is not None and cotrain:                 # Bob maximizes 1-r
            s2, cb = rng.randrange(1 << 30), mutate(bob, rng, cap=max(3.0, word_limit))
            if ev(alice, cb, s2) < ev(alice, bob, s2):
                bob = cb
        hist.append(rollout(alice, bob, word_limit, rng, N_EVAL, rlvr))
    return hist, alice, bob


def report(label, hist):
    bars = "▁▂▃▄▅▆▇█"
    sp = lambda v, lo, hi: "".join(bars[min(7, max(0, int((x - lo) / (hi - lo) * 7.99)))] for x in v)
    r, a, m = ([h[i] for h in hist] for i in range(3))
    print(f"\n{label}")
    print(f"  reward    {sp(r, 0.4, 1.0)}  {r[0]:.2f} -> {r[-1]:.2f}")
    print(f"  accuracy  {sp(a, 0.45, 0.90)}  peak {max(a):.3f} @{a.index(max(a))} -> end {a[-1]:.3f}")
    print(f"  judge MCC {sp(m, 0.0, 0.9)}  {m[0]:.2f} -> {m[-1]:.2f}")
    return max(a), a[-1], m[-1]


if __name__ == "__main__":
    print("=" * 78 + "\nDebate Training Reduces Reward Hacking in RLAIF -- simulation\n" + "=" * 78)
    print("Hacking signature: reward RISES while accuracy and judge MCC FALL.")

    cfg = [("1. RLAIF-A    single player          [BASELINE]", (False, False, 1.0, False)),
           ("2. Debate-AB  co-trained Bob, 100w   [THE METHOD]", (True, True, 1.0, False)),
           ("3. Ablation   FROZEN critic", (True, False, 1.0, False)),
           ("4. Ablation   co-trained, NO word limit", (True, True, 9.0, False)),
           ("5. RLVR       verifiable reward      [ROOFLINE]", (False, False, 1.0, True))]

    rows, traits = [], {}
    for label, args in cfg:
        hist, alice, bob = train(*args)
        traits[label[0]] = (alice, bob)
        rows.append((label, *report(label, hist)))

    print("\n" + "=" * 78)
    print(f"{'run':<50}{'peak':>7}{'end':>8}{'drop':>7}{'MCC':>6}\n" + "-" * 78)
    for label, peak, end, mcc in rows:
        print(f"{label:<50}{peak:>7.3f}{end:>8.3f}{peak - end:>7.3f}{mcc:>6.2f}")
    base, deb, roof = rows[0][1], rows[1][1], rows[4][1]
    print("-" * 78)
    print(f"peak-accuracy gap to the RLVR roofline recovered by debate: "
          f"{100 * (deb - base) / max(1e-9, roof - base):.0f}%   (paper: 45%)\n" + "=" * 78)

    print("\nLearned traits -- where did the optimizer actually spend its budget?")
    for k in ("1", "2", "4"):
        a, b = traits[k]
        print(f"  run {k} Alice: " + "  ".join(f"{n}={v:+.2f}" for n, v in a.items()))
        if b:
            print(f"        Bob:   " + "  ".join(f"{n}={v:+.2f}" for n, v in b.items()))
    print("""
Read the table, not the accuracies. Run 1 saturates reward at 1.00 while accuracy
halves and the judge decays to MCC 0 -- Alice bought impersonation and let her real
skill rot. Run 2 holds its peak to the last step. Run 3 shows a frozen critic buys
nothing: Alice routes around it and hacks anyway, which is the paper's "co-training
Bob is essential". Run 4 is the subtler failure -- Alice is fine, but Bob's unlimited
verbosity wins him almost every prompt (reward -> 0.14) and collapses the judge to a
constant classifier. Both players can hack. The word limit is what stops the second.""")
