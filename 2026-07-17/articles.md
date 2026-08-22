# Further Reading: Friction as a Feature — Blast-Radius Gates for Agent-Driven Architecture Changes

## Articles

### 1. [The Tower Keeps Rising](https://simonwillison.net/2026/Jul/14/armin-ronacher/)
**Source**: Armin Ronacher (via Simon Willison's blog) | **Date**: July 14, 2026 | **Read time**: ~8 min
> The primary source for today's session. Argues that a codebase's real "spec" is the
> distributed, undocumented shared understanding a team carries about boundaries, invariants,
> and ownership — and that traditional review friction quietly served to synchronize that
> understanding, not just gatekeep code quality. Agents can now bypass the friction without
> replacing the synchronization it produced.

### 2. [Directly Responsible Individuals (DRI)](https://simonwillison.net/2026/Jul/12/directly-responsible-individuals/)
**Source**: Simon Willison's blog | **Date**: July 12, 2026 | **Read time**: ~4 min
> Companion piece on human accountability in agent-assisted workflows: agents should never be
> the DRI for a project because "humans can take accountability for their actions where
> machines cannot." Cites IBM's 1979 line about computers never making management decisions.
> Useful counterpart to the blast-radius idea — accountability and synchronization are related
> but distinct problems.

### 3. [Vibe coding and agentic engineering are getting closer than I'd like](https://simonwillison.net/2026/May/6/vibe-coding-and-agentic-engineering/)
**Source**: Simon Willison's blog | **Date**: May 6, 2026 | **Read time**: ~6 min
> Earlier post naming the underlying tension this session's topic tries to resolve
> operationally: how do you keep the speed benefits of agentic coding without sliding into
> unreviewed "vibe coding" for changes that actually matter architecturally.

### 4. [datasette code-frequency chart on GitHub](https://simonwillison.net/2026/Jul/13/datasette-code-frequency/)
**Source**: Simon Willison's blog | **Date**: July 13, 2026 | **Read time**: ~3 min
> Concrete, measurable look at how agent-assisted commit velocity has changed on a real
> open-source project as newer models (Opus 4.8, GPT-5.5, Fable 5) came online — useful
> grounding for why the friction question is becoming urgent now rather than hypothetical.

## Related Practical Prior Art

> Not from today's fetch, but the pattern in `code_example.py` deliberately builds on ideas
> already common in large monorepos: CODEOWNERS-based required reviewers, "RFC required" path
> lists, and API-diff/breaking-change linters (e.g. semantic versioning checkers). The novel
> piece is combining them into a single blast-radius score used specifically to decide when an
> agent-authored diff needs a human synchronization step, rather than a full code review.
