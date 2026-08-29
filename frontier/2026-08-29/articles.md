# Further Reading: How a Model Trains Itself Without Knowing the Right Answer

Read 1 and 2 together — the paper states the asymmetry, the repo shows what it costs to
run. 3 and 4 are the background you need only if the two branches are unfamiliar.

## Articles

### 1. [TTPO code and training scripts](https://github.com/ZJU-REAL/TTPO)
**Source**: ZJU-REAL | **Date**: Aug 2026 | **Read time**: ~20 min
> The thing to open in an editor. `scripts/run_ttpo_1b.sh` through `run_ttpo_8b.sh` show the
> real setup — four GPUs, LoRA, colocated vLLM generation — which is the fastest way to find
> out whether this is affordable for you before reading another word of theory. Note that a
> dataset needs only a `problem` field; `answer` is optional and used solely for the
> ground-truth routing ablation, which tells you exactly how label-free the method really is.

### 2. [TTPO project page](https://zju-real.github.io/TTPO/)
**Source**: ZJU-REAL | **Date**: Aug 2026 | **Read time**: ~10 min
> Where the 85%/79% asymmetry is laid out with the figures behind it, plus the per-benchmark
> tables (AIME25/26, HMMT25/26, BRUMO25). Read this before the paper itself — it front-loads
> the one observation the whole method depends on, which the abstract states but does not
> justify.

### 3. [Test-Time Policy Optimization (arXiv:2608.27448)](https://arxiv.org/abs/2608.27448)
**Source**: arXiv | **Date**: 27 Aug 2026 | **Read time**: ~35 min
> The primary source. Go here for the token-level selection rules, which are the part most
> likely to be wrong if you reimplement from the summary alone — both masks are load-bearing
> and the paper is where their thresholds are defined. Skip unless you intend to build it.

### 4. [Agents in production](https://mlconcepts.viveksingh-heritage.workers.dev/)
**Source**: ML Concepts | **Date**: 2026 | **Read time**: ~15 min
> The intermediate on-ramp if "forward-KL distillation" and "grouped RL" are terms you have
> read but never implemented. Interactive primers on the underlying pieces; work through the
> distillation and RL pages first and the two branches above stop being jargon.

## Papers

### [Test-Time Policy Optimization](https://arxiv.org/abs/2608.27448)
**Authors**: Aozhe Wang, Zhengxi Lu, Jianze Wang, Shangke Lv, Ying Liu, Weiming Lu, Jun Xiao, Yueting Zhuang, Hua Yang, Qianglong Chen, Yongliang Shen | **Published**: 27 Aug 2026
> Without labels, TTPO matches label-supervised on-policy self-distillation on five
> competition benchmarks and lifts Qwen3-1.7B from 38.0% to 45.2% in test-time training.
> The result worth checking is the cross-task generalisation, since a method that only works
> on the distribution it was tuned against would not be usable at test time at all.
