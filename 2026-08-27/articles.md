# Further Reading: How to Catch the Broken Step Your Agent's Tests Miss

## Articles

### 1. [Layer-Isolated Evaluation: Gating the Deterministic Scaffold of a Production LLM Agent with a No-LLM, Regression-Locked Test Harness](https://arxiv.org/abs/2606.11686)
**Source**: arXiv | **Date**: June 2026 | **Read time**: ~20 min
> The primary source for this session — read this first. Zhang, Wang & Lei decompose a deployed ordering agent into eight layers, build a 238-case pure-mode suite that runs in 2.39 seconds, and validate it by injecting a regression into one layer at a time. The masking table in Section 4 is the whole argument in one place: aggregate score barely moves, matching slice craters.

### 2. [LLM Agent Evaluation Metrics in 2026: Tool Calling, Task Completion, Reasoning, and Trace-Based Evals](https://www.confident-ai.com/blog/llm-agent-evaluation-complete-guide)
**Source**: Confident AI | **Read time**: ~15 min
> The best mechanical explanation of *why* end-to-end scores under-inform: it names the same three-level split (end-to-end, trajectory, component) this session uses, with its own line worth remembering — "end-to-end tells you that something is wrong; component-level tells you what." Read this for the vocabulary before you read the paper's Section 3.

### 3. [Eval harness: what it is, how to use it, and why you should care](https://deepeval.com/blog/what-is-an-eval-harness)
**Source**: DeepEval | **Read time**: ~10 min
> The hands-on piece — a real pytest-based harness you can open in an editor, wired to run on every CI push and block a release on a metric regression. It stops at end-to-end and metric-level testing rather than per-layer slices, so treat it as the CI-wiring pattern to adapt, not a finished implementation of this session's technique.

### 4. [Effective Practices for Mocking LLM Responses During the Software Development Lifecycle](https://agiflow.io/blog/effective-practices-for-mocking-llm-responses-during-the-software-development-lifecycle)
**Source**: Agiflow | **Read time**: ~8 min
> Read this before you build your own pure-mode slices, not after — its core warning is exactly this session's `When Layer-Isolated Testing Is the Wrong Tool` section: "a cassette is not proof that the answer is good, it is proof your application can handle a captured exchange." A locked baseline tests your scaffold; it was never meant to catch the model getting worse.
