# Further Reading: How to Compile a Prompt Into a Function You Can Ship

## Articles

### 1. [The compiler, running, in a browser](https://programasweights.com/playground?compiler=paw-ft-bs48)
**Source**: Program as Weights (the authors' own service) | **Date**: September 2026 | **Read time**: ~15 min
> Read this second, right after the abstract, because the argument only lands once you have watched
> a sentence turn into a running artifact. Type a spec, wait about a minute, then feed the compiled
> function inputs it has never seen. Try a spec that needs a fact about the world and watch it fail —
> that is the counter-case in the write-up, demonstrated on yourself rather than taken on trust.

### 2. [paw-helper](https://github.com/programasweights/paw-helper)
**Source**: Program as Weights on GitHub | **Date**: current | **Read time**: ~20 min
> The one to open in an editor. It is a real deployment of a compiled function — a website helper —
> so you can see how a `.paw` artifact gets loaded, invoked and guarded at an actual call site. That
> call-site shape is the part worth stealing even if you never compile anything: the local attempt,
> the validation, and the remote fallback behind it. Its sibling
> [claudish](https://github.com/programasweights/claudish) is the same pattern for translation.

### 3. [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
**Source**: arXiv (Microsoft) | **Date**: 2021 | **Read time**: ~30 min
> Read this if "rank-64 adapter" went past you, because the whole economic argument rests on it.
> LoRA is why one frozen base can serve many compiled functions: the per-function weights are small
> enough to swap per call, so ten functions cost you one model in memory rather than ten. Skip the
> experiments and read sections 3 and 4 — rank, and what it trades away.

## Papers

### [Compile by Training: Turning Natural-Language Specifications into Local Neural Functions](https://arxiv.org/abs/2609.04199)
**Authors**: Yuntian Deng, Pengyu Nie (University of Waterloo), Stuart Shieber (Harvard) | **Published**: September 4, 2026
> The primary source. Two things to read closely and one to discount. Read the supervision sweep,
> because the teacher-mix result is the most portable finding in the paper and applies to any
> distillation you do. Read the limitations, which are unusually honest about synthetic supervision
> inheriting teacher errors. Discount the headline accuracy until you check what FuzzyBench-Hard is:
> it holds only the specs the fast path scored zero on, so 0.836 is a number from the hard end of the
> distribution, not an average over normal work.
