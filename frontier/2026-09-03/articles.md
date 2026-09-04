# Further Reading: How to Turn a Repo Into a Skill Your Agent Can Actually Run

## Articles

### 1. [AREX-Skill: the library and the pipeline](https://github.com/VectorSpaceLab/AREX-Skill)
**Source**: VectorSpaceLab on GitHub | **Date**: September 2026 | **Read time**: ~20 min
> The one to open in an editor. Read a handful of the distilled skills before you write another one
> by hand — the fastest way to internalize the three-layer split is to see what the authors chose to
> put in `scripts/` rather than describe in prose. Compare a skill's `SKILL.md` against the
> repository it came from and you can see the scoping decision being made.

### 2. [Claude Code: Agent Skills](https://code.claude.com/docs/en/skills)
**Source**: Claude Code documentation | **Date**: current | **Read time**: ~12 min
> The format you are actually shipping into, and the reference to keep open while you restructure.
> It defines the frontmatter, the progressive-disclosure model, and where skills are discovered from.
> Read it alongside the paper and the mapping is close enough to be uncomfortable: the same three
> layers, with the verification gate the only thing missing.

### 3. [From Registry to Repository: How AI Agent Skills Are Written, Adapted, and Maintained](https://arxiv.org/abs/2607.00911)
**Source**: arXiv | **Date**: July 2026 | **Read time**: ~25 min
> The empirical study that makes today's argument urgent, and the one to read if you are unconvinced
> a gate is worth building. Across 18,463 registry skills and 23,199 personal ones over 5,876
> repositories, **53% are never modified after adoption**, and changes that do happen are additive
> rather than corrective. A skill's behavioral contract is almost never touched again. So an
> unverified skill is not a draft someone will fix later — it is what your agent runs forever.

## Papers

### [Repo-To-Skill: Distilling GitHub Repositories Into AI4AI Skills](https://arxiv.org/abs/2609.02749)
**Authors**: Jianlyu Chen, Yuyang Hu, Hongjin Qian, Jiawei Liu, Wenqing Wei, Xiaolong Chen, Defu Lian, Zhicheng Dou, Chaozhuo Li, Qiwei Ye, Zheng Liu (Beijing Academy of Artificial Intelligence; University of Science and Technology of China; Renmin University of China; Hong Kong Polytechnic University) | **Published**: September 2, 2026
> The primary source. Read section by section rather than end to end: the four-stage pipeline and the
> verification step are what you can act on this week, while the benchmark tables are context. Note
> what it does not claim — there is no ablation isolating the gate, so the headline gains measure the
> library as a whole rather than the checking. Worth reading with that gap in mind, because it is the
> gap you would have to close before betting a budget on this.
