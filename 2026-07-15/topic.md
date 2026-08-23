# The Bun-in-Rust Rewrite: Engineering Practices for Trusting 1M+ Lines of Agent-Generated Code

**Category**: AI Engineering Practices
**Date**: 2026-07-15
**Level**: Building
**For**: Shipping AI
**Hook**: A million lines of agent code shipped because tests, not humans, were the source of truth.
**Time to read**: ~10 minutes

## What It Is

In May 2026 the Bun team rewrote their JavaScript runtime from Zig to Rust — **1,448 source files, ~1M net lines, 6,502 commits, in 11 days** — almost entirely with Claude agents (Fable 5, pre-release). One human (Jarred Sumner) monitored the run. The headline number is the cost (~$165K in API tokens; ~5.9B uncached input, 690M output, 72B cached reads), but the *interesting* part for a working engineer is not "AI wrote a lot of code." It's the **operational discipline that made a million lines of machine-generated systems code trustworthy enough to ship to production** (it now backs Claude Code v2.1.181+).

The whole run is a case study in three practices that generalize far below the million-line scale: (1) a **language-independent conformance suite as the correctness oracle**, (2) **adversarial code review with deliberately split context windows**, and (3) **"fix the process, not the code"** — treating the agent loop's prompt as the real artifact under maintenance, not the individual diffs.

The architecture: ~50 dynamic workflows, each running the loop `task → implementer writes code → 2 adversarial reviewers → fixer applies feedback → commit`. Up to **64 Claude instances at peak** (16 per workflow × 4 git worktrees), hitting **695 commits/hour** at one point. The worktrees plus a serialized-commit rule ("commit this one file before the next agent starts") were the entire concurrency-control strategy — crude, but it worked.

## Why It Matters

Everyone can now generate code faster than they can review it. That inverts the bottleneck: the scarce resource stops being "can the model write this" and becomes "can I *trust* what it wrote without reading every line." Bun's answer is a blueprint you can copy at any scale.

The critical enabler is one most teams already half-have: a **test suite that is independent of the implementation language**. Bun's 1.3M+ `expect()` assertions were written in TypeScript, testing *observable runtime behavior*, not Zig internals. That's why they survived a total language swap unchanged — zero tests skipped or deleted. Behavior-level tests are a portable correctness contract; implementation-coupled tests (mocks of internal calls, snapshot tests of private structures) are not. This run is the strongest argument yet for writing tests against the black-box interface.

The second lesson is about *review economics*. Human review of 6,502 commits is impossible. But the three bugs the writeup highlights — a use-after-free in a libuv close callback, an invalid negative `timespec`, an eager-evaluation `unwrap_or` — **all compiled cleanly and all looked plausible to a human skim**. They were caught by a second (and third) LLM told only "here is a diff, assume it is wrong." Adversarial review scales the way human review doesn't, and it catches the specific failure class agents produce: locally-plausible, subtly-wrong code.

## Key Technical Details

- **Conformance oracle**: 1,386,826 assertions (Debian), 1,259,953 (macOS arm64), 1,007,544 (Windows). Language-agnostic → survived Zig→Rust unchanged. Regressions surfaced within minutes.
- **Adversarial review = split context**: implementer sees porting guide + original Zig + its own reasoning; reviewers see **only the diff** + "assume this is wrong." Asymmetric context is the trick — reviewers can't rationalize from the author's intent.
- **"Fix the process, not the code"** — every failure fixed by editing the *loop prompt*, not the output:
  - Agents ran `git stash`/`git reset` and collided → prompt: "never run git stash or git reset."
  - Agents stubbed functions to pass the compiler → review rule: "if you need a paragraph-long comment to justify a workaround, the code is wrong — fix the code."
  - Debug-build tests timed out → wrapped execution in `systemd-run` (cgroups) instead of tweaking tests.
- **Concurrency control**: 4 worktrees (physical isolation) + serialized single-file commits (no interleaving) + crate-level partitioning of ~16,000 compiler errors across ~100 crates among 64 agents.
- **Prep phase (~3 hrs)**: generated `PORTING.md` (Zig→Rust pattern map) and `LIFETIMES.tsv` (per-struct field lifetime proposals, adversarially reviewed) *before* scaling. Trial run on 3 files first.
- **Convergence**: May 8 → 972 failing test files; May 10 → Linux green; May 11 → Windows green; May 14 → all 6 platforms green.
- **Defense in depth post-merge**: 11 rounds of Claude Code Security review (~15 fuzzer bugs), Fuzzilli parser fuzzing (100B executions → ~15 PRs), 19 known regressions tracked and fixed.
- **Faithful over idiomatic**: generated Rust mirrors Zig structure (defer idiomatic refactor); ~4% unsafe, 78% of which are single-line pointer declarations.

## How It Connects to What You Know

You already know ReAct/Reflexion-style loops and multi-agent orchestration. This is that, industrialized, with the reliability engineering bolted on. A few connections:

- **This is generator-verifier / actor-critic at systems scale.** The implementer is the actor; the two adversarial reviewers are critics; the conformance suite is a *ground-truth* verifier that the critics can't hallucinate past. The key insight over vanilla Reflexion: the verifier (tests) is external and deterministic, so the loop can't converge to a confidently-wrong fixpoint.
- **Split context windows** are the same idea as your `code-reviewer` sub-agent getting a clean context rather than the implementer's — but weaponized. Denying the reviewer the author's justification is deliberate debiasing.
- **"Fix the process, not the code"** is prompt engineering as *config management*. The loop prompt is the source of truth; diffs are build outputs. This is exactly why your polymath workflows encode rules in agent definitions rather than patching individual runs — it's the same lesson at 64× concurrency.
- **Worktree isolation** — the `isolation: "worktree"` option on your own Agent/Workflow tooling exists for precisely this reason: parallel agents mutating files conflict, and a fresh worktree per agent is the clean fix Bun arrived at empirically.

## Try It Yourself

`code_example.py` implements the **generator → dual adversarial reviewer → conformance-gate** loop in pure Python against a simulated buggy code-porting task. It plants the three real bug classes from the Bun run (use-after-free-style ownership bug, sign error, eager-evaluation bug), shows how a single reviewer with author-context misses them while adversarial reviewers with diff-only context catch them, and demonstrates "fix the process" by mutating the loop's rule-set so a whole bug *class* disappears on the next iteration. It prints pass rates per strategy so you can see the review-economics argument numerically.
