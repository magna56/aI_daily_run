"""
TTPO's router: using a pseudo-label you don't trust to sort rollouts you can.

Implements the part of Test-Time Policy Optimization (arXiv:2608.27448) that needs no
GPU: majority-vote clustering, the agree/disagree routing, and the token-level masks
each branch applies. majority_vote / route / the two mask functions are the liftable
pieces -- drop them in beside your own sampler and objective.

Then reproduces the asymmetry the method rests on: on hard prompts the vote is wrong
most of the time, yet the rollouts that disagree with a wrong vote are wrong far more
often than chance -- which is what makes disagreement a usable training signal.

Run: python3 code_example.py
"""

import random
from collections import Counter

# --- knobs -------------------------------------------------------------------
# P_CORRECT is per-rollout accuracy on a HARD prompt. Raise it toward 0.4 and watch
# the vote become trustworthy and the asymmetry collapse -- TTPO is aimed squarely
# at the low-accuracy regime where majority voting alone fails.
P_CORRECT = 0.15
TOP_WRONG = 0.30        # one wrong answer is more attractive than the rest
N_WRONG_MODES = 6       # how many distinct wrong answers the rest scatter across
K = 12                  # rollouts sampled per prompt
N_PROMPTS = 4000
SEED = 7


# --- the liftable core -------------------------------------------------------

def canon(answer):
    """Canonical form for clustering. Cluster on this, never on the raw string --
    0.5, 1/2 and \\frac{1}{2} are one answer, and treating them as three silently
    inflates disagreement and starves the distillation branch."""
    return str(answer).strip().rstrip(".0") or "0"


def majority_vote(rollouts, key=canon):
    """Largest cluster of equivalent answers wins. Returns (pseudo_label, members)."""
    clusters = {}
    for r in rollouts:
        clusters.setdefault(key(r["answer"]), []).append(r)
    winner = max(clusters.values(), key=len)
    return key(winner[0]["answer"]), winner


def route(rollouts, key=canon):
    """The whole idea: the pseudo-label picks a BRANCH, it is never a target.

    Returns (label, agreeing, disagreeing). Feed `agreeing` to a soft self-distillation
    loss and `disagreeing` to a grouped-RL penalty. If you ever write
    supervised_ce(rollout, label) you have rebuilt the naive version this replaces.
    """
    label, agreeing = majority_vote(rollouts, key)
    disagreeing = [r for r in rollouts if key(r["answer"]) != label]
    return label, agreeing, disagreeing


def distill_positions(token_entropy, converged_eps=0.15):
    """Positive branch mask: skip positions the policy already agrees with itself on,
    so the pull lands on genuinely uncertain steps instead of reinforcing what is done."""
    return [i for i, h in enumerate(token_entropy) if h > converged_eps]


def penalty_positions(token_logprob, confident_logprob=-0.35):
    """Negative branch mask: punish only where the rollout was CONFIDENT. A disagreeing
    trajectory still contains correct reasoning; unmasked, the penalty destroys it too."""
    return [i for i, lp in enumerate(token_logprob) if lp > confident_logprob]


# --- a sampler standing in for a real model ----------------------------------

def sample_rollouts(rng, k=K):
    """One hard prompt. Correct answers concentrate on 'C'; wrong ones scatter, with
    a single attractive distractor 'W0' that often out-votes the truth."""
    out = []
    rest = 1.0 - P_CORRECT - TOP_WRONG
    for _ in range(k):
        u = rng.random()
        if u < P_CORRECT:
            ans, ok = "C", True
        elif u < P_CORRECT + TOP_WRONG:
            ans, ok = "W0", False
        else:
            ans, ok = "W%d" % rng.randrange(1, N_WRONG_MODES + 1), False
        out.append({"answer": ans, "correct": ok})
    return out


# --- what it proves ----------------------------------------------------------

def main():
    rng = random.Random(SEED)
    votes_wrong = 0
    dis_total = dis_wrong = 0           # disagreers, restricted to WRONG-vote prompts
    naive_misdirected = ttpo_grounded = 0

    for _ in range(N_PROMPTS):
        rollouts = sample_rollouts(rng)
        label, agreeing, disagreeing = route(rollouts)
        vote_is_wrong = (label != "C")

        if vote_is_wrong:
            votes_wrong += 1
            dis_total += len(disagreeing)
            dis_wrong += sum(1 for r in disagreeing if not r["correct"])
            # naive: every rollout is pushed toward a wrong label, every token misled
            naive_misdirected += len(rollouts)

        # TTPO: a penalty on a disagreeing rollout is well-aimed whenever it is wrong,
        # which stays true whether or not the label that flagged it was right.
        ttpo_grounded += sum(1 for r in disagreeing if not r["correct"])

    print("hard prompts simulated:      %d  (K=%d rollouts each)" % (N_PROMPTS, K))
    print("per-rollout accuracy:        %.0f%%" % (100 * P_CORRECT))
    print()
    print("majority vote is WRONG:      %.1f%%   (paper reports ~85%% on hard prompts)"
          % (100 * votes_wrong / N_PROMPTS))
    print("of rollouts disagreeing with a WRONG vote, share also wrong:")
    print("                             %.1f%%   (paper reports ~79%%)"
          % (100 * dis_wrong / dis_total))
    print()
    print("Read those together: the label is unusable as truth and reliable as a router.")
    print()
    print("naive pseudo-label supervision")
    print("  rollouts pushed toward a wrong target: %d" % naive_misdirected)
    print("TTPO routing")
    print("  penalties landing on a genuinely wrong rollout: %d" % ttpo_grounded)

    print("\n-- token masks on one disagreeing rollout --")
    entropy = [0.62, 0.05, 0.41, 0.02, 0.30]
    logprob = [-0.10, -0.20, -0.80, -1.40, -0.05]
    print("  distillation updates positions:", distill_positions(entropy),
          "(skipped the converged ones)")
    print("  penalty applies at positions:  ", penalty_positions(logprob),
          "(confident tokens only -- a different set)")


if __name__ == "__main__":
    main()
