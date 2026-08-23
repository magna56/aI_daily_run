#!/usr/bin/env python3
"""
Same request, two surfaces: a chat box (paste only) vs a coding agent
(repo + CLAUDE.md + a permission gate).

No API. The "model" is a small policy so the printout is the lesson.

Run:  python3 code_example.py
"""


REPO = {
    "CLAUDE.md": (
        "Package manager: pnpm (never npm).\n"
        "Do not edit files under codegen/.\n"
        "Tests: pnpm test\n"
    ),
    "src/retry.py": "def retry(fn, n=3):\n    return fn()\n",
    "src/cli.py": "from retry import retry\n# caller\n",
    "codegen/api.py": "# generated — do not edit\nTIMEOUT = 5\n",
    "package.json": '{ "packageManager": "pnpm@9" }\n',
}


def chat_box(pasted, request):
    """Sees only the paste. Invents a helper the repo already has."""
    print("\n=== CHAT BOX (sees only the paste) ===")
    print(f"pasted:\n{pasted}")
    print(f"request: {request}")
    print("model output:")
    print("  Here's a new helper wait_and_retry() you can add.")
    print("  Also: run `npm test` after you paste this back.")
    print("missed: src/cli.py caller, pnpm, codegen/, the existing retry()")
    return {"invented_helper": True, "wrong_pm": True, "files_read": 0}


def allowed(path, write, perms, briefing):
    if write and path.startswith("codegen/") and "Do not edit files under codegen/" in briefing:
        return False, "deny: CLAUDE.md forbids codegen/"
    if write and perms == "ask":
        return False, "ask: write blocked until the user approves"
    if write and perms == "deny-writes":
        return False, "deny: writes off"
    return True, "allow"


def agent(request, perms, use_briefing):
    briefing = REPO["CLAUDE.md"] if use_briefing else ""
    print(f"\n=== AGENT  perms={perms}  CLAUDE.md={'on' if use_briefing else 'off'} ===")
    print(f"request: {request}")
    reads = ["package.json", "src/retry.py", "src/cli.py", "codegen/api.py"]
    print("tools:")
    for p in reads:
        print(f"  READ  {p}  ({len(REPO[p])} bytes) -> context")
    plan = ["src/retry.py"]
    if "timeout" in request and not use_briefing:
        plan.append("codegen/api.py")  # unbriefed agent "helps" by editing generated code
    results = []
    for p in plan:
        ok, why = allowed(p, write=True, perms=perms, briefing=briefing)
        mark = "WRITE" if ok else "BLOCK"
        print(f"  {mark:5} {p}  ({why})")
        results.append((p, ok, why))
    pm = "pnpm" if use_briefing else "npm"
    print(f"  SHELL would propose: {pm} test")
    return {
        "files_read": len(reads),
        "writes_ok": [p for p, ok, _ in results if ok],
        "writes_blocked": [p for p, ok, _ in results if not ok],
        "pm": pm,
    }


def main():
    request = "Add a timeout to retry and run the tests."
    pasted = REPO["src/retry.py"]
    chat = chat_box(pasted, request)
    a_ask = agent(request, perms="ask", use_briefing=True)
    a_allow = agent(request, perms="allow", use_briefing=True)
    a_raw = agent(request, perms="allow", use_briefing=False)

    print("\n=== SCOREBOARD ===")
    print(f"chat:   invented helper={chat['invented_helper']}  files_read={chat['files_read']}")
    print(f"agent + CLAUDE.md + ask:   wrote={a_ask['writes_ok']}  blocked={a_ask['writes_blocked']}  pm={a_ask['pm']}")
    print(f"agent + CLAUDE.md + allow: wrote={a_allow['writes_ok']}  blocked={a_allow['writes_blocked']}")
    print(f"agent, no briefing, allow: wrote={a_raw['writes_ok']}  blocked={a_raw['writes_blocked']}  pm={a_raw['pm']}")
    print("\nSame request. Chat invents. Agent sees callers. Briefing + ask stop the bad write.")


if __name__ == "__main__":
    main()
