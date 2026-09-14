"""Route a noisy preference pair three ways instead of trusting its label.

PLC-DPO (arXiv:2608.30597) from scratch: the model's own calibrated margin decides
whether each pair is kept, reversed, or canceled. Also runs the control that keeps
you honest -- the routing weights are a training signal, not an audit of your data.

Run:  python3 code_example.py
"""

import math
import random

# Fraction of preference labels that are simply backwards. This is the knob:
# raise it to 0.35 and watch plain DPO collapse. The routed run degrades too --
# correction recovers part of the damage, it does not undo it.
FLIP_RATE = 0.20

TIE_BAND = 0.06      # quality gaps below this are coin flips, not preferences
BETA = 0.5           # DPO reward scale
EPOCHS = 60
LR = 0.35
SEED = 7


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, x))))


class PreferenceRouter:
    """Turns a detached DPO margin into (clean, flip, tie) weights and a gradient.

    The router never sees the true label. Its evidence is where this pair's margin
    sits relative to every other pair -- which is why one backwards label loses the
    argument against the consensus around it.
    """

    def __init__(self, tau_dir=1.0, tau_tie=0.6, prior=(0.80, 0.10, 0.10),
                 gamma_max=1.0, kappa=1.0, alpha=0.05, sigma_min=1e-2, warmup=0.25):
        self.tau_dir, self.tau_tie, self.warmup = tau_dir, tau_tie, warmup
        self.log_prior = [math.log(p) for p in prior]
        self.gamma_max, self.kappa = gamma_max, kappa
        self.alpha, self.sigma_min = alpha, sigma_min
        self.mu, self.var = 0.0, 1.0          # EMA margin statistics

    def calibrate(self, margin):
        # Standardize against the running margin distribution. The evidence is
        # relative: after training here, correct pairs average +1.95 and backwards
        # ones +0.30 -- both positive. Centering is what makes that gap a signal.
        self.mu = (1 - self.alpha) * self.mu + self.alpha * margin
        d = margin - self.mu
        self.var = (1 - self.alpha) * self.var + self.alpha * d * d
        return d / max(math.sqrt(self.var), self.sigma_min)

    def route(self, z):
        # A margin far below the population means the model learned the opposite
        # of this label. One sitting near the middle is a tie: no direction at all.
        logits = [self.log_prior[0] + z / self.tau_dir,
                  self.log_prior[1] - z / self.tau_dir,
                  self.log_prior[2] - abs(z) / self.tau_tie]
        hi = max(logits)
        exps = [math.exp(l - hi) for l in logits]
        total = sum(exps)
        return [e / total for e in exps]

    def grad_wrt_margin(self, margin, progress):
        """d(loss)/d(margin), blending plain DPO with the routed correction."""
        q_clean, q_flip, q_tie = self.route(self.calibrate(margin))

        # Warm up on plain DPO: routing an untrained model would lock in whatever
        # the first few batches happened to suggest.
        gamma = 0.0 if progress < self.warmup else self.gamma_max
        confidence = ((max(q_clean, q_flip, q_tie) - 1 / 3) / (2 / 3)) ** self.kappa
        w = gamma * confidence

        g_clean = -sigmoid(-margin)                                  # -log sigmoid(m)
        g_flip = sigmoid(margin)                                     # -log sigmoid(-m)
        g_tie = sigmoid(abs(margin)) * (1 if margin >= 0 else -1)    # softplus(|m|)
        routed = q_clean * g_clean + q_flip * g_flip + q_tie * g_tie
        return (1 - w) * g_clean + w * routed, (q_clean, q_flip, q_tie)


def make_dataset(rng, flip_rate, n_prompts=40, n_responses=6):
    # Every response appears in five pairs, so consensus can outvote a bad label.
    prompts, pairs = [], []
    for p in range(n_prompts):
        quality = [rng.random() for _ in range(n_responses)]
        prompts.append(quality)
        for i in range(n_responses):
            for j in range(i + 1, n_responses):
                gap = quality[i] - quality[j]
                w, l = (i, j) if gap > 0 else (j, i)
                true_w = w
                if abs(gap) < TIE_BAND:
                    w, l = (i, j) if rng.random() < 0.5 else (j, i)  # annotator guesses
                elif rng.random() < flip_rate:
                    w, l = l, w                                       # label is backwards
                pairs.append({"p": p, "w": w, "l": l, "true_w": true_w,
                              "tie": abs(gap) < TIE_BAND})
    return prompts, pairs


def train(prompts, pairs, router=None):
    rng = random.Random(SEED)
    theta = [[0.0] * len(q) for q in prompts]
    ref = [[rng.gauss(0, 0.1) for _ in q] for q in prompts]
    mix = [0.0, 0.0, 0.0]
    for epoch in range(EPOCHS):
        rng.shuffle(pairs)
        for pr in pairs:
            p, w, l = pr["p"], pr["w"], pr["l"]
            margin = BETA * ((theta[p][w] - ref[p][w]) - (theta[p][l] - ref[p][l]))
            if router is None:
                grad = -sigmoid(-margin)
            else:
                grad, q = router.grad_wrt_margin(margin, epoch / EPOCHS)
                if epoch == EPOCHS - 1:
                    mix = [s + qi for s, qi in zip(mix, q)]
            theta[p][w] -= LR * grad * BETA
            theta[p][l] += LR * grad * BETA
    total = sum(mix) or 1.0
    return theta, [m / total for m in mix]


def ranking_accuracy(pairs, theta):
    # How often the trained scores rank a pair the way true quality does.
    hits = sum(1 for pr in pairs
               if theta[pr["p"]][pr["true_w"]]
               > theta[pr["p"]][pr["w"] if pr["w"] != pr["true_w"] else pr["l"]])
    return 100.0 * hits / len(pairs)


def main():
    # Same run twice: once on corrupted labels, once on clean ones. The second is
    # the control -- if flip weight were a noise detector it would collapse there.
    for tag, rate in ((f"{FLIP_RATE:.0%} noise", FLIP_RATE), ("0% noise, control", 0.0)):
        prompts, pairs = make_dataset(random.Random(SEED), rate)
        bad = sum(1 for pr in pairs if not pr["tie"] and pr["w"] != pr["true_w"])
        dpo, _ = train(prompts, pairs)
        plc, mix = train(prompts, pairs, PreferenceRouter())
        print(f"{tag}: {bad} of {len(pairs)} pairs backwards, "
              f"{sum(1 for pr in pairs if pr['tie'])} true ties")
        print(f"  plain DPO {ranking_accuracy(pairs, dpo):5.1f}%      "
              f"routed {ranking_accuracy(pairs, plc):5.1f}%")
        print(f"  routing mix: clean {mix[0]:.0%}  flip {mix[1]:.0%}  tie {mix[2]:.0%}\n")
    print("Flip weight barely moves between the two runs. Read it as a training\n"
          "signal, never as an estimate of how much of your data is wrong.")


if __name__ == "__main__":
    main()
