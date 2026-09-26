"""Average two prompts' embeddings and the model averages their answers.

A transformer is built out of nonlinear parts, so this should not work. Feed it
the element-wise mean of two sequences' token embeddings and the next-token
distribution comes back close to the mean of the two distributions you would
have got separately. The paper calls this the Superposition Linearity
Hypothesis, and reports it gets WORSE as pretraining proceeds -- evidence that
it is a property of the architecture rather than something learned.

This builds a toy stack with a tunable amount of nonlinearity and measures the
same ratio the paper does. Run: python3 code_example.py
"""

import math
import random

# --- The knob. Change this and watch superposition die. ----------------------
# How nonlinear the block is. 0.0 is a purely linear map, where superposition is
# exact by construction. Real transformers sit somewhere in the middle, which is
# the whole surprise.
NONLINEARITY = 0.35

SEED, VOCAB, DIM, TOKENS = 11, 256, 64, 12
TRIALS = 200


# --- Liftable core: the measurement the paper runs ---------------------------

def softmax(v, temp=1.0):
    m = max(v)
    e = [math.exp((x - m) / temp) for x in v]
    z = sum(e)
    return [x / z for x in e]


def kl(p, q):
    """D(p || q). Guarded, because a zero in q is a real possibility here."""
    return sum(p[i] * math.log(p[i] / max(q[i], 1e-12))
               for i in range(len(p)) if p[i] > 0)


def approximation_ratio(d_target_mix, d_a_b):
    """The paper's normalization: divergence to the target over divergence
    between two unrelated contexts.

    Below 1.0 means the mixed output is closer to the average of the two
    answers than the two answers are to each other -- which is the claim.
    Without this normalization a small KL means nothing, because you do not
    know what scale 'small' is on.
    """
    return d_target_mix / max(d_a_b, 1e-12)


def rank_survival(target, mixed, k):
    """Fraction of the target's top-k that survives in the mixed top-k.

    Distances are abstract; this is the number you can picture. The paper
    reports 30-40% at k=10 and 60-65% at k=100 on real models.
    """
    t = sorted(range(len(target)), key=lambda i: -target[i])[:k]
    m = set(sorted(range(len(mixed)), key=lambda i: -mixed[i])[:k])
    return sum(1 for i in t if i in m) / k


# --- A toy stack with a dial between linear and not --------------------------

class ToyModel:
    """embed -> block -> unembed. The block is linear blended with a squashing
    nonlinearity, so NONLINEARITY interpolates between the two regimes."""

    def __init__(self, rng, weight_scale=1.0):
        self.emb = [[rng.gauss(0, 0.4) for _ in range(DIM)] for _ in range(VOCAB)]
        # deliberately large: the pre-activation has to reach tanh's saturating
        # region or the nonlinearity dial is a no-op
        self.w = [[rng.gauss(0, 6.0 * weight_scale / math.sqrt(DIM)) for _ in range(DIM)]
                  for _ in range(DIM)]
        self.head = [[rng.gauss(0, 3.0 / math.sqrt(DIM)) for _ in range(DIM)]
                     for _ in range(VOCAB)]

    def embed(self, tokens):
        out = [0.0] * DIM
        for t in tokens:
            for d in range(DIM):
                out[d] += self.emb[t][d]
        return [x / len(tokens) for x in out]

    def forward(self, h, nonlin):
        mixed = []
        for row in self.w:
            acc = sum(row[d] * h[d] for d in range(DIM))
            # blend the linear response with a saturating one
            mixed.append((1 - nonlin) * acc + nonlin * 3.0 * math.tanh(acc))
        return softmax([sum(r[d] * mixed[d] for d in range(DIM)) for r in self.head])


def measure(model, rng, nonlin):
    ratios, surv10, surv100 = [], [], []
    for _ in range(TRIALS):
        a = [rng.randrange(VOCAB) for _ in range(TOKENS)]
        b = [rng.randrange(VOCAB) for _ in range(TOKENS)]
        ea, eb = model.embed(a), model.embed(b)
        pa, pb = model.forward(ea, nonlin), model.forward(eb, nonlin)
        # the mix happens at the EMBEDDING layer, exactly as the paper does it
        p_mix = model.forward([(ea[d] + eb[d]) / 2 for d in range(DIM)], nonlin)
        p_target = [(pa[i] + pb[i]) / 2 for i in range(VOCAB)]
        ratios.append(approximation_ratio(kl(p_target, p_mix), kl(pa, pb)))
        surv10.append(rank_survival(p_target, p_mix, 10))
        surv100.append(rank_survival(p_target, p_mix, 100))
    n = len(ratios)
    return sum(ratios) / n, sum(surv10) / n, sum(surv100) / n


def main():
    rng = random.Random(SEED)
    model = ToyModel(random.Random(SEED))

    print(f"vocab {VOCAB}, dim {DIM}, {TRIALS} prompt pairs\n")
    print("1. Superposition against how nonlinear the block is")
    print(f"   {'nonlinearity':>13}{'approx ratio':>15}{'top-10 kept':>14}{'top-100 kept':>15}")
    for nl in (0.0, 0.15, 0.35, 0.6, 0.9):
        r, s10, s100 = measure(model, random.Random(SEED), nl)
        # Not zero even at 0.0, and that is worth seeing: the block is linear
        # here, but softmax is not, so softmax(mean) != mean(softmax). The
        # output nonlinearity sets the floor before the body adds anything.
        tag = "  <- body is linear; softmax is not" if nl == 0.0 else ""
        print(f"   {nl:>13}{r:>15.3f}{s10:>13.0%}{s100:>15.0%}{tag}")

    print("\n   A ratio below 1.0 means the mixed output sits closer to the average of")
    print("   the two answers than the two answers sit to each other. Note the first")
    print("   row: even a linear body does not superpose exactly, because the softmax")
    print("   on the end is itself nonlinear. That is the floor everything else adds to.\n")

    print("2. The paper's stranger finding: it gets worse as training proceeds")
    print(f"   {'weight scale':>13}{'approx ratio':>15}   (a proxy for pretraining)")
    for scale in (0.5, 1.0, 2.0, 4.0):
        m = ToyModel(random.Random(SEED), weight_scale=scale)
        r, _, _ = measure(m, random.Random(SEED), NONLINEARITY)
        print(f"   {scale:>13}{r:>15.3f}")

    print("\nSuperposition is strongest in the untrained network and decays from there.")
    print("That is the evidence it belongs to the architecture, not to what was learned.")


if __name__ == "__main__":
    main()
