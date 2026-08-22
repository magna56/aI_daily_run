#!/usr/bin/env python3
"""
LUMI in miniature: prediction == compression, demonstrated from scratch.

Core idea (arXiv:2607.08221, and DeepMind 2309.10668 before it):
    A lossless compressor and a next-symbol predictor are the SAME object.
    If a model assigns probability p to the symbol that actually occurs,
    an arithmetic coder stores that symbol in ~ -log2(p) bits. So a model
    that PREDICTS pixels well COMPRESSES images well -- losslessly, because
    the decoder re-runs the identical model to recover identical probabilities.

This file implements a real, byte-exact arithmetic (range) coder in pure
Python and drives it with tiny "pixel predictors" standing in for LUMI's
frozen-LLM + 256-way head. No numpy, no torch, no GPU, no API keys.

Run:  python3 code_example.py
"""

import math

ALPHABET = 256          # native pixel alphabet, like LUMI's 256-way head
PREC = 32               # arithmetic coder precision (bits)
TOP = (1 << PREC) - 1
HALF = 1 << (PREC - 1)
QTR = 1 << (PREC - 2)


# ---------------------------------------------------------------------------
# 1. The arithmetic coder. It is model-AGNOSTIC: hand it a probability
#    distribution per symbol and it emits ~ -log2(p) bits. This is the piece
#    LUMI shares with classic codecs; only the probability SOURCE differs.
# ---------------------------------------------------------------------------
class ArithmeticEncoder:
    def __init__(self):
        self.low, self.high, self.pending, self.bits = 0, TOP, 0, []

    def _emit(self, bit):
        self.bits.append(bit)
        self.bits.extend([1 - bit] * self.pending)
        self.pending = 0

    def encode(self, sym, cum_low, cum_high, total):
        rng = self.high - self.low + 1
        self.high = self.low + (rng * cum_high) // total - 1
        self.low = self.low + (rng * cum_low) // total
        while True:
            if self.high < HALF:
                self._emit(0)
            elif self.low >= HALF:
                self._emit(1); self.low -= HALF; self.high -= HALF
            elif self.low >= QTR and self.high < 3 * QTR:
                self.pending += 1; self.low -= QTR; self.high -= QTR
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1

    def finish(self):
        self.pending += 1
        self._emit(0 if self.low < QTR else 1)
        return self.bits


class ArithmeticDecoder:
    def __init__(self, bits):
        self.bits, self.pos = bits, 0
        self.low, self.high = 0, TOP
        self.code = 0
        for _ in range(PREC):
            self.code = (self.code << 1) | self._read()

    def _read(self):
        b = self.bits[self.pos] if self.pos < len(self.bits) else 0
        self.pos += 1
        return b

    def target(self, total):
        rng = self.high - self.low + 1
        return ((self.code - self.low + 1) * total - 1) // rng

    def decode(self, cum_low, cum_high, total):
        rng = self.high - self.low + 1
        self.high = self.low + (rng * cum_high) // total - 1
        self.low = self.low + (rng * cum_low) // total
        while True:
            if self.high < HALF:
                pass
            elif self.low >= HALF:
                self.low -= HALF; self.high -= HALF; self.code -= HALF
            elif self.low >= QTR and self.high < 3 * QTR:
                self.low -= QTR; self.high -= QTR; self.code -= QTR
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1
            self.code = (self.code << 1) | self._read()


# ---------------------------------------------------------------------------
# 2. The "model". LUMI's frozen LLM outputs a 256-way distribution per pixel.
#    Here we use tiny adaptive predictors -- the KEY POINT is that swapping in
#    a better predictor shrinks the file with the SAME coder untouched.
# ---------------------------------------------------------------------------
class UniformModel:
    """Knows nothing. Every pixel costs a full 8 bits -> ratio ~1.0 (like raw)."""
    name = "uniform (no prediction)"
    def freqs(self, _ctx):        return [1] * ALPHABET
    def update(self, _ctx, _sym): pass


class Order0Model:
    """Learns the global pixel histogram adaptively (order-0 entropy coder)."""
    name = "order-0 histogram"
    def __init__(self): self.c = [1] * ALPHABET
    def freqs(self, _ctx):        return self.c
    def update(self, _ctx, sym):  self.c[sym] += 8


class PredictiveModel:
    """Predicts each pixel is NEAR the previous pixel (spatial locality) --
    a stand-in for LUMI's intra-patch positional modeling. Concentrates
    probability mass, so p(actual) is high and -log2(p) is small."""
    name = "predictive (neighbor-aware, LUMI-style)"
    def __init__(self): self.spread = 6
    def freqs(self, ctx):
        f = [1] * ALPHABET
        for d in range(-3 * self.spread, 3 * self.spread + 1):
            v = ctx + d
            if 0 <= v < ALPHABET:
                f[v] += int(400 * math.exp(-(d * d) / (2 * self.spread ** 2)))
        return f
    def update(self, _ctx, _sym): pass


# ---------------------------------------------------------------------------
# 3. Compress / decompress. Note the decode loop is EXACTLY an LLM generation
#    loop -- feed context, get distribution -- except we ENCODE the known
#    symbol against the distribution instead of SAMPLING from it.
# ---------------------------------------------------------------------------
def cum(freqs, sym):
    lo = sum(freqs[:sym]); return lo, lo + freqs[sym], sum(freqs)

def compress(data, model):
    enc, ideal_bits, ctx = ArithmeticEncoder(), 0.0, 128
    for sym in data:
        f = model.freqs(ctx)
        lo, hi, tot = cum(f, sym)
        ideal_bits += -math.log2((hi - lo) / tot)   # Shannon cost of this pixel
        enc.encode(sym, lo, hi, tot)
        model.update(ctx, sym); ctx = sym
    return enc.finish(), ideal_bits

def decompress(bits, n, model):
    dec, out, ctx = ArithmeticDecoder(bits), [], 128
    for _ in range(n):
        f = model.freqs(ctx)
        t = dec.target(sum(f))
        c, sym = 0, 0
        for i, fi in enumerate(f):          # find symbol whose interval holds t
            if c + fi > t: sym = i; break
            c += fi
        lo, hi, tot = cum(f, sym)
        dec.decode(lo, hi, tot)
        out.append(sym); model.update(ctx, sym); ctx = sym
    return out


def make_image(n=4000):
    """Synthetic smooth 'scan line' with structure -- pixels correlate with
    neighbors, exactly the redundancy a spatial predictor can exploit."""
    px, v = [], 128
    for i in range(n):
        v += int(12 * math.sin(i / 40)) - v // 30 + ((i * 37) % 7 - 3)
        px.append(max(0, min(255, v)))
    return px


if __name__ == "__main__":
    img = make_image()
    raw_bits = len(img) * 8
    print(f"Image: {len(img)} pixels, raw = {raw_bits} bits ({raw_bits//8} bytes)\n")
    print(f"{'model':<38}{'bytes':>8}{'ratio':>8}{'ideal':>9}  round-trip")
    print("-" * 75)
    for M in (UniformModel(), Order0Model(), PredictiveModel()):
        enc_model = M.__class__() if hasattr(M, "__dict__") else M
        bits, ideal = compress(img, M)
        out_bytes = math.ceil(len(bits) / 8)
        ok = decompress(bits, len(img), M.__class__()) == img
        ratio = out_bytes / (raw_bits / 8)
        print(f"{M.name:<38}{out_bytes:>8}{ratio:>8.3f}{ideal/8:>9.0f}  "
              f"{'OK (lossless)' if ok else 'MISMATCH!'}")

    print("\nTakeaways:")
    print(" * Same arithmetic coder for all three -- only the PREDICTOR changed.")
    print(" * Better prediction -> smaller file. Compression IS prediction.")
    print(" * 'ideal' column (-sum log2 p / 8) matches actual bytes to ~1 byte:")
    print("   the coder hits the Shannon bound. LUMI just makes the predictor")
    print("   a frozen LLM with a pixel-embedding front-end and 256-way head.")
    print(" * Every round-trip is byte-exact: losslessness is FREE when encoder")
    print("   and decoder run the identical deterministic model on identical context.")
