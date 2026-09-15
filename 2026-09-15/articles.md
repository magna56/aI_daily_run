# Further Reading: How to Find Permission Bugs in Your Code With a Coding Agent

## Articles

### 1. [Datasette 1.0a39 and 0.65.4 security releases](https://datasette.io/blog/2026/september-security-releases)
**Source**: Simon Willison, Datasette blog | **Date**: 11 September 2026 | **Read time**: ~5 min
> The announcement this session is built on, and the place to start because it is short. It names
> the audit setup — Claude Fable 5.1, GPT-5.6 Sol and GPT-6 Astra over several rounds — and the
> two-person rule that made the findings trustworthy. Note what it withholds: some of the
> automated tests are being held back so people can upgrade first, which is the disclosure half of
> the practice and the reason this article describes a bug class rather than an exploit.

### 2. [Datasette 1.0a39 changelog](https://docs.datasette.io/en/latest/changelog.html)
**Source**: Datasette documentation | **Date**: 10 September 2026 | **Read time**: ~10 min
> The actual evidence for the argument, and worth reading as a list rather than as release notes.
> Case-insensitive table and view names, full-text search index tables checking permission on their
> source, `sqlite_stat1` through `sqlite_stat4` denied by default, `?_through=` requiring the
> intermediate table, foreign-key APIs respecting `view-table`. Five different fixes, one shape:
> the check was asked about the wrong target. The 0.65.4 entry backports the same set to stable.

### 3. [API1:2023 Broken Object Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
**Source**: OWASP API Security Top 10 | **Date**: 2023 edition | **Read time**: ~10 min
> The bug class under the name the rest of the industry uses, and the reason it sits at number one
> on that list. Useful for the framing this session leaves out: OWASP treats it as a per-object
> check problem, where this article treats it as a name-resolution problem. Both are true, and the
> resolution view is what makes it testable — you can enumerate a schema, but you cannot enumerate
> "every object" in the abstract.

### 4. [From Naptime to Big Sleep: Using Large Language Models To Catch Vulnerabilities In Real-World Code](https://projectzero.google/2024/10/from-naptime-to-big-sleep.html)
**Source**: Big Sleep team, Google Project Zero and DeepMind | **Date**: 1 November 2024 | **Read time**: ~20 min
> The same practice run by a dedicated team, and the strongest support for how to task the agent.
> They did not ask it to find bugs. They handed it a specific commit with its message and diff and
> asked for variant analysis of the current code, which is the narrow, enumerative framing this
> session argues for. Read their own caveat too: they call the work experimental and say a
> target-specific fuzzer may be at least as effective, which belongs in your expectations.

### 5. [Datasette 1.0a39 and 0.65.4 security releases](https://simonwillison.net/2026/Sep/11/datasette-security/)
**Source**: Simon Willison's weblog | **Date**: 11 September 2026 | **Read time**: ~3 min
> The shortest thing here and the one with the process detail worth copying verbatim. It quotes
> Alex Garcia on the split: one person wrote the automated test demonstrating an issue, the other
> implemented the fix, so two humans saw every issue on top of the agents. That division is what
> separates an audit from a list of claims, and it costs more than the scan does.
