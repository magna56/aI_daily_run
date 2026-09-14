# How to Update an MCP Server Without Breaking Its Clients

**Category**: Building Agents & MCP
**Tags**: mcp, agents, production
**Date**: 2026-09-14
**Level**: Building
**For**: Building agents
**Hook**: The current MCP revision removed the opening handshake, so a server now reads the protocol version off every request. Old clients cannot learn that, and there is no mechanism for them to adapt, so a clean upgrade silently locks them out.
**Engineer's view**: You have moved an app from server-side sessions to a token on every request. The migration was the easy half. What hurt was the old clients still sending a session cookie, with no way to discover the new scheme and no code path that could have used it.
**TLDR**: MCP dropped its handshake and its sessions, and every request now carries its own version and capabilities. The upgrade is not symmetric: old clients cannot fall forward, so a server has to answer both eras.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine a shop that used to ask every customer at the door which language they speak, then
remembered it for the whole visit. The new shop asks nothing at the door — instead every
single request has the language written on it. That is faster and the shop needs no memory.
But customers who only know how to answer the door question now walk in, say nothing, and
get turned away. They have no way to learn the new habit.

## The Problem

You have done this migration without a model in sight. You moved an app off server-side
sessions so it could run on more than one box. Every request started carrying its own token
and the servers stopped remembering anything. That part worked.

What hurt was the clients. Old ones still sent a session cookie, got a 401, and had no code
path that could have done anything else. They could not discover the new scheme, because
discovering it was itself a feature of the new scheme.

The current MCP revision, `2026-07-28`, is that migration. The `initialize` handshake is
gone. So are protocol-level sessions and the `Mcp-Session-Id` header. Every request now
declares its own protocol version, client identity and capabilities in `_meta`, and the
server accepts or rejects each request on its own.

The upgrade looks symmetric and is not. The specification's own compatibility matrix says a
new-style client meeting an old server fails, and an old client meeting a new server also
fails — with the note that matters: **legacy clients have no fall-forward mechanism.**

**The fix is to answer both eras from one server**, and to make the failure legible when you
cannot.

## The Fix: Serve Both Eras, and Decide by How the Client Opens

The specification names the two sides. The **modern era** carries version, identity and
capabilities as per-request metadata. The **legacy era** establishes a session with an
`initialize` handshake. A server implementing both is **dual-era**. It is the only column of
the matrix that works with everything.

```figure
{ "kind": "bars",
  "title": "Which client and server combinations actually work",
  "bars": [
    { "label": "dual-era server", "v": 100, "d": "both", "s": "ok" },
    { "label": "modern-only server", "v": 50, "d": "modern only", "s": "bad" },
    { "label": "legacy-only server", "v": 50, "d": "legacy only", "s": "bad" }
  ],
  "note": "Share of client eras served. Only one of the three talks to everybody." }
```

### How does the server know which era it is talking to?

It reads how the request opens, and nothing else.

A request arriving with modern `_meta` is served statelessly. A request arriving as
`initialize` selects legacy semantics. That session is scoped to the process on stdio, or to
the connection on HTTP. One endpoint can serve both eras at once.

A client that wants certainty first can make the discovery call instead of guessing.

```figure
{ "kind": "route",
  "title": "One endpoint, two eras, decided by the first request",
  "source": "an incoming request",
  "parts": [
    { "t": "carries _meta version", "to": 0, "via": "modern", "s": "ok" },
    { "t": "is an initialize call", "to": 1, "via": "legacy", "s": "new" }
  ],
  "dests": [
    { "t": "served statelessly", "s": "ok" },
    { "t": "served with a session", "s": "new" }
  ],
  "note": "The era is a property of the server, so clients cache which one they found and stop probing." }
```

### What does a version mismatch look like?

An error that tells the client what to do, which is the part worth copying.

```json
{ "jsonrpc": "2.0", "id": 1,
  "error": { "code": -32022, "message": "Unsupported protocol version",
             "data": { "supported": ["2026-07-28", "2025-11-25"],
                       "requested": "1900-01-01" } } }
```

The `supported` list is what lets a modern client pick a version and retry. That is a
fall-forward path, and it exists precisely because the designers knew the other direction
had none.

## What This Means for You

**When this matters.** You maintain an MCP server other people's clients connect to, or a
client that talks to servers you do not control. If you own both ends and ship them
together, this is a one-line version bump and none of the rest applies.

**How it affects you.** It changes who absorbs the cost of your upgrade. A modern-only
server pushes the whole cost onto clients that cannot pay it — they have no mechanism to
adapt, so the failure is permanent until a human edits their configuration. Dual-era is
slightly more code on your side and the only choice that keeps that from happening.

It also gives you something concrete to do about the case you cannot fix. A modern-only
server should **name the versions it supports in the error it returns to `initialize`**, on
every transport. A legacy client cannot act on it, but a human reading the log can, and that
message may be the only diagnostic anyone ever sees.

**What to do about it.**

1. Find out which era your clients speak before changing anything. If they are all yours and
   all current, this is a version bump.
2. Keep the `initialize` path working and add the modern one beside it. The two are
   distinguishable from the first request, so no flag is needed.
3. Replace any per-session state with an explicit handle the client passes back as an
   ordinary tool argument. That is the migration the statelessness actually forces.
4. Put your supported versions in every rejection, including the one you send to a legacy
   `initialize` you have chosen not to serve.

## Implementing It

**The change.** Three places, and the third is the one people postpone.

*The request reader.* Version, identity and capabilities now arrive per request:

```python
PROTOCOL = "2026-07-28"
VERSION_KEY = "io.modelcontextprotocol/protocolVersion"
CLIENT_KEY = "io.modelcontextprotocol/clientInfo"
CAPS_KEY = "io.modelcontextprotocol/clientCapabilities"

def handle(req):
    meta = req.get("_meta") or {}
    asked = meta.get(VERSION_KEY)
    if asked is None:
        return legacy_path(req)            # no _meta at all: an old-era request
    if asked != PROTOCOL:
        return {"jsonrpc": "2.0", "id": req.get("id"), "error": {
            "code": -32022, "message": "Unsupported protocol version",
            "data": {"supported": [PROTOCOL, "2025-11-25"], "requested": asked}}}
    return dispatch(req, client=meta.get(CLIENT_KEY), caps=meta.get(CAPS_KEY))
```

On HTTP the same version arrives as the `MCP-Protocol-Version` header too. That lets a server
reject a bad request before it parses a body.

Notice what the first branch does. A request with no `_meta` at all is not an error here — it
is an old client, and sending it down the legacy path is the whole compatibility strategy in
one line.

*The dual-era switch.* One endpoint, decided by the shape of what arrived:

```python
def route(req):
    # `initialize` is the tell. It is the one method the modern era does not
    # have, so its presence is an unambiguous era signal — no flag, no config.
    if req.get("method") == "initialize":
        return legacy_initialize(req)      # keep sessions for these callers
    return handle(req)

def server_discover(_req):
    """Servers MUST implement this. Clients may probe it before anything else."""
    return {"protocolVersions": [PROTOCOL, "2025-11-25"],
            "capabilities": {"tools": {}, "extensions": {}},
            "serverInfo": {"name": "example", "version": "1.4.0"}}
```

*State becomes an argument.* This is the real work, and no compatibility shim covers it:

```python
# Before: the server remembered the cursor for the connection.
# After: the server mints a handle and the client hands it back like any
# other tool argument. Nothing is connection-scoped, so any replica can serve
# the next call — which is the point of dropping sessions.
def open_query(sql):
    handle = mint_handle({"sql": sql, "offset": 0})
    return {"resultType": "complete", "handle": handle, "rows": first_page(sql)}

def next_page(handle):
    state = load_handle(handle)            # explicit, server-minted, replica-agnostic
    return {"resultType": "complete", "rows": page(state), "handle": bump(handle)}
```

That token is a **server-minted handle**. The server creates it and the client returns it
untouched. Nothing is scoped to a connection, so any replica can serve the next call. That is
the whole reason sessions were dropped.

Note `resultType` too. Every result now carries it, and `"complete"` is the ordinary value. A
client reading an older server that omits the field must treat it as `"complete"`.

**How you know it worked.** Point an old client and a new client at the same endpoint and
confirm both get answers. That is the whole test, and it takes two runs. If you have kept
only the modern path, verify the second thing instead: that your rejection of `initialize`
names your supported versions in a form a person can read in a log.

The slower signal is error rates by client. A modern-only server does not fail loudly — old
clients simply stop appearing, so watch for a client that used to call and no longer does.

**When not to.** Skip the dual-era work if every client is yours and deploys with the server.
The compatibility surface is the only reason for it, and paying for a surface you do not have
is how a server accumulates code nobody can delete.

## When Supporting Both Eras Is the Wrong Choice

Dual-era is insurance, and insurance is wrong when there is nothing to insure.

The clearest case is a closed deployment. If the server and every client ship in the same
release, the legacy path is dead code from the day you merge it — and dead compatibility code
is the kind that survives longest, because nobody can prove it is unused.

It is also wrong when the statelessness is the point. The reason to drop sessions is that any
replica can serve any request; a legacy path that reintroduces session state on the same
process quietly gives that back, and you now scale to whatever your stickiest caller needs.
If you moved to stateless in order to scale, keeping a session path undoes the reason.

And the deprecations in this revision have a schedule. Roots, Sampling and Logging are
deprecated with a minimum twelve-month window, so a compatibility layer written today has a
known expiry — worth writing down next to the code, because the next reader will not know it.

Three questions before adding the second era:

- Do I actually have clients I do not ship?
- Does my legacy path reintroduce per-connection state I removed on purpose?
- When I drop it, how will I know no one is still using it?

## Glossary

- **Modern era** — protocol revision `2026-07-28` and later, where each request carries its
  own version, identity and capabilities in `_meta` and the server keeps nothing.
- **Legacy era** — `2025-11-25` and earlier, where an `initialize` handshake established a
  session that later requests relied on.
- **Dual-era** — one server implementing both, choosing per request by whether it arrived as
  an `initialize` call or with modern metadata.
- **Discovery call** — the `server/discover` RPC every modern server must implement. It
  returns supported versions, capabilities and identity, so a client can check before
  committing.
- **Fall-forward** — a client's ability to discover a newer protocol and retry against it.
  Modern clients have one, via the error's `supported` list; legacy clients have none.
- **Server-minted handle** — an opaque token the server returns and the client passes back as
  an ordinary argument, replacing state that used to live on the connection.
