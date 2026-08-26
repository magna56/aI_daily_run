# How a Coding-Agent Hook Decides to Fire (And Why It Still Isn't a Gate)

**Category**: Coding Agents & Productivity
**Tags**: coding-agents, security, reliability
**Date**: 2026-08-25
**Level**: Building
**For**: Using tools
**Hook**: A hook runs only after two text checks say yes — one on the tool name, one on the command — and neither check is the permission system that can actually block the call.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine you hire a very fast assistant and pin a note above their desk: "check with me before you throw anything away." Before the note is even read, two other checks run. First: is this a throwing-away job at all, or a different job? Second: does the request's wording match the note? Those checks are cleverer than they look — they even peek inside "do whatever that other note says." They are still just checks. If the wording is too tangled to read, the assistant does the job anyway, and nobody rings a bell. A locked bin is a different thing from a note about the bin.

## The Problem

A coding-agent hook does not run the moment the model asks for a tool. Two filters decide whether the handler even starts: one on the **tool name** (`matcher`), then one on the **tool input** (`if`). Most people's first hook is a safety rule — stop `rm`, stop `git push --force`, stop writes to production config. The rule looks like `"if": "Bash(rm *)"`, it reads like a firewall rule, and it sits in the same settings file as permissions. So the two-step fire decision gets treated as a boundary.

It is not one, and the gap between "this looks like a firewall rule" and "this is best-effort text matching" is where a whole class of false confidence lives. That is not a flaw in the design — the documentation is unusually direct about it, and fail-open is the *correct* default for a workflow hook, because one that failed closed on an unparseable command would wedge your agent constantly. The mistake is the reader's, and it is an easy one: the syntax borrows from the permission system, the file is the same file, and the mental model comes along for free.

What it costs is asymmetric, which is what makes it worth thirty minutes rather than a footnote. A rule that fires too often costs you a prompt you did not need — annoying, and you notice it within a day. A rule that silently does not fire costs you the thing the rule existed to prevent, and **nothing is logged as skipped**, so the cost is paid before you find out the rule was decorative. Version 2.1.243 shipped a fix for the noisy direction — hook `if` conditions "firing on unrelated Bash commands when containing `$()`" — which is a good bug report and a better hint about what the decision actually is.

## How the Two Filters Read Your Rule

Start with the case that surprises people. `"if": "Bash(rm *)"` catches `rm -rf build`, as you would expect. It also catches `echo $(rm -rf /)`, which never runs `rm` at the top level. And it misses `find . -delete`, which deletes your files. All three are documented, and all three follow from what these filters are.

A hook is a handler — shell command, HTTP endpoint, MCP tool, prompt, or subagent — attached to a lifecycle event. `PreToolUse` is the one that matters here: it fires before a tool runs, reads JSON on stdin (`tool_name`, `tool_input`, `cwd`, `permission_mode`), and is the only common event that can both block a call and rewrite its input.

Whether it fires is three filters in sequence, and only the last is a program you control: **`matcher`** on the tool name, **`if`** on the tool input, then your handler. The first two are pattern matching over text.

### The Matcher's Invisible Mode Switch

If the string contains only `[A-Za-z0-9_-, |,]` it is an exact match, or a `|`/`,`-separated list of them. **One character outside that set promotes the whole string to an unanchored regex** — a pattern with no `^` or `$`, matching anywhere inside the tool name. `Edit|Write` is a two-item list; `^Notebook` is a regex; nothing in the syntax says which you wrote. `mcp__github` matches `internal__mcp__github__admin`. The fix is anchors: `^mcp__brave-search$`.

The set has also moved between versions — hyphen joined it in 2.1.195, so `code-reviewer` is now exact where it once needed anchors.

### What the `if` Condition Actually Parses

`if` uses **permission-rule syntax** — the `Tool(argument-pattern)` spelling that `permissions` settings also use, which is why the two get conflated. For Bash it does real structural work: leading assignments are stripped (`FOO=bar git push` matches `Bash(git *)`), chains are split (`npm test && git push` matches), and **command substitutions** (`$(...)` and backticks, which paste one command's output into another) are descended into — which is why `echo $(rm -rf /)` matches and `echo $(date)` does not.

What it never does is reason about effects. `find . -delete` is not spelled `rm`, so no `rm` rule sees it.

### Where Every Layer Fails Open

**Fail-open** means that when a check cannot decide, the action is allowed. Three layers here do it, and one does not:

- The `if` condition is documented as *best-effort*: when it cannot parse complex Bash, **the hook runs anyway**. Your handler must therefore re-check its own input.
- A **timeout is not a block**. Default 600s; on timeout the hook is cancelled, no decision is rendered, the action proceeds.
- 2.1.243 narrowed the `$()` descent, which had been firing `Bash(cat *)` on unrelated commands containing a substitution. The descent is intentional; its scoping was wrong.
- `permissions.deny` **refuses**, and a denied call cannot be interactively approved. That is the observable difference between a lock and a note.

Blocking has two spellings: **exit code 2** blocks outright with stderr as the reason, and a JSON `permissionDecision` of `deny` blocks *with a reason the model sees* — the form used in the handler below.

## For a Software Engineer

**You have shipped this bug.** A pattern language good enough to feel authoritative and not structured enough to be a parser is the same thing as the regex that validates email addresses, or the `grep ERROR` that also catches `ERROR_SUPPRESSED`. The `if` condition is a lexer wearing a parser's clothes, and the giveaway is the one in this article: it descends into `$()` correctly and misses `find . -delete` entirely, because it matches *text shapes*, not *effects*.

The second surprise is the one you would catch in code review anywhere else. A field whose behaviour flips between two modes based on which characters happen to be in the string is the same class of bug as a config value that is a string until it looks like a number — and it is unannounced in both cases.

**Monday morning:** open your `settings.json`, find every `matcher` and every `if`, and decide for each one whether you meant *workflow* or *policy*. The ones that meant policy belong in `permissions.deny`, not in a hook.

New to agent tooling? Start at AI basics → [How the Coding-Agent Harness Works](#learn/the-coding-agent-harness). Elsewhere on this site, [blast-radius gates](#2026-07-17) argues for deterministic checks an agent cannot talk past, and [the tool schema](#2026-07-05) covers the other half of this surface — what the agent is allowed to *see* versus what it is allowed to *do*.

## What This Means for You

**When this matters.** You have written a hook, a `permissions` rule, or a plugin that gates tool calls — or you are about to, because your team is adopting a coding agent and someone asked "how do we stop it doing something stupid?" It matters most if the answer you gave was "we have a hook for that."

**How it affects you.** Two failure directions, and they are not symmetrical. The over-firing direction is noisy but safe: your `Bash(cat *)` hook fires on a command that merely mentions `cat` inside `$()`, you get a spurious prompt, you are annoyed. The under-firing direction is silent and unsafe: a command shaped in a way the matcher can't parse sails through and *nothing is logged as skipped*. You will notice the first within a day. You may never notice the second.

**What to do about it.**
1. **Move policy out of hooks.** Anything you would be upset to have bypassed goes in `permissions.deny`, which is the enforcement path. Hooks are for workflow — formatting, logging, adding context, nudging.
2. **Anchor every regex matcher.** If your matcher contains any character outside `[A-Za-z0-9_-, |,]`, it is an unanchored regex and it matches substrings. `^mcp__github__.*$` is a rule; `mcp__github` is a suggestion.
3. **Test your matchers against a command corpus** before you trust them — the code below does this, and finding one surprise in your own rules takes about a minute.
4. **Upgrade to 2.1.243 or later** if you use `if` conditions at all, then re-check them: the `$()` over-firing fix changes which commands your existing rules match.

## Implementing It

**The change.** A hook fires only after `matcher` (tool name) and `if` (tool input) both pass. Two audiences then need opposite things. If you are **writing hooks**, the job is to stop guessing what those two steps match. If you are **relying on hooks for policy**, the job is to move that policy somewhere that enforces it.

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

Note what that `if [[ ... =~ ... ]]` is: another lexer. It re-checks because the `if` fails open, but it is a regex over text rather than a parse of the command, so it misses the same shapes for the same reason — `find . -delete` sails through it too. It is a better note, not a lock. That is what the next block is for.

The `deny` list is the lock. The hook is the note — keep it for the logging, the reason string, and the nudge, but stop treating it as the thing standing between your agent and your filesystem.

*Anchor anything that became a regex.* One character decides this, so make the decision visible:

```json
{ "matcher": "^mcp__github__.*$" }
```

**How you know it worked.** Three checks, in increasing order of effort:

1. **Count the surprises.** Run `code_example.py` — it takes a list of matchers and a corpus of tool names and commands and prints every pair where the match result differs from what a reasonable person would predict. On the shipped corpus it finds **4** such pairs. On your own rules, anything above zero is a rule to rewrite.
2. **Watch a hook actually fire.** Add `"statusMessage": "guard checked"` to the handler and run a command you expect it to catch and one you expect it to ignore. If the message appears on both, your `if` is broader than you think; if it appears on neither, your `matcher` never matched and the `if` was never consulted.
3. **Prove the deny rule bites.** Ask the agent to run a command your `permissions.deny` list covers. You should see a denial that you *cannot* approve interactively — that is the observable difference between deny and a hook. If you can click through it, it was never policy.

## When a Hook Is the Wrong Tool

Do not move everything into `permissions.deny`. A deny rule is absolute and unappealable, and an over-broad one makes the agent useless in ways that are annoying to debug — `Bash(rm *)` in `deny` also kills `rm` inside a build script the agent legitimately needs to run. The split that works: **deny for things that would be bad if they happened once** (force-push to main, writing `.env`, touching production config), **hooks for things you want to know about or shape** (formatting after edits, logging every `Bash`, adding context on session start).

And do not write a hook to enforce something a file permission or a CI check already enforces. The strongest guarantee available is the one the agent cannot talk its way past, and a read-only mount beats every pattern in this article.

Three questions before you write one. **Would you be upset if this were bypassed?** Then it is policy, and it belongs in `permissions.deny` where it is enforced, not in a hook where it is best-effort. **Can you state the failure you would see if it silently stopped firing?** If not, you will not notice when it does. **Is there a layer underneath that already enforces this** — a file permission, a read-only mount, a CI check? The strongest guarantee available is the one the agent cannot talk its way past, and that layer beats every pattern in this article.
