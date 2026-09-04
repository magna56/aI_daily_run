# Further Reading: Why GPT-6 Astra Has Two Scores on ARC-AGI-3: 63% and 99%

## Articles

### 1. [OpenAI's GPT-6 Astra on ARC-AGI-3](https://arcprize.org/blog/astra)
**Source**: ARC Prize Foundation | **Date**: September 3, 2026 | **Read time**: ~15 min
> The primary source, and note who wrote it: the people who maintain the benchmark, not the lab that
> scored on it. It carries the full six-by-two table this session is built on, the definitions of
> both harnesses, and the sentence worth quoting back at anyone waving a leaderboard — that these
> results should be read as the combined performance of the model and its tools. Read the table
> before the prose.

### 2. [GPT-6 Astra: verified results](https://arcprize.org/results/openai-gpt-6-astra)
**Source**: ARC Prize Foundation | **Date**: September 2026 | **Read time**: ~5 min
> The scores and dollar costs for every configuration, on one page, with a verified badge attached.
> Keep it open next to the blog post: this is where you can check that the older benchmarks in the
> family really do sit near the ceiling at every effort setting, which is the evidence that the
> harness effect scales with how much state a task carries.

### 3. [arc-agi-3-benchmarking](https://github.com/arcprize/arc-agi-3-benchmarking)
**Source**: ARC Prize Foundation on GitHub | **Date**: current | **Read time**: ~25 min
> The one to open in an editor, and the reason this session is not just an interesting anecdote. Both
> harnesses are implemented here against the same games, actions, limits and scoring, so you can read
> the diff between them rather than trusting either description. If you take one thing to your own
> eval code, take the shape of that separation — the scaffold is a swappable component with a name,
> not something smeared through the runner.

### 4. [ARC Prize Verified Testing Policy](https://arcprize.org/policy)
**Source**: ARC Prize Foundation | **Date**: current | **Read time**: ~8 min
> What it takes for a number to earn the verified label here. Worth reading even if you never touch
> this benchmark, because it is a written-down answer to a question most teams have never answered
> for their own evals: what has to be true before a score is allowed into the record. Steal the idea,
> not the specific rules.

### 5. [GPT-6 Astra](https://simonwillison.net/2026/Sep/3/gpt6-astra/)
**Source**: Simon Willison | **Date**: September 3, 2026 | **Read time**: ~6 min
> The practitioner's read on the launch, useful here as the counterweight. It covers what else
> shipped — pricing, context behavior, the security numbers — and is careful to flag the harness
> asterisk rather than quoting the headline figure. Read it if you want the rest of the release; skip
> it if you only came for the measurement argument.
