# Further Reading: How a Coding Agent Decides to Re-Read Your Whole Conversation

## Articles

### 1. [How Claude Code uses prompt caching](https://code.claude.com/docs/en/prompt-caching)
**Source**: Claude Code documentation | **Date**: current | **Read time**: ~15 min
> The primary source for everything in this session, and the page to keep open while you change
> anything. It carries both lists in full — the nine actions that invalidate the cache and the eight
> that keep it — plus the TTL default table, the six-step precedence order, and the cache-scope rule
> that explains why two worktrees of one repository never share an entry. Read the two lists first
> and skip the provider section unless you route through a gateway.

### 2. [Lessons from building Claude Code: prompt caching is everything](https://claude.com/blog/lessons-from-building-claude-code-prompt-caching-is-everything)
**Source**: Anthropic (Thariq Shihipar, Claude Code team) | **Date**: April 30, 2026 | **Read time**: ~10 min
> The same rules read from the other side of the fence: why plan mode injects a message instead of
> swapping the tool set, why compaction copies the parent's parameters exactly so the summarization
> call can reuse the prefix, and why static content goes first. Read this if you are building a
> harness of your own rather than driving one — it turns this session's list of things to avoid into
> a set of design decisions you can copy.

### 3. [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
**Source**: Claude API documentation | **Date**: current | **Read time**: ~20 min
> The mechanism underneath, and the one to open in an editor. It gives you the pieces this session
> abstracts away: `cache_control` breakpoints, the four-breakpoint limit, the per-model minimum
> cacheable prefix, and the exact write and read multipliers. Anyone calling the API directly should
> read the breakpoint-placement section before writing prompt-assembly code, because the ordering
> mistakes it describes are silent — the requests still succeed, the bill is just higher.

### 4. [Manage costs effectively](https://code.claude.com/docs/en/costs)
**Source**: Claude Code documentation | **Date**: current | **Read time**: ~12 min
> Where to look once you have made the change. The `Prompt cache (main)` line in `/usage` is
> documented here field by field, including what counts as a miss and what an expected rebuild is,
> and the "why usage climbs in a long session" section names the four causes that are not caching at
> all. Read it the day a session costs more than you expected, rather than in advance.

### 5. [How a coding agent picks the model for each subagent](#2026-08-30)
**Source**: this site | **Date**: August 30, 2026 | **Read time**: ~10 min
> The companion case, and worth reading next. It works through the four-layer precedence chain that
> decides which model a subagent actually runs on — the same kind of first-match-wins ordering as the
> TTL precedence list here, and the same failure mode, where a setting you wrote is quietly beaten by
> one you forgot about. Every model that chain resolves differently is also a separate cache.
