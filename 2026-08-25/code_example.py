"""
How a coding-agent hook decides to fire.

Two filters run before your handler starts, both pattern matching over text
rather than a parser you can trust as a gate:

  1. `matcher` -> the TOOL NAME. Exact-match if the string holds only
     [A-Za-z0-9_-, |,]; otherwise an UNANCHORED regex. The characters decide.
  2. `if` -> the TOOL INPUT, in permission-rule syntax like Bash(rm *). For Bash
     it strips leading assignments, splits chains, and descends into $() and
     backticks, then glob-matches each piece. Best-effort by documentation:
     when it cannot parse, the hook runs anyway.

Both are implemented below as documented. Point MATCHERS and CASES at your own
settings.json, re-run, and read the rows marked `!`.

Run:  python3 code_example.py     (pure stdlib, no network, no API key)
"""

import fnmatch
import re

# ---------------------------------------------------------------- liftable core

# One character outside this set promotes the whole string to a regex.
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
    """Every command a shell would actually run, flattened. Chains split,
    assignments stripped, substitutions descended into -- recursively."""
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
    # Not used by main() -- this is the entry point to lift into your own tooling.
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
    ("Bash(rm *)",  "find . -delete",                False),   # deletes, matches nothing
]


def banner(text):
    print("=" * 74 + f"\n{text}\n" + "=" * 74)


def main():
    banner("1. `matcher` -- the mode switch is invisible in the syntax")
    for matcher, tool in MATCHERS:
        mode = matcher_mode(matcher)
        hit = matches_tool(matcher, tool)
        flag = "  <-- substring match" if mode == "regex-unanchored" and hit else ""
        print(f"  {matcher:22} vs {tool:30} {mode:17} {str(hit):5}{flag}")

    print()
    banner("2. `if` -- what the Bash walk really covers")
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
    print("  Note the last row: `find . -delete` deletes files and matches no rule here.")
    print("  That is not a gap in this implementation -- it is why policy belongs in")
    print("  permissions.deny, which enforces, rather than in a hook, which is best-effort.")


if __name__ == "__main__":
    main()
