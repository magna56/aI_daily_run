# Stateless MCP (MCP 2.0): One Request, No Sessions, Trivial Horizontal Scaling

**Category**: Building Agents & MCP
**Tags**: mcp, agents, production
**Date**: 2026-08-05
**Time to read**: ~10 minutes

## What It Is

The July 28, 2026 Model Context Protocol spec (`MCP-Protocol-Version: 2026-07-28`) introduced
a **stateless transport** — described by Simon Willison as "the most significant change to the
MCP spec since it first launched." The old Streamable HTTP transport was implicitly *stateful*:
a client first POSTed an `initialize` request, the server minted an `Mcp-Session-Id`, and every
subsequent `tools/call` had to carry that session ID back. The server had to remember every live
session, and — critically — every request for a given session had to be routed back to the
*same backend process* that created it.

Stateless MCP collapses this to **a single self-contained HTTP request**. There is no
initialize handshake and no session ID. The routing information that used to live in the session
moves into request headers (`Mcp-Method: tools/call`, `Mcp-Name: <tool>`) and the client
identity/context that used to be established at init time moves into a `_meta` field inside the
request body's `params` (under the key `io.modelcontextprotocol/clientInfo`). One POST in, one
JSON-RPC result out.

Concretely, calling a tool is now just: POST to the server URL, headers declaring protocol
version + method + tool name, body carrying the JSON-RPC `tools/call` payload with arguments.
No prior round-trip. `mcp-explorer` demonstrates this — `uvx mcp-explorer call <url> render_svg
-a source 'graph TD; A-->B'` lists or invokes a tool over a cold connection with zero session
setup — and `datasette-mcp` exposes a `/-/mcp` endpoint (list_databases / get_database_schema /
execute_sql) that any stateless client can hit repeatedly with no server-side bookkeeping.

## Why It Matters

The stateful model made MCP servers behave like classic sticky-session web apps: you needed a
session store, session expiry/GC, and a load balancer configured for session affinity. That is
exactly the architecture that *doesn't* scale cleanly — you can't just put N identical replicas
behind a round-robin LB, because request #2 might land on a replica that never saw the
`initialize` for that session.

Stateless MCP makes an MCP server a **pure function of its request**: any replica can serve any
request. That unlocks the entire boring-but-bulletproof serverless/horizontal-scale toolkit —
AWS Lambda / Cloud Functions, round-robin load balancing, aggressive autoscaling, edge
deployment, zero-downtime rolling restarts — none of which play nicely with server-held session
state. It also shrinks the implementation: no session table, no session lifecycle, no affinity
config. Willison shipped three separate MCP projects in a single week and credited the reduced
complexity: "so much cleaner from both a client- and server-side implementation perspective."

## Key Technical Details

- **One request, not two.** Old flow: `initialize` POST → get `Mcp-Session-Id` → `tools/call`
  POST with that ID. New flow: a single `tools/call` POST.
- **Routing moves to headers:** `MCP-Protocol-Version: 2026-07-28`, `Mcp-Method: tools/call`,
  `Mcp-Name: <tool-name>`. The header duplication of method/name lets proxies and gateways route
  and authorize without parsing the JSON-RPC body.
- **Context moves to `_meta`:** client info that was negotiated at init time now rides in
  `params._meta` under `io.modelcontextprotocol/clientInfo` on each call.
- **No `Mcp-Session-Id`.** The server keeps nothing between requests.
- **Transport is plain request/response.** No mandatory long-lived SSE stream just to hold a
  session open (SSE can still be used for streaming *results*, but it's no longer the backbone
  of session identity).
- **Reference tools:** `mcp-explorer` (stateless CLI client — list/call any HTTP MCP server),
  `datasette-mcp` (`/-/mcp` endpoint, read-only SQL), `llm-mcp-client` (surfaces remote MCP
  tools as local `llm` tools).
- **Security framing:** an explicit, enumerable tool surface is easier to audit and threat-model
  than handing an agent raw shell/`curl`.

## How It Connects to What You Know

You already run a large MCP fleet — internal code-hosting and ticketing servers, several
internal platform servers, and a personal knowledge-base server. Every one of those is a *tool schema over a transport*, and the
transport choice is exactly what changed here. The stateful→stateless shift is the same
architectural move as **REST's statelessness vs. sticky HTTP sessions**, or JWT-in-the-request
vs. server-side session cookies: push the context the server needs into the request itself so
any node can answer. It's dependency-shape identical to why REST scaled where session-heavy RPC
didn't.

It also composes with two things from your recent sessions: the *tool schema trap* (07-05) —
stateless transport doesn't change that the schema is still the moat, it just makes the plumbing
under the schema disposable — and *model cascades* (08-03), where a stateless tool endpoint is
trivially callable from any tier of a cascade without the cheap model and the frontier model
fighting over one session.

## Try It Yourself

`code_example.py` implements a minimal stateless MCP server **and** a stateful one as pure
Python (stdlib `http.server` + JSON-RPC by hand), then puts a 3-replica round-robin load
balancer in front of both. It fires a realistic client sequence (initialize + several tool
calls) at each and shows the stateful cluster throwing "unknown session" errors whenever a
follow-up request lands on the wrong replica, while the stateless cluster answers every request
from every replica. It prints a side-by-side success-rate + request-count comparison so you can
*see* why affinity-free horizontal scaling is the whole point.
