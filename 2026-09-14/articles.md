# Further Reading: How to Update an MCP Server Without Breaking Its Clients

## Articles

### 1. [Versioning and compatibility](https://modelcontextprotocol.io/specification/2026-07-28/basic/lifecycle)
**Source**: Model Context Protocol specification | **Date**: revision 2026-07-28 | **Read time**: ~20 min
> The page this session is built on, and the compatibility matrix near the end is the reason to
> read it rather than a summary. Seven client-server era combinations, two of them marked as
> failures, and one sentence that decides the whole design: legacy clients have no fall-forward
> mechanism. Everything else in the article follows from that asymmetry.

### 2. [Key changes in revision 2026-07-28](https://modelcontextprotocol.io/specification/latest/changelog)
**Source**: Model Context Protocol specification | **Date**: 28 July 2026 | **Read time**: ~25 min
> The full list, and worth reading in one pass because the individual entries understate the
> total. Sessions, the `initialize` handshake, `Mcp-Session-Id`, `ping`, `logging/setLevel` and SSE
> resumability all leave; `server/discover`, per-request `_meta` and a required `resultType`
> arrive. Read the Deprecated section too — Roots, Sampling and Logging are on a twelve-month
> clock, so anything you write against them now has a known expiry.

### 3. [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
**Source**: Model Context Protocol specification | **Date**: revision 2026-07-28 | **Read time**: ~25 min
> Where the abstract change becomes wire format. The `MCP-Protocol-Version` header, the server
> validation rules that turn a legacy request into a `400`, and the backward-compatibility section
> that tells a client how to detect a server's era from the body of that `400`. Read it before
> implementing the dual-era branch, because the HTTP detection differs from the stdio probe.

### 4. [The next generation of MCP](https://blog.cloudflare.com/mcp-v2/)
**Source**: Cloudflare | **Date**: 6 August 2026 | **Read time**: ~15 min
> The same change from the implementer's side, and useful for the motivation the specification
> states only briefly. The concrete version of "stateless" is here: an MCP server can now run as
> an ordinary HTTP workload on Workers, with no Durable Objects, because nothing needs a sticky
> session or an open stream. It also names the SDK releases that landed alongside the revision,
> which is what you will actually reach for. Read it if you want the reason rather than the rules.

### 5. [Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
**Source**: Model Context Protocol specification | **Date**: revision 2026-07-28 | **Read time**: ~20 min
> Where server-minted handles land in practice, since a tool argument is now the place
> per-connection state goes. Also carries a detail worth knowing after yesterday's session on
> prompt caching: servers should return tools in a deterministic order, because a reordered tool
> list breaks a client's prompt cache as surely as an edited one.
