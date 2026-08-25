# `Bash(rm *)` Even Catches `echo $(rm -rf /)`. It's Still Not a Gate.

**Category**: Coding Agents & Productivity
**Tags**: coding-agents, security, reliability
**Date**: 2026-08-25
**Level**: Building
**For**: Using tools
**Hook**: The rules you write to stop your coding agent running dangerous commands are cleverer than most people expect and weaker than most people assume — and the difference decides whether they are a workflow tool or a safety net that isn't there.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine you hire a very fast assistant and pin a note above their desk: "check with me before you throw anything away." The note is good. It catches them when they say "throw this away," and it even catches them when they say "do whatever that other note says" and *that* note says throw something away. Clever. But the note is still just a note. If your assistant phrases the request in a way the note's wording doesn't cover, they don't stop — and nobody rings a bell to tell you the note was skipped. A locked bin is a different thing from a note about the bin. Most people writing rules for AI coding assistants have written a very good note and believe they installed a lock.

## The Problem

Claude Code lets you attach hooks to your agent — small programs that run before a tool call and can block it. Most people's first hook is a safety rule: stop `rm`, stop `git push --force`, stop writes to production config. The rule looks like `"if": "Bash(rm *)"`, it reads like a firewall rule, and it goes into a settings file next to the permission settings. So it gets treated as a boundary. Then two things happen that nobody expects: it matches commands you never wrote, and it misses commands you did. Version 2.1.243 shipped a fix for exactly the first case — hook `if` conditions "firing on unrelated Bash commands when containing `$()`" — which is a good bug report and a better hint about what these rules actually are.

## For a Software Engineer

**This is a lexer masquerading as a parser, and you have shipped this bug yourself.** Anyone who has written a regex to validate email addresses, or grepped a log for `ERROR` and caught `ERROR_SUPPRESSED`, has met this exact shape: a pattern language that is good enough to feel authoritative and not structured enough to be one. The matcher does not build a syntax tree of your shell command and reason about it. It does light structural work over text.

**The light structural work is better than you'd guess.** `Bash(git *)` matches `FOO=bar git push`, because leading environment assignments are stripped first. It matches `npm test && git push`, because each subcommand of a chain is checked separately. And `Bash(rm *)` matches `echo $(rm -rf /)`, because commands inside `$()` and backticks are checked too. That is real analysis, and it catches the three tricks people actually try.

**The documentation tells you the limit in one sentence, and it is the most important sentence in the page:** the `if` condition is *best-effort* — when it cannot parse complex Bash, **the hook runs anyway**, and you should "use the permission system for hard policy enforcement." Fail-open, by design, stated out loud.

**And there is a second surprise one layer up.** The `matcher` field decides between two completely different matching modes based on which *characters* you happened to type. Only `[A-Za-z0-9_-, |,]` in the string? Exact match. One character outside that set? Unanchored JavaScript regex. `Edit|Write` is an exact two-item list. `^Notebook` is a regex. Nothing in the syntax tells you which one you wrote.

**Monday morning:** open your `settings.json`, find every `matcher` and every `if`, and decide for each one whether you meant *workflow* or *policy*. The ones that meant policy belong in `permissions.deny`, not in a hook.

## What This Means for You

**When this matters.** You have written a hook, a `permissions` rule, or a plugin that gates tool calls — or you are about to, because your team is adopting a coding agent and someone asked "how do we stop it doing something stupid?" It matters most if the answer you gave was "we have a hook for that."

**How it affects you.** Two failure directions, and they are not symmetrical. The over-firing direction is noisy but safe: your `Bash(cat *)` hook fires on a command that merely mentions `cat` inside `$()`, you get a spurious prompt, you are annoyed. The under-firing direction is silent and unsafe: a command shaped in a way the matcher can't parse sails through and *nothing is logged as skipped*. You will notice the first within a day. You may never notice the second.

**What to do about it.**
1. **Move policy out of hooks.** Anything you would be upset to have bypassed goes in `permissions.deny`, which is the enforcement path. Hooks are for workflow — formatting, logging, adding context, nudging.
2. **Anchor every regex matcher.** If your matcher contains any character outside `[A-Za-z0-9_-, |,]`, it is an unanchored regex and it matches substrings. `^mcp__github__.*$` is a rule; `mcp__github` is a suggestion.
3. **Test your matchers against a command corpus** before you trust them — the code below does this, and finding one surprise in your own rules takes about a minute.
4. **Upgrade to 2.1.243 or later** if you use `if` conditions at all, then re-check them: the `$()` over-firing fix changes which commands your existing rules match.

## What It Is

A Claude Code hook is a handler — a shell command, an HTTP endpoint, an MCP tool, a prompt, or a subagent — attached to a lifecycle event. The events that matter here fire per tool call: `PreToolUse`, `PostToolUse`, `PermissionRequest`, `PermissionDenied`. The handler receives a JSON object on stdin carrying `tool_name`, `tool_input`, `session_id`, `cwd` and `permission_mode`, and answers with an exit code, JSON on stdout, or both.

Whether a handler runs at all is decided by **three** filters in sequence, and this is the part worth internalising because each filter has different semantics:

1. **`matcher`** — filters on the *tool name* (or, for non-tool events, the event reason). Exact-match or unanchored regex depending on the characters used.
2. **`if`** — filters on the *tool input*, written in permission-rule syntax like `Bash(git *)` or `Edit(*.ts)`. Only evaluated on tool events. Best-effort.
3. **The handler's own logic** — the script actually reading `tool_input.command` and deciding.

Only the third of those is a program you control. The first two are pattern matching over strings, and both have surprises baked in.

## Why It Matters

The gap between "this looks like a firewall rule" and "this is best-effort text matching" is where a whole class of false confidence lives. It is not a flaw in the design — the documentation is unusually direct about it, and fail-open is the *correct* default for a workflow hook, because a hook that fail-closed on an unparseable command would wedge your agent constantly. The mistake is the reader's, and it is an easy one: the syntax borrows from the permission system, the file is the same file, and the mental model comes along for free.

What makes this worth thirty minutes rather than a footnote is that hooks are becoming the standard way teams put policy around agents. Cursor shipped subscriptions and custom modes in August; Claude Code's 2.1.243 alone added `modelPicker`, `modelPricing` and managed-settings visibility. The governance surface is growing fast, which means more teams are writing rules, and more of those rules are being written by people who reasonably assume that a rule in a settings file is enforced. Knowing which of the three filters is a lock and which is a note is the difference between a policy and a decoration.

## Key Technical Details

**Background first.** A hook config nests three levels: an event name, a list of matcher groups, and inside each group a list of handlers. The `matcher` sits on the group; the `if` sits on the individual handler. "Permission-rule syntax" means the `Tool(argument-pattern)` form that the `permissions` settings also use — the same spelling in both places, which is exactly why the two get conflated.

- **The matcher's mode switch is invisible.** If the string contains only `[A-Za-z0-9_-, |,]` it is an exact match, or a `|`/`,`-separated list of exact matches. Any other character promotes the whole string to an unanchored `RegExp.test()`. So `Edit|Write` is a two-item list, not an alternation regex — same result here, different mechanism, and the difference bites the moment you add a `.` or `*`.
- **Unanchored means substring.** A regex matcher without `^` and `$` matches anywhere in the tool name. The docs call this out and give the fix: `^mcp__brave-search$`.
- **The classification has changed across versions.** Hyphen is in the exact-match set as of 2.1.195, so `code-reviewer` is now an exact match; before that it was a regex and needed `^code-reviewer$`. A rule that was correct in one version can silently change mode in another.
- **`if` does real shell structure work.** Leading assignments are stripped (`FOO=bar git push` matches `Bash(git *)`). Chains are split and each subcommand checked (`npm test && git push` matches). Command substitutions are descended into, both `$()` and backticks — which is why `echo $(rm -rf /)` matches `Bash(rm *)` and `echo $(date)` does not.
- **`if` fails open.** "Can't parse complex Bash → hook runs anyway." The handler is invoked when the matcher is unsure. For a *blocking* hook that is a safe default; for a hook that only acts on some commands it means your script must re-check the input itself.
- **2.1.243 fixed the `$()` descent over-firing.** Conditions like `Bash(cat *)` were firing on unrelated commands that merely contained a `$()`. The descent is intentional; its scoping was wrong.
- **Exit code 2 blocks; JSON is richer.** On `PreToolUse`, exit 2 blocks the call outright. Returning `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}` blocks it *with a reason the model sees*, and `permissionDecision` also accepts `allow` and `escalate`. `PreToolUse` uniquely also honours `updatedInput`, letting a hook rewrite a command rather than reject it.
- **A timeout is not a block.** Default 600s for command hooks; on timeout the hook is cancelled, no decision is rendered, and the action proceeds. Another fail-open path.

## Implementing It

**The change.** Two audiences here, and they need opposite things. If you are **writing hooks**, the job is to stop guessing what your matchers match. If you are **relying on hooks for policy**, the job is to move that policy somewhere that enforces it.

*Hook author — make the matcher mode explicit.* The classification rule is small enough to implement, which means it is small enough to test:

```python
import re

EXACT_ONLY = re.compile(r"^[A-Za-z0-9_\-, |,]+$")

def matcher_mode(matcher: str) -> str:
    """Exact-match or unanchored regex? The characters decide, not the intent."""
    if matcher in ("", "*"):
        return "match-all"
    return "exact-list" if EXACT_ONLY.match(matcher) else "regex-unanchored"

def matches_tool(matcher: str, tool_name: str) -> bool:
    mode = matcher_mode(matcher)
    if mode == "match-all":
        return True
    if mode == "exact-list":
        return tool_name in [p.strip() for p in re.split(r"[|,]", matcher) if p.strip()]
    return re.search(matcher, tool_name) is not None      # unanchored, on purpose
```

Run your real matchers through it. `matcher_mode("Edit|Write")` returns `exact-list`; `matcher_mode("mcp__github__.*")` returns `regex-unanchored`, and `matches_tool("mcp__github__.*", "internal__mcp__github__admin")` returns `True`, which is probably not what the author meant.

*Hook author — write the handler defensively, because `if` fails open.* Never assume the `if` condition already filtered for you:

```bash
#!/bin/bash
# .claude/hooks/guard.sh — invoked with "if": "Bash(rm *)"
CMD=$(jq -r '.tool_input.command')

# The `if` is best-effort and fail-open, so re-check here. This is the only
# layer that is a program rather than a pattern.
if [[ "$CMD" =~ (^|[[:space:];&|])rm([[:space:]]|$) ]]; then
  jq -n --arg c "$CMD" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: ("Blocked by guard.sh: " + $c)
    }
  }'
  exit 0
fi
exit 0    # no decision — normal permission flow applies
```

*Policy owner — move it to the permission system.* This is the layer the docs point at for "hard policy enforcement." Same spelling, different guarantees:

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push --force*)",
      "Write(.env)",
      "Read(./secrets/**)"
    ]
  },
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "if": "Bash(rm *)",
        "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/guard.sh",
        "args": []
      }]
    }]
  }
}
```

The `deny` list is the lock. The hook is the note — keep it for the logging, the reason string, and the nudge, but stop treating it as the thing standing between your agent and your filesystem.

*Anchor anything that became a regex.* One character decides this, so make the decision visible:

```json
{ "matcher": "^mcp__github__.*$" }
```

**How you know it worked.** Three checks, in increasing order of effort:

1. **Count the surprises.** Run `code_example.py` — it takes a list of matchers and a corpus of tool names and commands and prints every pair where the match result differs from what a reasonable person would predict. On the shipped corpus it finds **4** such pairs. On your own rules, anything above zero is a rule to rewrite.
2. **Watch a hook actually fire.** Add `"statusMessage": "guard checked"` to the handler and run a command you expect it to catch and one you expect it to ignore. If the message appears on both, your `if` is broader than you think; if it appears on neither, your `matcher` never matched and the `if` was never consulted.
3. **Prove the deny rule bites.** Ask the agent to run a command your `permissions.deny` list covers. You should see a denial that you *cannot* approve interactively — that is the observable difference between deny and a hook. If you can click through it, it was never policy.

**When not to.** Do not move everything into `permissions.deny`. A deny rule is absolute and unappealable, and an over-broad one makes the agent useless in ways that are annoying to debug — `Bash(rm *)` in `deny` also kills `rm` inside a build script the agent legitimately needs to run. The split that works: **deny for things that would be bad if they happened once** (force-push to main, writing `.env`, touching production config), **hooks for things you want to know about or shape** (formatting after edits, logging every `Bash`, adding context on session start).

And do not write a hook to enforce something a file permission or a CI check already enforces. The strongest guarantee available is the one the agent cannot talk its way past, and a read-only mount beats every pattern in this article.

## How It Connects to What You Know

You have seen every piece of this before outside AI. The matcher's silent mode switch is the same class of bug as a config value that is a string until it looks like a number. The unanchored-regex default is `grep` without `-x`, and it has been catching people out for fifty years. The fail-open `if` is a WAF in detection-only mode. And "use the permission system for hard policy enforcement" is the same advice as "validate on the server" — the convenient layer near the user is a UX affordance, and the boring layer underneath is the control.

Inside this site: the [blast-radius gates](#2026-07-17) session argued for deterministic checks an agent cannot talk past, and this is the mechanical detail of where those checks must live to actually be deterministic. The [tool schema](#2026-07-05) session covers the other half of the same surface — what the agent is allowed to *see* versus what it is allowed to *do*.

## Try It Yourself

`code_example.py` implements both matching layers as documented — the character-set mode switch for `matcher`, and the Bash structural walk for `if` (assignment stripping, `&&`/`;`/`|` chain splitting, and descent into `$()` and backticks). It then runs a corpus of real matchers against a corpus of real commands and prints a table of every match, flagging the ones whose result contradicts naive intuition. Change `MATCHERS` at the top to your own rules from `settings.json` and re-run it. Pure stdlib.

## Glossary

- **Hook** — a handler (shell command, HTTP endpoint, MCP tool, prompt, or subagent) that Claude Code runs at a lifecycle point, such as before a tool call. It can allow, deny, or modify the call.
- **`PreToolUse`** — the hook event that fires before a tool runs. The only common event that can both block a call and rewrite its input.
- **`matcher`** — the first filter, on the tool's *name*. Exact-match or unanchored regex depending on which characters the string contains.
- **`if`** — the second filter, on the tool's *input*, written in permission-rule syntax. Tool events only, and explicitly best-effort.
- **Permission-rule syntax** — the `Tool(argument-pattern)` spelling, e.g. `Bash(git *)` or `Edit(*.ts)`. Used by both `if` conditions and `permissions` rules, which is the root of the confusion this article is about.
- **`permissions.deny`** — the settings list that actually enforces. A denied call cannot be interactively approved, which is the observable difference from a hook.
- **Unanchored regex** — a pattern without `^` and `$`, so it matches anywhere inside the string. `mcp__github` matches `internal__mcp__github__admin`.
- **Command substitution** — `$(...)` or backticks, which run a command and paste its output into another command. The `if` matcher deliberately looks inside these.
- **Fail-open** — when a check cannot reach a verdict, the action is allowed. The `if` condition and hook timeouts both fail open, which is right for workflow and wrong for policy.
- **Exit code 2** — the hook exit code that blocks the action outright, using stderr as the reason. Any other non-zero code is non-blocking.
- **`permissionDecision`** — the JSON field a hook returns to decide a call: `allow`, `deny`, or `escalate`. Richer than exit codes because the reason reaches the model.
- **`updatedInput`** — a `PreToolUse`-only JSON field that rewrites the tool's input instead of rejecting it, e.g. replacing a command with a safer one.
