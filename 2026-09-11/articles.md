# Further Reading: How an AI Audit Found Three Names for One Protected Table

## Articles

### 1. [Datasette 1.0a39 and 0.65.4 security releases](https://simonwillison.net/2026/Sep/11/datasette-security/)
**Source**: Simon Willison | **Date**: 11 September 2026 | **Read time**: ~5 min
> The account of how the audit was run, and short enough to read in full. The sentence worth
> copying is the review protocol — "one of us would create the automated tests highlighting the
> issue, then the other would implement the fix" — which is what separates this from a list of
> model output. Note also what it cost: two experienced maintainers, close to a week, on a
> codebase one of them wrote.

### 2. [Datasette changelog, 1.0a39](https://docs.datasette.io/en/latest/changelog.html)
**Source**: Datasette documentation | **Date**: 10 September 2026 | **Read time**: ~15 min
> The fixes themselves, and the primary source for every claim in this session. Read the
> permission entries as a group rather than individually: table and view names now matched the way
> SQLite matches them, full-text search index tables checking the table they draw from, and the
> statistics tables denied by default. Written out one after another, the shared cause is hard to
> miss.

### 3. [Datasette's permissions system](https://docs.datasette.io/en/latest/authentication.html)
**Source**: Datasette documentation | **Date**: current | **Read time**: ~25 min
> Worth reading before you conclude your own system is simpler than this. The model is
> resource-scoped — permissions apply to an instance, a database, a table — which is exactly the
> design that makes "what counts as this table" a load-bearing question. Any authorization layer
> keyed on resource names has the same exposure whether or not it has a plugin system.

### 4. [SQLite: full-text search](https://www.sqlite.org/fts5.html)
**Source**: SQLite documentation | **Date**: current | **Read time**: ~30 min
> Where the derived tables come from. The section on shadow tables is the relevant one: creating an
> FTS5 index creates several companion tables holding the indexed content, under names derived from
> yours. Read it to see that this is documented, expected behavior rather than an obscure corner —
> which is the point about aliases being invisible rather than hidden.

### 5. [Patterns for building cybersecurity evals](https://eugeneyan.com/writing/cybersecurity-evals/)
**Source**: Eugene Yan | **Date**: 21 June 2026 | **Read time**: ~19 min
> The systematic version of what this session does by hand. It lays out the pieces of a security
> eval — a sandboxed target, inputs that vary task difficulty, tools, and a grader — and the grader
> discussion is the useful part here, because a finding you cannot grade automatically is a finding
> you cannot trust at volume.
