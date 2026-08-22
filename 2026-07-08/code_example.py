"""
Truncated Jump Sampling (TJS) — Training-Free Diffusion Acceleration
=====================================================================
Demonstrates TJS on a 2D toy flow-matching model (mixture of Gaussians).

What this shows:
1. How the affine path decoder extracts x0 from intermediate states
2. TJS vs full ODE sampling — same model, fewer steps, comparable quality
3. Endpoint uncertainty decay proving late steps have diminishing returns

Run: python3 ~/ai_learning/2026-07-08/code_example.py
Requires: pip install numpy matplotlib  (use ~/ai_learning/.venv/bin/python3)
"""

import numpy as np
import matplotlib.pyplot as plt


# --- Schedule: Linear flow matching (simplest affine path) ---
# Path: xt = (1-t)*x0 + t*epsilon, so alpha(t) = 1-t, sigma(t) = t
# This means at t=0 we have clean data, at t=1 we have noise.
# ODE goes from t=1 (noise) to t=0 (data).

def alpha(t): return 1.0 - t
def sigma(t): return t
def alpha_dot(t): return -1.0
def sigma_dot(t): return 1.0
def path_det(t): return alpha_dot(t) * sigma(t) - alpha(t) * sigma_dot(t)
# path_det = -t - (1-t) = -1 (constant! always nonzero — perfect for decoder)


def make_data(n: int) -> np.ndarray:
    """5-mode Gaussian mixture in 2D."""
    centers = np.array([[2, 2], [-2, 2], [-2, -2], [2, -2], [0, 0]], dtype=float)
    std = 0.35
    idx = np.random.randint(0, 5, n)
    return centers[idx] + np.random.randn(n, 2) * std


def conditional_velocity(xt: np.ndarray, t: float, x0_data: np.ndarray,
                         model_noise: float = 0.0) -> np.ndarray:
    """
    Velocity field for the flow ODE. For the optimal transport path:
    v*(xt, t) = E[x0 - epsilon | xt] = E[x0 | xt] - E[epsilon | xt]

    With linear interpolation xt = (1-t)*x0 + t*eps:
    v*(xt, t) = (x0_hat - xt) / (1 - t)  where x0_hat = E[x0|xt]

    We approximate E[x0|xt] via posterior weights over training data.
    """
    # Compute posterior: p(x0_i | xt) ∝ N(xt; (1-t)*x0_i, t²*I)
    a_t = 1.0 - t
    s_t = max(t, 1e-4)

    diffs = xt[:, None, :] - a_t * x0_data[None, :, :]  # (N, M, 2)
    log_w = -0.5 * np.sum(diffs**2, axis=2) / (s_t**2)  # (N, M)
    log_w -= log_w.max(axis=1, keepdims=True)
    w = np.exp(log_w)
    w /= w.sum(axis=1, keepdims=True) + 1e-10  # (N, M)

    # E[x0 | xt] = sum_i w_i * x0_i
    x0_hat = np.einsum('nm,md->nd', w, x0_data)  # (N, 2)

    # Velocity: points from xt toward x0_hat
    v = (x0_hat - xt) / max(1.0 - t, 1e-4)

    # Simulate imperfect neural network
    if model_noise > 0:
        noise_scale = model_noise * (0.2 + 0.8 * t)  # More error at noisy states
        v += np.random.randn(*v.shape) * noise_scale * (np.abs(v).mean() + 0.1)

    return v


def decode_endpoint(xt: np.ndarray, vt: np.ndarray, t: float) -> np.ndarray:
    """
    THE KEY FORMULA: decode x0 from intermediate state.

    For linear flow matching: xt = (1-t)*x0 + t*eps
    Velocity: vt = x0 - eps = (x0 - xt + (1-t)*x0) / ...

    General decoder: x̂₀ = (σₜ·vθ - σ̇ₜ·xₜ) / Δₜ
    With σ(t)=t, σ̇=1, α(t)=1-t, α̇=-1, Δₜ=-1:
    x̂₀ = (t·vθ - 1·xₜ) / (-1) = xₜ - t·vθ

    Or equivalently: x̂₀ = xₜ + (1-t)·vθ·(dt_remaining)...
    Actually simplest: from v = (x0 - xt)/(1-t), solve for x0:
    x̂₀ = xₜ + (1-t)·v
    """
    return xt + (1.0 - t) * vt


def full_ode_sample(n: int, K: int, x0_data: np.ndarray,
                    noise: float = 0.0) -> np.ndarray:
    """Full ODE from t=1 (noise) to t=0 (data) with K Euler steps."""
    xt = np.random.randn(n, 2)
    dt = 1.0 / K

    for i in range(K):
        t = 1.0 - i * dt  # Goes from 1 toward 0
        v = conditional_velocity(xt, t, x0_data, noise)
        xt = xt - v * dt  # Step toward t=0 (subtract because t decreases)

    return xt


def tjs_sample(n: int, K: int, gamma: float, x0_data: np.ndarray,
               noise: float = 0.0):
    """TJS: run gamma fraction of steps, then decode. Returns (samples, nfe)."""
    xt = np.random.randn(n, 2)
    dt = 1.0 / K
    k_star = int(np.ceil(gamma * K))

    for i in range(k_star):
        t = 1.0 - i * dt
        v = conditional_velocity(xt, t, x0_data, noise)
        xt = xt - v * dt

    # At truncation time, decode endpoint
    t_star = 1.0 - k_star * dt
    v_star = conditional_velocity(xt, t_star, x0_data, noise)
    x0_hat = decode_endpoint(xt, v_star, t_star)

    return x0_hat, k_star + 1  # +1 for the decode velocity eval


def quality_metric(samples: np.ndarray, centers: np.ndarray) -> float:
    """Mean distance to nearest mode center (lower = better, like FID)."""
    samples = np.clip(samples, -10, 10)
    diffs = samples[:, None, :] - centers[None, :, :]
    dists = np.sqrt(np.sum(diffs**2, axis=2))
    return np.mean(dists.min(axis=1))


def endpoint_uncertainty(n_points: int = 200):
    """U(t) = σ²/Δ² for linear flow matching. Shows diminishing returns."""
    t_vals = np.linspace(0.01, 0.99, n_points)
    # For linear FM: sigma=t, delta=-1, so U(t) = t²
    return t_vals, t_vals**2


def main():
    np.random.seed(42)
    centers = np.array([[2, 2], [-2, 2], [-2, -2], [2, -2], [0, 0]], dtype=float)
    n_samples = 1500
    K = 50  # total ODE steps

    # Training data (used as "model memory" for our analytic velocity field)
    x0_data = make_data(500)

    # Noise level simulates neural network imperfection
    noise_level = 0.12

    gammas = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
    results = []

    print("=" * 65)
    print("  Truncated Jump Sampling — Quality vs Speed Tradeoff")
    print(f"  (K={K} steps, {noise_level:.0%} model noise, linear flow matching)")
    print("=" * 65)
    print(f"{'γ':>6} {'NFEs':>5} {'Saved':>7} {'AvgDist':>8} {'vs Base':>8}")
    print("-" * 65)

    for gamma in gammas:
        np.random.seed(123)  # Same noise for fair comparison
        if gamma == 1.0:
            samples = full_ode_sample(n_samples, K, x0_data, noise_level)
            nfe = K
        else:
            samples, nfe = tjs_sample(n_samples, K, gamma, x0_data, noise_level)

        dist = quality_metric(samples, centers)
        saving = 1.0 - nfe / K
        results.append((gamma, nfe, saving, dist, samples))

        if gamma == 1.0:
            rel = "baseline"
        else:
            rel = f"{(results[0][3] / max(dist, 1e-8)) * 100:.0f}%"
        print(f"{gamma:>6.2f} {nfe:>5d} {saving:>6.0%} {dist:>8.4f} {rel:>8}")

    # --- Visualization ---
    fig, axes = plt.subplots(2, 3, figsize=(14, 9))
    fig.suptitle('Truncated Jump Sampling (TJS) — Training-Free Diffusion Acceleration',
                 fontsize=13, fontweight='bold')

    # Row 1: Samples at different γ
    plot_indices = [0, 3, 6]  # γ=1.0, 0.7, 0.4
    for idx, pi in enumerate(plot_indices):
        ax = axes[0, idx]
        gamma, nfe, saving, dist, samples = results[pi]
        ax.scatter(samples[:, 0], samples[:, 1], s=1, alpha=0.4, c='steelblue')
        ax.scatter(centers[:, 0], centers[:, 1], s=120, c='red',
                   marker='x', linewidths=2.5, zorder=5)
        ax.set_xlim(-4.5, 4.5)
        ax.set_ylim(-4.5, 4.5)
        label = "Full ODE" if gamma == 1.0 else f"TJS γ={gamma:.1f}"
        ax.set_title(f'{label}\n{nfe} NFEs ({saving:.0%} saved) | dist={dist:.3f}')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)

    # Row 2, Left: Quality-speed curve
    ax = axes[1, 0]
    nfes = [r[1] for r in results]
    dists = [r[3] for r in results]
    ax.plot(nfes, dists, 'bo-', markersize=8, linewidth=2)
    for gamma, nfe, _, dist, _ in results:
        ax.annotate(f'γ={gamma:.1f}', (nfe, dist), fontsize=7,
                    xytext=(5, 3), textcoords='offset points')
    ax.axhline(y=results[0][3], color='red', linestyle='--', alpha=0.5, label='Full ODE baseline')
    ax.set_xlabel('Neural Function Evaluations (NFEs)')
    ax.set_ylabel('Avg Distance to Mode (lower = better)')
    ax.set_title('Quality-Speed Tradeoff')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Row 2, Middle: Endpoint uncertainty
    ax = axes[1, 1]
    t_vals, u_vals = endpoint_uncertainty()
    ax.plot(t_vals, u_vals, 'r-', linewidth=2.5)
    ax.fill_between(t_vals, u_vals, alpha=0.1, color='red')
    # Mark truncation points
    ax.axvline(x=0.3, color='green', linestyle='--', alpha=0.8, label='γ=0.7 (t*=0.3)')
    ax.axvline(x=0.6, color='orange', linestyle='--', alpha=0.8, label='γ=0.4 (t*=0.6)')
    ax.set_xlabel('Time t (0=clean, 1=noise)')
    ax.set_ylabel('Endpoint Uncertainty U(t) = t²')
    ax.set_title('Late Steps = Diminishing Returns')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.annotate('Low uncertainty\n→ decoder is accurate', xy=(0.15, 0.02),
                fontsize=8, color='green')
    ax.annotate('High uncertainty\n→ must integrate', xy=(0.7, 0.55),
                fontsize=8, color='red')

    # Row 2, Right: The decoder in action
    ax = axes[1, 2]
    # Show one trajectory: ODE path vs TJS jump
    np.random.seed(7)
    xt_traj = np.random.randn(1, 2)
    trajectory = [xt_traj.copy()]
    dt = 1.0 / K
    for i in range(K):
        t = 1.0 - i * dt
        v = conditional_velocity(xt_traj, t, x0_data, 0.0)
        xt_traj = xt_traj - v * dt
        trajectory.append(xt_traj.copy())
    trajectory = np.array(trajectory)[:, 0, :]

    ax.plot(trajectory[:, 0], trajectory[:, 1], 'b-', alpha=0.6, linewidth=1.5, label='Full ODE path')
    ax.scatter(trajectory[0, 0], trajectory[0, 1], s=80, c='purple', zorder=5, marker='s')
    ax.scatter(trajectory[-1, 0], trajectory[-1, 1], s=80, c='blue', zorder=5)

    # TJS jump from midpoint
    mid_idx = int(0.7 * K)  # γ=0.7
    mid_pt = trajectory[mid_idx]
    t_mid = 1.0 - mid_idx * dt
    v_mid = conditional_velocity(mid_pt.reshape(1, -1), t_mid, x0_data, 0.0)
    decoded = decode_endpoint(mid_pt.reshape(1, -1), v_mid, t_mid)[0]
    ax.annotate('', xy=(decoded[0], decoded[1]), xytext=(mid_pt[0], mid_pt[1]),
                arrowprops=dict(arrowstyle='->', color='red', lw=2.5))
    ax.scatter(mid_pt[0], mid_pt[1], s=100, c='orange', zorder=5, marker='D', label=f'Truncate (t*={t_mid:.2f})')
    ax.scatter(decoded[0], decoded[1], s=100, c='red', zorder=5, marker='*', label='TJS decoded x̂₀')
    ax.scatter(centers[:, 0], centers[:, 1], s=60, c='gray', marker='x', linewidths=1.5, alpha=0.5)
    ax.set_title('Single Trajectory: ODE vs TJS Jump')
    ax.legend(fontsize=7, loc='upper left')
    ax.set_xlim(-4.5, 4.5)
    ax.set_ylim(-4.5, 4.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    # Write beside wherever this is run from, not to an absolute path: hardcoding
    # one breaks on any other machine, and it also escaped the build's temp
    # working directory and wrote back into the repo on every rebuild.
    plt.savefig('tjs_results.png', dpi=150, bbox_inches='tight')
    plt.close()

    # --- Summary ---
    print("\n" + "=" * 65)
    print("  KEY TAKEAWAYS")
    print("=" * 65)
    baseline = results[0][3]
    sweet = results[3]  # γ=0.7
    aggressive = results[6]  # γ=0.4
    print(f"  Sweet spot (γ=0.7): {sweet[2]:.0%} fewer NFEs, quality = {baseline/sweet[3]*100:.0f}% of full ODE")
    print(f"  Aggressive (γ=0.4): {aggressive[2]:.0%} fewer NFEs, quality = {baseline/aggressive[3]*100:.0f}% of full ODE")
    print(f"\n  The decoder formula (linear flow matching):")
    print(f"    x̂₀ = xₜ + (1-t)·vθ(xₜ, t)")
    print(f"\n  General formula (any affine schedule):")
    print(f"    x̂₀ = (σₜ·vθ - σ̇ₜ·xₜ) / Δₜ")
    print(f"\n  In production: just stop your sampler early and decode. Done.")
    print(f"\n  Plot: ./tjs_results.png")


if __name__ == "__main__":
    main()
