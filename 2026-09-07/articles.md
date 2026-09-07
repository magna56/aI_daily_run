# Further Reading: Why Your Tool's Output Format Only Hurts the Cheap Model

## Articles

### 1. [datasette-mcp 0.2](https://github.com/datasette/datasette-mcp/releases/tag/0.2)
**Source**: Datasette on GitHub | **Date**: 1 September 2026 | **Read time**: ~5 min
> The release that runs against the grain, and the shortest thing here. `execute_sql` now
> returns an array of objects instead of arrays of arrays, which makes every reply bigger on
> purpose. The stated reason is the whole article in one line: it stops weaker models losing
> track of which position maps to which column. Read it as a worked example of choosing the
> reader over the token count.

### 2. [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
**Source**: Anthropic Engineering | **Date**: current | **Read time**: ~25 min
> The section to find is the one on response format, because it refuses to name a winner —
> "there is no one-size-fits-all solution" — and instead suggests a `ResponseFormat` parameter
> so the caller asks for detailed or concise. That is the design this session lands on, arrived
> at from the other direction. The Slack example cuts 206 tokens to 72, which is the same order
> of saving as the benchmark below.

### 3. [TOON format benchmarks](https://toonformat.dev/guide/benchmarks)
**Source**: TOON project documentation | **Date**: current | **Read time**: ~15 min
> The numbers this session is built on, and worth reading with one eye open: the benchmark is
> run by the format's own authors and TOON wins it. Skip the headline. The two tables that
> matter are per-model accuracy, where Grok-4.5 varies 1.6 points across six formats and
> GPT-5.4 Nano varies 4.9, and accuracy by question type, where field retrieval sits at 97.8%
> or better everywhere and structural validation runs from 45% to 100%.

### 4. [Tool results in the MCP specification](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
**Source**: Model Context Protocol specification | **Date**: 28 July 2026 | **Read time**: ~20 min
> Where to check what you are actually allowed to return before you redesign a payload. The
> section on structured content and `outputSchema` is the relevant one: it lets a tool declare
> the shape of its result, which is a different lever from how the rows are written down and is
> easy to conflate with it. Read it if you are tempted to solve this with a schema instead.

### 5. [Stateless MCP](https://simonwillison.net/2026/Jul/31/stateless-mcp/)
**Source**: Simon Willison | **Date**: 31 July 2026 | **Read time**: ~10 min
> Background for why tool payload size is a recurring cost rather than a one-off. A stateless
> server re-sends what it returned on every turn that keeps it in context, so a verbose result
> is charged again and again. Useful for calibrating how much the 40% actually matters to your
> bill before you trade accuracy for it.
