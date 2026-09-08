# Further Reading: How Spotify Stops a Large File From Entering Claude's Context

## Articles

### 1. [Hooks reference](https://code.claude.com/docs/en/hooks)
**Source**: Claude Code documentation | **Date**: current | **Read time**: ~25 min
> The authority for everything in this session, and the section to jump to is PreToolUse. It has
> the exact JSON your hook receives on stdin, the `hookSpecificOutput` shape it prints back, and
> the rule that decides everything else: exit 2 blocks unconditionally and beats your JSON, while
> exit 0 hands the decision to `permissionDecision`. The `matcher` and `if` filters are documented
> here too, which is what stops a read blocker from firing on every tool you own.

### 2. [The shunt plugin](https://github.com/spotify/portal-ai-plugins/blob/main/plugins/shunt/README.md)
**Source**: Spotify on GitHub | **Date**: current | **Read time**: ~10 min
> The reference implementation, and short enough to read in full. Worth opening for two things the
> blog post skips: the environment variables that make the threshold configurable
> (`SHUNT_MIN_LINES`, default 350), and the fact that `check-bash-read` covers `cat`, `head`,
> `tail`, `less` and `more` while letting piped commands through. That second detail is the one
> people rediscover the hard way. Note the README reports 82-94%, not the blog's 90%.

### 3. [Portal by Spotify cut my Claude Code token usage by 90%](https://engineering.atspotify.com/2026/9/portal-by-spotify-cut-my-claude-code-token-usage-by-90)
**Source**: Spotify Engineering, by Dimitri Mazmanov | **Date**: 3 September 2026 | **Read time**: ~12 min
> Where this session started, and worth reading with the caveats in mind. The measurement is one
> Java monorepo across four scenarios with no published data, and the delegation half depends on
> Portal, Spotify's Backstage platform, which you do not have. What survives the trip is the hook
> layer and the framing — that the cheapest token is the one that never enters the context. Read
> it for the design decision, not for the number in the title.

### 4. [Subagents](https://code.claude.com/docs/en/sub-agents)
**Source**: Claude Code documentation | **Date**: current | **Read time**: ~15 min
> The realistic answer to "denied, but go where instead" if you do not have a platform to call.
> A subagent runs with its own context, so a summary comes back without the source material
> following it home — the same property Spotify gets from a Portal mode, using something already
> in the product. Read it before you build any delegation of your own.

### 5. [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
**Source**: Anthropic Engineering | **Date**: current | **Read time**: ~20 min
> The wider argument this technique sits inside: context is a budget with real limits, and what
> you leave out matters as much as what you put in. Useful for deciding your threshold, because it
> reframes the question from "how do I fit more in" to "what earns its place" — which is the same
> question a 350-line cutoff is answering, just with a number attached.
