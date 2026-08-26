# Further Reading: How a Coding-Agent Harness Learns to Patch Itself

## Papers

### [AutoSaddler: Automatic Harness Optimization with Durable Updates from Agent Execution Traces](https://arxiv.org/abs/2608.23041)
**Authors**: Sungho Park et al. (Microsoft Research) | **Published**: August 2026
> The primary source for this whole session — the five-stage loop, the three patch types (prompt, tool, middleware), the two-gate acceptance rule, and every number quoted above (62.0% Pass@1 on GAIA2, the three ablations) come straight from here. Read the ablation section (RQ1–RQ3) first if you only have ten minutes; it's the part with the actual evidence for why the dev-set gate matters more than the other two components combined.

## Articles

### 1. [AutoSaddler — project page](https://autosaddler-projectpage.github.io/)
**Source**: Microsoft Research | **Date**: August 2026 | **Read time**: ~5 min
> An interactive visualization of the patch history across a run — click any dot to inspect what was proposed, whether it passed each gate, and what it changed. Worth opening after you've run `code_example.py`, so the abstract "gate 1 / gate 2" language has a picture behind it before you go looking at real patches.

### 2. [github.com/microsoft/AutoSaddler](https://github.com/microsoft/AutoSaddler)
**Source**: Microsoft Research | **Date**: current | **Read time**: ~10 min to skim
> The actual repo, with a working CLI (`autosaddler.v2.cli`) and a config schema that splits `scenario`, `optimization`, `provider`, and `storage` into separate, versioned sections — `optimization` is the one that owns "task selection, acceptance, development gate, ranking, budget, retries." Read this if you want to see the two-gate rule as a real config surface rather than the toy version this session implements.

### 3. [From Failed Trajectories to Reliable LLM Agents: Diagnosing and Repairing Harness Flaws](https://arxiv.org/abs/2606.06324)
**Source**: arXiv | **Date**: June 2026 | **Read time**: ~8 min
> A related, earlier paper on the same general problem — diagnosing why an agent harness fails and repairing it — from a different angle. Useful for seeing which parts of AutoSaddler's design (the typed patch taxonomy, the two-gate check) are genuinely new versus which parts of "diagnose and repair a harness" several teams are independently converging on.
