# Further Reading: How Agent Context Gets Re-Read Every Turn

## Articles

### 1. [Claude Code CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
**Source**: Anthropic | **Date**: continuously updated (read at 2.1.239) | **Read time**: ~10 min
> The primary source for this session. Read versions 2.1.212 through 2.1.239 as one
> document and the theme is unmistakable: subagent spawn caps, `/code-review` moved to
> a background subagent "so review work no longer fills your conversation", subagent
> tool results released once they leave the display window, and
> `CLAUDE_CODE_DISABLE_1M_CONTEXT` extended to hold every 1M-native model down to 200K.
> A changelog is an unusually honest design document — these are the problems that were
> worth engineering time.

### 2. [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
**Source**: Anthropic Engineering | **Date**: 29 Sep 2025 | **Read time**: ~15 min
> The conceptual foundation the changelog entries are implementing. Argues context is a
> finite budget to be curated rather than a bucket to fill, and covers the sub-agent and
> compaction patterns before they became default behaviour. Read this first if the
> "why" matters more to you than the "what shipped".

### 3. [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
**Source**: Anthropic docs | **Date**: current | **Read time**: ~12 min
> The mechanics behind every number in this session: the prefix-match invariant, the
> 0.1x read / 1.25x write multipliers, the tiered invalidation table, the 20-block
> lookback window, per-model minimum cacheable prefixes, and the concurrent-request
> race. The silent-invalidator checklist is the single most directly actionable page —
> grep your prompt-building code against it.

### 4. [The New MCP Roadmap](https://blog.modelcontextprotocol.io/posts/mcp-roadmap/)
**Source**: Model Context Protocol blog | **Date**: 22 Aug 2026 | **Read time**: ~8 min
> Published the same day as this session, and makes the identical argument at the
> protocol layer: "connecting to a server with a hundred tools means the model pays for
> that entire surface before the user has asked a single question." Proposes progressive
> discovery — a limited initial interface that expands as the conversation narrows.
> Confirms the context bill is now a protocol-design concern, not just a harness one.

### 5. [Cursor Changelog — Cloud Agents and harness improvements](https://cursor.com/changelog)
**Source**: Cursor | **Date**: 19 Aug 2026 | **Read time**: ~5 min
> The cross-tool check. Subagents on isolated VMs with independent project copies, a
> `/goal` command for long-lived objectives, and mid-task steering. Different vendor,
> different architecture, same conclusion about where the work should happen. Useful for
> separating what is a Claude Code design choice from what is a property of the problem.

### 6. [Conceptual integrity and counting lines of code](https://simonwillison.net/2026/Aug/19/)
**Source**: Simon Willison | **Date**: 19 Aug 2026 | **Read time**: ~6 min
> The counterweight. Where the rest of this reading list optimises the cost of a long
> session, this asks whether coherence survives one — and whether lines of code shipped
> is measuring the right thing at all. Worth reading immediately after the changelog, as
> a reminder that cheaper context is not the same as better output.
