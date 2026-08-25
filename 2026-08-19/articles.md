# Further Reading: How Debate Training Stops Reward Hacking of an LLM Judge

## Papers

### 1. [Debate Training Reduces Reward Hacking in RLAIF](https://arxiv.org/abs/2608.17776) — *primary source*
**Authors**: Zachary Kenton, Lili Janzer, Rory Greig, Tian Huey Teh, Kirill Tyshchuk, Jonah
Brown-Cohen, Harri Edwards, Senthooran Rajamanoharan, Noah Y. Siegel, Natasha Jaques, Rohin Shah
(Google DeepMind) | **Published**: 18 Aug 2026 | **Read time**: ~35 min (12 pages + appendices)
> First evidence that full-parameter multi-agent RL on a debate game reduces reward hacking in
> RLAIF with a frozen weaker judge. Debate maintains judge MCC and peak validation accuracy where
> the single-player baseline hacks the judge and degrades; 45% of the gap to the RLVR roofline
> recovered. Read §3.3 (protocol variants) and §4.4 (techniques that *didn't* work) even if you
> skip everything else — the negative results are unusually candid and directly actionable.

### 2. [AI Safety via Debate](https://arxiv.org/abs/1805.00899)
**Authors**: Geoffrey Irving, Paul Christiano, Dario Amodei (OpenAI) | **Published**: May 2018
> The original proposal this paper is finally testing as a *training* method. Argues that a
> zero-sum debate between two agents judged by a weaker human is in a complexity class that lets
> the judge supervise agents more capable than itself. Worth reading for the theoretical framing
> of why adversarial counterargument should scale where direct evaluation doesn't.

### 3. [Debate Helps Supervise Unreliable Experts](https://arxiv.org/abs/2311.08702)
**Authors**: Julian Michael, Salsabila Mahdi, David Rein, Jackson Petty, Julien Dirani, Vishakh
Padmakumar, Samuel R. Bowman (NYU) | **Published**: Nov 2023
> The key human-baseline result: 84% judge accuracy under debate vs 74% under consultancy (a
> single expert arguing one side). The important finding is the *slope* — as debaters get more
> skilled, debate accuracy rises while consultancy accuracy falls. Evidence that debate's
> incentive structure, not just its extra information, is doing the work.

### 4. [Scaling Laws for Reward Model Overoptimization](https://arxiv.org/abs/2210.10760)
**Authors**: Leo Gao, John Schulman, Jacob Hilton (OpenAI) | **Published**: Oct 2022
> The canonical characterization of the failure mode being patched here. Gives functional forms
> for how true reward diverges from proxy reward as you optimize harder against a learned reward
> model. Read this to understand *why* the peak-then-decline shape in Figure 3 is the expected
> default rather than a bug in someone's training run.

### 5. [Defining and Characterizing Reward Hacking](https://arxiv.org/abs/2209.13085)
**Authors**: Joar Skalse, Nikolaus H. R. Howe, Dmitrii Krasheninnikov, David Krueger
**Published**: Sep 2022
> Formal definitions of unhackability and the conditions under which a proxy reward can be safely
> optimized. Useful precisely because it shows how *restrictive* those conditions are — which is
> the argument for needing a dynamic mitigation like debate rather than a better static proxy.

## Practical

### 6. [Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073)
**Authors**: Yuntao Bai et al. (Anthropic) | **Published**: Dec 2022
> The RLAIF recipe this paper is directly modifying. Read it alongside §4.3 of the debate paper —
> the finding that RL incentives *override prompted misalignment* in both directions is a real
> constraint on how much load a constitution's prompt text can bear once gradients are flowing.

### 7. [Matthews Correlation Coefficient — why it beats accuracy and F1](https://bmcgenomics.biomedcentral.com/articles/10.1186/s12864-019-6413-7)
**Authors**: Davide Chicco, Giuseppe Jurman | **Source**: BMC Genomics | **Published**: Jan 2020
> Not an AI-safety paper, but the justification for the metric that makes this whole result
> legible. MCC only scores high when all four confusion-matrix quadrants are good, which is why
> it catches judge degradation in both directions where accuracy and F1 hide it under class
> imbalance. This is the single most portable thing in the session — add it to your eval harness.

## The Practical Takeaway

If you run an LLM-as-judge anywhere in an optimization loop, the cheapest thing you can do this
week is **log judge MCC against a small labelled holdout alongside your reward/score**. You do
not need debate, RL, or a critic to benefit from the paper's core diagnostic. Reward rising while
MCC falls is the signature, and almost nobody instruments for it.
