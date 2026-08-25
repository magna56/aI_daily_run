# Further Reading: How to Write Prompts That Hold Up

## Primary Sources

### 1. [Prompt engineering overview (Anthropic)](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
**Source**: docs.anthropic.com | **Read time**: ~12 min
> Anthropic's own order of operations: be clear, use examples, then reach for fancier techniques. The page is explicit that prompt work is for criteria you can control with text — not a substitute for picking a cheaper model or writing an eval.

### 2. [Prompt engineering guide (OpenAI)](https://platform.openai.com/docs/guides/prompt-engineering)
**Source**: platform.openai.com | **Read time**: ~15 min
> OpenAI's tactics with copy-pasteable patterns: write instructions, provide examples, split complex tasks, give the model an out. Useful as a second vendor saying the same boring things.

### 3. [Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices)
**Source**: anthropic.com/engineering | **Read time**: ~20 min
> How prompting changes when the model can edit your repo: explore first, give a verification loop, put standing rules in `CLAUDE.md`. This is the production-agent half of the chapter, not the chat-box half.

## Background & Ecosystem

### 4. [Prompting guide](https://www.promptingguide.ai/)
**Source**: promptingguide.ai | **Read time**: browse
> A long, maintained catalog of techniques (few-shot, chain-of-thought, and the rest) with citations. Use it as an index when you need a named pattern; do not try to apply every section to a coding agent.

### 5. [Give Claude context: CLAUDE.md and better prompts](https://support.claude.com/en/articles/14553240-give-claude-context-claude-md-and-better-prompts)
**Source**: support.claude.com | **Read time**: ~8 min
> Short help-center piece that ties standing project context to the prompt you type once. A bridge into the next Learn chapter, where the repo and the permission gate take over from the prompt.

## The one-line takeaway
A prompt that holds up is a ticket: scope, examples, non-goals, and a check the model cannot talk past. Adjectives are not a spec.
