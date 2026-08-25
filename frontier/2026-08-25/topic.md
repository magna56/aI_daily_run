# How to Read Skipped Tokens in 8 Bits

**Category**: AI Hardware for Engineers
**Tags**: quantization, inference-serving, paper, latency
**Date**: 2026-08-25
**Level**: Deeper
**For**: How models work
**Hook**: Sparse attention decides some parts of a long prompt do not matter and throws them away. A paper this month takes the exact same map and, instead of skipping those parts, reads them cheaply — keeping every token connected while running 2.2 times faster.
**Time to read**: ~10 minutes

## Explain Like I'm 5

You are given a very long book and one question to answer. You do not have time to read every page carefully. One approach: decide in advance which pages probably matter, read those, and rip the rest out — now they cannot help you even if you were wrong about them. Another approach: read every single page, but read the probably-boring ones fast and sloppily. You still come away knowing *something* from every page. If a crucial sentence was hiding on page 400, the first method has no chance of catching it and the second has a decent one. Both take about the same time. This session is about a paper that noticed the second option was available and nobody had taken it.

## The Problem

Feeding a long prompt to a model is expensive before a single word is generated. That phase is *prefill*, and its cost is dominated by attention comparing every token to every other token — quadratic work and quadratic memory traffic. The field has two standard answers and both give something up. **Uniform low precision** runs the whole attention computation in INT8: fast everywhere, and it measurably loses long-context accuracy. **Sparse attention** keeps full precision but computes only some token interactions, deciding structurally that the rest are worth nothing — which breaks dense connectivity, and is wrong exactly when the thing you needed was in a block that got skipped. What nobody had done is treat precision as a *spatial* decision inside a normal dense attention kernel.

## For a Software Engineer

**This is mipmapping, and you have shipped it.** In graphics you do not render distant geometry at full texture resolution; you render it at a lower one, because it still needs to be *there* and it does not need to be *sharp*. The near/far decision is made from a spatial map, cheaply, ahead of time. That is precisely this paper: attention's score matrix is cut into tiles, a map says which tiles are "far," and far tiles are computed in INT8 rather than skipped. The alternative approaches map to "render everything at full res" and "don't draw distant objects at all."

**The trade is real and it is measured.** On LV-Eval question answering at 64k tokens with LLaMA 3.2 3B, FP16 scores **7.75**, uniform INT8 collapses to **5.42**, and this method scores **7.44** — recovering most of what uniform quantization destroys. Throughput at 4k tokens goes from **14.33K tokens/s** for FlashAttention to **31.80K tokens/s**, a **2.22×** speedup.

**The part that surprised me is what the routing is not.** I expected an adaptive criterion — compute some cheap statistic per tile, route the low-energy ones to INT8. There is no such statistic. The routing map is **static and data-free**, instantiated offline from the same spatial templates sparse attention already uses (BigBird, Sparse Transformer). The paper's contribution is not a better way to *find* unimportant regions. It is the observation that once you have such a map, **skipping is a strictly worse use of it than cheapening**.

**Monday morning:** nothing, honestly — this is a fused CUDA kernel, not a config flag. But if you maintain a serving stack and have ever rejected INT8 attention because it cost you long-context recall, this is the shape of the fix, and the mechanism is worth being able to reason about before it shows up in your inference library.

## What This Means for You

**When this matters.** You serve long-context prompts and prefill dominates your latency and your bill. Or you evaluated INT8 attention, watched retrieval quality drop, and went back to FP16 concluding that quantized attention does not work for your workload.

**How it affects you.** The conclusion "INT8 attention loses long-context quality" is true of *uniform* INT8 and this paper is evidence it is not true of INT8 as such. That distinction matters if you are making roadmap decisions about quantized serving. It also gives you a knob that did not exist before: an INT8 coverage budget (the paper evaluates 25%, 50%, 75%) that trades accuracy for throughput continuously, rather than the binary choice you have today.

**What to do about it.** Nothing yet, and that is the honest answer — there is no released kernel to drop in. What you *can* do is stop treating precision as a global setting when you think about attention. If your stack quantizes attention, it almost certainly does so uniformly, and the measurements here say uniform is the worst way to spend a fixed precision budget. Watch for tile-level precision routing appearing in FlashAttention-family kernels; that is the signal that this becomes an option rather than a paper.

## What It Is

TileMix (arXiv 2608.17336, Zhang et al., 18 August 2026) is a fused attention kernel that makes numerical precision a *spatial* decision. The attention score matrix is partitioned into hardware-aligned tiles — 128 query tokens by 64 key tokens in the default configuration. A binary routing map, indexed by KV head, query-tile row, and key-tile group, says which groups run INT8 and which run FP16: `R = 1` dispatches to INT8, `R = 0` to FP16.

Both precision paths write into a **shared online-softmax state**. This is the piece that makes it a single fused kernel rather than two passes: online softmax already maintains a running maximum and a running sum so it can process the score matrix tile by tile without materialising it, and both the FP16 and INT8 tiles update that same running state. The precision of a tile changes how its scores are computed, not how they are combined.

Because every legal tile group is routed somewhere rather than dropped, **dense token connectivity is preserved** — every query still attends to every key, some of them coarsely. The method needs no training, and supports grouped-query attention, variable-length batches, and INT8 KV caches.

## Why It Matters

The interesting claim here is not the speedup. It is that a spatial prior which the field has spent years using to justify *deletion* turns out to be better spent on *degradation*. Sparse attention's templates encode "these interactions are probably unimportant." Acting on that belief by skipping is an irreversible bet: if the belief is wrong for this particular input, the information is simply gone. Acting on it by lowering precision is a recoverable one — a wrong guess costs you accuracy on that tile, not its existence. The numbers say the recoverable bet is better, and it costs the same.

There is a real critique to make, and the paper is upfront enough that it is easy to make fairly: **the routing is static and data-free**, so this is not adaptive computation. It inherits whatever biases the sparse-attention templates carry, and it cannot notice that a particular prompt puts something important in a region the template calls boring. An adaptive router — cheap per-tile statistic, runtime decision — is the obvious next paper, and this one does not claim to be it. What it does claim, and supports, is that the *dispatch mechanism* works: you can route precision spatially inside a fused dense kernel without breaking the softmax, and the metadata stays small enough to be free.

## Key Technical Details

**Background first.** Attention computes a score for every query-key pair, softmaxes each query's row, and uses the result to average value vectors. *Online softmax* is the trick that lets you do this tile by tile without holding the full score matrix: you keep a running max and a running normaliser per query row, rescaling the accumulated output whenever a new tile raises the max. *Blockwise INT8* means quantising a block of numbers to 8-bit integers with one shared scale factor, so the block's largest magnitude maps to 127.

- **Tiles are hardware-shaped, not semantic.** `BLOCK_M = 128` query tokens, `BLOCK_N = 64` key tokens, matching the tile sizes the fused kernel already uses. The routing decision rides along with a tiling that exists anyway.
- **The grouping factor exists to fit a machine word.** One routing bit governs `g` adjacent key tiles: `BLOCK_N_mask = g · BLOCK_N`, with `T_mask = ⌈L_k / BLOCK_N_mask⌉ ≤ 64`. That bound is the whole point — the entire routing map for a query-tile row fits in **one 64-bit word**, so metadata stays constant-size as context grows. Coarser grouping is the price of that.
- **The routing map is static.** "Static, data-free structured templates instantiate R." No per-tile statistic, no calibration pass, no runtime measurement. The knob is an INT8 coverage budget, evaluated at 25%, 50% and 75%.
- **Quantisation is per-block with a max-abs scale**: `δ = max|x| / 127`, applied blockwise with `BLK_Q = 128`, `BLK_K = 64`.
- **Accuracy recovered, measured.** LV-Eval QA at 64k on LLaMA 3.2 3B: FP16 **7.75**, uniform INT8 **5.42**, TileMix at 50% coverage **7.44**. LongEval retrieval at 38.7k: FP16 ≈**0.50** exact match, uniform INT8 ≈**0.44**, TileMix ≈**0.47**.
- **Throughput.** At 4k tokens, 75% INT8 coverage reaches **31.80K tokens/s** against FlashAttention's **14.33K tokens/s** — **2.22×**.
- **Output deviation is small and scales with coverage.** Mean absolute deviation from the FP16 output is **1.10×10⁻³** at 10% INT8 coverage and **1.78×10⁻³** at 25%.
- **Evaluated on prefill, on A100**, across LLaMA, Qwen and Vicuna. Decode is a different regime and is not the claim.

## Implementing It

**The change.** The core idea is small enough to write from scratch, and writing it is the only way to see why the shared softmax state is the load-bearing part. Three pieces: tile the score matrix, quantise the routed tiles, and make both paths update one running softmax.

*Blockwise INT8, exactly as specified.* The scale is max-abs over the block, mapped to 127:

```python
def quantize_block(xs):
    """delta = max|x| / 127, as in the paper. Returns (int8 codes, scale)."""
    peak = max(abs(x) for x in xs) or 1e-9
    delta = peak / 127.0
    return [max(-127, min(127, round(x / delta))) for x in xs], delta

def dequantize_block(codes, delta):
    return [c * delta for c in codes]
```

*The routing map — static, data-free, and one bit per tile group.* This is the part that surprised me, so it is worth writing plainly: nothing here looks at the data.

```python
def routing_bits(n_q_tiles, n_k_groups, band=1, n_global=1):
    """1 = INT8, 0 = FP16. A BigBird-shaped template: keep FP16 on the
    diagonal band and the global prefix, send everything else to INT8.
    No statistic, no calibration — the map is fixed before any input."""
    rows = []
    for m in range(n_q_tiles):
        bits = 0
        for g in range(n_k_groups):
            near_diagonal = abs(g - m) <= band
            is_global = g < n_global
            if not (near_diagonal or is_global):
                bits |= (1 << g)          # route to INT8
        rows.append(bits)                  # the whole row is one integer
    return rows
```

That `bits` integer is the paper's metadata argument made concrete: with `T_mask ≤ 64`, a query-tile row's entire routing map is one 64-bit word regardless of context length.

*One softmax, two precisions.* The tile's precision changes how scores are produced; the accumulator never learns which path produced them:

```python
def attend_row(q, keys, values, row_bits, group_of):
    """Online softmax over tiles, mixing FP16-ish and INT8 score paths."""
    running_max, running_sum = float("-inf"), 0.0
    acc = [0.0] * len(values[0])
    for j, (k, v) in enumerate(zip(keys, values)):
        score = sum(a * b for a, b in zip(q, k))
        if (row_bits >> group_of(j)) & 1:              # this tile routed to INT8
            codes, delta = quantize_block([score])
            score = dequantize_block(codes, delta)[0]
        new_max = max(running_max, score)
        rescale = 1.0 if running_max == float("-inf") else pow(2.718281828, running_max - new_max)
        w = pow(2.718281828, score - new_max)
        running_sum = running_sum * rescale + w
        acc = [a * rescale + w * vi for a, vi in zip(acc, v)]
        running_max = new_max
    return [a / running_sum for a in acc]
```

The rescale line is the whole reason this can be one fused kernel: when a later tile raises the running max, everything already accumulated is corrected in place. An INT8 tile that shifts a score slightly perturbs the output; it cannot corrupt the normalisation, because the normaliser is recomputed from the same running state either way.

**How you know it worked.** Reproducing the paper's *shape* is the check, not its exact figures — you are running a toy, not an A100 kernel:

1. **Deviation must scale with coverage, and stay small.** Sweep the INT8 budget from 0% to 100% and plot mean absolute deviation from the FP16 output. The paper reports **1.10×10⁻³** at 10% coverage and **1.78×10⁻³** at 25%; your toy should show the same monotone, gentle growth. If deviation jumps discontinuously, your online-softmax rescale is wrong — that is the bug this check is really for.
2. **Skipping must be worse than cheapening at equal coverage.** This is the paper's actual claim. Run the same routing map twice: once sending routed tiles to INT8, once dropping them entirely. Compare both against the FP16 reference. If dropping is not clearly worse, your routed tiles are not carrying any signal and your template is degenerate.
3. **The routing map must fit one word.** Assert `n_k_groups <= 64`. If it does not, your grouping factor `g` is too small and you have silently given up the constant-size metadata that makes this cheap at long context.

**When not to.** Do not reach for this shape when prefill is not your bottleneck. It is a prefill optimisation measured on prefill; decode is memory-bound in a different way and none of these numbers transfer. Do not use it to justify quantising attention uniformly — the measurements say the opposite. And do not read "2.22× faster" as free: that figure is at 75% INT8 coverage, which is the aggressive end of the accuracy trade, and the quality numbers quoted above are at 50%.

Most importantly, do not implement a static template and call it adaptive computation. The routing here cannot notice that *your* prompt put the answer in a region the template calls boring. That limitation is inherited wholesale from sparse attention, and it is the reason a per-tile runtime statistic is the obvious next thing — which this paper does not claim to have done.

## How It Connects to What You Know

Mipmapping is the closest analogue and it is nearly exact: a spatial map, decided ahead of time, that lowers fidelity rather than removing geometry. Lossy image compression makes the same move — JPEG does not delete high-frequency blocks, it quantises them more coarsely, and the quality-vs-size knob is the same shape as the INT8 coverage budget here. And the online-softmax rescale is just a numerically-stable running aggregate, the same pattern as computing a variance in one pass.

Inside this site: the [pixels are not tokens](#2026-08-21) session covered the other end of the same pipeline — how an image becomes tokens before attention ever runs — and the [prefill-pressure scheduling](#2026-08-18) session is about the phase this paper is optimising, from the scheduler's side rather than the kernel's.

## Try It Yourself

`code_example.py` implements the mechanism end to end in pure stdlib: blockwise INT8 with the paper's max-abs scale, a static BigBird-shaped routing template packed into one integer per query-tile row, and a tiled online-softmax attention that mixes both precision paths into one accumulator. It then runs the experiment that matters — the same routing map used to *skip* tiles versus used to *cheapen* them, both measured against an FP16 reference — and sweeps the INT8 coverage budget so you can watch deviation grow. Change `BAND`, `GROUP` or `N_KEYS` and re-run.

## Glossary

- **Prefill** — the pass that processes your whole prompt before the first output token. Compute-bound and quadratic in prompt length, which is why it dominates long-context cost.
- **Score tile** — a rectangular block of the query-by-key score matrix, sized to the hardware (here 128 queries × 64 keys). Fused attention kernels already work tile by tile.
- **Online softmax** — computing a softmax incrementally over tiles by keeping a running maximum and running sum, rescaling accumulated output whenever the max rises. It is what lets attention never materialise the full score matrix.
- **Fused kernel** — one GPU kernel doing several logical steps without writing intermediates to memory. Fusion is why attention is fast; anything added to attention has to survive inside it.
- **INT8 / FP16** — 8-bit integer and 16-bit float number formats. INT8 roughly halves memory traffic against FP16 and runs on faster hardware paths, at the cost of precision.
- **Blockwise quantisation** — giving a block of numbers one shared scale factor, here `δ = max|x| / 127`, so the block's largest magnitude maps to the top of the INT8 range.
- **Routing map / bitmask** — the binary table saying which tile groups run INT8. One bit per group, packed so a query-tile row's whole map is a single 64-bit word.
- **Grouping factor (`g`)** — how many adjacent key tiles share one routing bit. Larger `g` means coarser control but constant-size metadata as context grows.
- **INT8 coverage budget** — the fraction of tile groups routed to INT8; the paper evaluates 25%, 50% and 75%. The accuracy-throughput knob.
- **Dense token connectivity** — the property that every query still attends to every key. Sparse attention gives this up; routing every tile somewhere preserves it.
- **Grouped-query attention (GQA)** — several query heads sharing one key/value head, standard in modern models to shrink the KV cache.
- **LongEval / LV-Eval** — long-context benchmarks. LongEval measures retrieval from a long prompt; LV-Eval measures question answering at lengths up to 64k tokens.
