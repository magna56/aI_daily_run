# Further Reading: How Coding Agents Work

## Primary Sources

### 1. [Claude Code overview](https://code.claude.com/docs/en/overview)
**Source**: code.claude.com | **Read time**: ~10 min
> The product shape: a terminal/IDE agent that works in your repository, not a paste box. Start here to see what the harness is responsible for (tools, session, working directory) versus what the model does.

### 2. [Claude Code memory (CLAUDE.md)](https://code.claude.com/docs/en/memory)
**Source**: code.claude.com | **Read time**: ~12 min
> How `CLAUDE.md` and auto-memory are loaded, where the files live (project, user, subdirectory), and why a long briefing becomes noise. This is the canonical spec for the briefing file the chapter keeps pointing at.

### 3. [Configure permissions](https://code.claude.com/docs/en/permissions)
**Source**: code.claude.com | **Read time**: ~15 min
> Allow / ask / deny rules, `/permissions`, and why deny is enforced by the harness even if the model is feeling cooperative. Read this before you allowlist a shell command or consider bypass mode.

## Background & Ecosystem

### 4. [Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices)
**Source**: anthropic.com/engineering | **Read time**: ~20 min
> Anthropic's engineering post on using the agent: explore before you edit, give Claude a way to check its work, keep `CLAUDE.md` short. The same advice applies, with different filenames, to Cursor and other repo-rooted agents.

### 5. [Using CLAUDE.md files](https://claude.com/blog/using-claude-md-files)
**Source**: claude.com | **Read time**: ~8 min
> A shorter, example-driven pitch for project briefings: build commands, conventions, and the `/init` starter. Useful if the docs page is more reference than narrative.

## The one-line takeaway
Chat is a function of the prompt you typed. A coding agent is that function plus the working tree, a briefing file, and a permission gate — use it when the tree matters, and do not turn the gate off on a trusted machine.
