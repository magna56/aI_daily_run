# How to Turn AI Code Review Comments Into a CI Gate

**Category**: AI Engineering Practices
**Tags**: coding-agents, reliability, observability, production
**Date**: 2026-08-26
**Level**: Building
**For**: Using tools
**Hook**: The same AI code review can come back as a paragraph you have to read or a typed, severity-ranked list a script can act on — which one you get depends only on who asked, not on what it found.
**Time to read**: ~11 minutes

## Explain Like I'm 5

Imagine you ask two different friends to check your homework. One of them just talks at you: "yeah looks mostly fine, oh and question 4 is wrong." You have to listen carefully and remember it. The other friend hands you a checklist: question, what's wrong, how bad it is, a box to tick when you fix it. Same homework, same friend even — they just answer differently depending on whether you asked out loud or handed them a form. The checklist is the one your teacher can actually grade against. The talking is the one only you can use.

## The Problem

A team turns an AI reviewer loose on every pull request and gets back paragraphs: "this looks fine, though the token refresh at line 142 might race with logout." Someone has to read that, decide if it's real, decide if it's serious, and decide whether to block the merge — every time, by hand. Reading review comments does not scale past the first few weeks, and a prose reply cannot be wired into a merge gate without someone writing a fragile regex against sentences an LLM is free to phrase differently next time.

The fix teams reach for first is usually wrong: skip the reading, treat the review as decoration, and merge anyway. That is not a compromise, it is turning the reviewer off. Simon Willison, writing about coding agents generally, names the real skill gap directly: "the key skill required to make productive use of coding agents is being able to confidently instruct them on how to make changes and then confidently verify that those changes have been applied in the correct way... eyeballing every line of code has never been the most effective way to validate a change." He does not say what the other way is. Claude Code's own review pipeline is one concrete answer, and it is a genuinely different mechanism from "read what it said" — not a nicer paragraph, a different output shape entirely.

## How the Same Review Becomes Two Different Things

Run `/code-review` in a terminal and Claude reports findings as text in its reply, the same as any other answer. Run the identical review from a host application that asks for a findings list instead — the desktop app, or any tool built against Claude Code's Agent SDK the way this reader's own review tooling is — and Claude reports through the **`ReportFindings`** tool instead of prose. Same review. Same model. The only variable is which shape the caller asked for.

### The Typed Shape

`ReportFindings` is a real tool in Claude Code's toolset, and its schema is the mechanism worth studying, not just the name. Each finding it returns carries: a file and line, a one-sentence `summary`, a `failure_scenario` (concrete inputs that trigger the bug, not a vague "could be an issue"), a `category` tag such as `correctness`, and — after a verification pass — a `verdict` of `CONFIRMED` or `PLAUSIBLE`. Findings come back **most-severe first**, and an **empty array is a valid report**: "nothing survived verification" is itself a result, not a missing one.

That last part is the detail people miss. A prose review that finds nothing says so in a sentence you still have to read to be sure. A typed report that finds nothing returns `[]` — a value your code can check with an `if`, not a paragraph you parse for the word "nothing."

### The Verification Step That Filters Guesses

Before any finding reaches either shape, "a verification step checks candidates against actual code behavior to filter out false positives" — the docs' own description of the step that turns a raw guess into a `CONFIRMED` or `PLAUSIBLE` verdict. A finding that claims a race condition has to point at the actual interleaving that causes it; a finding that survives that check outranks one that is merely plausible-sounding. This is why `REVIEW.md` lets a team demand a "verification bar" explicitly: *"behavior claims need a `file:line` citation in the source, not an inference from naming"* — you are tuning how hard the verification step has to work before it is allowed to report something as real.

### The Line a CI Script Actually Parses

The GitHub-integrated version of the same review writes a machine-readable summary into the check run's output text, in the exact shape `bughunter-severity: {"normal": 2, "nit": 1, "pre_existing": 0}`, and a workflow reads it with:

```bash
gh api repos/OWNER/REPO/check-runs/CHECK_RUN_ID \
  --jq '.output.text | split("bughunter-severity: ")[1] | split(" -->")[0] | fromjson'
```

That is the second half of "not prose": even the version that *does* post human-readable comments still embeds one machine-parseable line a script can act on without reading a single sentence.

## For a Software Engineer

This is the same lesson as an API that returns a typed error object instead of a message string: `{code: "RACE_CONDITION", severity: "important", file: "session.ts", line: 142}` is code your caller can branch on; "there might be a race condition around line 142" is a string your caller can only display. You already refuse to build a service around parsing another service's error prose — a code review from an agent is exactly that service, and until it returns a shape instead of a sentence, nothing downstream of it can be automated.

**The number worth feeling:** a check run with a non-zero `normal` (Important) count in that JSON line is a fact your CI can gate a merge on directly. A check run whose only signal is "I left some comments" is a fact only a human reading GitHub can act on — which is exactly the bottleneck this session opened with.

## What This Means for You

**When this matters:** you have wired an AI reviewer — Claude Code's, or your own agent built on a similar loop — into your workflow, and either people are still reading every comment by hand, or nobody trusts the review enough to gate anything on it.

**How it affects you:** you are one config file and one output convention away from turning a review your team reads into a review your CI enforces. The gap is not model quality — it is whether the review's output has a shape a machine can check.

**What to do about it:**
1. If you use Claude Code's managed review, add a `REVIEW.md` today — even five lines. An unconfigured review reports at the default calibration for production code generically; a `REVIEW.md` that says what "Important" means *for your repo* is the fastest way to stop nit-fatigue without losing real findings.
2. Wire your CI to the `bughunter-severity` line (`gh api ... check-runs ... --jq`) instead of relying on someone reading the PR. That line already exists on every review you are running; most teams never read it.
3. If you are building your own review agent, do not skip straight to the CI line — build the typed `Finding` shape first, the way `Implementing It` does below. The CI line is a derived summary of the typed shape, not a replacement for it.

## Implementing It

**The change.** Two roles, because this mechanism moves work between the agent producing findings and the CI consuming them — and most teams only build one side.

*Tooling engineer — commit to the shape first.* Before you write a verification pass, decide the fields a finding must carry — this is the actual decision, and it mirrors `ReportFindings`'s real contract:

```python
from dataclasses import dataclass

@dataclass
class Finding:
    file: str
    summary: str
    failure_scenario: str      # concrete inputs -> wrong output, never a guess
    category: str = "correctness"
    verdict: str | None = None      # CONFIRMED | PLAUSIBLE — set by verify(), never the finder
    outcome: str | None = None      # set on re-report: fixed | skipped | no_change_needed
```

`failure_scenario` is the field teams skip and the one that matters most: "could be an issue" is not a finding, it is a guess wearing a finding's shape. `verify()` in `code_example.py` is the full logic that turns a list of these into `CONFIRMED`/`PLAUSIBLE` candidates or drops one entirely — the point here is that nothing upstream of that pass is allowed to set `verdict` itself.

*CI engineer — the shape a script actually reads*, not a comment count. Whatever produces your findings, emit one line your workflow can `--jq` the way the real check run's docs example does:

```
bughunter-severity: {"normal": 1, "nit": 1, "pre_existing": 0} -->
```

`normal` is what `should_block_merge()` in `code_example.py` checks — a non-zero count there, on a `CONFIRMED` finding outside `style`, is the one fact your CI needs to gate a merge without anyone reading a comment.

The full runnable version — including `_text_supports`, the false-positive it correctly filters, and the report-fix-re-report loop that sets `outcome` — is in `code_example.py`.

**How you know it worked.** Run `code_example.py` and read the two representations of the *same* three-candidate review it produces: the prose block and the typed list. The prose block is one paragraph you have to parse by eye. `verify()` prints `2 of 3 survived verify(); 1 filtered out (no source support)` — the SQL-injection false positive is gone entirely, not demoted, while the real race condition comes back `[CONFIRMED]` (the source shows the exact unguarded await) and the input-validation bug comes back `[PLAUSIBLE]` (real, but the fixture's slice doesn't prove the exact trigger). The CI line prints `{"normal": 1, "nit": 1, "pre_existing": 0}` and `should_block_merge() -> True` — a bug that would matter to production is exactly the one that trips the gate. Then it re-runs against a "fixed" version of the source and reprints the same finding with `outcome=fixed` — proving the schema round-trips the same way `ReportFindings` does when Claude re-reports after applying a fix. If your own review tool's output cannot be reduced to a boolean `should_block_merge()`, you have not built this yet — you have built a nicer paragraph.

## When This Is the Wrong Tool

Do not build a typed-findings pipeline for a review nobody reads yet. If your team currently ignores AI review comments entirely, the problem is trust in the *findings*, not the *format* — fix the false-positive rate and the `REVIEW.md` calibration first, or a typed CI gate just automates blocking merges on noise nobody wanted blocked on in the first place.

And do not gate merges on a review whose verification step you have not checked. The severity table in Claude Code's own check run explicitly does not block via GitHub branch protection by default — "the check run always completes with a neutral conclusion so it never blocks merging" — and that default exists because a false `CONFIRMED` blocking every PR is worse than a missed bug. Turn on hard gating only after you have watched the verdict field long enough to trust its false-positive rate on *your* codebase, the same caution any new CI check deserves before it can fail a build.

Three questions before you wire any of this into a merge gate: **Do you know your false-positive rate**, measured, not assumed? **Can a human still override it** when the gate is wrong, or does "CONFIRMED" become unappealable the way a hook's `permissions.deny` is? **Have you defined what "Important" means for your repo** in writing — `REVIEW.md` or its equivalent — or are you gating on someone else's default calibration for a codebase that is not yours?
