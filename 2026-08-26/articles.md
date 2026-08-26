# Further Reading: How an AI Code Review Becomes Something CI Can Gate On

## Articles

### 1. [Code Review — Claude Code Docs](https://code.claude.com/docs/en/code-review)
**Source**: Anthropic docs | **Date**: current | **Read time**: ~12 min
> The primary source for this whole session — the severity table, the `REVIEW.md` customization options (nit caps, skip rules, the verification-bar pattern), the `bughunter-severity` machine-readable line and its exact `gh api` parse command, and the `ReportFindings` tool behavior all come from here. Read the "Review a diff locally" section first if you only use `/code-review` in a terminal; read "Customize reviews" first if you're the one deciding what "Important" means for your repo.

### 2. [More than just code review](https://simonwillison.net/2026/Aug/22/more-than-just-code-review/)
**Source**: Simon Willison | **Date**: 22 August 2026 | **Read time**: ~1 min
> The provocation this session is built on: "eyeballing every line of code has never been the most effective way to validate a change to a piece of software." It's a note, not an essay — three sentences — but it names the actual skill gap precisely: confidently instructing an agent, then confidently verifying the result, are two different capabilities and most teams have only built the first one.

### 3. [How Anthropic secures its AI-native software development lifecycle](https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle)
**Source**: Anthropic (Jason Clinton, Deputy CISO) | **Date**: 21 July 2026 | **Read time**: ~8 min
> The wider-context piece: automated review is one layer in a six-stage SDLC security model built for a codebase where roughly 80% of merged code has AI authorship. Read this after you've set up a `REVIEW.md` — it's the case for why a typed, gated review is table stakes rather than a nice-to-have once AI-authored code is the majority, not the exception.

### 4. [GitHub Actions — Claude Code Docs](https://code.claude.com/docs/en/github-actions)
**Source**: Anthropic docs | **Date**: current | **Read time**: ~10 min
> The hands-on piece: how to run Claude in your own CI instead of the managed Code Review service, if you want the verification step running on infrastructure you control. Read this if `Implementing It`'s `should_block_merge()` made you want to wire the whole thing into an Actions workflow rather than parse a check run from outside.
