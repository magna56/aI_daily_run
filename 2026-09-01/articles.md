# Further Reading: How to Check AI-Written Code Against Someone Else's Test Suite

## Articles

### 1. [Introducing wrapture](https://grahamdumpleton.me/posts/2026/08/introducing-wrapture/)
**Source**: Graham Dumpleton (author of `wrapt` and `mod_wsgi`) | **Date**: 31 Aug 2026 | **Read time**: ~12 min
> The session's primary source, and the reason this technique is worth copying rather than
> admiring: a library with over a thousand tests and 150-plus pages of documentation, written by an
> AI under direction, by someone whose name on it means something. Read the section on method, not
> the feature list — the days of design documents before any code, the layer-by-layer sequencing,
> and the borrowed test suites are the transferable part. Read first if you are about to let an
> agent build something you will have to maintain.

### 2. [wrapture on PyPI](https://pypi.org/project/wrapture/)
**Source**: PyPI | **Date**: 1.0.0a12, Aug 2026 | **Read time**: ~20 min hands-on
> The thing to open in an editor. `pip install wrapture` and read the tests rather than the docs:
> the ported suites are in there, and seeing what a faithful port of somebody else's assertions
> actually looks like is worth more than any description of the technique. Requires Python 3.12+.

### 3. [Enhancing Differential Testing With LLMs For Testing Deep Learning Libraries](https://arxiv.org/abs/2406.07944)
**Source**: arXiv (also in ACM TOSEM) | **Date**: Jun 2024 | **Read time**: ~25 min
> Where the technique in this session comes from, named and measured. Differential testing solves
> the *test oracle problem* — the fact that most programs have no executable definition of
> "correct" — by making two implementations argue. Read it for the vocabulary and for the failure
> modes: it is candid about how often a divergence turns out to be a difference rather than a bug,
> which is exactly the triage step this article's `spec` verdict exists for.

### 4. [How to Turn AI Code Review Comments Into a CI Gate](#2026-08-26)
**Source**: this site | **Date**: 2026-08-26 | **Read time**: ~10 min
> The complement. That session is about making a machine's *opinion* of your code enforceable;
> this one is about not trusting the tests that came with it. Read them together if you are
> building the review path for an AI-heavy repository — they are the two halves of the same
> question, and neither is sufficient alone.
