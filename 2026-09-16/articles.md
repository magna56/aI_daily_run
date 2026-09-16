# Further Reading: What a Coding Agent Loads Into Every Subagent You Spawn

## Articles

### 1. [Subagents — what loads at startup](https://code.claude.com/docs/en/sub-agents)
**Source**: Claude Code documentation | **Date**: current | **Read time**: ~8 min
> The authority for this session. Two things here are worth more than the rest of the page: the list of six items already in a subagent's context before your task arrives, and the matching list of what never reaches it — no conversation history, no files the parent read, no auto memory. The frontmatter table below it is the reference to keep open while you edit an agent file, and `omitClaudeMd` is one row of it. Read this first.

### 2. [How Claude remembers your project](https://code.claude.com/docs/en/memory)
**Source**: Claude Code documentation | **Date**: current | **Read time**: ~15 min
> Where the size comes from. It gives the full load order — managed policy, user, project, local — and the rule that catches people out in monorepos: every ancestor directory is read, not just your working directory. It also states plainly that `@path` imports expand at launch and do not reduce context, which kills the most common workaround. The `claudeMdExcludes` section is the lever for files you did not write and cannot delete.

### 3. [Hooks reference](https://code.claude.com/docs/en/hooks)
**Source**: Claude Code documentation | **Date**: current | **Read time**: ~12 min
> The one you open in an editor. `InstructionsLoaded` is how you verify the change instead of believing it — it fires per instruction file, with a matcher naming why the file loaded (`session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact`). The docs do not publish the payload schema for this event, so log the raw event first and read the fields off your own output before writing anything that parses it.

### 4. [The context window](https://code.claude.com/docs/en/context-window)
**Source**: Claude Code documentation | **Date**: current | **Read time**: ~10 min
> Read this when you want the whole budget rather than this one line item. It shows where instructions sit relative to system prompt, tools and history, and has the breakdown of what survives compaction — which explains why a project CLAUDE.md is re-injected after `/compact` and a conversation-only instruction is not. Useful for deciding whether your instruction load is actually your problem, or whether something else is eating the window.

### 5. [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
**Source**: Anthropic Engineering | **Read time**: ~20 min
> The wider argument, and the one to read if you are building a fan-out rather than tuning one. It treats context as a budget to be spent deliberately, which is the frame that makes `omitClaudeMd` obvious rather than fiddly: the question is never "can I afford these tokens" but "is this the best use of the window I am handing this agent". Skip it if you only wanted the config key.
