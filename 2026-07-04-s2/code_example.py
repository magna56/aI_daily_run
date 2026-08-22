"""NVFP4 Quantization: 4-Bit Floating Point from Scratch

Implements NVIDIA's NVFP4 quantization scheme including all three scaling
strategies (max, MSE, four-over-six). Shows how neural network weights
compress to just 8 representable values with minimal accuracy loss.

Run: python3 code_example.py
Dependencies: none (stdlib only)
"""

import random
import math

# The 8 positive values representable in NVFP4
FP4_GRID = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0]
FP4_SIGNED = sorted([-v for v in FP4_GRID if v > 0] + FP4_GRID)  # 15 values + 0


def generate_weights(n: int, seed: int = 42) -> list[float]:
    """Generate realistic neural network weights (roughly Gaussian, some outliers)."""
    random.seed(seed)
    weights = []
    for _ in range(n):
        if random.random() < 0.02:  # 2% outliers
            weights.append(random.gauss(0, 0.3))
        else:
            weights.append(random.gauss(0, 0.05))
    return weights


def quantize_to_fp4(value: float, scale: float) -> float:
    """Quantize a single value to the nearest NVFP4 grid point."""
    if scale == 0:
        return 0.0
    normalized = value / scale
    sign = -1.0 if normalized < 0 else 1.0
    abs_val = abs(normalized)
    best = min(FP4_GRID, key=lambda g: abs(g - abs_val))
    return sign * best * scale


# --- Scaling Strategy 1: Max Scaling ---

def max_scale(block: list[float]) -> float:
    """Scale = max(|w|) / 6.0  (simple, outlier-sensitive)."""
    max_abs = max(abs(w) for w in block)
    return max_abs / 6.0 if max_abs > 0 else 1.0


# --- Scaling Strategy 2: MSE Scaling ---

def mse_scale(block: list[float], n_search: int = 20) -> float:
    """Find scale that minimizes reconstruction MSE via grid search."""
    max_abs = max(abs(w) for w in block)
    if max_abs == 0:
        return 1.0
    best_scale, best_mse = max_abs / 6.0, float('inf')
    for i in range(1, n_search + 1):
        s = max_abs / 6.0 * (i / n_search * 2)
        mse = sum((w - quantize_to_fp4(w, s)) ** 2 for w in block) / len(block)
        if mse < best_mse:
            best_mse = mse
            best_scale = s
    return best_scale


# --- Scaling Strategy 3: Four-over-Six Scaling ---

def four_over_six_scale(block: list[float]) -> tuple[float, str]:
    """Try both M=4 and M=6 grids, pick the one with lower MSE.
    M=4 grid: {0, 0.5, 1, 1.5, 2, 2.5, 3, 4} scaled to max/4
    M=6 grid: {0, 0.5, 1, 1.5, 2, 3, 4, 6} scaled to max/6
    Returns (scale, grid_choice)."""
    max_abs = max(abs(w) for w in block)
    if max_abs == 0:
        return 1.0, "M=4"
    s6 = max_abs / 6.0
    mse6 = sum((w - quantize_to_fp4(w, s6)) ** 2 for w in block) / len(block)
    s4 = max_abs / 4.0
    mse4 = sum((w - quantize_to_fp4(w, s4)) ** 2 for w in block) / len(block)
    return (s4, "M=4") if mse4 < mse6 else (s6, "M=6")


def quantize_block(block: list[float], scale: float) -> list[float]:
    return [quantize_to_fp4(w, scale) for w in block]


def compute_mse(original: list[float], quantized: list[float]) -> float:
    return sum((a - b) ** 2 for a, b in zip(original, quantized)) / len(original)


def compute_snr(original: list[float], quantized: list[float]) -> float:
    signal_power = sum(w ** 2 for w in original) / len(original)
    noise_power = compute_mse(original, quantized)
    if noise_power == 0:
        return float('inf')
    return 10 * math.log10(signal_power / noise_power)


def main():
    print("=" * 65)
    print("  NVFP4 QUANTIZATION — 4-Bit Floating Point from Scratch")
    print("  Based on NVIDIA Developer Blog (June 26, 2026)")
    print("=" * 65)

    # --- Show the FP4 grid ---
    print(f"\nNVFP4 representable values (positive): {FP4_GRID}")
    print(f"Total values with sign: {len(FP4_SIGNED)} "
          f"(vs 65536 for FP16, 256 for INT8, 16 for INT4)")

    # --- Generate weights ---
    N = 1024
    BLOCK_SIZE = 32
    weights = generate_weights(N)
    blocks = [weights[i:i+BLOCK_SIZE]
              for i in range(0, N, BLOCK_SIZE)]

    print(f"\nWeight stats: n={N}, mean={sum(weights)/N:.4f}, "
          f"std={math.sqrt(sum((w-sum(weights)/N)**2 for w in weights)/N):.4f}, "
          f"range=[{min(weights):.4f}, {max(weights):.4f}]")

    # --- Compare scaling strategies ---
    print(f"\n{'─' * 65}")
    print("SCALING STRATEGY COMPARISON")
    print(f"{'─' * 65}")
    print(f"{'Strategy':<20} {'MSE':>12} {'SNR (dB)':>10} {'Max Err':>10}")
    print(f"{'─' * 20} {'─' * 12} {'─' * 10} {'─' * 10}")

    strategies = {
        "Max Scaling": max_scale,
        "MSE Scaling": mse_scale,
    }

    for name, scale_fn in strategies.items():
        all_q = []
        for block in blocks:
            s = scale_fn(block)
            all_q.extend(quantize_block(block, s))
        mse = compute_mse(weights, all_q)
        snr = compute_snr(weights, all_q)
        max_err = max(abs(a - b) for a, b in zip(weights, all_q))
        print(f"{name:<20} {mse:>12.8f} {snr:>10.1f} {max_err:>10.6f}")

    # Four-over-six (special case)
    all_q_46 = []
    m4_count = 0
    for block in blocks:
        s, grid = four_over_six_scale(block)
        if grid == "M=4":
            m4_count += 1
        all_q_46.extend(quantize_block(block, s))
    mse_46 = compute_mse(weights, all_q_46)
    snr_46 = compute_snr(weights, all_q_46)
    max_err_46 = max(abs(a - b) for a, b in zip(weights, all_q_46))
    print(f"{'Four-over-Six':<20} {mse_46:>12.8f} {snr_46:>10.1f} {max_err_46:>10.6f}")
    print(f"\n  Four-over-six chose M=4 for {m4_count}/{len(blocks)} blocks "
          f"({m4_count/len(blocks):.0%})")

    # --- Compression analysis ---
    print(f"\n{'─' * 65}")
    print("COMPRESSION ANALYSIS")
    print(f"{'─' * 65}")
    fp16_bytes = N * 2
    fp4_bytes = N * 0.5 + len(blocks) * 1  # 4 bits/weight + 8-bit scale/block
    fp4_46_bytes = fp4_bytes + len(blocks) * 0.125  # +1 bit per block for grid choice
    bpe = fp4_46_bytes * 8 / N

    print(f"  FP16 size:           {fp16_bytes:>6} bytes ({N * 16} bits)")
    print(f"  NVFP4 size:          {fp4_bytes:>6.0f} bytes "
          f"(4 bits/weight + FP8 scale/block)")
    print(f"  Four-over-six size:  {fp4_46_bytes:>6.1f} bytes "
          f"(+1 bit/block for grid select)")
    print(f"  Compression ratio:   {fp16_bytes / fp4_46_bytes:.1f}x")
    print(f"  Effective BPE:       {bpe:.2f} bits/element "
          f"(NVIDIA reports 5.03 BPE)")

    # --- Distribution of quantized values ---
    print(f"\n{'─' * 65}")
    print("QUANTIZED VALUE DISTRIBUTION (four-over-six)")
    print(f"{'─' * 65}")
    from collections import Counter
    rounded = [round(v, 4) for v in all_q_46]
    counts = Counter(rounded)
    top_values = counts.most_common(10)
    total = sum(counts.values())
    for val, count in top_values:
        bar = "#" * int(count / total * 60)
        print(f"  {val:>8.4f}: {count:>4} ({count/total:>5.1%}) {bar}")

    # --- Simulate per-layer sensitivity ---
    print(f"\n{'─' * 65}")
    print("PER-LAYER SENSITIVITY (why mixed precision matters)")
    print(f"{'─' * 65}")
    print(f"{'Layer Type':<25} {'Weights':<10} {'FP4 SNR':>10} {'Recommendation':>16}")
    print(f"{'─' * 25} {'─' * 10} {'─' * 10} {'─' * 16}")

    layers = [
        ("Embedding", generate_weights(256, seed=1), "BF16"),
        ("Attention QKV", generate_weights(256, seed=2), "FP8"),
        ("MoE Shared Expert", generate_weights(256, seed=3), "FP8"),
        ("MoE Routed Expert", generate_weights(256, seed=4), "NVFP4"),
        ("LayerNorm", generate_weights(256, seed=5), "BF16"),
    ]

    for name, lw, rec in layers:
        lb = [lw[i:i+32] for i in range(0, len(lw), 32)]
        lq = []
        for b in lb:
            s, _ = four_over_six_scale(b)
            lq.extend(quantize_block(b, s))
        snr = compute_snr(lw, lq)
        print(f"{name:<25} {len(lw):<10} {snr:>9.1f}  {rec:>16}")

    print(f"\n  Lower SNR = more quantization noise = needs higher precision")
    print(f"  MoE routed experts tolerate FP4 because they're sparsely activated")
    print()


if __name__ == "__main__":
    main()
