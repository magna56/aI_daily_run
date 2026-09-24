"""Train the think/don't-think switch into the data mix, not around the model.

Phi-4-reasoning-vision-15B is trained on a hybrid mix: reasoning traces carrying
an explicit mode token, and direct answers carrying the other one. A single
model then answers simple things fast and reasons on hard ones, with no router
in front of it.

This builds that mix from scratch and measures the Pareto claim the paper
makes -- competitive with slower models, more accurate than equally fast ones.
It also shows the thing the headline average hides: a hard subset where the
small model falls off a cliff regardless of how long it thinks.

Run: python3 code_example.py
"""

import random

# --- The knob. Change this and watch the tradeoff move. ----------------------
# Share of training examples that carry the THINK mode token. The paper's mix is
# roughly a fifth reasoning, four fifths direct. Push this to 1.0 and you have
# retrained a model that thinks about everything.
THINK_SHARE = 0.20

SEED, N = 5, 4000
NOTHINK_TOKENS, THINK_TOKENS = 40, 640


# --- Liftable core: the mix, and the switch it teaches ------------------------

def build_example(task, think):
    """One training row. The mode token is the whole mechanism: it is a literal
    token in the sequence, so the model learns to emit it and then condition on
    what it just emitted."""
    return {
        "prompt": task["prompt"],
        "mode": "<think>" if think else "<nothink>",
        "target": task["reasoning_trace"] if think else task["direct_answer"],
    }


def build_mix(tasks, think_share, rng):
    """Assign modes by DIFFICULTY, not at random.

    This is the part that carries the lesson. A mix that labels hard tasks
    THINK teaches a useful switch. A mix that labels random tasks THINK teaches
    the model that the token means nothing.
    """
    ordered = sorted(tasks, key=lambda t: -t["difficulty"])
    cut = int(len(ordered) * think_share)
    return [build_example(t, i < cut) for i, t in enumerate(ordered)]


def predict_mode(task, learned_threshold):
    """What the trained model does at inference: emit a mode, then answer."""
    return "<think>" if task["difficulty"] >= learned_threshold else "<nothink>"


def learned_threshold_from(mix, tasks):
    """Recover the difficulty boundary the mix implies. A real model learns this
    in its weights; here it is one number, which is the point -- the switch is
    simple, and the data is what decides where it sits."""
    by_prompt = {t["prompt"]: t["difficulty"] for t in tasks}
    thinkers = [by_prompt[e["prompt"]] for e in mix if e["mode"] == "<think>"]
    return min(thinkers) if thinkers else 1.1


# --- The demonstration --------------------------------------------------------

def make_tasks(n, rng):
    """Most work is ordinary perception. A minority is genuinely hard, and a
    small slice is hard in a way no amount of thinking fixes -- the paper's
    ScreenSpot-Pro column, where a 15B model scores in single digits."""
    tasks = []
    for i in range(n):
        d = rng.random()
        beyond = d > 0.94                      # past the model's ceiling
        tasks.append({
            "prompt": f"task-{i}", "difficulty": d, "beyond_ceiling": beyond,
            "reasoning_trace": "...", "direct_answer": "...",
        })
    return tasks


def solve(task, mode):
    """Thinking buys accuracy on hard-but-reachable work, and nothing on work
    past the ceiling or work that was already easy."""
    if task["beyond_ceiling"]:
        return False, (THINK_TOKENS if mode == "<think>" else NOTHINK_TOKENS)
    if mode == "<think>":
        return random.random() < 0.93, THINK_TOKENS
    # Direct answers are strong on ordinary perception and fall off only as the
    # task approaches the point where reasoning was going to be needed.
    d = task["difficulty"]
    return random.random() < max(0.05, 0.95 - max(0.0, d - 0.45) * 0.85), NOTHINK_TOKENS


def evaluate(tasks, policy, threshold=None):
    random.seed(SEED)
    solved = tokens = 0
    hard_solved = hard_n = 0
    for t in tasks:
        mode = policy if policy != "hybrid" else predict_mode(t, threshold)
        ok, tok = solve(t, mode)
        solved += ok
        tokens += tok
        if t["beyond_ceiling"]:
            hard_n += 1
            hard_solved += ok
    return solved / len(tasks), tokens / len(tasks), (hard_solved / hard_n if hard_n else 0)


def main():
    rng = random.Random(SEED)
    tasks = make_tasks(N, rng)
    mix = build_mix(tasks, THINK_SHARE, rng)
    threshold = learned_threshold_from(mix, tasks)

    print(f"{N} tasks | mix is {THINK_SHARE:.0%} reasoning, "
          f"{1 - THINK_SHARE:.0%} direct | learned switch at difficulty {threshold:.2f}\n")
    print(f"{'policy':<22}{'accuracy':>10}{'tokens/task':>14}{'acc per Ktok':>15}")
    print("-" * 61)

    rows = {}
    for label, pol in (("always direct", "<nothink>"),
                       ("always reason", "<think>"),
                       ("hybrid, mode token", "hybrid")):
        acc, tok, _ = evaluate(tasks, pol, threshold)
        rows[label] = (acc, tok)
        print(f"{label:<22}{acc:>9.1%}{tok:>14.0f}{acc / (tok / 1000):>15.2f}")

    slow, hy = rows["always reason"], rows["hybrid, mode token"]
    print(f"\nThe hybrid keeps {hy[0] / slow[0]:.1%} of the always-reason accuracy "
          f"for {hy[1] / slow[1]:.0%} of the tokens.")
    print("That is the whole claim: competitive with slower models, cheaper than them.\n")

    _, _, hard = evaluate(tasks, "<think>", threshold)
    beyond = sum(1 for t in tasks if t["beyond_ceiling"]) / N
    print(f"And the part an average hides: {beyond:.0%} of tasks are past the ceiling.")
    print(f"On those, always-reason scores {hard:.1%}. More thinking does not move it.")
    print("Report that subset separately or your headline number is an average over")
    print("two populations -- one you serve well and one you do not serve at all.")


if __name__ == "__main__":
    main()
