"""
AGENTS.md: one rules file for Claude, Codex, Cursor and Copilot.

Implements each tool's instruction-file lookup — including Claude Code's
one-way fallback, Copilot's four filenames, and the nearest-wins rule for
nested files — then reports which tools would read which file for a given
edit, and which of them disagree.

`resolve` is the part to lift. Point TOOLS and a file listing at your own
repository to find the drift before an agent does.

Run: python3 code_example.py
"""
# REQUIRES: none (standard library only)

import posixpath

# ---------------------------------------------------------------- knobs ----
# The file an agent is about to edit. Change it and watch the nearest-wins
# rule pick a different AGENTS.md for the tools that support nesting.
EDITING = "packages/api/handlers/orders.py"

# Each tool's lookup order, first match wins. Sourced from the Claude Code
# changelog (2.1.277), GitHub's custom-instructions docs, and agents.md.
TOOLS = {
    "Claude Code":    ["CLAUDE.md", "AGENTS.md"],
    "Claude (Bedrock)": ["CLAUDE.md"],          # no AGENTS.md fallback yet
    "GitHub Copilot": [".github/copilot-instructions.md", "AGENTS.md",
                       "CLAUDE.md", "GEMINI.md"],
    "Codex":          ["AGENTS.md"],
    "Cursor":         ["AGENTS.md", ".cursorrules"],
}
NESTS = {"AGENTS.md"}   # only this filename is looked up per-directory


# ------------------------------------------------------ the liftable core ----
def _dirs_upward(path: str):
    """Every directory from the edited file up to the repo root, nearest first.
    This ordering is the nearest-wins rule: a rule next to the code beats a
    rule at the root."""
    d = posixpath.dirname(path)
    while True:
        yield d
        if not d:
            return
        d = posixpath.dirname(d)


def resolve(tool: str, repo_files: set, editing: str):
    """Which instruction file this tool actually reads, or None.

    Two rules interact. A tool tries its filenames in order and takes the first
    that exists, which is why a leftover CLAUDE.md silently disables Claude
    Code's AGENTS.md fallback. And a nesting filename is searched from the
    edited file upward, so the same tool can read a different file per edit."""
    for name in TOOLS[tool]:
        if name in NESTS:
            for d in _dirs_upward(editing):
                candidate = posixpath.join(d, name) if d else name
                if candidate in repo_files:
                    return candidate
        elif name in repo_files:
            return name
    return None


def disagreements(repo_files: set, editing: str) -> dict:
    """Group tools by the file they read. More than one group means two agents
    are following different instructions on the same repo, with nothing in any
    log to say so."""
    groups = {}
    for tool in TOOLS:
        groups.setdefault(resolve(tool, repo_files, editing), []).append(tool)
    return groups


# ------------------------------------------------------------------ demo ----
LAYOUTS = {
    "the usual mess": {
        "CLAUDE.md", "AGENTS.md", ".cursorrules",
        ".github/copilot-instructions.md", "packages/api/AGENTS.md",
    },
    "consolidated (CLAUDE.md deleted)": {
        "AGENTS.md", "packages/api/AGENTS.md",
    },
    "consolidated, but an empty CLAUDE.md was left behind": {
        "CLAUDE.md", "AGENTS.md", "packages/api/AGENTS.md",
    },
    "Bedrock-safe: AGENTS.md imports CLAUDE.md": {
        "CLAUDE.md", "AGENTS.md",
    },
}


def main():
    print(f"agent is editing: {EDITING}\n")
    for label, files in LAYOUTS.items():
        groups = disagreements(files, EDITING)
        print(f"  {label}")
        for path, tools in sorted(groups.items(), key=lambda kv: (kv[0] or "~")):
            shown = path if path else "nothing — no instructions at all"
            print(f"    {shown:<38} {', '.join(tools)}")
        n = len(groups)
        verdict = "all agree" if n == 1 else f"{n} different files in play"
        print(f"    -> {verdict}\n")

    print("read the third layout again: deleting CLAUDE.md's CONTENTS is not enough.")
    print("the fallback is 'is there a CLAUDE.md', not 'does it say anything', so an")
    print("empty file keeps Claude Code on it while Codex and Cursor read AGENTS.md.\n")

    print("nearest-wins, same repo, different edit:")
    files = LAYOUTS["consolidated (CLAUDE.md deleted)"]
    for target in ("packages/api/handlers/orders.py", "packages/web/app.tsx", "README.md"):
        print(f"  {target:<34} Codex reads {resolve('Codex', files, target)}")


if __name__ == "__main__":
    main()
