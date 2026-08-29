# Further Reading: How an Agent Calls a Tool That Takes Twenty Minutes

## Articles

### 1. [Tasks — MCP extension specification (revision 2026-07-28)](https://github.com/modelcontextprotocol/ext-tasks/blob/main/specification/2026-07-28/tasks.md)
**Source**: modelcontextprotocol/ext-tasks | **Date**: revision 2026-07-28 | **Read time**: ~20 min
> The normative text, and the one to keep open in a second tab while you implement. Every MUST in this article comes from here: the durability requirement before returning a handle, the `-32021` path for clients that did not opt in, the `failed` versus `completed`-with-`isError` split, and the security rules for task IDs. Read the "Task Update Requests" section twice if you are writing the client — the key-uniqueness guarantee is what makes deduplication safe.

### 2. [Tasks overview and implementation guide](https://modelcontextprotocol.io/extensions/tasks/overview)
**Source**: modelcontextprotocol.io | **Date**: current | **Read time**: ~8 min
> The gentler route in, with a sequence diagram and two step-by-step checklists — one for clients, one for servers — that map almost line for line onto `## Implementing It` above. Read this first if you have never touched the extension; it also states plainly why blocking is not a substitute, which is the argument you will need when someone on your team asks why the tool cannot just wait.

### 3. [Multi Round-Trip Requests](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)
**Source**: modelcontextprotocol.io | **Date**: revision 2026-07-28 | **Read time**: ~12 min
> The pattern `inputRequests` and `inputResponses` are borrowed from, with worked JSON for an elicitation and a sampling request. Worth reading even if you never ship tasks: it is how *all* server-initiated requests work now, the old server-initiated pattern is gone, and the `requestState` integrity rules (HMAC, principal binding, short TTL) are a security review waiting to happen if you skip them.

### 4. [The tasks schema, in TypeScript](https://github.com/modelcontextprotocol/ext-tasks/blob/main/schema/2026-07-28/schema.ts)
**Source**: modelcontextprotocol/ext-tasks | **Date**: revision 2026-07-28 | **Read time**: ~5 min
> Open this in an editor and paste the types straight into your client. It is the fastest way to see that `Task` is five status variants rather than one bag of optional fields — which is exactly the shape your `tasks/get` handler should have — and it settles arguments about whether `ttlMs` can be null (it can) or whether a `tasks/list` exists (it does not, deliberately).

### 5. [Agents in production](https://mlconcepts.viveksingh-heritage.workers.dev/)
**Source**: ML Concepts | **Date**: current | **Read time**: ~15 min
> The intermediate on-ramp, for readers who want the surrounding picture before the protocol detail: what an agent loop is, where tool calls sit inside it, and why long-running work is awkward there in the first place. Skip it if you already maintain an MCP server; start here if this session was your first encounter with tool calling.
