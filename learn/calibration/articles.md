# Further Reading: How Model Calibration Works

## Primary Sources

### 1. [On Calibration of Modern Neural Networks](https://arxiv.org/abs/1706.04599)
**Source**: arXiv | **Read time**: ~30 min
> Guo et al., 2017. Reliability diagrams, ECE, and temperature scaling as a one-parameter fix. The paper interviewers mean.

### 2. [Obtaining Well Calibrated Probabilities Using Bayesian Binning](https://www.cs.cmu.edu/~pstrohman/papers/bbq.pdf)
**Source**: cs.cmu.edu | **Read time**: ~20 min
> Histogram binning and why a score that looks like a probability still needs a plot. Background for ECE.

### 3. [Language Models (Mostly) Know What They Know](https://arxiv.org/abs/2207.05221)
**Source**: arXiv | **Read time**: ~35 min
> Kadavath et al. Token softmax is not task truth. Read this before you threshold a chat model's "confidence."

## Background & Ecosystem

### 4. [Uncertainty Quantification and Deep Ensembles](https://huggingface.co/blog/ensemble-uncertainty)
**Source**: huggingface.co | **Read time**: ~12 min
> When temperature scaling is not enough and people reach for ensembles. Still start with the bins.

### 5. [Evals that catch regressions](https://www.anthropic.com/research/evaluating-ai)
**Source**: anthropic.com | **Read time**: ~15 min
> Measuring the thing you ship. Calibration is one plot inside that habit.

## The one-line takeaway
Accuracy can look fine while the bins lie. Plot confidence against frequency, then fit a temperature on held-out data.
