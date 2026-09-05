# Further Reading: The Two Things Missing From Most Coding Agent Requests

## Articles

### 1. [SWE-bench](https://www.swebench.com/)
**Source**: SWE-bench (Princeton NLP and collaborators) | **Date**: current | **Read time**: ~10 min
> Read this second, to see what today's paper is arguing with. It is the leaderboard almost every
> coding-agent claim you have seen traces back to, and the task viewer is the part worth your time:
> open three or four problems and read them as prompts rather than as tasks. They are long, formal
> and complete in a way your own requests never are, which is the entire premise of the session and
> is much more convincing when you have seen the inputs yourself.

### 2. [SWE-bench: Can Language Models Resolve Real-World GitHub Issues?](https://arxiv.org/abs/2310.06770)
**Source**: arXiv (Jimenez, Yang, Wettig, et al.) | **Date**: October 2023 | **Read time**: ~30 min
> The original benchmark paper, and worth reading for its construction section rather than its
> results, which are long out of date. It is explicit that issues were filtered for being
> well-specified and resolvable, which was the right call for a benchmark and is exactly the
> selection today's paper measures the cost of. Read section 2 and skip the rest unless you are
> building a benchmark yourself.

## Papers

### [RealSWE: A Compositional Evaluation of Coding Agents under Realistic User Requests](https://arxiv.org/abs/2608.27831)
**Authors**: Gyuhyeong Kim, Hyojung Gwon, Jeonghyeon Kim, Kyuhong Shim, Sunjae Lee (Sungkyunkwan University) | **Published**: August 2026
> The primary source. Three things to take from it, in descending order of usefulness. The ablation
> table is the finding: desired behavior is worth 7.1 to 8.9 points and is present in 5% of real
> requests, while reproduction steps and environment details together are worth about 1.8. The
> corpus comparison is the setup, built from 718 real prompts against the curated issues benchmarks
> use. And the ranking change is the caveat with the longest reach — one model moved from fourth to
> second purely on how the prompts were written, which is worth remembering the next time you read
> any agent comparison at all.
