"""Two callers, one tool: the MCP Apps bridge, implemented from scratch.

A tool used to have exactly one caller, the model. When a tool renders a page in
the conversation, that page can call the tool too -- so a handler that decided
what to allow by reasoning about the model's intent is now reasoning about the
wrong thing.

This models the whole path in the standard library: JSON-RPC messages over an
in-memory channel standing in for postMessage, a host that brokers every call,
and an app that calls back. Nothing here needs a browser or a network.

Run: python3 code_example.py

Set GUARD = "trust_the_host" to ship the common bug and watch an unauthorized
call succeed because the host already approved a different one.
"""

import json

# --- knobs: edit these ---------------------------------------------------
GUARD = "check_in_handler"     # or "trust_the_host" -- the bug
SHOW_WIRE = True               # print the JSON-RPC messages as they pass

# Who may see what. The model never sees this table; the server owns it.
GRANTS = {"alice": {"NA", "EU"}, "bob": {"NA"}}
SALES = {"NA": 412_000, "EU": 288_000, "APAC": 96_000}

RESOURCE_URI = "ui://pick-region/mcp-app.html"


class Server:
    """The MCP server. One tool, declared with a UI, and its own authorization."""

    def __init__(self, guard):
        self.guard = guard
        self.calls = []

    def describe_tool(self):
        # The UI lives in _meta, never in the result -- that is the whole
        # compatibility story. A host that ignores _meta sees an ordinary tool.
        return {"name": "pick-region",
                "description": "Regional sales. Lets the user drill in.",
                "_meta": {"ui": {"resourceUri": RESOURCE_URI,
                                 "csp": {"connect-src": []}}}}

    def call_tool(self, name, arguments, ctx):
        """ctx carries who is asking and how. Both are needed to decide."""
        self.calls.append((ctx["caller"], arguments.get("region")))
        region = arguments.get("region", "NA")

        if self.guard == "check_in_handler":
            # Authorize the request, not the route it arrived on.
            if region not in GRANTS.get(ctx["user"], set()):
                return {"content": [{"type": "text",
                                     "text": "not permitted for this user"}],
                        "isError": True}
        # else: trust_the_host -- the bug. The host approved *a* call, so this
        # handler assumes every later call is equally fine.

        return {"content": [{"type": "text",
                             "text": "%s sales: $%s" % (region, f"{SALES[region]:,}")}]}


class Host:
    """Brokers everything. Renders the page, pushes results, forwards calls."""

    def __init__(self, server, user, supports_ui=True):
        self.server, self.user, self.supports_ui = server, user, supports_ui
        self.approved = False

    def wire(self, direction, message):
        if SHOW_WIRE:
            print("    %-14s %s" % (direction, json.dumps(message)[:96]))

    def model_calls(self, arguments):
        """Path one: the model decided, and the user approved this call."""
        self.approved = True
        self.wire("model -> host", {"method": "tools/call",
                                    "params": {"name": "pick-region",
                                               "arguments": arguments}})
        result = self.server.call_tool("pick-region", arguments,
                                       {"user": self.user, "caller": "model"})
        if self.supports_ui:
            self.wire("host -> app", {"method": "ui/initialize",
                                      "params": {"resourceUri": RESOURCE_URI}})
            self.wire("host -> app", {"method": "ui/toolresult",
                                      "params": {"result": result}})
        return result

    def app_calls(self, arguments):
        """Path two: a button. No model turn happened at all."""
        if not self.supports_ui:
            raise RuntimeError("this host cannot render an app")
        self.wire("app -> host", {"method": "tools/call",
                                  "params": {"name": "pick-region",
                                             "arguments": arguments}})
        return self.server.call_tool("pick-region", arguments,
                                     {"user": self.user, "caller": "app"})


def text_of(result):
    return result["content"][0]["text"]


def scenario(label, user, supports_ui, clicks):
    print("\n%s (user=%s, ui=%s)" % (label, user, supports_ui))
    server = Server(GUARD)
    host = Host(server, user, supports_ui)
    first = host.model_calls({"region": "NA"})
    print("    model result  %s" % text_of(first))
    leaked = 0
    for region in clicks:
        if not supports_ui:
            print("    (no app, so no second caller exists)")
            break
        result = host.app_calls({"region": region})
        ok = not result.get("isError")
        print("    click %-5s   %s" % (region, text_of(result)))
        if ok and region not in GRANTS.get(user, set()):
            leaked += 1
    return leaked, server.calls


def main():
    print("MCP Apps: one tool, two callers.  GUARD = %s\n" % GUARD)
    print("  The model calls the tool once. Then the rendered page calls it")
    print("  directly, with regions the user never asked for.")

    leaked_a, calls_a = scenario("Alice, allowed NA and EU", "alice", True, ["EU", "APAC"])
    leaked_b, calls_b = scenario("Bob, allowed NA only", "bob", True, ["EU", "APAC"])
    scenario("A host with no app support", "bob", False, ["EU"])

    total = len(calls_a) + len(calls_b)
    by_app = sum(1 for c, _ in calls_a + calls_b if c == "app")
    print("\n  %d calls reached the tool, %d of them from the page, not the model."
          % (total, by_app))
    print("  unauthorized calls that succeeded: %d" % (leaked_a + leaked_b))
    if leaked_a + leaked_b:
        print("  The host approved one call and the handler trusted the rest.")
    else:
        print("  The handler checked each call on its own merits, so the route")
        print("  it arrived on stopped mattering.")


if __name__ == "__main__":
    main()
