# Plan: Interactive Explorers

**Status:** designed, not started. Parked deliberately — pick this up when other work clears.

## What this is

An optional per-session interactive widget that lets a reader **drag a parameter and watch
the result change**, rather than reading one fixed run of the code example.

The idea came from a reference artifact (a LoRA visualiser) that ran a real forward/backward
pass in the browser and let you move a rank slider. What made it good was not that it was
React — it was that it ran a **real, tiny computation** and let you manipulate it.

## The reframe that drives the design

**We already generate the simulation.** Every session ships a `code_example.py` that is a real
tiny simulation, already executes in the browser via Pyodide, and is already verified at build
time. The gap is not generation — it is **presentation**: today that simulation is a script you
run once and read as text.

So this feature is about making the existing computation *manipulable*, not about generating
new visualisations from scratch.

## Decision: sidecar `explore.py`, and `code_example.py` is never touched

```
YYYY-MM-DD/
  code_example.py   # untouched. Same file, same output, still `python3 code_example.py`
  explore.py        # optional, new. Imports from code_example.
```

### Format

```python
# explore.py — optional interactive layer. Never imported by code_example.py.
from code_example import simulate

EXPLORE = {
    "title": "Drag the session length",
    "look_for": "Past ~40 turns, subagent offload flips from losing money to saving it.",
    "params": [
        {"name": "turns", "label": "Session length (turns)", "min": 10, "max": 200, "default": 60},
        {"name": "mode",  "label": "Strategy",
         "choices": ["nocache", "cached", "thrash", "offload"], "default": "cached"},
    ],
}

def explore(turns, mode):
    billed, sub, ctx = simulate(mode, turns)
    return {"Cost": f"${(billed + sub) * 5e-6:.2f}", "Context": f"{ctx:,} tokens"}
```

`explore()` returns a plain dict of label → display string. The reader renders it. Keep the
return shape dumb on purpose — formatting decisions belong in Python where they can be tested,
not in the reader.

### Why this shape

- **`code_example.py` stays the source of truth.** It still runs standalone and is still
  executed/captured at build time exactly as today. Delete `explore.py` and nothing breaks.
- **The sidecar absorbs the awkwardness.** Real example: `simulate()` returns a bare tuple
  `(billed, sub, prefix)` — not renderable. The wrapper adapts it. No reshaping anyone's
  function to fit a widget.
- **It is real Python, so the build can verify it** — see validation below. This is the
  decisive advantage over generated JS/JSX, which can only be eyeballed.
- **Generation risk is small** — the model writes ~15 lines that mostly call code it already
  wrote, not a from-scratch UI.

### Rejected alternatives (do not relitigate without new information)

| Option | Why not |
|---|---|
| Generate bespoke React/JS per session | Unverifiable; can silently ship a blank box; doubles the generation surface; throws away the build-time-verified property that makes this pipeline trustworthy. |
| `# PARAMS:` comment in `code_example.py`, reader regex-rewrites the source | Requires string-substituting into source code to change a value. Fragile, fails silently, and couples the feature into the file we want left alone. |
| A fixed library of parameterised widget *templates* | Cannot express the thing that made the reference artifact good — the insight was specific to that topic's actual math. Templates would produce decoration. |
| `explore.json` (data-only sidecar, no Python) | Cannot adapt an awkward return shape without code, which most sessions need. |

## Prerequisite: `__main__` guard convention

`code_example.py` must not fire its prints on import. **15 of 20 existing sessions already have
`if __name__ == "__main__":`**; making it standard in the skill is behaviour-neutral —
`python3 code_example.py` output is byte-identical either way.

Sessions currently missing it (would need it only if we backfill an explorer for them):
`2026-08-22`, `2026-08-03-s2`, and 3 others — check with:

```bash
grep -L '__name__ == "__main__"' 2026-*/code_example.py
```

## Build-time validation (`build.js`)

This is the part that makes the feature safe, and the reason for choosing Python over JS.
When `explore.py` is present:

1. It imports cleanly (and importing `code_example` produces no stdout — guard is working).
2. `EXPLORE["params"]` names match `explore()`'s actual signature — no typos, no missing args.
3. **Run `explore()` at every range extreme** (min and max of each numeric param, each choice
   value) and fail the build if any combination raises. A slider must not be able to reach a
   crash the author never tried.
4. Return value is a flat dict of str/number — reject nested structures the reader can't render.

Treat a broken `explore.py` as a **warning, not a hard error**: the session is still valid and
publishable without its widget, same philosophy as a missing diagram today.

## Reader changes (`index.html`)

- New panel in the **Code** tab, below the existing code/output columns.
- Controls rendered from `EXPLORE["params"]` — range input for numeric, select for choices.
- On change (debounced ~50ms), call `explore(**values)` through the already-loaded Pyodide and
  render the returned dict.
- Show `look_for` as a hint line — this is what told the reader *what to notice* in the
  reference artifact, and it's most of the educational value.
- Pyodide is already loaded for this tab and these scripts run in **0–30ms** (measured across
  all 20 sessions), so it updates live while dragging with no perceptible lag.

## Skill changes (`ai-daily-learn/SKILL.md`)

- New optional step: emit `explore.py` **only when the article's central claim is about a
  relationship** — a cost that compounds, a threshold, a crossover, a tradeoff curve.
- Explicitly: **do not force it.** A slider that changes nothing is worse than no slider.
- Require the `__main__` guard in `code_example.py` (behaviour-neutral, see above).
- Good candidates are common in practice — Context Budget (turns × cache mode → cost),
  AutoRAG (chunk size × top-k), LoRA capacity (rank → bits), Model Cascades (price threshold
  → routing). A strong technical article usually *is* an argument about a relationship, and a
  relationship is a slider.

## Sequencing

1. **Pilot by hand first.** Build `2026-08-22/explore.py` manually (Context Budget — the
   cost sign-flip around 40 turns is genuinely fun to discover) plus the minimum reader code
   to render it. Judge whether it's actually compelling before writing any generator.
2. Only if the pilot lands: add build validation, then the skill step.
3. Backfill a few strong existing sessions by hand rather than regenerating them.

## Deferred: richer visuals

The reference artifact was also visually rich — matrix heatmaps, a loss sparkline. A dict of
numbers won't match that.

Closing that is a **separate later step**: a small `viz` helper the Python can call —
`viz.heatmap(M)`, `viz.line(series)`, `viz.bars(labels, values)` — returning data the reader
draws. Still Python, still build-verified. Do this only after params prove out; doing both at
once conflates "is this compelling?" with "can we render heatmaps?"

Worth knowing: **19 of 20 examples are pure stdlib** (only one uses numpy/matplotlib), so the
`viz` helper should emit plain data structures rather than depend on a plotting library in
Pyodide.

## Open questions

- Should the explorer be its own reader tab rather than a panel under Code? Probably not —
  it's most useful next to the code it's driving, but revisit if the Code tab gets crowded.
- Does `explore.py` need to appear in the published Gist? Probably yes when it exists, as a
  third file — decide during the pilot.
