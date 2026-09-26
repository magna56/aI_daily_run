"""Multiply against packed 4-bit weights without ever expanding them.

A 4B model at Q4_K_M is 2.74 GB on disk and 8.42 GB once dequantized to bf16.
The old path did exactly that expansion to run a matmul, so the file you could
download was not the memory you needed. Transformers now reads the packed
weights directly through ggml kernels, and the expanded tensor is never built.

This implements both read paths over the same quantized weights and accounts
for the bytes each one allocates. Run: python3 code_example.py
"""

import array
import math
import random
import struct

# --- The knob. Change this and watch the ratio move. -------------------------
# Weights per block, each block carrying its own scale. Smaller blocks track the
# weight distribution more closely and cost more scale bytes per weight; this is
# the whole quality-versus-size dial inside a quantization scheme.
BLOCK = 32

BITS, SEED, ROWS, COLS = 4, 5, 64, 512


# --- Liftable core: pack, and the two ways to read it back -------------------

def quantize_block(weights):
    """One block -> (scale, packed nibbles). The scale is what keeps 4 bits usable.

    Every block picks its own scale, so a row with one large outlier does not
    crush the resolution of every other weight in the tensor.
    """
    peak = max(abs(w) for w in weights) or 1e-8
    scale = peak / 7.0                                   # 4 bits signed: -8..7
    codes = [max(0, min(15, int(round(w / scale)) + 8)) for w in weights]
    packed = bytearray()
    for i in range(0, len(codes), 2):                    # two weights per byte
        packed.append((codes[i] & 0xF) | ((codes[i + 1] & 0xF) << 4))
    return scale, bytes(packed)


def unpack_block(scale, packed, out):
    """Write one block's weights into a reusable buffer. Allocates nothing."""
    j = 0
    for byte in packed:
        out[j] = ((byte & 0xF) - 8) * scale
        out[j + 1] = (((byte >> 4) & 0xF) - 8) * scale
        j += 2


class PackedMatrix:
    """Rows of quantized blocks. This is the shape a GGUF file stores."""

    def __init__(self, rows, cols, rng):
        self.rows, self.cols = rows, cols
        self.blocks = []
        for _ in range(rows):
            row = [rng.gauss(0, 0.06) for _ in range(cols)]
            self.blocks.append([quantize_block(row[i:i + BLOCK])
                                for i in range(0, cols, BLOCK)])

    def packed_bytes(self):
        # 4 bits per weight, plus one float32 scale per block
        per_row = (self.cols * BITS) // 8 + (self.cols // BLOCK) * 4
        return per_row * self.rows

    def expanded_bytes(self):
        return self.rows * self.cols * 2                 # bf16, two bytes each


def matmul_dequantized(mat, x):
    """The old path: build the whole float tensor, then multiply.

    Correct, simple, and it needs the expanded tensor resident before the first
    multiply happens. That peak is what decides whether the model loads at all.
    """
    weights = array.array("f", bytes(4 * mat.rows * mat.cols))
    buf = array.array("f", bytes(4 * BLOCK))
    k = 0
    for row in mat.blocks:
        for scale, packed in row:
            unpack_block(scale, packed, buf)
            for v in buf:
                weights[k] = v
                k += 1
    out = []
    for r in range(mat.rows):
        base = r * mat.cols
        out.append(sum(weights[base + c] * x[c] for c in range(mat.cols)))
    return out, 4 * mat.rows * mat.cols                  # bytes held at the peak


def matmul_packed(mat, x):
    """The new path: unpack one block at a time into a buffer you reuse.

    The full tensor is never materialized. Peak allocation is one block, which
    does not grow with the model.
    """
    buf = array.array("f", bytes(4 * BLOCK))
    out = []
    for row in mat.blocks:
        acc, c = 0.0, 0
        for scale, packed in row:
            unpack_block(scale, packed, buf)
            for t in range(BLOCK):
                acc += buf[t] * x[c + t]
            c += BLOCK
        out.append(acc)
    return out, 4 * BLOCK                                # bytes held at the peak


def main():
    rng = random.Random(SEED)
    mat = PackedMatrix(ROWS, COLS, rng)
    x = [rng.gauss(0, 1) for _ in range(COLS)]

    print(f"{ROWS}x{COLS} weight matrix, {BITS}-bit, block size {BLOCK}\n")
    print(f"  on disk, packed     : {mat.packed_bytes():>10,} bytes")
    print(f"  expanded to bf16    : {mat.expanded_bytes():>10,} bytes")
    print(f"  ratio               : {mat.expanded_bytes() / mat.packed_bytes():>10.2f}x\n")

    deq, peak_deq = matmul_dequantized(mat, x)
    packed_out, peak_pack = matmul_packed(mat, x)

    print("Both paths compute the same thing:")
    drift = max(abs(a - b) for a, b in zip(deq, packed_out))
    print(f"  largest difference between the two outputs: {drift:.2e}\n")

    print("They do not cost the same to run:")
    print(f"  dequantize first, peak held : {peak_deq:>10,} bytes")
    print(f"  read packed, peak held      : {peak_pack:>10,} bytes")
    print(f"  ratio                       : {peak_deq / peak_pack:>10,.0f}x\n")

    print("What that ratio buys on a real machine:")
    print(f"   {'unified memory':>16}{'largest bf16 model':>22}{'largest 4-bit model':>22}")
    for ram in (8, 16, 32, 64):
        usable = ram * 0.75                    # OS and activations need room too
        bf16_b = usable / 2.0                  # 2 bytes per parameter
        q4_b = usable / 0.56                   # ~4.5 bits per weight with scales
        print(f"   {ram:>13} GB{bf16_b:>19.1f} B{q4_b:>21.1f} B")

    print("\nThe file you can download was never the constraint. The tensor the old")
    print("read path built before the first multiply was.")


if __name__ == "__main__":
    main()
