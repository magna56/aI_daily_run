"""One MCP endpoint answering two protocol eras.

The 2026-07-28 revision removed the initialize handshake and protocol-level
sessions. Every request now carries its own version in _meta. This builds the
router that decides, per request, which era it is talking to -- and shows why
a modern-only server locks old clients out permanently.

Pure standard library. No transport: the point is the dispatch, not the socket.

Run: python3 code_example.py

Set DUAL_ERA = False to watch the legacy clients stop being served.
"""

import json

PROTOCOL = "2026-07-28"
ALSO_SPEAK = ["2025-11-25"]          # what the legacy path still answers
DUAL_ERA = True

VERSION_KEY = "io.modelcontextprotocol/protocolVersion"
CLIENT_KEY = "io.modelcontextprotocol/clientInfo"
CAPS_KEY = "io.modelcontextprotocol/clientCapabilities"
UNSUPPORTED = -32022                 # UnsupportedProtocolVersionError

SESSIONS = {}                        # only the legacy path ever writes here
HANDLES = {}


def err(rid, code, message, data=None):
    e = {"code": code, "message": message}
    if data is not None:
        e["data"] = data
    return {"jsonrpc": "2.0", "id": rid, "error": e}


def ok(rid, result):
    result.setdefault("resultType", "complete")   # required from 2026-07-28
    return {"jsonrpc": "2.0", "id": rid, "result": result}


# --- modern: stateless, version on every request -------------------------
def modern(req):
    meta = req.get("_meta") or {}
    asked = meta.get(VERSION_KEY)
    if asked != PROTOCOL:
        # The `supported` list is the client's fall-forward path: it can pick a
        # version and retry. Legacy clients have no equivalent.
        return err(req.get("id"), UNSUPPORTED, "Unsupported protocol version",
                   {"supported": [PROTOCOL] + ALSO_SPEAK, "requested": asked})
    if req["method"] == "server/discover":
        return ok(req.get("id"), {
            "protocolVersions": [PROTOCOL] + ALSO_SPEAK,
            "capabilities": {"tools": {}, "extensions": {}},
            "serverInfo": {"name": "example", "version": "1.4.0"}})
    if req["method"] == "tools/call":
        # State goes in a server-minted handle, never on the connection, so any
        # replica can serve the next call.
        h = "h%d" % (len(HANDLES) + 1)
        HANDLES[h] = {"cursor": 0}
        return ok(req.get("id"), {"handle": h, "rows": 3,
                                  "client": (meta.get(CLIENT_KEY) or {}).get("name")})
    return err(req.get("id"), -32601, "Method not found")


# --- legacy: a handshake, then a session ---------------------------------
def legacy(req):
    if not DUAL_ERA:
        # A modern-only server SHOULD still name its versions here. The legacy
        # client cannot act on it, but a human reading the log can.
        return err(req.get("id"), -32601,
                   "initialize not supported; this server speaks %s"
                   % ", ".join([PROTOCOL] + ALSO_SPEAK))
    if req["method"] == "initialize":
        sid = "s%d" % (len(SESSIONS) + 1)
        SESSIONS[sid] = {"version": "2025-11-25"}
        return {"jsonrpc": "2.0", "id": req.get("id"),
                "result": {"protocolVersion": "2025-11-25", "sessionId": sid}}
    sid = req.get("sessionId")
    if sid not in SESSIONS:
        return err(req.get("id"), -32600, "No session; call initialize first")
    return {"jsonrpc": "2.0", "id": req.get("id"),
            "result": {"rows": 3, "sessionId": sid}}


def route(req):
    """The era is decided by how the request opens, with no flag and no config.

    `initialize` is the one method the modern era does not have, and a missing
    _meta is the other tell. Everything else is modern.
    """
    if req.get("method") == "initialize" or (req.get("_meta") is None):
        return legacy(req)
    return modern(req)


def main():
    print("server speaks %s (dual-era: %s)\n" % (PROTOCOL, DUAL_ERA))

    calls = [
        ("modern client, current version",
         {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
          "_meta": {VERSION_KEY: PROTOCOL, CLIENT_KEY: {"name": "new-cli"},
                    CAPS_KEY: {"tools": {}}}}),
        ("modern client, ancient version",
         {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
          "_meta": {VERSION_KEY: "1900-01-01"}}),
        ("modern client, discovery probe",
         {"jsonrpc": "2.0", "id": 3, "method": "server/discover",
          "_meta": {VERSION_KEY: PROTOCOL}}),
        ("legacy client, opens with initialize",
         {"jsonrpc": "2.0", "id": 4, "method": "initialize"}),
        ("legacy client, a call with no _meta",
         {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "sessionId": "s1"}),
    ]

    for label, req in calls:
        res = route(req)
        served = "result" in res
        detail = ""
        if not served:
            d = res["error"].get("data") or {}
            detail = "code %d" % res["error"]["code"]
            if "supported" in d:
                detail += ", can retry with %s" % d["supported"][0]
            else:
                detail += ", NO retry path"
        print("  %-38s %-8s %s" % (label, "served" if served else "REJECTED", detail))

    print("\n  sessions created: %d   handles minted: %d"
          % (len(SESSIONS), len(HANDLES)))
    rejected = [l for l, r in ((l, route(q)) for l, q in calls) if "error" in r]
    if DUAL_ERA:
        print("\n  Every era is served. The one rejection is a version the server does")
        print("  not speak, and that client can retry: it was handed a `supported`")
        print("  list. Set DUAL_ERA = False to see the asymmetry this guards against.")
    else:
        print("\n  %d of %d calls rejected, and they are not equivalent:" % (len(rejected), len(calls)))
        print("    the modern client got a `supported` list and can retry;")
        print("    the legacy ones got an error they have NO code path for.")
        print("\n  There is no fall-forward in that direction. A modern-only server")
        print("  locks those callers out until a human edits their config, which is")
        print("  why the specification's compatibility matrix marks that cell as a")
        print("  failure rather than a downgrade.")


if __name__ == "__main__":
    main()
