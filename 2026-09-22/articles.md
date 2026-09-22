# Further Reading: How Jev Answers Five Questions in One Round Trip

## Articles

### 1. [Speculative fan-out](https://docs.typesafe.ai/patterns/fan-out)
**Source**: TypeSafe AI | **Date**: September 2026 | **Read time**: ~4 min
> The page this session is built on, and the shortest thing here worth your time. It states the property the whole argument rests on — questions are evaluated in parallel, so adding more has little effect on response time — and then draws the conclusion most teams would not: put every question your system needs in a single request, including the ones that probably will not apply. Read it first.

### 2. [State](https://docs.typesafe.ai/concepts/state)
**Source**: TypeSafe AI | **Date**: September 2026 | **Read time**: ~4 min
> The reference to keep open while you implement. String, object or array; text only, no images or audio; English strongest. It is also where the design rule lives that the article leans on: keep facts in the state and judgments in the questions, because the state is shared across every question and the question text is not.

### 3. [Building a harness with Jev](https://www.langchain.com/blog/building-a-harness-with-jev)
**Source**: LangChain, by Sydney Runkle and Hunter Lovell | **Date**: 2026-09-17 | **Read time**: ~8 min
> The one to open in an editor. Three shapes you can lift — classification, model-routing middleware, and a guardrail that blocks a risky tool call before it runs. Read it for the framing as much as the code: the authors say plainly this is not a drop-in replacement for a language model, and that the pairing is an LLM for generation with a structured model for the decisions along the way.

### 4. [Workflow evals](https://evals.typesafe.ai/)
**Source**: TypeSafe AI | **Date**: September 2026 | **Read time**: ~5 min
> The accuracy numbers, and the reason to read them with your guard up. Four workflows across roughly ten models. Read the methodology note before the charts: the reference answers are an average of two frontier models rather than human labels, and TypeSafe's own team wrote the workflows, so the figure measures agreement with an expensive model rather than correctness. Useful for shape, not for a procurement decision.

### 5. [API reference](https://docs.typesafe.ai/api)
**Source**: TypeSafe AI | **Date**: September 2026 | **Read time**: ~3 min
> Skip unless you are writing the client today. One endpoint, the request and response bodies field by field, and the error codes that matter in production — 429 and 529 both want exponential backoff, which is worth wiring before you point real traffic at it rather than after.
