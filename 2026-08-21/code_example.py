"""
Pixels Are Not Tokens: fixed tiling vs. native resolution in VLM input pipelines.

Implements BOTH production image->token pipelines exactly, then measures what they
cost and what they throw away:

  1. Padding tax      - the tile grid's ceil() waste, 20-96%, never zero
  2. DPI ceiling      - 200/300/600 dpi scans collapsing to ONE identical input
  3. min_pixels trap  - the copy-pasted "256-1024 token" recipe costing 28x on icons
  4. Batch packing    - where native resolution relocates the cost (NaViT patch-n-pack)

Pure stdlib. No deps, no API keys, no network.
Run: python3 code_example.py
"""

import math
from collections import Counter

# ---------------------------------------------------------------- pipeline A: fixed tiling
# OpenAI documented high-detail path. GPT-4o/4.1/4.5 = 85 + 170/tile; o1/o3 = 75 + 150.
BASE, PER_TILE, TILE, MAX_BOX, SHORT_SIDE = 85, 170, 512, 2048, 768


def tile_pipeline(w, h):
    """Scale into 2048 box -> shortest side to 768 -> ceil onto a 512 grid."""
    if max(w, h) > MAX_BOX:                      # stage 1: fit the box
        s = MAX_BOX / max(w, h); w, h = w * s, h * s
    if min(w, h) > SHORT_SIDE:                   # stage 2: shortest side down to 768
        s = SHORT_SIDE / min(w, h); w, h = w * s, h * s
    cols, rows = math.ceil(w / TILE), math.ceil(h / TILE)
    grid_px = (cols * TILE) * (rows * TILE)      # what you are billed for
    return dict(w=round(w), h=round(h), cols=cols, rows=rows, tiles=cols * rows,
                tokens=BASE + PER_TILE * cols * rows,
                waste=1 - (w * h) / grid_px)     # ...vs what actually holds pixels


# ------------------------------------------------------- pipeline B: native resolution
# Qwen2-VL: patch_size=14, spatial_merge_size=2 -> one visual token IS a 28x28 px block.
FACTOR = 14 * 2
MIN_PX, MAX_PX = 56 * 56, FACTOR * FACTOR * 1280


def smart_resize(w, h, factor=FACTOR, min_px=MIN_PX, max_px=MAX_PX):
    """Round to the 28px quantum, rescale only to honor the pixel budget."""
    wb, hb = round(w / factor) * factor, round(h / factor) * factor
    if wb * hb > max_px:                                    # over budget: shrink, floor
        beta = math.sqrt((w * h) / max_px)
        wb, hb = (math.floor(w / beta / factor) * factor,
                  math.floor(h / beta / factor) * factor)
    elif wb * hb < min_px:                                  # under floor: grow, ceil
        beta = math.sqrt(min_px / (w * h))
        wb, hb = (math.ceil(w * beta / factor) * factor,
                  math.ceil(h * beta / factor) * factor)
    wb, hb = max(wb, factor), max(hb, factor)
    return dict(w=wb, h=hb, tokens=(wb // factor) * (hb // factor), waste=0.0)


CORPUS = [("A4 doc @200dpi", 1654, 2339), ("A4 doc @300dpi", 2480, 3508),
          ("Laptop screenshot", 2880, 1800), ("Phone screenshot", 1170, 2532),
          ("Receipt (tall)", 600, 3000), ("Wide banner", 3000, 500),
          ("Square photo", 1024, 1024), ("Small icon", 96, 96)]


def exp1_padding_tax():
    print("=" * 78, "\n1. THE PADDING TAX - the tile grid's ceil() is never free\n")
    print(f"{'input':20} {'grid':>6} {'tiles':>6} {'tok':>6} {'wasted':>8}   {'native':>11} {'tok':>6}")
    print("-" * 78)
    for name, w, h in CORPUS:
        t, q = tile_pipeline(w, h), smart_resize(w, h)
        print(f"{name:20} {t['cols']}x{t['rows']:<4} {t['tiles']:6} {t['tokens']:6} "
              f"{t['waste']*100:7.1f}%   {q['w']:5}x{q['h']:<5} {q['tokens']:6}")
    worst = max(CORPUS, key=lambda c: tile_pipeline(c[1], c[2])['waste'])
    print(f"\n  -> a PERFECT SQUARE wastes {tile_pipeline(1024,1024)['waste']*100:.1f}%: 768x768 needs a 2x2 "
          f"grid = 1024x1024 of billed area.")
    print(f"  -> worst case {worst[0]!r} at {tile_pipeline(worst[1],worst[2])['waste']*100:.1f}%. "
          f"There is no safe aspect ratio.")


def exp2_dpi_ceiling():
    print("\n" + "=" * 78, "\n2. THE DPI CEILING - re-scanning at 600dpi changes literally nothing\n")
    print("   A4 = 8.27 x 11.69 in. Tiling path:")
    seen = set()
    for dpi in (200, 300, 600):
        w, h = round(8.27 * dpi), round(11.69 * dpi)
        t = tile_pipeline(w, h)
        seen.add((t['w'], t['h'], t['tokens']))
        print(f"     {dpi:3}dpi  {w:4}x{h:<5} -> {t['w']}x{t['h']} = {t['w']/8.27:5.1f} dpi, {t['tokens']} tok")
    print(f"   -> {len(seen)} distinct model input(s) from 3 source resolutions. "
          f"The 768-shortest-side rule is a hard ~93 dpi cap.\n")
    print("   Native path - max_pixels is a dial you own:")
    for cap in (1280, 2560, 4096, 8192):
        q = smart_resize(1654, 2339, max_px=FACTOR * FACTOR * cap)
        note = "  <- SATURATED at source res; budget is a cap, not a target" if q['tokens'] < cap * 0.8 else ""
        print(f"     max_pixels={cap:5} tok -> {q['w']:4}x{q['h']:<5} = {q['w']/8.27:5.1f} dpi, {q['tokens']:4} tok{note}")


def exp3_min_pixels_trap():
    print("\n" + "=" * 78, "\n3. THE min_pixels TRAP - the most-copied config line, on small assets\n")
    ui = [("icon 96x96", 96, 96), ("button 240x64", 240, 64), ("toolbar 800x48", 800, 48)]
    print(f"{'input':18} {'default(56^2)':>14} {'256-recipe':>12} {'tiling':>8}   inflation")
    print("-" * 66)
    tot_d = tot_r = 0
    for name, w, h in ui:
        d = smart_resize(w, h)['tokens']
        r = smart_resize(w, h, min_px=256 * FACTOR * FACTOR)['tokens']
        tot_d, tot_r = tot_d + d, tot_r + r
        print(f"{name:18} {d:14} {r:12} {tile_pipeline(w,h)['tokens']:8}   {r/d:6.1f}x")
    print(f"\n  -> min_pixels is a FLOOR. `min_pixels=256*28*28` upscales assets that were never "
          f"captured\n     at that size: {tot_d} -> {tot_r} tokens ({tot_r/tot_d:.1f}x) across this UI corpus.")
    print("  -> it discards native resolution's single biggest structural win: cheap small images.")


def _pad_to_max(seqs, B):
    return sum(max(c) * len(c) for c in (seqs[i:i + B] for i in range(0, len(seqs), B)))


def _packed(seqs, S):
    """Greedy first-fit into fixed-length sequences (NaViT patch-n-pack)."""
    used, cur = 0, 0
    for n in seqs:
        if cur + n > S:
            used += S; cur = 0
        cur += n
    return used + (S if cur else 0)


def exp4_packing():
    print("\n" + "=" * 78, "\n4. WHERE THE COST GOES - variable length is the scheduler's problem\n")
    # A UI-agent workload: mostly small assets, punctuated by full-page captures.
    rng, mix = _lcg(7), [(96, 96, .34), (240, 64, .18), (800, 48, .12),
                         (1170, 2532, .16), (1654, 2339, .12), (2880, 1800, .08)]
    seqs = []
    for _ in range(600):
        r, acc = rng(), 0.0
        for w, h, p in mix:
            acc += p
            if r <= acc:
                seqs.append(smart_resize(w, h)['tokens']); break
    real = sum(seqs)
    print(f"   workload: {len(seqs)} images, {min(seqs)}-{max(seqs)} tokens each "
          f"({max(seqs)//min(seqs)}x spread), {real:,} real tokens")
    print(f"   mean {real/len(seqs):6.1f} tok, median {sorted(seqs)[len(seqs)//2]:5} tok"
          f"  <- mean >> median: a few big pages dominate the bill\n")

    row = lambda lbl, p: print(f"         {lbl}: {p:8,} tok  ({(1-real/p)*100:5.1f}% padding)")

    print("   (a) naive pad-to-max - every batch pays for its longest member")
    for B in (1, 2, 4, 8, 16):
        row(f"batch={B:2}", _pad_to_max(seqs, B))
    print("       -> saturates by batch=4: with this spread ANY batch almost surely holds")
    print("          one full-page capture, so everything pads up to it.\n")

    print("   (b) length-bucketed batching - sort by length, then batch")
    for B in (4, 8, 16):
        row(f"batch={B:2}", _pad_to_max(sorted(seqs), B))
    print("       -> ~free in code, recovers nearly all of it, but costs you arrival order:")
    print("          it trades tail latency for throughput.\n")

    print("   (c) NaViT patch-n-pack - many images per fixed-length sequence, block-diagonal")
    print("       attention mask to stop cross-image attention")
    for S in (2048, 4096, 8192):
        row(f"seq={S:5}", _packed(seqs, S))
    print(f"       -> seq=2048 is WORSE than 4096: two {max(seqs)}-token pages don't fit, so every")
    print("          pack strands a big tail. Pack length must clear 2x your largest item.\n")

    print("  -> native resolution removed the ENCODER's padding tax and handed you a BATCHING one.")
    print("  -> the ladder is cheap but it is YOURS to build, and (b) and (c) both reorder work,")
    print("     which is exactly what a latency SLO does not want.")
    print("  -> max_pixels is admission control, not an image-quality setting: it caps the")
    print("     spread every stage downstream has to absorb.")


def _lcg(seed):
    s = [seed]
    def nxt():
        s[0] = (1103515245 * s[0] + 12345) % (1 << 31)
        return s[0] / (1 << 31)
    return nxt


if __name__ == "__main__":
    exp1_padding_tax(); exp2_dpi_ceiling(); exp3_min_pixels_trap(); exp4_packing()
    print("\n" + "=" * 78)
    print("Tiling  : predictable cost, invisible waste, HARD resolution ceiling, no dial.")
    print("Native  : faithful pixels, a real dial, variance pushed into your scheduler.")
    print("Neither is 'efficient'. They differ in WHERE the variance lives - and only one")
    print("of them lets you schedule against it.")
