# Further Reading: `Bash(rm *)` Even Catches `echo $(rm -rf /)`

## Articles

### 1. [Claude Code Hooks reference](https://code.claude.com/docs/en/hooks)
**Source**: Anthropic docs | **Date**: current | **Read time**: ~20 min
> The primary source for everything in this session, and the page to keep open while you write a hook. The two tables worth bookmarking are the matcher evaluation rules (which characters make your string a regex) and the Bash pattern-matching table showing that `Bash(git *)` matches `FOO=bar git push` and `Bash(rm *)` matches `echo $(rm -rf /)`. Read the Security Warnings section first — it is four bullets and it tells you the `if` condition is best-effort before you build anything on top of it.

### 2. [Claude Code settings and permissions](https://code.claude.com/docs/en/settings)
**Source**: Anthropic docs | **Date**: current | **Read time**: ~15 min
> Where policy actually lives. Read this to write the `permissions.deny` rules that replace the hooks you thought were enforcing something, and to understand settings precedence — managed settings beat command line beat project-local beat shared project beat user, which matters the moment more than one person edits a rule. The reference to keep open while implementing.

### 3. [Claude Code CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
**Source**: anthropics/claude-code | **Date**: 2.1.243, August 2026 | **Read time**: ~5 min
> The entry this session hangs on: *"Fixed hook `if` conditions like `Bash(cat *)` firing on unrelated Bash commands when containing `$()`."* Worth reading the surrounding release too — `modelPicker`, `modelPricing` and the `Skipped sources` line in `/status` are all governance surface landing in the same version, which is why more teams are writing rules right now than were six months ago. Read first if you maintain a shared `settings.json`.

### 4. [Anthropic Engineering blog](https://www.anthropic.com/engineering)
**Source**: Anthropic | **Date**: ongoing | **Read time**: varies
> Background on why agent harnesses are built this way — the posts on agent design and context engineering explain the reasoning behind fail-open defaults, which is the part of this session most likely to feel wrong until you have tried to operate a hook that fail-closed on every command it could not parse.

### 5. [Cursor changelog — Cloud Agents and harness improvements](https://cursor.com/changelog)
**Source**: Cursor | **Date**: 19 August 2026 | **Read time**: ~5 min
> The cross-tool check. Subscriptions that respond to events, custom modes pinned with a keystroke, and subagents on isolated machines — a different vendor building the same governance surface in the same month. Useful for seeing which of the ideas in this session are Claude Code specifics and which are becoming conventions across coding agents.
