#!/usr/bin/env python3
"""
Stateless MCP (2026-07-28) vs. Stateful MCP — why statelessness is the whole scaling story.

This is a pure-stdlib SIMULATION (no sockets, no network, no API keys). It models two MCP
server implementations and a round-robin load balancer sitting in front of a 3-replica cluster
of each, then replays a realistic client sequence:

    initialize  ->  tools/call render_svg  ->  tools/call render_svg  ->  tools/call list

- STATEFUL server:  `initialize` mints an Mcp-Session-Id stored ON THAT REPLICA. A later
  tools/call carrying that session ID only works if the load balancer happens to route it back
  to the SAME replica. Round-robin does not, so most follow-up calls fail with "unknown session".

- STATELESS server (MCP 2.0): every request is self-contained (method + name in headers,
  client info in params._meta). ANY replica answers ANY request. No session table. 100% success.

Run:
    python3 code_example.py

No dependencies. Just the standard library.
"""

from __future__ import annotations
import itertools
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# A "request" is just headers + a JSON-RPC-ish body, like a real HTTP MCP call.
# ---------------------------------------------------------------------------
@dataclass
class Request:
    headers: dict
    body: dict  # {"method": ..., "params": {...}, "id": ...}


@dataclass
class Response:
    ok: bool
    payload: object
    replica: str  # which replica served it (for illustration)


# A tiny "tool" the servers expose.
def render_svg(source: str) -> str:
    return f"<svg><!-- {len(source)} chars of diagram --></svg>"


TOOLS = {
    "render_svg": lambda args: render_svg(args.get("source", "")),
    "list": lambda args: ["render_svg", "list"],
}


# ---------------------------------------------------------------------------
# STATEFUL MCP server: holds session state per replica.
# ---------------------------------------------------------------------------
class StatefulServer:
    _session_seq = itertools.count(1)

    def __init__(self, name: str):
        self.name = name
        self.sessions: set[str] = set()  # server-side state -> the scaling problem

    def handle(self, req: Request) -> Response:
        method = req.body.get("method")

        if method == "initialize":
            sid = f"{self.name}-sess-{next(self._session_seq)}"
            self.sessions.add(sid)
            # Session ID handed back in a response header, exactly like real stateful MCP.
            return Response(True, {"Mcp-Session-Id": sid}, self.name)

        # Any tool call REQUIRES a valid session that THIS replica knows about.
        sid = req.headers.get("Mcp-Session-Id")
        if sid is None:
            return Response(False, "error: missing Mcp-Session-Id", self.name)
        if sid not in self.sessions:
            # Landed on the wrong replica — it never saw this session's initialize.
            return Response(False, f"error: unknown session {sid}", self.name)

        tool = req.body["params"]["name"]
        args = req.body["params"].get("arguments", {})
        return Response(True, TOOLS[tool](args), self.name)


# ---------------------------------------------------------------------------
# STATELESS MCP server (2026-07-28): pure function of the request.
# ---------------------------------------------------------------------------
class StatelessServer:
    def __init__(self, name: str):
        self.name = name  # no session table at all

    def handle(self, req: Request) -> Response:
        # Everything needed is IN the request: method + name in headers, client info in _meta.
        if req.headers.get("Mcp-Method") == "tools/call":
            tool = req.headers["Mcp-Name"]
            args = req.body["params"].get("arguments", {})
            return Response(True, TOOLS[tool](args), self.name)
        return Response(False, "error: unsupported method", self.name)


# ---------------------------------------------------------------------------
# Round-robin load balancer over a cluster of identical replicas.
# ---------------------------------------------------------------------------
@dataclass
class LoadBalancer:
    replicas: list
    _rr: itertools.cycle = field(init=False)

    def __post_init__(self):
        self._rr = itertools.cycle(self.replicas)

    def route(self, req: Request) -> Response:
        return next(self._rr).handle(req)


# ---------------------------------------------------------------------------
# Client sequences.
# ---------------------------------------------------------------------------
def run_stateful(lb: LoadBalancer):
    print("  1. initialize ..............", end=" ")
    r = lb.route(Request({"MCP-Protocol-Version": "2026-03-26"},
                         {"method": "initialize", "id": 1}))
    sid = r.payload.get("Mcp-Session-Id") if r.ok else None
    print(f"served by {r.replica}, got session {sid}")

    results = [r.ok]
    # Three follow-up tool calls, all carrying the session ID from step 1.
    for i, (tool, args) in enumerate(
        [("render_svg", {"source": "graph TD; A-->B"}),
         ("render_svg", {"source": "graph LR; X-->Y-->Z"}),
         ("list", {})], start=2):
        req = Request({"Mcp-Session-Id": sid},
                      {"method": "tools/call", "params": {"name": tool, "arguments": args}, "id": i})
        r = lb.route(req)
        status = "OK  " if r.ok else "FAIL"
        print(f"  {i}. tools/call {tool:<10} [{status}] via {r.replica}: {r.payload}")
        results.append(r.ok)
    return results


def run_stateless(lb: LoadBalancer):
    results = []
    seq = [("render_svg", {"source": "graph TD; A-->B"}),
           ("render_svg", {"source": "graph LR; X-->Y-->Z"}),
           ("list", {})]
    for i, (tool, args) in enumerate(seq, start=1):
        req = Request(
            {"MCP-Protocol-Version": "2026-07-28", "Mcp-Method": "tools/call", "Mcp-Name": tool},
            {"params": {"name": tool, "arguments": args,
                        "_meta": {"io.modelcontextprotocol/clientInfo": {"name": "demo", "version": "1"}}},
             "id": i})
        r = lb.route(req)
        status = "OK  " if r.ok else "FAIL"
        print(f"  {i}. tools/call {tool:<10} [{status}] via {r.replica}: {r.payload}")
        results.append(r.ok)
    return results


def main():
    print("=" * 72)
    print("STATEFUL MCP  —  3 replicas, round-robin LB, session affinity NOT configured")
    print("=" * 72)
    sf_lb = LoadBalancer([StatefulServer(f"replica-{i}") for i in range(1, 4)])
    sf = run_stateful(sf_lb)

    print()
    print("=" * 72)
    print("STATELESS MCP (2026-07-28)  —  same 3 replicas, same round-robin LB")
    print("=" * 72)
    sl_lb = LoadBalancer([StatelessServer(f"replica-{i}") for i in range(1, 4)])
    sl = run_stateless(sl_lb)

    def rate(rs):
        return 100.0 * sum(rs) / len(rs)

    print()
    print("=" * 72)
    print("SCORECARD")
    print("=" * 72)
    print(f"  Stateful  success rate : {rate(sf):5.1f}%   ({sum(sf)}/{len(sf)} requests)")
    print(f"  Stateless success rate : {rate(sl):5.1f}%   ({sum(sl)}/{len(sl)} requests)")
    print()
    print("  The stateful cluster fails whenever a follow-up call is routed to a replica that")
    print("  never saw the session's `initialize`. Fixing it means sticky sessions + a session")
    print("  store + affinity-aware LB config. Stateless MCP deletes that entire class of")
    print("  problem: any replica is a pure function of the request, so round-robin just works.")


if __name__ == "__main__":
    main()
