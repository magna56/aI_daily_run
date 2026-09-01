"""
Sliding-window attention, with and without sinks.

Builds both masks, runs a toy retrieval task through a softmax attention layer,
and scores whether the answer survives. The only difference between the two runs
is four columns of the mask -- the first four tokens staying visible.

Follows arXiv:2608.28444 (Jolicoeur-Martineau et al., Microsoft ASG, Aug 2026),
which found that every linear-attention paper benchmarked against the sink-free
variant, the one known to collapse.

WHAT THIS SHOWS, and what it does not. It shows REACHABILITY: without sinks the
opening tokens become invisible once the window has moved past them, so anything
stated at the top of the prompt is simply gone. That is real and it is the part
that bites in production, because the system prompt lives there.

It does NOT show the other half of the mechanism -- that a trained model learns
to route surplus attention onto those early positions, so removing them distorts
the scores of the tokens that remain. That effect only exists in a model that was
trained with the sinks present, and no toy softmax can stand in for it. Read the
paper's numbers for that half.

Pure stdlib, no numpy. Run: python3 code_example.py
"""

import math

# Knobs. WINDOW is the paper's range (64-512, scaled down here); SINKS is fixed
# at 4 in the paper. Set SINKS = 0 to reproduce the broken baseline.
WINDOW = 8
SINKS = 4
SEQ = 40
NEEDLE_AT = 3          # the fact lands early, then scrolls out of the window


# --- The liftable core: the mask, and attention over it -----------------------

def swa_sink_mask(seq_len, window, sinks):
    """True where query i may attend to key j.

    Three terms, and the third is the entire finding: `is_sink` pins the first
    few positions so they are never evicted, however far the window has moved."""
    mask = []
    for i in range(seq_len):
        row = []
        for j in range(seq_len):
            causal = j <= i
            in_window = i - j < window
            is_sink = j < sinks
            row.append(causal and (in_window or is_sink))
        mask.append(row)
    return mask


def softmax(xs):
    hi = max(xs)
    exps = [math.exp(x - hi) for x in xs]
    total = sum(exps)
    return [e / total for e in exps]


def attend(scores_row, mask_row):
    """Softmax over the visible positions only. Masked positions get no weight,
    so the surplus they would have absorbed is redistributed over what is left --
    which is exactly what goes wrong when the sinks are gone."""
    visible = [j for j, ok in enumerate(mask_row) if ok]
    weights = softmax([scores_row[j] for j in visible])
    return dict(zip(visible, weights))


# --- A toy sequence with one fact worth retrieving ----------------------------

def build_scores(seq_len, needle_at, query_at):
    """Raw attention scores for one query row. The needle stands in for a rule
    stated at the top of the prompt -- a system instruction, a format contract --
    which is where the tokens that matter longest actually live."""
    scores = []
    for j in range(seq_len):
        if j == needle_at:
            scores.append(4.0)          # the fact the query is looking for
        elif j < SINKS:
            scores.append(1.0)          # sink tokens: mildly attractive by default
        else:
            scores.append(0.2)          # background
    return scores


def run(window, sinks, seq_len=SEQ, needle_at=NEEDLE_AT):
    mask = swa_sink_mask(seq_len, window, sinks)
    query = seq_len - 1                                # ask at the very end
    scores = build_scores(seq_len, needle_at, query)
    weights = attend(scores, mask[query])
    on_needle = weights.get(needle_at, 0.0)
    # how concentrated is the rest? a flat spread over background is the failure
    background = [w for j, w in weights.items() if j != needle_at and j >= sinks]
    return {
        "sees_needle": needle_at in weights,
        "needle_weight": on_needle,
        "visible": len(weights),
        "max_background": max(background) if background else 0.0,
    }


def render_mask(mask, rows=(10, 20, 39)):
    print("    " + "".join(str(j % 10) for j in range(len(mask))))
    for i in rows:
        line = "".join("#" if ok else "." for ok in mask[i])
        print(f"  {i:>2}{line}")


def main():
    print(f"seq={SEQ} tokens, window={WINDOW}, needle at position {NEEDLE_AT}, "
          f"query at {SEQ - 1}\n")

    for label, sinks in (("WITHOUT sinks (the baseline every paper used)", 0),
                         ("WITH 4 sinks   (the paper's proposal)", SINKS)):
        print(label)
        render_mask(swa_sink_mask(SEQ, WINDOW, sinks))
        r = run(WINDOW, sinks)
        seen = "yes" if r["sees_needle"] else "NO — scrolled out of the window"
        print(f"    needle visible : {seen}")
        print(f"    weight on it   : {r['needle_weight']:.4f}")
        print(f"    keys visible   : {r['visible']}")
        print(f"    heaviest background key: {r['max_background']:.4f}\n")

    print("window   needle weight without sinks   with sinks")
    for w in (4, 8, 16, 32, SEQ):
        a = run(w, 0)["needle_weight"]
        b = run(w, SINKS)["needle_weight"]
        print(f"  {w:<6}  {a:>22.4f}   {b:>9.4f}")

    print("\nThe rule sits at position 3, where a system prompt does. Without sinks it")
    print("leaves the window and its weight goes to zero: by token 39 the model cannot")
    print("see the instruction it was given, and spreads attention over background it")
    print("has no reason to care about. Note the last row of the sweep — at window=40")
    print("the whole sequence fits, both variants agree, and the difference vanishes.")
    print("That is the tell: this is about what the window can still REACH, and the")
    print("four pinned columns cost no training at all.")


if __name__ == "__main__":
    main()
