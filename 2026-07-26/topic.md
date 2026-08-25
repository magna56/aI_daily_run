# How Many Bits a LoRA Adapter Can Write

**Category**: Hands-on Techniques
**Date**: 2026-07-26
**Level**: Deeper
**For**: How models work
**Hook**: A LoRA adapter stores only a couple of bits per parameter — and where you attach it matters more than how big it is.
**Time to read**: ~10 minutes

## What It Is

This paper (arXiv:2607.21351, "How Many Bits Can an Adapter Write?", Tan et al.) asks a
deceptively simple question about the fine-tuning technique most engineers reach for first:
when you attach a LoRA adapter to a frozen base model, *how much information can that adapter
actually store?* Not "how many parameters does it have" — how many **bits of new knowledge**
can it write into the model before it saturates.

The framing matters because we talk about LoRA loosely. Some people treat an adapter as a
"skill" — a small nudge that unlocks latent behavior already in the base weights. Others treat
it as a place to cram new facts (a customer's product catalog, private documents). The paper
uses a **compression-based memorization measurement**: information stored is measured as the
number of bits by which the adapted model can compress a target dataset beyond what the frozen
base model already compresses it. This is the same information-theoretic lens as the 2025
"language models memorize ~3.6 bits/parameter" line of work, but applied to the *delta*, not
the full model.

The headline result: a LoRA adapter stores only **a couple of bits per trainable parameter** —
far below full fine-tuning — and, more surprisingly, capacity depends less on the parameter
count than on **where the adapter sits**. Moving the same parameter budget from attention
projections to MLP layers roughly *doubles* storage capacity. Strip away the frozen base
structure (adapt a randomly-initialized or zeroed base) and capacity nearly collapses. The
adapter is not a standalone memory bank; it is a low-rank *steering* of a rich frozen basis,
and its capacity is borrowed from that basis.

## Why It Matters

Every LoRA config decision — rank, which modules to target (`q_proj,v_proj` vs. `gate,up,down`),
how much data to shove through — is usually made by folklore and a sweep. This paper gives a
first-principles reason for what the sweeps keep finding:

- **Rank has diminishing returns for memorization.** Once you pass the information the task
  actually contains, extra rank buys you almost nothing but overfitting surface. Capacity is
  bounded by bits, not by rank.
- **Target the MLP, not just attention, when you need to store facts.** The default
  "attention-only" LoRA recipe (from the original 2021 paper) is a *behavior-steering* recipe.
  If you're trying to inject knowledge, the MLP is where the storage is.
- **LoRA is the wrong tool for large-scale fact injection.** A couple of bits per parameter
  means memorizing a big private corpus needs either a lot of adapter parameters or a different
  mechanism (RAG). This quantifies the "just fine-tune it in" instinct and shows why it fails.

## Key Technical Details

- **Capacity metric = compression delta.** bits_stored ≈ H_base(data) − H_adapted(data),
  estimated via the model's own log-likelihood (−Σ log2 p). Information is measured, not counted.
- **~2 bits / trainable parameter** for LoRA adapters, vs. the ~3.6 bits/param regime reported
  for full-model memorization — adapters are strictly less efficient per parameter.
- **Placement dominates count.** Same parameter budget, MLP placement ≈ 2× the attention
  placement capacity. Capacity is a property of (rank × where), not rank alone.
- **The frozen base is load-bearing.** Remove/zero the base structure and adapter capacity
  nearly vanishes — the low-rank delta only works because it reprojects an already-rich basis.
- **Evaluated on Qwen2.5** models across placements and budgets, extending prior compression-
  based memorization analysis from full models to adapters.

## How It Connects to What You Know

This is the adapter-scale version of the **compression = intelligence** thread from the
2026-07-11 LUMI session: there, a good next-token predictor *is* a good compressor, and bits =
−log2 p under arithmetic coding. Here the same identity is turned into a *ruler* — you measure
what an adapter learned by how many bits of compression it adds. It also sharpens the
RAG-vs-fine-tune decision from the 2026-07-07 listwise-pruning session: if an adapter physically
can't hold your corpus (bits/param ceiling), retrieval isn't a preference, it's a requirement.
And it echoes the LoRA intuition from transformer internals — attention routes, MLPs store —
now with an information-theoretic price tag on each.

## Try It Yourself

`code_example.py` builds a **capacity probe** from scratch (numpy only): a frozen random base
linear map plus a trainable rank-r LoRA delta, trained to memorize N random key→bit-pattern
associations. It sweeps N to find the saturation point (the capacity), converts recovered bits
into **bits-per-trainable-parameter**, and runs the paper's two key contrasts: (1) capacity vs.
rank, and (2) capacity *with* the frozen base present vs. removed. You'll watch bits/param
plateau and see the base-structure collapse — the paper's two headline claims, reproduced on a
laptop in seconds.
