"""
What stateless MCP actually costs on the wire — and where the cost really lives.

The 2026-07-28 MCP spec deleted the `initialize` handshake and the `Mcp-Session-Id`
header. Every request now carries its own protocol version, client identity and
capabilities in `_meta`, plus three mirrored HTTP headers. That sounds expensive:
you re-send the preamble on every single call.

This script measures it. The request bodies below are the *literal* examples from
the specification, so the per-request overhead is a real byte count, not a guess.
Then it prices a 40-call agent session four ways and shows that the `_meta` block
is noise — the bill is decided by whether your client honours `ttlMs` on
`tools/list`, because removing sessions also removed the free push channel that
used to tell you the tool list changed.

Run:  python3 code_example.py     (pure stdlib, no network, no API key)
"""

import json

PROTOCOL = "2026-07-28"

# ---------------------------------------------------------------- A. wire sizes
# Verbatim from modelcontextprotocol.io/specification/2026-07-28 (Streamable HTTP).
META = {
    "io.modelcontextprotocol/protocolVersion": PROTOCOL,
    "io.modelcontextprotocol/clientInfo": {"name": "ExampleClient", "version": "1.0.0"},
    "io.modelcontextprotocol/clientCapabilities": {},
}
CALL = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "get_weather", "arguments": {"location": "Seattle, WA"}}}

STATELESS_HEADERS = f"MCP-Protocol-Version: {PROTOCOL}\r\nMcp-Method: tools/call\r\nMcp-Name: get_weather\r\n"
LEGACY_HEADERS = "MCP-Protocol-Version: 2025-11-25\r\nMcp-Session-Id: 1868a90c-1c8f-4b1e-9d2f-8a3c0e5b7a41\r\n"
# The one-time handshake the old protocol paid before any real work could happen.
INITIALIZE = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {
    "protocolVersion": "2025-11-25", "clientInfo": {"name": "ExampleClient", "version": "1.0.0"},
    "capabilities": {"roots": {"listChanged": True}, "sampling": {}, "elicitation": {}}}}


def wire(obj, headers):
    return len(json.dumps(obj, separators=(",", ":")).encode()) + len(headers.encode())


bare = wire(CALL, "")
stateful_call = wire(CALL, LEGACY_HEADERS)
stateless_call = wire({**CALL, "params": {**CALL["params"], "_meta": META}}, STATELESS_HEADERS)
handshake = wire(INITIALIZE, LEGACY_HEADERS) * 2  # initialize + initialized round trip

print("=" * 74)
print("A. One tools/call on the wire")
print("=" * 74)
print(f"  bare JSON-RPC body, no transport metadata   {bare:6,} B")
print(f"  2025-11-25 (session id in a header)         {stateful_call:6,} B")
print(f"  2026-07-28 (self-describing _meta)          {stateless_call:6,} B"
      f"   +{stateless_call - stateful_call} B / +{(stateless_call / stateful_call - 1) * 100:.0f}%")
print(f"  one-time initialize handshake it replaces   {handshake:6,} B"
      f"   = {handshake / (stateless_call - stateful_call):.1f} calls' worth of _meta")

# ------------------------------------------------------- B. a real agent session
# 18 tools is a mid-sized MCP server (a GitHub or Spanner connector is bigger).
CATALOG = [(f"tool_{i:02d}", 260 + (i * 97) % 540) for i in range(18)]
LIST_BYTES = sum(n for _, n in CATALOG) + 64          # tools/list response payload
CALLS, MINUTES, TTL_MS = 40, 12, 300_000              # 40 calls over a 12-minute session
LIST_CHANGES = 1                                      # the server adds a tool once, mid-session


def session_bytes(mode):
    """Total client->server + server->client bytes for one agent session."""
    up = down = 0
    if mode == "legacy":
        up += handshake                               # pay the handshake once
        up += CALLS * stateful_call
        down += LIST_BYTES * (1 + LIST_CHANGES)       # GET SSE stream pushes list_changed
        listens = 0
    else:
        up += CALLS * stateless_call
        if mode == "no-cache":                        # ignores ttlMs, re-lists before each call
            fetches = CALLS
        elif mode == "ttl":                           # honours ttlMs: one fetch per 5-min window
            fetches = max(1, MINUTES * 60_000 // TTL_MS)
        else:                                         # "listen": fetch once, subscribe for changes
            fetches = 1 + LIST_CHANGES
        down += LIST_BYTES * fetches
        up += 96 * fetches                            # each tools/list POST carries _meta too
        listens = 1 if mode == "listen" else 0
        up += listens * 180                           # one subscriptions/listen request
    return up, down, listens


print()
print("=" * 74)
print(f"B. One agent session: {CALLS} tool calls, {MINUTES} min, {len(CATALOG)}-tool catalog"
      f" ({LIST_BYTES / 1024:.1f} KB per tools/list)")
print("=" * 74)
print(f"  {'client strategy':<34}{'total':>10}{'vs legacy':>12}  long-lived stream")
rows = {}
for mode, label in [("legacy", "2025-11-25 sessions + GET stream"),
                    ("no-cache", "stateless, ignores ttlMs"),
                    ("ttl", "stateless, honours ttlMs (5 min)"),
                    ("listen", "stateless + subscriptions/listen")]:
    up, down, listens = session_bytes(mode)
    rows[mode] = up + down
    delta = "baseline" if mode == "legacy" else f"{(up + down) / rows['legacy'] - 1:+.0%}"
    print(f"  {label:<34}{(up + down) / 1024:8.1f} KB{delta:>12}  {'yes' if listens else 'no':>17}")

print(f"\n  The _meta tax across all {CALLS} calls: "
      f"{CALLS * (stateless_call - stateful_call) / 1024:.1f} KB")
print(f"  The cost of ignoring ttlMs:          "
      f"{(rows['no-cache'] - rows['ttl']) / 1024:.1f} KB"
      f"  ({(rows['no-cache'] - rows['ttl']) / (CALLS * (stateless_call - stateful_call)):.0f}x larger)")

# --------------------------------------------------------------- C. the TTL knob
print()
print("=" * 74)
print("C. The only knob that matters: how long you cache tools/list")
print("=" * 74)
print(f"  {'ttlMs':>10}{'list fetches':>15}{'session total':>16}{'vs 5-min TTL':>15}")
base = rows["ttl"]
for ttl in (0, 30_000, 60_000, 300_000, 900_000):
    fetches = CALLS if ttl == 0 else max(1, MINUTES * 60_000 // ttl)
    total = CALLS * stateless_call + fetches * (LIST_BYTES + 96)
    label = "ignored" if ttl == 0 else f"{ttl:,}"
    print(f"  {label:>10}{fetches:>15}{total / 1024:>13.1f} KB{total / base - 1:>14.0%}")

# ------------------------------------------------- D. what statelessness buys you
print()
print("=" * 74)
print("D. A pod restart six minutes in (rolling deploy, autoscaler, spot reclaim)")
print("=" * 74)
for mode, label in [("legacy", "2025-11-25 sessions"), ("ttl", "2026-07-28 stateless")]:
    if mode == "legacy":
        # The session lived in that pod's memory. It is gone.
        cost = handshake + stateful_call                     # re-initialize, then retry the call
        print(f"  {label:<22} in-flight call -> HTTP 400 'Session Not Found'")
        print(f"  {'':<22} recovery: re-initialize + replay  ({cost:,} B, "
              f"and every prior tool result the server cached is lost)")
        print(f"  {'':<22} to avoid this you run sticky routing or a shared Redis")
    else:
        print(f"  {label:<22} in-flight call -> retried on any pod, "
              f"({stateless_call:,} B), nothing else to do")
        print(f"  {'':<22} round-robin load balancing, scale-to-zero, no Redis")

print()
print(f"  Byte-for-byte, statelessness LOSES: +{stateless_call - stateful_call} B on every call to "
      f"save {handshake:,} B once per connection,")
print(f"  so any connection past ~{handshake // (stateless_call - stateful_call)} calls is a net loss. "
      "Bytes were never the trade being made.")
print("  You are spending them to buy round-robin routing, scale-to-zero, and a restart that")
print("  costs one retry instead of a lost conversation.")
