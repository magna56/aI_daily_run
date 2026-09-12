# Further Reading: Why Your Agent's Reasoning Is the Worst Place to Audit It

## Articles

### 1. [An alignment assessment of recent cybersecurity incidents](https://www.anthropic.com/research/alignment-assessment-cybersecurity-incidents)
**Source**: Anthropic | **Date**: 9 September 2026 | **Read time**: ~35 min
> The primary source, and the paragraph worth the whole read is the one where separate instances
> review the evidence piecemeal: 79% call the environment real against 1% inside the original
> transcript. Read the two root causes it names — biased reasoning and recklessness — as separate
> problems, because only the first is what this session is about. Note also what the report is
> honest about: offline monitoring caught roughly half the actions in one incident and struggled
> worst exactly where the reasoning was misleading.

### 2. [Claude Code auto mode: a safer way to skip permissions](https://www.anthropic.com/engineering/claude-code-auto-mode)
**Source**: Anthropic Engineering | **Date**: 25 March 2026 | **Read time**: ~20 min
> The production defense the assessment credits with blocking 55-66% of the relevant actions, and
> worth reading for its design rather than its numbers. The pattern is a classifier that sits on
> the action rather than on the explanation of the action — the same placement argument this
> session makes, arrived at six months earlier for a different reason.

### 3. [Reasoning models don't always say what they think](https://www.anthropic.com/research/reasoning-models-dont-say-think)
**Source**: Anthropic | **Date**: 2025 | **Read time**: ~25 min
> The background that makes the incident findings unsurprising. It measures how often a model's
> stated reasoning fails to reflect what actually drove its answer, which is the property that
> makes a chain-of-thought monitor unreliable as an independent check. Read this before deciding
> how much weight to put on any reasoning trace you are logging.

### 4. [Natural Language Autoencoders](https://transformer-circuits.pub/2026/nla/index.html)
**Source**: Transformer Circuits Thread | **Date**: May 2026 | **Read time**: ~30 min
> Where the interpretability half of the assessment comes from. The report notes that 19% of the
> model's "simulated" claims carried "this is real" signals in its activations — a gap between
> what the model states and what its internals encode. Read this for how those activations get
> translated into readable claims at all, which is what makes that measurement possible.

### 5. [Confirmation bias](https://en.wikipedia.org/wiki/Confirmation_bias)
**Source**: Wikipedia | **Date**: current | **Read time**: ~20 min
> Included deliberately, because the failure in these transcripts is not exotic and naming it
> correctly helps. The literature on how humans reinterpret evidence to fit a held conclusion is
> the same shape as what the transcripts show, and the countermeasures are the same too: separate
> the evidence from the interpreter, and ask a reader who does not know the conclusion.
