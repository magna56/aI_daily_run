# Further Reading: How a Coding Agent Picks the Model for Each Subagent

## Articles

### 1. [Claude Code CHANGELOG — 2.1.251](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
**Source**: Anthropic | **Date**: Aug 2026 | **Read time**: ~6 min
> The primary source, and the only place the precedence change is stated: *"Changed `CLAUDE_CODE_SUBAGENT_MODEL` to set the default subagent model rather than override everything."* Read the same release's `PreModelSwitch` / `PostModelSwitch` and `/cost` prompt-cache entries in the same pass — they are the two halves of the control and observation story this session builds on. Open this first if you maintain a shared `.claude/` directory for a team.

### 2. [Configure permissions](https://code.claude.com/docs/en/permissions)
**Source**: Claude Code docs | **Date**: current | **Read time**: ~12 min
> The reference to keep open while you write the deny rules. The "Match by input parameter" section is the one that matters: it states that only deny and ask rules can match a parameter, that an omitted parameter never matches even against `*`, and that the value is compared to the literal input *before normalization* — which is why a rule naming `opus` sails past `claude-opus-5`. Every failure mode in this session's code example is documented on that page.

### 3. [Subagents](https://code.claude.com/docs/en/sub-agents)
**Source**: Claude Code docs | **Date**: current | **Read time**: ~10 min
> The agent-definition frontmatter reference — `model`, `effort`, `tools`, `disallowedTools`, and what `inherit` means. Worth reading with the changelog beside it: at the time of writing this page still lists the pre-2.1.251 resolution order with the environment variable first, which is a useful reminder that a version number beats a docs page when the two disagree.

### 4. [Hooks reference](https://code.claude.com/docs/en/hooks)
**Source**: Claude Code docs | **Date**: current | **Read time**: ~15 min
> Open in an editor and copy from it. The `PreModelSwitch` entry gives the exact JSON input (`from_model`, `to_model`), the `hookSpecificOutput.permissionDecision` shape, the exit-code-2 path, and the rule that a timeout blocks the switch — everything you need to write the guard script in this session without guessing a field name. Skip the rest of the page unless you are writing your first hook.

### 5. [Reducing costs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
**Source**: Anthropic | **Date**: current | **Read time**: ~14 min
> The wider-context piece, and the reason a mixed-model fan-out costs more than the per-token table suggests: prompt caches are scoped per model, so every model a helper runs on is its own cache namespace. Read this if the `/cost` hit ratio drops after you change model routing and the per-token arithmetic does not explain the bill.
