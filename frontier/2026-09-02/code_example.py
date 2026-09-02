"""
Why looping each layer in place pays for itself.

Models the activation-memory term that makes the Loopie Recipe work, applies the
recipe to a reference config, and measures the reuse distance of the two loop
schedules. Reproduces the shape of the argument in arXiv:2607.16051 (Gao et al.,
IQuest Research) -- not its wall-clock numbers, which depend on Megatron-LM, a
checkpointing implementation and a particular GPU.

The claim being checked: executed depth does not appear in the activation-memory
term, so running a stored layer twice costs compute but not memory, and the freed
memory is what buys the compute back.

Pure stdlib. Run: python3 code_example.py
"""

# Reference: a non-recurrent MoE baseline, Qwen3-30B-A3B shaped.
REFERENCE = {
    "stored_layers": 48,
    "hidden_dim": 2048,
    "loop_steps": 1,
    "microbatch": 1,
    "grad_accum": 16,
    "seq_len": 4096,
}


# --- The liftable core --------------------------------------------------------

def activation_memory(cfg):
    """The dominant term, in arbitrary units. Note what is absent: loop_steps.
    All recurrent applications of a stored layer share one checkpointed unit, so
    memory tracks STORED depth, not EXECUTED depth."""
    return (cfg["seq_len"] * cfg["microbatch"]
            * cfg["hidden_dim"] * cfg["stored_layers"])


def executed_depth(cfg):
    return cfg["stored_layers"] * cfg["loop_steps"]


def tokens_per_step(cfg):
    return cfg["seq_len"] * cfg["microbatch"] * cfg["grad_accum"]


def loopie_recipe(reference):
    """(i) halve stored depth, (ii) run each stored layer twice, (iii) spend the
    freed activation memory on a doubled microbatch. Step (iii) is the one that
    makes the first two pay; without it you have a smaller, slower model."""
    cfg = dict(reference)
    cfg["stored_layers"] //= 2
    cfg["loop_steps"] = 2
    cfg["microbatch"] *= 2
    cfg["grad_accum"] //= 2          # tokens per optimizer step held constant
    return cfg


def reuse_distance(schedule, n_layers, loop_steps):
    """How many layer applications separate consecutive uses of the same weights.
    This is the loop-interchange argument, made countable."""
    order = []
    if schedule == "model-loop":
        for _ in range(loop_steps):
            order.extend(range(n_layers))
    else:                                    # layer-loop
        for i in range(n_layers):
            order.extend([i] * loop_steps)
    last, gaps = {}, []
    for pos, layer in enumerate(order):
        if layer in last:
            gaps.append(pos - last[layer])
        last[layer] = pos
    return sum(gaps) / len(gaps) if gaps else 0


def show(name, cfg):
    print(f"  {name:<22} stored={cfg['stored_layers']:<3} executed={executed_depth(cfg):<3} "
          f"mbs={cfg['microbatch']:<2} ga={cfg['grad_accum']:<3} "
          f"act_mem={activation_memory(cfg)/1e9:>6.2f}  tok/step={tokens_per_step(cfg):,}")


def main():
    ref = REFERENCE
    loopie = loopie_recipe(ref)

    print("Applying the Loopie Recipe to a 48-layer reference:\n")
    show("reference", ref)
    show("loopie", loopie)

    mem_ratio = activation_memory(loopie) / activation_memory(ref)
    print(f"\n  activation memory   {mem_ratio:.2f}x  (unchanged, because the halved stored")
    print("                        depth was spent on doubling the microbatch)")
    print(f"  executed depth      {executed_depth(loopie)/executed_depth(ref):.2f}x")
    print(f"  tokens per step     {tokens_per_step(loopie)/tokens_per_step(ref):.2f}x  (held constant by design)")

    print("\nWhat happens if you skip step (iii) and keep the microbatch at 1:")
    half_only = dict(ref); half_only["stored_layers"] //= 2; half_only["loop_steps"] = 2
    show("halved, unspent", half_only)
    print(f"  activation memory   {activation_memory(half_only)/activation_memory(ref):.2f}x of reference")
    print("  ...which is the memory headroom the recipe exists to convert into throughput.")

    print("\nReuse distance — how far apart the uses of one layer's weights are:\n")
    print("  schedule       layers  steps   mean distance")
    for n in (3, 12, 48):
        for sched in ("model-loop", "layer-loop"):
            d = reuse_distance(sched, n, 2)
            print(f"  {sched:<14} {n:<7} {2:<7} {d:>6.1f}")
    print("\n  Identical arithmetic in both. Layer-loop keeps every reuse adjacent,")
    print("  which is what lets one checkpointed unit cover all of a layer's repeats")
    print("  and what keeps every repeat inside one pipeline stage.")

    print("\nThe order is the whole change. The paper's ablation — same looped compute")
    print("budget, layer-loop ordering removed — reports the ordered version reaching")
    print("the same downstream average 2.14x faster.")


if __name__ == "__main__":
    main()
