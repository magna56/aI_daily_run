# Further Reading: How MCP Dropped the Handshake: Server vs Client

## Articles

### 1. [The 2026-07-28 Specification](https://blog.modelcontextprotocol.io/posts/2026-07-28/)
**Source**: Model Context Protocol Blog | **Date**: 28 July 2026 | **Read time**: ~9 min
> The primary source, and the one to read first. Announces the stateless protocol core, Multi Round-Trip Requests, header-based routing, cacheable list results, authorization hardening and the formal extensions framework, along with the deprecation clock for Roots, Sampling and Logging. Start here, then go to the spec pages for the exact field names.

### 2. [Specification: Streamable HTTP (2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
**Source**: modelcontextprotocol.io | **Date**: 28 July 2026 | **Read time**: ~15 min
> The normative detail behind every byte count in this session: the required `MCP-Protocol-Version` / `Mcp-Method` / `Mcp-Name` headers, the literal `tools/call` example with its `_meta` block, the `-32020 HeaderMismatch` rule and why it is a security control, `x-mcp-header` parameter mirroring with its Base64 sentinel encoding, and the backward-compatibility probing rules for pre-2026 clients.

### 3. [Scaling AI Agent Infrastructure with the MCP Stateless Updates](https://developers.googleblog.com/scaling-ai-agent-infrastructure-with-the-mcp-stateless-updates/)
**Source**: Google Developers Blog | **Date**: August 2026 | **Read time**: ~7 min
> The infrastructure argument, written by people running MCP on Cloud Run. Names the four concrete failure modes sessions caused — round-robin load balancers not knowing which container holds which session, sticky-affinity rules blocking autoscaling, pod restarts destroying live conversations, and Redis or gateway packet inspection as the expensive workaround — and what each one costs you once it is gone.

### 4. [MCP Goes Stateless, and Developers Ask Whether That Just Makes it an API Again](https://www.infoq.com/news/2026/08/mcp-stateless-gateway/)
**Source**: InfoQ | **Date**: August 2026 | **Read time**: ~5 min
> The counterweight, and worth reading precisely because it is skeptical. Covers the argument that a stateless protocol with method and resource names in HTTP headers has rediscovered REST, and Cloudflare's Matt Carey's response that `x-mcp-header` — a server declaring which tool parameters a gateway may route on — is an affordance a plain API does not have.

### 5. [The New MCP Roadmap](https://blog.modelcontextprotocol.io/posts/mcp-roadmap/)
**Source**: Model Context Protocol Blog | **Date**: 22 August 2026 | **Read time**: ~6 min
> Published two days ago, and the best signal for what to build against next. Priorities are agentic messaging primitives (moving Tasks from extension into the spec, plus subscriptions and server-initiated events via webhooks and channels "so clients aren't left polling"), HTTP-native transport unification including local servers over stdio, agent identity via DPoP and Workload Identity Federation, and SDK conformance testing. Note it carries no dates or delivery commitments — it is directional, and SEPs in these areas just get expedited review.

### 6. [Migrate MCP Servers to Stateless Architecture (2026-07-28)](https://aaif.io/blog/migrate-sessions-to-stateless-requests-with-mcp-2026-07-28)
**Source**: Agentic AI Foundation | **Date**: August 2026 | **Read time**: ~10 min
> The practical migration path if you maintain a server: what to do with existing session state, how to answer legacy traffic (`405` on GET/DELETE, ignore `Mcp-Session-Id`, ignore `Last-Event-ID`), and how to stage the change while older clients are still on the wire. Pair it with the same site's ecosystem-adoption post for which SDKs and platforms had shipped support.
