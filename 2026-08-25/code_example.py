"""
What your Claude Code hook matchers actually match.

Two filters decide whether a hook handler runs, and both are pattern matching
over text rather than a parser you can trust as a gate:

  1. `matcher`  -> filters on the TOOL NAME. Exact-match if the string contains
                   only [A-Za-z0-9_-, |,]; otherwise an UNANCHORED regex. The
                   characters you typed decide, not your intent.
  2. `if`       -> filters on the TOOL INPUT, in permission-rule syntax such as
                   Bash(rm *). For Bash it strips leading assignments, splits
                   command chains, and descends into $() and backticks -- then
                   glob-matches each piece. Documented as best-effort: when it
                   cannot parse, the hook runs anyway.

Both layers are implemented below exactly as documented, so you can point them
at your own settings.json instead of guessing.

    Edit MATCHERS / IF_RULES / COMMANDS at the bottom and re-run.

Run:  python3 code_example.py     (pure stdlib, no network, no API key)
"""

import fnmatch
import re

# ---------------------------------------------------------------- liftable core

# The exact-match character set. One character outside it promotes the whole
# string to a regex -- this single line is the mode switch people trip over.
EXACT_ONLY = re.compile(r"^[A-Za-z0-9_\-, |,]+$")

# Leading VAR=value assignments, which are stripped before matching.
ASSIGNMENT = re.compile(r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=(?:\"[^\"]*\"|'[^']*'|\S*)\s+)+")

# $(...) and `...` -- the substitutions the `if` matcher deliberately looks inside.
SUBSTITUTION = re.compile(r"\$\(([^()]*)\)|`([^`]*)`")


def matcher_mode(matcher):
    """Which of the two matching modes this string actually selects."""
    if matcher in ("", "*", None):
        return "match-all"
    return "exact-list" if EXACT_ONLY.match(matcher) else "regex-unanchored"


def matches_tool(matcher, tool_name):
    """Layer 1: does `matcher` fire for this tool name?"""
    mode = matcher_mode(matcher)
    if mode == "match-all":
        return True
    if mode == "exact-list":
        return tool_name in [p.strip() for p in re.split(r"[|,]", matcher) if p.strip()]
    return re.search(matcher, tool_name) is not None    # unanchored, as documented


def subcommands(command):
    """Every command a shell would actually run, flattened.

    Chains are split, leading assignments stripped, and substitutions descended
    into -- recursively, since $(...) can nest a chain of its own.
    """
    out = []
    inner = [m.group(1) or m.group(2) for m in SUBSTITUTION.finditer(command)]
    outer = SUBSTITUTION.sub(" ", command)
    for piece in re.split(r"&&|\|\||[;|\n]", outer):
        piece = ASSIGNMENT.sub("", piece).strip()
        if piece:
            out.append(piece)
    for nested in inner:
        out.extend(subcommands(nested))
    return out


def parse_rule(rule):
    """'Bash(rm *)' -> ('Bash', 'rm *'). A bare 'Bash' means any input."""
    m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)\s*$", rule)
    return (m.group(1), m.group(2)) if m else (rule.strip(), None)


def matches_if(rule, tool_name, tool_input):
    """Layer 2: does the `if` condition fire for this tool call?"""
    rule_tool, pattern = parse_rule(rule)
    if rule_tool != tool_name:
        return False
    if pattern is None:
        return True
    if tool_name == "Bash":
        return any(fnmatch.fnmatchcase(c, pattern) for c in subcommands(tool_input))
    return fnmatch.fnmatchcase(tool_input, pattern)


def hook_fires(matcher, rule, tool_name, tool_input):
    """Both filters, in the order Claude Code applies them."""
    return matches_tool(matcher, tool_name) and matches_if(rule, tool_name, tool_input)


# ------------------------------------------------------------------- your rules

MATCHERS = [
    ("Bash", "Bash"),
    ("Edit|Write", "Edit"),
    ("mcp__github__.*", "internal__mcp__github__admin"),
    ("^mcp__github__.*$", "internal__mcp__github__admin"),
    ("code-reviewer", "code-reviewer-v2"),
]

# (if-rule, command, what a reasonable person would predict)
CASES = [
    ("Bash(git *)", "git push",                      True),
    ("Bash(git *)", "FOO=bar git push",              False),   # assignments stripped
    ("Bash(git *)", "npm test && git push",          False),   # chain split
    ("Bash(rm *)",  "echo $(rm -rf /)",              False),   # descends into $()
    ("Bash(rm *)",  "echo $(date)",                  False),
    ("Bash(rm *)",  "echo \"rm is dangerous\"",      False),
    ("Bash(cat *)", "grep x f && echo $(cat /etc/p)", False),  # 2.1.243's bug shape
    ("Bash(npm *)", "npx npm-check",                 False),
]


def main():
    print("=" * 74)
    print("1. `matcher` -- the mode switch is invisible in the syntax")
    print("=" * 74)
    for matcher, tool in MATCHERS:
        mode = matcher_mode(matcher)
        hit = matches_tool(matcher, tool)
        flag = "  <-- substring match" if mode == "regex-unanchored" and hit else ""
        print(f"  {matcher:22} vs {tool:30} {mode:17} {str(hit):5}{flag}")

    print()
    print("=" * 74)
    print("2. `if` -- what the Bash walk really covers")
    print("=" * 74)
    surprises = 0
    for rule, cmd, naive in CASES:
        actual = matches_if(rule, "Bash", cmd)
        mark = " "
        if actual != naive:
            surprises += 1
            mark = "!"
        print(f" {mark} {rule:14} {cmd:34} -> {str(actual):5} (naive guess: {naive})")
        if actual != naive:
            print(f"      shell would run: {subcommands(cmd)}")

    print()
    print(f"  {surprises} of {len(CASES)} cases contradict the naive reading.")
    print("  Every one of them is documented behaviour, not a bug -- which is the point:")
    print("  the rule is cleverer than you expect AND still fails open when it cannot parse.")

    print()
    print("=" * 74)
    print("3. Both filters together, as Claude Code applies them")
    print("=" * 74)
    combo = [
        ("Bash", "Bash(rm *)", "Bash", "echo $(rm -rf /)"),
        ("Edit|Write", "Bash(rm *)", "Bash", "rm -rf build"),
        ("Bash", "Bash(rm *)", "Bash", "find . -delete"),
    ]
    for matcher, rule, tool, cmd in combo:
        m1, m2 = matches_tool(matcher, tool), matches_if(rule, tool, cmd)
        why = "matcher rejected" if not m1 else ("if rejected" if not m2 else "handler runs")
        print(f'  matcher={matcher:11} if={rule:12} {cmd:22} -> {str(m1 and m2):5}  {why}')

    print()
    print("  `find . -delete` deletes files and matches no rule here. That is not a")
    print("  gap in this implementation -- it is why policy belongs in permissions.deny.")


if __name__ == "__main__":
    main()
