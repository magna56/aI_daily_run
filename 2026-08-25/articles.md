# Further Reading: How a Coding-Agent Hook Decides to Fire (And Why It Still Isn't a Gate)

## Articles

### 1. [Claude Code Hooks reference](https://code.claude.com/docs/en/hooks)
**Source**: Anthropic docs | **Date**: current | **Read time**: ~20 min
> The primary source for everything in this session, and the page to keep open while you write a hook. The two tables worth bookmarking are the matcher evaluation rules (which characters make your string a regex) and the Bash pattern-matching table showing that `Bash(git *)` matches `FOO=bar git push` and `Bash(rm *)` matches `echo $(rm -rf /)`. Read the Security Warnings section first — it is four bullets and it tells you the `if` condition is best-effort before you build anything on top of it.

### 2. [Claude Code settings and permissions](https://code.claude.com/docs/en/settings)
**Source**: Anthropic docs | **Date**: current | **Read time**: ~15 min
> Where policy actually lives. Read this to write the `permissions.deny` rules that replace the hooks you thought were enforcing something, and to understand settings precedence — managed settings beat command line beat project-local beat shared project beat user, which matters the moment more than one person edits a rule. The reference to keep open while implementing.

### 3. [Claude Code CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
**Source**: anthropics/claude-code | **Date**: 2.1.243, August 2026 | **Read time**: ~5 min
> The entry this session hangs on: *"Fixed hook `if` conditions like `Bash(cat *)` firing on unrelated Bash commands when containing `$()`."* Read it to find out whether the version you are on descends into `$()` the old way or the fixed way, because that decides which commands your existing `if` conditions match today. If you maintain a shared `settings.json`, diff your rules against this before and after upgrading.
