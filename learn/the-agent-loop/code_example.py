#!/usr/bin/env python3
"""
Observe / think / act. Tool names are the contract.

A fake model was trained to emit edit_file(path, old_string, new_string).
The same policy is pointed at three dispatchers: a matching schema, a renamed
tool (mutate_buffer), and an MCP-shaped list/call server. The loop is identical.
The name is what succeeds or misses.

Run:  python3 code_example.py
"""

import json

TRAINED = {
    "name": "edit_file",
    "arguments": {
        "path": "app.py",
        "old_string": "debug = True",
        "new_string": "debug = False",
    },
}


def think(_obs):
    """Stand-in for a model call: always emits the trained tool shape."""
    return dict(TRAINED)


def observe(user, results):
    return {"user": user, "results": list(results)}


def act(call, tools):
    name, args = call["name"], call["arguments"]
    if name not in tools:
        known = ", ".join(tools) or "(none)"
        return False, f"schema miss: {name!r} not in [{known}]"
    spec = tools[name]["required"]
    extra = set(args) - set(tools[name]["properties"])
    missing = [k for k in spec if k not in args]
    if extra or missing:
        return False, f"schema miss: extra={sorted(extra)} missing={missing}"
    return True, f"{name}({args['path']}): {args['old_string']!r} → {args['new_string']!r}"


def loop(title, tools, mcp=False):
    print(f"\n== {title} ==")
    results = []
    obs = observe("turn off debug in app.py", results)
    print(f"  observe: {obs['user']}")
    if mcp:
        catalog = [{"name": n, "required": t["required"]} for n, t in tools.items()]
        print(f"  mcp tools/list → {json.dumps(catalog)}")
    call = think(obs)
    print(f"  think:   {call['name']}({json.dumps(call['arguments'])})")
    if mcp:
        print(f"  mcp tools/call name={call['name']!r}")
    ok, msg = act(call, tools)
    results.append(msg)
    print(f"  act:     {msg}")
    print(f"  observe: {results[-1]}")
    print(f"  {'ok' if ok else 'stopped — contract missed'}")
    return ok


def main():
    matching = {
        "edit_file": {
            "properties": {"path": {}, "old_string": {}, "new_string": {}},
            "required": ["path", "old_string", "new_string"],
        }
    }
    renamed = {
        "mutate_buffer": {
            "properties": {"path": {}, "old_string": {}, "new_string": {}},
            "required": ["path", "old_string", "new_string"],
        }
    }
    a = loop("matching name (edit_file)", matching)
    b = loop("renamed tool (mutate_buffer)", renamed)
    c = loop("MCP list + call, still edit_file", matching, mcp=True)
    print("\nRESULTS")
    print(f"  matching: {a}   renamed: {b}   mcp+matching: {c}")
    print("The loop did not change. The name did.")
    print("Daily lab 2026-07-05: trained schemas leak into third-party tools.")


if __name__ == "__main__":
    main()
