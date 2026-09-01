# Further Reading: How to Tell If Your Model's Confidence Score Means Anything

## Articles

### 1. [When Linguistic and Internal Confidence Diverge in Large Language Models](https://arxiv.org/abs/2608.28382)
**Source**: arXiv (Zhang, Zhang, Cheng, Hassanpour, Ma & Vosoughi; Dartmouth College / Oakland University) | **Date**: 28 Aug 2026 | **Read time**: ~30 min
> The session's primary source. Read Section 5.1 first even if you read nothing else: it is where
> the aggregate correlation of r = 0.483 splits into r = 0.261 for base models and r = -0.005 for
> instruction-tuned ones, and seeing those three numbers next to each other is the argument. The
> rest of the paper is the case that association, magnitude agreement and calibration have to be
> reported separately, which is the part you will actually reuse.

### 2. [HF-heaven/Correlation-between-Confidence-Measurements](https://github.com/HF-heaven/Correlation-between-Confidence-Measurements)
**Source**: GitHub (the paper's authors) | **Date**: released with the paper | **Read time**: ~30 min hands-on
> The thing to open in an editor. The prompt templates matter as much as the metrics here — the
> paper's own finding is that prompt design mostly moves the *distribution* of reported confidence,
> so seeing exactly how they elicited a score is what lets you compare your pipeline against theirs
> rather than guessing. Read first if you already ask for confidence in production.

### 3. [Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation](https://arxiv.org/abs/2302.09664)
**Source**: arXiv (Kuhn, Gal & Farquhar; Oxford / OATML) | **Date**: Feb 2023 | **Read time**: ~25 min
> The source of the internal signal this session uses for free-form generation, and the reason
> "just take the token probabilities" does not work there. Two answers that say the same thing in
> different words are not two disagreements, and semantic entropy is the fix: cluster samples by
> meaning first, then measure the spread. The reference to keep open when you have no logprobs and
> have to build the internal channel out of repeated sampling.

### 4. [Teaching Models to Express Their Uncertainty in Words](https://arxiv.org/abs/2205.14334)
**Source**: arXiv (Lin, Hilton & Evans; OpenAI / Oxford) | **Date**: May 2022 | **Read time**: ~20 min
> The paper that established verbalised confidence as a thing a model can be trained to do well,
> and therefore the right counterweight to today's. It shows the channel is not inherently broken —
> it can be made calibrated on a task the model was tuned for. Read it to keep the conclusion
> narrow: the finding is that an *untrained, prompted* confidence score is unreliable, not that
> spoken confidence is unusable in principle.

### 5. [How Model Calibration Works](#learn/calibration)
**Source**: this site's own AI basics track | **Date**: 2026-08-23 | **Read time**: ~10 min
> The on-ramp if "calibration" and "expected calibration error" are not already familiar. Start
> here before the papers above — today's session assumes you know what it means for a model that
> says eighty percent to be right eight times in ten, and the whole argument turns on calibration
> being a different question from association.
