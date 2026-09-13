# Further Reading: Why a Prompt Cache Miss Costs More Than No Cache at All

## Articles

### 1. [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
**Source**: OpenAI API documentation | **Date**: current | **Read time**: ~20 min
> The primary source, and the two numbers to find are the ones that decide everything: a cache
> read is 0.1x the uncached input rate and a write is 1.25x. Read the invalidation list next —
> `model`, `tools`, `parallel_tool_calls`, `text.format`, `reasoning.effort`, `text.verbosity` and
> `context_management` all break reuse, because the requirement is that the entire *rendered*
> prefix matches, not just the prompt text.

### 2. [Prompt cache diagnostics](https://developers.openai.com/api/docs/guides/prompt-caching/diagnostics)
**Source**: OpenAI API documentation | **Date**: current | **Read time**: ~10 min
> The feature this session is built on, generally available since 8 September 2026. Short enough
> to read in full, and the useful half is the table of nine miss reasons — eight of which name a
> configuration field rather than your prompt. Worth reading before you go hunting, because it
> tells you what the API can and cannot distinguish: `tools_changed` covers a reorder and an edit
> alike.

### 3. [API changelog](https://developers.openai.com/api/docs/changelog)
**Source**: OpenAI | **Date**: 8 September 2026 | **Read time**: ~5 min
> The dated entry, and worth the visit for the surrounding week rather than the one line. Reading
> a changelog as a list is how you notice that diagnostics arrived alongside key-expiry policies
> and an Agents API beta — the same release cadence you are choosing a caching strategy inside of.

### 4. [Why an Idle GPU Is the Wrong Place to Send a Request](https://theaicommit.com/#2026-09-09)
**Source**: The AI Commit | **Date**: 9 September 2026 | **Read time**: ~10 min
> The same mechanism from the other side of the API. That session is about prefix caching when you
> run the server and route the traffic; this one is about prefix caching when you are the caller
> and can only see the bill. Read them together and the shared fact is that a prefix is an asset
> with a location and an expiry, whichever end of the connection you are on.

### 5. [Anthropic prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
**Source**: Claude platform documentation | **Date**: current | **Read time**: ~20 min
> The contrast, and worth reading even if you never send a request there. The design is explicit
> rather than implicit — you mark cache breakpoints yourself — which makes the trade-off visible in
> a different place: you control what is cacheable and you own the mistake when it is wrong. Useful
> for deciding how much of your prefix discipline is portable.
