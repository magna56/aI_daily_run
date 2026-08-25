# How MCP Dropped the Handshake: Server vs Client

**Category**: Building Agents & MCP
**Tags**: mcp, caching, production, latency
**Date**: 2026-08-24
**Level**: Building
**For**: Building agents
**Hook**: The protocol that connects AI agents to tools just removed the idea of a connection, which makes servers far easier to run and quietly moves the hard part into the client.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine a big office building. The old way: you check in once at the front desk, they hand you a badge number, and every desk inside recognises that number — but only in *that* building, and if the receptionist goes home for the day, your badge means nothing and you start over from the lobby. The new way: there is no front desk. You carry your own ID and say what you want at every desk you visit. You repeat yourself a little more, but any desk in any building can help you, and nobody going home can ruin your afternoon. The tool protocol that AI agents use just tore out its front desk.

## The Problem

For about eighteen months, running a remote MCP server meant fighting your own infrastructure. The protocol opened a session with an `initialize` handshake and handed back an `Mcp-Session-Id`, and that session lived in one process's memory — so an ordinary round-robin load balancer, which has no idea which container holds which session, would route your second request to the wrong pod and get back `400 Session Not Found`. Teams papered over it with sticky routing rules, a shared Redis session store, or a gateway doing deep packet inspection to find the session id, all of which fight autoscaling and none of which survive a pod restart. Every horizontal-scaling story for MCP started with an apology.

## For a Software Engineer

**This is session affinity, and you have already watched this movie.** It is the same problem web applications solved fifteen years ago when they moved from server-side sessions (`JSESSIONID` pointing at an in-memory map) to self-describing signed tokens. MCP just ran that exact migration. The state did not disappear; it moved from the server's memory into the request payload, which is the only place every replica can reach it.

**The cost is real and it is small.** Re-sending the preamble on every call takes one `tools/call` from 205 bytes to 391 bytes — 186 extra bytes, a 91% larger request. The handshake it replaces was 618 bytes, paid once. So byte-for-byte, statelessness *loses* on any connection that makes more than about three calls. That was never the trade being made: you are spending bytes to buy round-robin routing, scale-to-zero on serverless, and a pod restart that costs one retry instead of a lost conversation.

**The bill moved somewhere you are not looking.** Deleting sessions also deleted the free push channel. There used to be a standing GET stream on which the server could send `notifications/tools/list_changed`; without it, a client that does not cache has no way to know its tool list is stale except to ask again. In a 40-call session against an 18-tool server, a client that re-fetches `tools/list` before every call burns **383 KB instead of 34 KB** — and the `_meta` you were worried about is 7 KB of that. **The cost of ignoring one cache header is 48× the cost of the entire statelessness change.**

**Monday morning:** go find the sticky-session rule and the Redis instance in your MCP deployment, because they may now be deletable — and go check whether your client reads `ttlMs`.

## What This Means for You

**When this matters.** You run a remote MCP server behind a load balancer, on Cloud Run / Lambda / Fargate, or anywhere with more than one replica. Or you maintain an MCP client or gateway. Or you have ever seen `400 Session Not Found` in a log, configured session affinity to make an agent tool work, or wondered why your MCP server could not scale to zero.

**How it affects you.** Three things change. Server-side, a whole class of infrastructure disappears: no sticky rules, no shared session store, no gateway body-parsing, and a rolling deploy stops interrupting agents mid-task. Client-side, you inherit a cache you did not have before, and getting it wrong is an order-of-magnitude bandwidth and latency regression that no error message will tell you about. And your integration is on a clock: the legacy `initialize` era still interoperates, but `Roots`, `Sampling` and `Logging` are now deprecated with a 12-month minimum support window, Dynamic Client Registration is deprecated in favour of Client ID Metadata Documents, and `Last-Event-ID` stream resumption is simply gone.

**What to do about it.**
1. **Delete infrastructure, carefully.** Audit your MCP deployment for session affinity rules and Redis session stores. Once every client on the path speaks `2026-07-28`, they are dead weight. Until then they are still load-bearing — check your client versions before you remove anything.
2. **Verify your client honours `ttlMs`.** Log how often your client calls `tools/list` during one agent session. If that number is anywhere near your tool-call count, you have the 48× bug. It should be closer to one.
3. **Decide whether you need `subscriptions/listen` at all.** It is the opt-in replacement for the old push stream, and it *is* a long-lived connection — so adopting it reintroduces a sticky connection, just one that carries no protocol state and costs a re-listen if it drops. If your tool list is stable, a TTL is enough and you stay fully stateless.
4. **If you own a server, upgrade the SDK and reject mismatches.** TypeScript, Python, Go and C# are updated; Rust is in beta. Return `405` on `GET`/`DELETE`, ignore any `Mcp-Session-Id`, and validate the mirrored headers against the body — that check is a security requirement, not a nicety (see below).

## What It Is

The `2026-07-28` MCP specification is the largest revision since the protocol launched, and its centrepiece is that the core is now completely stateless. The `initialize`/`initialized` handshake and the `Mcp-Session-Id` header are removed outright. Every request carries its own protocol version, client identity and client capabilities inline, in `_meta` fields on `params`, so a request is fully self-describing and any server instance can answer it with no shared storage.

The Streamable HTTP transport additionally *mirrors* a few of those body fields into HTTP headers — `MCP-Protocol-Version`, `Mcp-Method`, and `Mcp-Name` — so that load balancers, gateways and observability tooling can route, meter and audit MCP traffic without parsing the JSON body. The body remains the source of truth; the headers are a projection of it.

Removing sessions forced three compensating changes. Server-initiated requests are gone, replaced by **Multi Round-Trip Requests**: instead of pushing a question down an open stream, the server returns an `InputRequiredResult` and the client re-issues the call with the answers attached. Long-lived change notifications became opt-in through a `subscriptions/listen` request whose response stream stays open. And list results gained `ttlMs` and `cacheScope`, modelled directly on HTTP `Cache-Control`, so clients know how long a `tools/list` answer is fresh and whether it is safe to share across users.

## Why It Matters

The reaction, fairly, has been split. Plenty of developers looked at a stateless protocol with method and resource names promoted into HTTP headers and asked whether MCP has simply rediscovered REST. That critique lands on the transport and misses what the standard is actually for: MCP's value was never that it held a connection open, it was the agreed shape of tool discovery, tool schemas, and consent — the part that lets any client talk to any server without a bespoke integration. Cloudflare's Matt Carey and others have pointed out that the protocol keeps affordances a plain API does not have, notably `x-mcp-header`, which lets a *server* declare that a specific tool parameter must be mirrored into an HTTP header so a gateway can route or rate-limit on a tenant or region it can read without opening the body.

The more interesting point is the one the spec makes by accident: statelessness is not free, it is *relocated*. The protocol handed itself an easier operational story and handed clients a cache-invalidation problem, which is the trade every distributed system makes when it moves state to the edge. Ecosystem adoption was unusually fast — infrastructure providers, SDK maintainers and cloud platforms shipped support and migration guidance within days — which means the client-side half of this trade is being implemented right now, at speed, by a lot of people who have read the "no more Redis" headline and not the caching section.

## Key Technical Details

**Background first.** MCP is JSON-RPC 2.0 messages carried over a transport. The two standard transports are stdio (for a local subprocess) and Streamable HTTP, where each message is one HTTP POST to a single endpoint and the reply is either a JSON object or a Server-Sent Events stream — SSE being a one-way "server keeps writing to an open response" channel. A *client* is the connector inside an app like Claude Code; a *server* exposes tools, resources and prompts. `tools/list` returns the full JSON schema of every tool a server offers, which is why it is by far the largest routine message in the protocol.

- **Every request is self-describing.** Three `_meta` fields ride on `params`: `io.modelcontextprotocol/protocolVersion`, `io.modelcontextprotocol/clientInfo` (name and version), and `io.modelcontextprotocol/clientCapabilities`. Capability negotiation is now per-request instead of once per connection. Measured on the spec's own `get_weather` example, this is 186 bytes on top of a 205-byte call.
- **Three headers are required, and mismatches are rejected.** `MCP-Protocol-Version` on every POST, `Mcp-Method` mirroring `method`, and `Mcp-Name` mirroring `params.name` or `params.uri` on `tools/call`, `resources/read` and `prompts/get`. If a header disagrees with the body, the server **must** return `400` with JSON-RPC error `-32020` (`HeaderMismatch`). That rule is a security control, not pedantry: without it a load balancer routing on the header and a server executing on the body are two components trusting different sources of truth, which is a request-smuggling shape.
- **The GET stream is gone; `subscriptions/listen` replaces it.** There is no standalone SSE endpoint and no `Last-Event-ID` resumption. A client that wants `notifications/tools/list_changed` or `notifications/resources/updated` POSTs a `subscriptions/listen` request with a notification filter and holds its response stream open. Request-scoped notifications like `notifications/progress` still flow on the response stream of the request they belong to, never on the listen stream.
- **Cacheable lists are what make the stateless design affordable.** `tools/list`, `prompts/list`, `resources/list` and `resources/read` now return `ttlMs` and `cacheScope`. Honouring a 5-minute TTL over a 12-minute session means 2 list fetches instead of 40 — 34 KB instead of 383 KB in the simulation. A 60-second TTL still costs 273% more than a 5-minute one.
- **MRTR turns server questions into client retries.** When a tool needs a user answer or an LLM completion mid-execution, the server returns an `InputRequiredResult` carrying `inputRequests` plus an encoded `requestState`. The client gathers the input and re-POSTs the original call with `inputResponses` and the echoed state. Because everything needed is in the payload, *any* replica can pick up the retry — which is the whole point.
- **Tool parameters can be promoted into headers.** A server marks a parameter with `x-mcp-header` in its `inputSchema`, and conforming clients must mirror that value into `Mcp-Param-{Name}` — so a gateway can route on, say, `Mcp-Param-Region: us-west1` without reading the query. Values that are not plain ASCII use a `=?base64?…?=` sentinel, and the server must decode before comparing to the body.
- **Deprecations run on a 12-month clock.** `Roots`, `Sampling` and `Logging` are deprecated with a 12-month minimum support window. Dynamic Client Registration is deprecated in favour of Client ID Metadata Documents. Authorization hardened to RFC 9207 (the authorization server must return `iss`; clients must validate it before redeeming a code), and `application_type` at registration fixes localhost redirects for CLI and desktop clients. Tasks moved out of the experimental core into the `io.modelcontextprotocol/tasks` extension.
- **Backward compatibility is by probing, not negotiation.** A modern server receiving legacy traffic should answer `405 Method Not Allowed` to `GET`/`DELETE`, ignore any `Mcp-Session-Id` without minting or echoing one, and ignore `Last-Event-ID`. A client detects the era by trying a modern request first and, on `400`, inspecting the body — a recognisable modern JSON-RPC error means retry differently, an unrecognisable one means fall back to `initialize`.

## How It Connects to What You Know

If you have ever migrated a web app off server-side sessions onto signed tokens, you have already made this exact trade — larger requests, no shared session store, any replica can serve anyone. The `ttlMs`/`cacheScope` pair is `Cache-Control` by another name, and the header/body mismatch rule is the same defence you apply at any proxy boundary where two components could disagree about what a request says.

Inside this site: the [agent loop](#learn/the-agent-loop) chapter is the loop this protocol feeds, and [tool schemas](#2026-07-05) is why `tools/list` is the biggest message on the wire — a fat schema catalog is exactly what you do not want to re-download 40 times. The [pluggy session](#2026-07-13) called MCP "the same dependency-inversion pattern across process boundaries", and this revision is that pattern getting an ordinary HTTP deployment story. And the [context budget session](#2026-08-22) is the sibling result: there, re-sending the conversation prefix every turn was the cost you had to cache your way out of; here it is re-sending the tool catalog.

## Try It Yourself

`code_example.py` builds the literal request bodies from the specification and measures them, so every byte count above is a real `len()` rather than an estimate. It then prices a 40-call agent session four ways — legacy sessions, stateless with no cache, stateless honouring `ttlMs`, and stateless plus `subscriptions/listen` — sweeps the TTL to show where the cost actually lives, and injects a pod restart six minutes in to show what the legacy protocol loses that the stateless one does not. Pure stdlib, no network.

## Glossary

- **MCP** (Model Context Protocol) — an open standard for how AI applications discover and call external tools and data, so any client can talk to any server without a custom integration.
- **JSON-RPC 2.0** — a tiny convention for encoding "call this method with these params" as JSON. MCP messages are JSON-RPC; the transport just carries them.
- **Stateless** — the server keeps nothing between requests. Everything a request needs is in that request, so any replica can answer it and losing one costs a retry, not a conversation.
- **Handshake** (`initialize`/`initialized`) — the removed opening exchange where client and server agreed on a protocol version and capabilities once, up front, for the life of a connection.
- **`Mcp-Session-Id`** — the removed header that named a server-side session. Because the session lived in one process's memory, this header is what forced sticky routing.
- **Session affinity / sticky sessions** — a load balancer rule pinning a client to the same backend instance every time. It buys correctness for stateful protocols and costs you even traffic distribution, easy autoscaling, and painless restarts.
- **Round-robin load balancer** — the ordinary kind, which sends each request to the next instance in turn and knows nothing about who a client is.
- **`_meta`** — the field on `params` where MCP now puts its own protocol metadata (version, client info, capabilities), namespaced under `io.modelcontextprotocol/`.
- **Streamable HTTP** — MCP's HTTP transport: one POST per message to a single endpoint, answered with either JSON or an SSE stream scoped to that request.
- **SSE** (Server-Sent Events) — a one-way channel where the server holds an HTTP response open and keeps writing events. MCP uses it for progress notifications and for `subscriptions/listen`.
- **`tools/list`** — the call returning every tool a server offers, with full JSON schemas. It is the largest routine message in the protocol, which is why caching it is what the cost hinges on.
- **`ttlMs` / `cacheScope`** — how many milliseconds a list result stays fresh, and whether it may be shared across users. Modelled on HTTP `Cache-Control`; honouring it is the difference between 34 KB and 383 KB in a 40-call session.
- **`subscriptions/listen`** — the opt-in request whose response stream stays open to deliver change notifications. It is the replacement for the deleted GET stream, and the one place a long-lived connection still appears.
- **MRTR** (Multi Round-Trip Requests) — the pattern replacing server-initiated requests: the server returns `InputRequiredResult` with `inputRequests` and state; the client re-sends the call with `inputResponses`. Any replica can serve the retry.
- **Elicitation** — a server asking the end user for extra information mid-tool-call. Now delivered through MRTR rather than a pushed request.
- **Sampling** — a server asking the client's model to generate something on its behalf. Deprecated in this revision, with 12 months of support.
- **Roots** — the deprecated mechanism by which a client told a server which filesystem or URI scopes it was allowed to work in.
- **DCR / CIMD** (Dynamic Client Registration / Client ID Metadata Documents) — two ways an OAuth client gets an identity. DCR registered on the fly and is now deprecated; CIMD instead publishes client metadata at a URL that serves as the client id.
- **`x-mcp-header`** — a server-declared annotation in a tool's `inputSchema` saying "mirror this parameter into an HTTP header", so gateways can route or rate-limit on it without parsing the body.
- **Scale to zero** — running no instances at all when idle and paying nothing. Impossible when a live session lives in an instance's memory; routine once the protocol is stateless.
