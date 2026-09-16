"""
What a coding agent loads into every subagent you spawn.

Resolves the instruction hierarchy that enters an agent's context window before
its task arrives, then prices a parallel fan-out three ways: the default, with
`omitClaudeMd: true` on the helpers, and with `claudeMdExcludes` cutting an
ancestor file out of everything.

`instruction_context()` is the part to lift. Point START_DIR at a real checkout
and it reports what your own hierarchy costs per agent launch.

Run: python3 code_example.py
"""
# REQUIRES: none (standard library only)

import fnmatch
import os
import re
import tempfile
from pathlib import Path

# ---------------------------------------------------------------- knobs ----
START_DIR = None      # set to a real path to measure your own repo; None = demo tree
FAN_OUT = 5           # helpers spawned by one parallel search; raise it and watch the bill
CHARS_PER_TOKEN = 4   # rough estimate; real tokenizers land within ~10% for prose
PRICE_PER_MTOK = 3.0  # dollars per million input tokens

MAX_IMPORT_HOPS = 4                          # the documented import recursion limit
IMPORT_RE = re.compile(r"(?<![`\w])@([\w./~-]+)")


# ------------------------------------------------------ the liftable core ----
def _expand_imports(path: Path, seen: set, hops: int) -> list:
    """An @path import is expanded at launch, so it costs the same as inlining it."""
    if hops > MAX_IMPORT_HOPS or path in seen or not path.is_file():
        return []
    seen.add(path)
    text = path.read_text(errors="ignore")
    out = [(path, len(text))]
    for target in IMPORT_RE.findall(text):
        resolved = (path.parent / target.replace("~", str(Path.home()))).resolve()
        out += _expand_imports(resolved, seen, hops + 1)
    return out


def instruction_context(cwd, home, managed=None, excludes=(), omit_claude_md=False):
    """Every instruction file that enters one agent's window, in load order.

    Returns [(path, scope, chars)]. `omit_claude_md` reproduces the subagent
    frontmatter key: it drops user/project/local and *keeps* managed policy,
    which is why it is a context lever and not a policy escape.
    """
    cwd, home = Path(cwd).resolve(), Path(home).resolve()
    candidates = []

    if managed:                                   # managed policy always loads first
        candidates.append((Path(managed), "managed"))
    if not omit_claude_md:
        candidates.append((home / ".claude" / "CLAUDE.md", "user"))
        candidates += [(p, "user") for p in sorted((home / ".claude" / "rules").glob("*.md"))]
        # root-down, so the directory you launched in is read last
        for d in reversed([cwd, *cwd.parents]):
            candidates.append((d / "CLAUDE.md", "project"))
            candidates.append((d / ".claude" / "CLAUDE.md", "project"))
            candidates += [(p, "project") for p in sorted((d / ".claude" / "rules").glob("*.md"))]
            candidates.append((d / "CLAUDE.local.md", "local"))

    resolved, seen = [], set()
    for path, scope in candidates:
        # excludes are globs against the absolute path, and never reach managed policy
        if scope != "managed" and any(fnmatch.fnmatch(str(path), g) for g in excludes):
            continue
        for found, chars in _expand_imports(path, seen, 1):
            resolved.append((found, scope, chars))
    return resolved


def tokens(files) -> int:
    return sum(chars for _, _, chars in files) // CHARS_PER_TOKEN


# ------------------------------------------------------------ demo tree ----
def build_demo_tree(root: Path) -> Path:
    """A monorepo three levels deep, with another team's rules in an ancestor."""
    def w(rel, body):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)

    w("CLAUDE.md", "# Monorepo rules\n" + "- Every service ships a health endpoint.\n" * 40)
    w(".claude/rules/platform.md", "# Platform\n" + "- Use the shared logger.\n" * 30)
    w("services/CLAUDE.md", "# Services\n" + "- Handlers live in handlers/.\n" * 25)
    w("services/billing/CLAUDE.md",
      "# Billing\n@./conventions.md\n" + "- Money is integer cents, never float.\n" * 20)
    w("services/billing/conventions.md", "# Conventions\n" + "- Table names are plural.\n" * 35)
    w("services/billing/CLAUDE.local.md", "# Mine\n" + "- Sandbox is localhost:8931.\n" * 10)
    w("home/.claude/CLAUDE.md", "# Personal\n" + "- Prefer short functions.\n" * 25)
    w("managed/CLAUDE.md", "# Corporate policy\n" + "- Never log customer data.\n" * 12)
    return root / "services" / "billing"


def report(label, per_agent_tokens, helper_tokens):
    total = per_agent_tokens + helper_tokens * FAN_OUT
    print(f"  {label:<34} main {per_agent_tokens:>6,}  x{FAN_OUT} helpers {helper_tokens * FAN_OUT:>7,}"
          f"  total {total:>7,} tok  ${total / 1e6 * PRICE_PER_MTOK:0.4f}")
    return total


def main():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    cwd = Path(START_DIR) if START_DIR else build_demo_tree(root)
    home = root / "home" if not START_DIR else Path.home()
    managed = (root / "managed" / "CLAUDE.md") if not START_DIR else None

    baseline = instruction_context(cwd, home, managed)
    print(f"Instruction files loading at launch in {cwd.name}/ ({len(baseline)} files)")
    for path, scope, chars in baseline:
        print(f"  {scope:<8} {chars // CHARS_PER_TOKEN:>5,} tok  {path.name}")
    main_tok = tokens(baseline)
    print(f"\nOne agent pays {main_tok:,} tokens before it reads a word of its task.\n")

    print(f"A repo-wide search that fans out to {FAN_OUT} helpers:")
    a = report("default", main_tok, main_tok)

    # omitClaudeMd is per agent: helpers drop everything but managed policy
    helper = tokens(instruction_context(cwd, home, managed, omit_claude_md=True))
    b = report("omitClaudeMd on the helpers", main_tok, helper)

    # claudeMdExcludes is per file: it cuts the ancestor out of main and helpers alike.
    # Globs match the *resolved* absolute path, which is the detail that bites on macOS.
    top = root.resolve()
    ex = [str(top / "CLAUDE.md"), str(top / ".claude" / "rules" / "*")]
    excluded = tokens(instruction_context(cwd, home, managed, excludes=ex))
    c = report("claudeMdExcludes on the ancestor", excluded, excluded)

    print(f"\nomitClaudeMd saves {(1 - b / a) * 100:0.0f}% of the fan-out and leaves your session alone.")
    print(f"claudeMdExcludes saves {(1 - c / a) * 100:0.0f}%, and the file is gone from your session too.")
    print(f"Managed policy survives both: {tokens(instruction_context(cwd, home, managed, omit_claude_md=True)):,} tokens.")
    tmp.cleanup()


if __name__ == "__main__":
    main()
