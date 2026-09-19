# Further Reading: AGENTS.md: One Rules File for Claude, Codex, Cursor and Copilot

## Articles

### 1. [AGENTS.md](https://agents.md/)
**Source**: Agentic AI Foundation (Linux Foundation) | **Read time**: ~10 min
> The spec, and it is short enough to read in full before you write anything. There is no schema, which is most of why it spread — the useful parts are the worked example of what sections to include, and the one sentence that does the real work: the closest file to the one being edited wins, and an explicit chat instruction overrides everything. Read this first, then open your own file and see how much of it is advice about one specific tool.

### 2. [Adding repository custom instructions for GitHub Copilot](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)
**Source**: GitHub Docs | **Read time**: ~12 min
> The surprising one. Copilot reads four kinds of instruction file, and two of them are named after other vendors' tools — `CLAUDE.md` and `GEMINI.md` in the repository root. Read it if you maintain a repo that more than one team uses, because it means a file you thought only Claude Code read is shaping Copilot's behavior too. The precedence section, personal over repository over organization, is the part to keep open while you consolidate.

### 3. [Claude Code CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
**Source**: anthropics/claude-code | **Read time**: ~5 min for the entry
> The primary source for the change that prompted this session. Find 2.1.277 and read the `AGENTS.md` line twice: the fallback is one-way, and the parenthetical — "not yet on Bedrock, Vertex or Foundry" — is the detail that decides whether consolidating is safe for your team. Worth scanning the surrounding entries too, since instruction loading has moved several times this month.

### 4. [How Claude remembers your project](https://code.claude.com/docs/en/memory)
**Source**: Claude Code documentation | **Read time**: ~15 min
> The reference to keep open while you implement. It has the full load order, the rule that every ancestor directory is read and not just your working directory, and `claudeMdExcludes` for files you did not write and cannot delete. It also documents `@path` imports, which is the mechanism behind the Bedrock-safe layout in this session — one file importing the other rather than two copies of the same prose.

### 5. [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
**Source**: Anthropic Engineering | **Read time**: ~20 min
> The wider argument, and the reason to keep the file short once you have only one. Consolidating four files into one 900-line file solves the drift problem and creates a worse one, because every instruction competes for the same window on every turn. Read it if your instructions are already long; skip it if you only came for the lookup order.
