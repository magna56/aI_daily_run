# Further Reading: How Skills Work

## Articles

### 1. [Extend Claude with skills](https://code.claude.com/docs/en/skills)
**Source**: code.claude.com | **Read time**: ~15 min
> The canonical Claude Code guide: a skill is a directory with `SKILL.md` (YAML frontmatter plus markdown), discovered from `~/.claude/skills/` or `.claude/skills/`. Covers trigger `description`s, `/skill-name` invocation, `disable-model-invocation`, `allowed-tools`, and dynamic `!` command injection. This is the file format the session describes.

### 2. [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
**Source**: platform.claude.com | **Read time**: ~8 min
> The API-side view of the same pack: required `name` and `description` fields, character limits, and how custom skills differ from Claude Code's filesystem install. Useful once you want the same `SKILL.md` to travel beyond one repo.

### 3. [Claude Skills are awesome, maybe a bigger deal than MCP](https://simonwillison.net/2025/Oct/16/claude-skills/)
**Source**: simonwillison.net | **Read time**: ~8 min
> The essay that named the pattern for a lot of engineers: a skill is markdown plus optional scripts, the frontmatter catalog is token-cheap, and any agent that can read a filesystem can use one. Frames skills as closer to a README than to a protocol or a fine-tune.

### 4. [Agent Skills](https://agentskills.io)
**Source**: agentskills.io | **Read time**: ~10 min
> The open specification the format grew into — a small, readable standard for `SKILL.md` so Cursor, Codex, and other harnesses can share folders. Read the spec page if you want the portable contract, not just Claude Code's implementation.

### 5. [Hooks](https://code.claude.com/docs/en/hooks)
**Source**: code.claude.com | **Read time**: ~12 min
> Lifecycle scripts (`PreToolUse`, `PostToolUse`, `SessionStart`, and the rest) that run *outside* the model. Use this when you are choosing skill vs hook: hooks enforce and inject; they do not replace a playbook.

## The one-line takeaway
A skill is a lazy-loaded instruction file. The description is the router; the body is the procedure; a hook is a different primitive; a sub-agent is a different process.
