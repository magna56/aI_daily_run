#!/usr/bin/env python3
"""
A fake coding agent following a vague wish vs a spec with examples.

The "model" is a handful of if-rules — the point is the *instruction*, not
neural nets. A rubric scores the resulting diff the way a reviewer would:
in-scope edit, no extra files, tests still make sense.

Run:  python3 code_example.py
"""

SRC = '''\
def retry(fn, attempts=3):
    """Call fn, retrying on any Exception."""
    last = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
    raise last
'''

# What a reviewer asked for: timeout only, same signature otherwise.
SPEC_DONE = ("deadline", "attempts")


def apply(prompt, files):
    """Return a new files dict. Deliberately dumb; follows prompt keywords."""
    out = {k: v for k, v in files.items()}
    wish = prompt.lower()
    src = out["src/net.py"]

    if "timeout" in wish or "deadline" in wish:
        src = src.replace(
            "def retry(fn, attempts=3):",
            "def retry(fn, attempts=3, deadline=None):",
        )
        src = src.replace(
            '    """Call fn, retrying on any Exception."""\n',
            '    """Call fn, retrying on any Exception. Stop if deadline (epoch s) passed."""\n'
            "    import time\n",
        )
        src = src.replace(
            "    for _ in range(attempts):\n",
            "    for _ in range(attempts):\n"
            "        if deadline is not None and time.time() > deadline:\n"
            "            raise TimeoutError(last)\n",
        )

    # Vague "improve" / "best practices" invents scope.
    if "improve" in wish or "best practices" in wish or "robust" in wish:
        src = src.replace("except Exception as e:", "except Exception as e:  # noqa")
        out["src/utils.py"] = "# helper added by the agent\ndef unused():\n    pass\n"
        out["README.md"] = files["README.md"] + "\n## Retry is now more robust\n"

    out["src/net.py"] = src
    return out


def rubric(before, after):
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    net = after["src/net.py"]
    has_deadline = "deadline" in net
    signature_ok = "def retry(fn, attempts=3, deadline=None):" in net
    extra = [p for p in changed if p != "src/net.py"]
    tests_ok = "def retry(" in net and "raise last" in net
    score = (
        (2 if has_deadline else 0)
        + (2 if signature_ok else 0)
        + (2 if tests_ok else 0)
        + (2 if not extra else 0)
        + (2 if changed == ["src/net.py"] else 0)
    )
    return score, changed, extra, has_deadline, signature_ok


def run(label, prompt, files):
    after = apply(prompt, files)
    score, changed, extra, has_deadline, signature_ok = rubric(files, after)
    print(f"\n=== {label} ===")
    print("prompt:")
    print("  " + prompt.replace("\n", "\n  "))
    print(f"files changed: {changed or '[none]'}")
    if extra:
        print(f"scope creep:   {extra}")
    print(f"deadline added: {has_deadline}   signature kept: {signature_ok}")
    print(f"reviewer score: {score}/10  (10 = mergeable)")
    return score


def main():
    files = {
        "src/net.py": SRC,
        "README.md": "# net\nretry() calls fn.\n",
    }
    vague = "Improve retry and make it more robust. Follow best practices."
    spec = """
Add an optional deadline (epoch seconds) to retry() in src/net.py.
Do not change the meaning of attempts. Do not edit other files.
Example — allowed: def retry(fn, attempts=3, deadline=None)
Example — reject: new helpers, README edits, catching BaseException.
Done when: src/net.py is the only diff and retry() still raises last.
""".strip()

    s1 = run("VAGUE WISH", vague, files)
    s2 = run("SPEC + EXAMPLES", spec, files)
    print(f"\nVague scored {s1}/10. Spec scored {s2}/10.")
    print("The fake model is the same. The prefix is not.")


if __name__ == "__main__":
    main()
