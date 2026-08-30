# How a Coding Agent Picks the Model for Each Subagent

**Category**: Coding Agents & Productivity
**Tags**: cost, agents, observability
**Date**: 2026-08-30
**Level**: Start here
**For**: Using tools
**Hook**: One setting used to force every helper task onto a cheap model. It now loses to the agent files sitting in your repo, and nothing tells you.
**Time to read**: ~8 minutes

## Explain Like I'm 5

Imagine a kitchen with an expensive oven and a cheap one. The manager writes "use the cheap oven" on a whiteboard by the door. But every recipe card names an oven too, and so does the waiter's slip.

Nothing changes about the whiteboard. But one week the kitchen starts reading the recipe cards first — and the expensive oven runs all day.

## The Problem

Your coding agent hands work to helpers. A review, a repo-wide search, a long file summary — each is farmed out to a second agent that runs on its own, reports back, and disappears. You do not choose a model for each one; something else does.

Four places can name that model: the spawning call, a `model:` line in the helper's definition file, an environment variable, and your session's model. They disagree constantly, and only one wins.

Which one wins just changed. The environment variable used to beat everything — set it to the cheapest model and every helper obeyed. It is now a *default*, below the two things it used to override.

So if you exported it to cap spend and your repo has agent files naming a model, your cap stopped working. No warning, no log line, no error. The bill is the only signal, and it arrives a month late.

## How Model Resolution Works

A subagent is a second copy of the agent with its own context, tools and model. Four inputs can name it, checked in order until one answers.

### The chain that just inverted

| Order | Where the model comes from |
| --- | --- |
| 1 | The `model` parameter on the spawning call |
| 2 | `model:` in the helper's definition file |
| 3 | `CLAUDE_CODE_SUBAGENT_MODEL` |
| 4 | Your main session's model |

Release 2.1.251 moved the environment variable from position 1 to position 3: *"an agent definition's `model:` and an explicit per-spawn model now take precedence over it."* The reference page still documents the old order — believe `claude --version`.

### Enforcement sees less than resolution does

Resolution decides. Two mechanisms can *veto*, and neither sees the whole chain.

A permission rule can match a tool's input parameter: `Agent(model:opus)` in the `deny` list blocks a spawn asking for Opus. Three constraints matter more than the syntax. Only deny and ask rules can match a parameter. A parameter the model omits never matches, so `Agent(model:*)` misses every spawn naming no model. And the value is compared to the literal string sent, before normalization — so `opus` sails past `claude-opus-5`.

The other veto is the `PreModelSwitch` hook, which fires before the *session* changes model and can deny it. It never fires on a spawn.

| Layer naming a model | Deny rule | `PreModelSwitch` |
| --- | --- | --- |
| Per-spawn parameter | literal only | no |
| Definition file `model:` | **no** | no |
| `CLAUDE_CODE_SUBAGENT_MODEL` | no | no |
| Session model | no | yes |

Read the middle row twice: the layer just promoted above your environment variable is the one neither veto sees.

## For a Software Engineer

This is a configuration precedence bug, and you have shipped one. Same shape as a framework that reads `DATABASE_URL`, a config file and a CLI flag, then reorders them in a minor release: every value is still correct and production quietly connects somewhere else.

What makes this variety expensive is that the losing layer stays visible. Your `.zshrc` still exports the variable; `env | grep SUBAGENT` still prints it. Nothing looks different from the week it worked, which is why nobody goes looking.

And the cost is not marginal. Opus 5 is $5 per million input tokens and $25 per million output; Haiku 4.5 is $1 and $5 — a flat 5× per token. `code_example.py` prices a five-helper fan-out both ways: $1.19 under the old order, $4.55 under the new one, 3.8× for a change nobody made. Prompt caches are also scoped per model, so a fan-out that shared one namespace now pays cold reads across several.

## What This Means for You

**When this matters.** You set `CLAUDE_CODE_SUBAGENT_MODEL` to a cheap model to control spend, and your repo or a plugin has agent files with a `model:` line. If both are true, your cap is already off.

**How it affects you.** Those helpers now run on whatever their file asks for, at up to 5× the token rate, with cache reuse split across model namespaces. On the sample fleet in `code_example.py`, four of five changed model and the deny rules caught one. Nothing warned you when it started, and nothing confirms it if you fix it.

**What to do about it.** Grep your agent files for `model:` now and decide, per file, whether that line is load-bearing or a leftover. Most are leftovers; the fix is deleting the line. Add the deny rules and hook below for the files that must keep theirs.

## Implementing It

**The change.**

*Agent file author.* The `model:` line in a definition file is now the strongest thing in your repo short of an explicit spawn parameter. Leave it out unless the agent genuinely cannot do its job on a cheaper tier — omitting it means `inherit`, which follows the session:

```yaml
---
name: repo-search
description: Finds files matching a description
tools: Read, Glob, Grep
# model: opus        <- delete this; searching does not need it
effort: low          # cheaper still, and it survives the model change
---
```

Find the ones you have inherited without noticing:

```bash
grep -rn '^model:' .claude/agents ~/.claude/agents ~/.claude/plugins 2>/dev/null
```

*Operator.* Deny rules catch the per-spawn layer only, and they compare literal strings. Write the alias **and** the full IDs, because one rule matches one exact value:

```json
{
  "permissions": {
    "deny": [
      "Agent(model:opus)",
      "Agent(model:fable)",
      "Agent(model:claude-opus-5)",
      "Agent(model:claude-fable-5)"
    ]
  }
}
```

Confirm what your rules are compared against with `claude --verbose`, which prints the literal parameter values in each tool call. A rule naming `opus` while the caller sends `claude-opus-5` looks correct and matches nothing.

*Session guard.* `PreModelSwitch` covers the layer deny rules cannot — the session model itself. Deny by exit code 2, or by JSON on exit 0:

```json
{
  "hooks": {
    "PreModelSwitch": [
      { "matcher": ".*opus.*",
        "hooks": [{ "type": "command", "command": "~/.claude/guard-model.sh" }] }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
# guard-model.sh — refuse a switch up unless SPEND_OK is set
read -r payload
to=$(printf '%s' "$payload" | python3 -c 'import json,sys;print(json.load(sys.stdin)["to_model"])')
[ -n "$SPEND_OK" ] && exit 0
printf '{"hookSpecificOutput":{"permissionDecision":"deny",' 
printf '"permissionDecisionReason":"%s blocked; export SPEND_OK=1 to allow"}}' "$to"
```

The matcher is the canonical name derived from `to_model`, so `claude-opus-5-20250514` matches as `claude-opus-5`.

**How you know it worked.** Run a task that fans out, then open `/tasks` — as of 2.1.251 it records the model *and* effort level each subagent actually ran on. That is the only place the four-layer chain resolves into an observed fact rather than an intention. Every helper row should name the tier you expect; a single Opus row when you expected Haiku means one file still carries a `model:` line, and the row tells you which agent.

Then check `/cost`, which now prints a per-session prompt-cache line — hit ratio, misses, tokens re-cached, warm or cold. A fan-out that suddenly shows a low hit ratio is the model-scoped cache split showing up as money. If you script your status line, the same numbers arrive as a `prompt_cache` object.

## When a Model Deny Rule Is the Wrong Tool

A deny rule is a string comparison against one parameter, and it is bad at three jobs. It cannot express a budget — it blocks the tier forever, not after the ninth call. It cannot see the definition-file layer, so a repo that pins models in its agent files defeats it. And exact matching makes every new model ID a rule you have not written yet: the rule that covered your fleet in July fails open the day a new alias ships. That is the wrong direction for a cost control.

Where the tier genuinely matters — a reviewer that misses real bugs on a cheap model — pinning `model:` is correct. Keep it and name the reason in a comment.

Three questions before reaching for any of this:

1. Do you know which model your helpers ran on last week, or are you assuming? Open `/tasks` first.
2. Is the expensive tier buying a better answer or just a slower one? Effort is the cheaper lever, and it survives a precedence change.
3. If a teammate adds an agent file with `model: opus` tomorrow, which control notices? If none, what you need is code review, not configuration.
