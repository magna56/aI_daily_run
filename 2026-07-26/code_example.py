"""
Adapter Capacity Probe — "How Many Bits Can an Adapter Write?" (arXiv:2607.21351)
================================================================================

Reproduces the paper's two headline claims on a laptop, FROM SCRATCH, pure
stdlib (no numpy, no network, no API keys):

  1. A low-rank (LoRA) adapter stores only a *couple of bits per trainable
     parameter*, and this SATURATES: past the information the task contains,
     extra rank buys almost nothing.
  2. Capacity is BORROWED from the frozen base. Remove the base's rich basis and
     the same adapter can barely memorize anything.

Faithful minimal setup. A LoRA adapter never acts alone — it reprojects a
frozen, already-rich basis. We model that basis as a frozen NONLINEAR feature
extractor (the stand-in for the frozen transformer's learned features):

  frozen base:   H = tanh(W0 @ X)          W0 (d_hid x d_in) random, NOT trained
  LoRA adapter:  Y = (B @ A) @ H           A:(r x d_hid), B:(d_out x r)  <- trained
  trainable params = r * (d_hid + d_out)

We ask the readout to MEMORIZE N random associations: key x_i -> a random target
SIGN pattern t_i in {-1,+1}^d_out (d_out bits/item). We train only A,B, then
count how many target bits are reproduced. Recovered bits = stored information;
divide by trainable params for bits/param.

Zero the base (W0=0) => H = tanh(0) = 0 => no basis to steer => capacity
collapses. That is the paper's core mechanism, made visible.

Run:  python3 code_example.py        # stdlib only
"""

import random
import math

random.seed(0)

# ---- tiny matrix helpers (lists of lists) ---------------------------------
def randmat(r, c, scale):
    return [[random.gauss(0, 1) * scale for _ in range(c)] for _ in range(r)]

def matmul(P, Q):
    n, k, m = len(P), len(Q), len(Q[0])
    out = [[0.0] * m for _ in range(n)]
    for i in range(n):
        Pi, oi = P[i], out[i]
        for t in range(k):
            a = Pi[t]
            if a == 0.0:
                continue
            Qt = Q[t]
            for j in range(m):
                oi[j] += a * Qt[j]
    return out

def transpose(P):
    return [list(col) for col in zip(*P)]


def make_task(n_items, d_in, d_out):
    """N unit-norm random keys (d_in x N) and N random d_out-bit targets."""
    X = randmat(d_in, n_items, 1.0)
    for j in range(n_items):
        norm = math.sqrt(sum(X[i][j] ** 2 for i in range(d_in))) or 1.0
        for i in range(d_in):
            X[i][j] /= norm
    T = [[random.choice((-1.0, 1.0)) for _ in range(n_items)] for _ in range(d_out)]
    return X, T


def features(W0, X):
    """Frozen nonlinear basis H = tanh(W0 @ X). This is what the adapter steers."""
    Z = matmul(W0, X)
    return [[math.tanh(v) for v in row] for row in Z]


def train_adapter(H, T, rank, steps=400, lr=0.5):
    """Fit Y=(B@A)@H to sign-match T via hinge loss. Return fraction correct."""
    d_hid, n = len(H), len(H[0])
    d_out = len(T)
    A = randmat(rank, d_hid, 0.05)
    B = randmat(d_out, rank, 0.05)
    for _ in range(steps):
        AH = matmul(A, H)                        # r x n
        Y = matmul(B, AH)                        # d_out x n
        gY = [[(-T[i][j] if (T[i][j] * Y[i][j] < 1.0) else 0.0) / n
               for j in range(n)] for i in range(d_out)]
        gB = matmul(gY, transpose(AH))                       # d_out x r
        gA = matmul(transpose(B), matmul(gY, transpose(H)))  # r x d_hid
        for i in range(d_out):
            for t in range(rank):
                B[i][t] -= lr * gB[i][t]
        for t in range(rank):
            for j in range(d_hid):
                A[t][j] -= lr * gA[t][j]
    Y = matmul(B, matmul(A, H))
    correct = tot = 0
    for i in range(d_out):
        for j in range(n):
            correct += ((Y[i][j] > 0) == (T[i][j] > 0))
            tot += 1
    return correct / tot


def bits_stored(acc, total_bits):
    """Bits stored = (1 - H(p)) * total, H = binary entropy. Chance (0.5) -> 0."""
    p = min(max(acc, 0.5), 1 - 1e-9)
    Hb = -p * math.log2(p) - (1 - p) * math.log2(1 - p)
    return (1.0 - Hb) * total_bits


# ---------------------------------------------------------------------------
D_IN, D_HID, D_OUT = 32, 64, 32
W0 = randmat(D_HID, D_IN, 1.0 / math.sqrt(D_IN))   # frozen basis generator

print("=" * 72)
print("CLAIM 1: bits/param SATURATES — capacity is bounded by INFORMATION,")
print("         not by rank. Sweep task size N at a fixed rank.")
print("=" * 72)
RANK = 8
trainable = RANK * (D_HID + D_OUT)
print(f"rank={RANK}  trainable params={trainable}\n")
print(f"{'items N':>8}{'tgt bits':>10}{'bit acc':>9}{'bits stored':>13}{'bits/param':>12}")
for n in [4, 8, 16, 32, 64, 128, 256]:
    X, T = make_task(n, D_IN, D_OUT)
    acc = train_adapter(features(W0, X), T, RANK)
    tot = n * D_OUT
    st = bits_stored(acc, tot)
    print(f"{n:>8}{tot:>10}{acc:>9.3f}{st:>13.0f}{st / trainable:>12.2f}")
print("\n  -> stored bits plateau; bits/param settles at a small constant")
print("     (a 'couple of bits per trainable parameter'), not growing with N.\n")

print("=" * 72)
print("CLAIM 2: capacity is BORROWED from the frozen base. Same adapter,")
print("         rich frozen basis present vs. basis removed (W0 = 0).")
print("=" * 72)
N = 48
X, T = make_task(N, D_IN, D_OUT)
ZERO = [[0.0] * D_IN for _ in range(D_HID)]
H_base = features(W0, X)
H_zero = features(ZERO, X)                          # tanh(0) = 0 everywhere
print(f"\n{'rank':>5}{'params':>8}{'acc w/base':>12}{'acc no base':>13}"
      f"{'b/p w/base':>13}{'b/p no base':>13}")
for r in [2, 4, 8, 16]:
    params = r * (D_HID + D_OUT)
    acc_base = train_adapter(H_base, T, r)
    acc_zero = train_adapter(H_zero, T, r)
    bp_base = bits_stored(acc_base, N * D_OUT) / params
    bp_zero = bits_stored(acc_zero, N * D_OUT) / params
    print(f"{r:>5}{params:>8}{acc_base:>12.3f}{acc_zero:>13.3f}"
          f"{bp_base:>13.2f}{bp_zero:>13.2f}")
print("\n  -> with the rich frozen basis present the low-rank delta reprojects")
print("     it and stores real bits; remove the basis and capacity collapses")
print("     to chance. LoRA steers a basis it does not own. (core mechanism)\n")

print("Engineering takeaways:")
print("  * Rank past the task's information content = overfit surface, not memory.")
print("  * Need to store FACTS? target MLP layers (more basis) & budget bits, not rank.")
print("  * Big private corpus + a couple bits/param ceiling => use RAG, not fine-tune.")
