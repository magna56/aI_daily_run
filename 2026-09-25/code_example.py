"""Watermark a model's output without changing a word of it.

Gumbel-max: adding Gumbel noise to logits and taking the argmax draws from
exactly the same distribution as ordinary sampling. Replace that noise with a
pseudorandom function of a secret key and the recent context, and the sampler
still draws from the true distribution -- but you can replay the noise later
and check whether the choices were yours. Detection needs the tokenizer and the
key, not the model.

Both halves are here, plus the finding that matters: the signal comes from
entropy, so the outputs you most want to trace are the hardest to trace.

Run: python3 code_example.py
"""

import hashlib
import math
import random

# --- The knob. Change this and watch detection collapse. ---------------------
# How peaked the model's distribution is, as the probability of its top token.
# 0.05 is a genuinely uncertain model; 0.99 is one emitting boilerplate, JSON or
# the only syntactically legal next token. Peaked output carries almost no
# watermark signal, because the sampler never had a real choice to hide it in.
TOP_P_MASS = 0.20

KEY, VOCAB, CONTEXT_WIDTH = 42, 64, 4
SEED = 7


# --- Liftable core: the PRF, the sampler, the detector -----------------------

def prf(key, context, token_id):
    """Uniform in (0,1), reproducible from the key and the recent context.

    The whole trick. It replaces random() at sampling time, and the detector
    recomputes the same value later: every input is either public (the tokens)
    or held by you (the key).
    """
    material = f"{key}|{','.join(map(str, context))}|{token_id}".encode()
    d = hashlib.sha256(material).digest()
    return (int.from_bytes(d[:7], "big") >> 3) / float(1 << 53)   # 53 bits = f64 mantissa


def watermarked_choice(logits, key, context):
    """Gumbel-max: argmax(logit + Gumbel(u)) draws exactly as sampling does.

    The distribution is untouched. Which valid token wins is now a function of
    the key.
    """
    best, best_score = 0, -math.inf
    for tid, logit in enumerate(logits):
        u = max(prf(key, context, tid), 1e-12)
        score = logit + -math.log(-math.log(u))      # Gumbel(0,1) from u
        if score > best_score:
            best, best_score = tid, score
    return best


def detect(tokens, key, context_width=CONTEXT_WIDTH):
    """p-value that this text is unwatermarked. Needs no model weights.

    A key-chosen token carries an unusually large u, so its score runs high.
    Under the null the sum of scores is Gamma(N, 1).
    """
    scores = [-math.log(1 - max(prf(key, tokens[i - context_width:i], tokens[i]), 1e-12) + 1e-12)
              for i in range(context_width, len(tokens))]
    return gamma_sf(sum(scores), len(scores)), len(scores)


def gamma_sf(s, n):
    """P(Gamma(shape=n, scale=1) >= s), exact for integer n, computed in logs."""
    if n == 0:
        return 1.0
    terms = [k * math.log(s + 1e-12) - math.lgamma(k + 1) for k in range(n)]
    m = max(terms)
    return min(1.0, math.exp(-s + m + math.log(sum(math.exp(t - m) for t in terms))))


# --- The demonstration --------------------------------------------------------

def make_logits(rng, top_mass):
    """Softmax puts roughly `top_mass` on the top token. Parametrized by peak
    rather than temperature, so the question stays interpretable: how much
    choice did the sampler actually have?"""
    # geometric decay over ranks: top token takes roughly `top_mass` of the mass
    decay = -math.log(max(1e-9, 1 - min(top_mass, 0.9999)))
    ranks = list(range(VOCAB))
    rng.shuffle(ranks)
    return [-decay * ranks[i] for i in range(VOCAB)]


def entropy_bits(logits):
    m = max(logits); w = [math.exp(x - m) for x in logits]; z = sum(w)
    return -sum((x / z) * math.log2(x / z) for x in w if x > 0)


def generate(n, key, rng, top_mass, watermark=True):
    tokens = [rng.randrange(VOCAB) for _ in range(CONTEXT_WIDTH)]
    for _ in range(n):
        logits = make_logits(rng, top_mass)
        if watermark:
            tokens.append(watermarked_choice(logits, key, tokens[-CONTEXT_WIDTH:]))
        else:
            m = max(logits)
            tokens.append(rng.choices(range(VOCAB),
                                      weights=[math.exp(x - m) for x in logits])[0])
    return tokens


def main():
    print(f"vocab {VOCAB}, context width {CONTEXT_WIDTH}, top-token mass {TOP_P_MASS}\n")

    print("1. The distribution is untouched -- that is the point of Gumbel-max")
    logits = make_logits(random.Random(1), 0.20)
    m = max(logits)
    w = [math.exp(x - m) for x in logits]
    z, counts, ctx_rng, TRIALS = sum(w), [0] * VOCAB, random.Random(99), 60000
    for _ in range(TRIALS):
        ctx = [ctx_rng.randrange(1 << 30) for _ in range(CONTEXT_WIDTH)]
        counts[watermarked_choice(logits, KEY, ctx)] += 1
    print("   token   true p   watermarked p")
    for t in sorted(range(VOCAB), key=lambda i: -w[i])[:5]:
        print(f"   {t:>5}  {w[t] / z:>7.4f}  {counts[t] / TRIALS:>13.4f}")

    print("\n2. Detection, and how much text it needs")
    print(f"   {'tokens':>8}{'watermarked p':>16}{'plain text p':>15}")
    for n in (25, 50, 100, 200, 400):
        wm = detect(generate(n, KEY, random.Random(SEED), TOP_P_MASS, True), KEY)[0]
        plain = detect(generate(n, KEY, random.Random(SEED), TOP_P_MASS, False), KEY)[0]
        print(f"   {n:>8}{wm:>16.2e}{plain:>15.3f}")

    print("\n3. Where it fails: entropy IS the signal")
    print("   Short text, and a detector that had to try 100 candidate keys --")
    print("   so the threshold tightens to 0.01/100, which is the paper's finding.\n")
    print(f"   {'top-token p':>12}{'entropy':>10}{'p at 60 tokens':>18}  verdict")
    for mass in (0.05, 0.30, 0.70, 0.95, 0.999):
        bits = entropy_bits(make_logits(random.Random(3), mass))
        p = detect(generate(60, KEY, random.Random(SEED), mass, True), KEY)[0]
        verdict = "detected" if p < 0.01 / 100 else "NOT detected"
        print(f"   {mass:>12}{bits:>9.2f}b{p:>18.2e}  {verdict}")

    print("\nA confident model makes no real choice, so there is nothing to hide a")
    print("mark in. Code and structured output are exactly that -- which is why the")
    print("outputs you most want to trace are the ones you can trace least well.")


if __name__ == "__main__":
    main()
