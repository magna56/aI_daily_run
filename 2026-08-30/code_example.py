"""Subagent model resolution, and why your deny rules miss most of it.

resolve_subagent_model() is the four-layer precedence chain, before and after
Claude Code 2.1.251 moved CLAUDE_CODE_SUBAGENT_MODEL from first to third.
rule_matches() is the Tool(param:value) permission rule, with the three
documented behaviours that make a rule you wrote match nothing.

Run: python3 code_example.py     (pure stdlib, no keys, no network)
Point it at your own fleet by editing SPAWNS and DENY_RULES at the bottom.
"""

from dataclasses import dataclass
from typing import Optional

# Per-million-token API rates. Edit these and the whole cost column moves.
RATES = {  # model id -> (input $/MTok, output $/MTok)
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
}
ALIASES = {"opus": "claude-opus-5", "sonnet": "claude-sonnet-5", "haiku": "claude-haiku-4-5"}


@dataclass
class Spawn:
    """One launch. `param` is what the caller literally sent."""
    agent: str
    param: Optional[str]      # per-invocation model=, or None if omitted
    frontmatter: Optional[str]  # model: in the agent definition file, or None
    in_tokens: int
    out_tokens: int


def resolve_subagent_model(spawn, env_model, session_model, legacy=False):
    """Return the model alias/id that wins, and the layer that supplied it.

    legacy=True reproduces the pre-2.1.251 order, where the environment
    variable overrode both the spawn parameter and the definition file.
    A frontmatter value of "inherit" is a pass, not an answer -- that is what
    an omitted `model:` line means, so it must not stop the chain.
    """
    env = None if env_model in (None, "inherit") else env_model
    fm = None if spawn.frontmatter in (None, "inherit") else spawn.frontmatter

    chain = (
        [("env", env), ("param", spawn.param), ("frontmatter", fm)]
        if legacy
        else [("param", spawn.param), ("frontmatter", fm), ("env", env)]
    )
    for layer, value in chain:
        if value is not None:
            return value, layer
    return session_model, "session"


def rule_matches(rule, tool, params):
    """True if a rule like 'Agent(model:opus)' matches this call. Three
    behaviours decide whether a rule does anything: the value is compared to the
    literal input before normalization (an alias rule misses a full model ID), a
    parameter the caller omitted never matches, and '*' is the only wildcard."""
    if not (rule.startswith(tool + "(") and rule.endswith(")")):
        return False
    body = rule[len(tool) + 1:-1]
    if ":" not in body:
        return False
    name, _, want = body.partition(":")
    name, want = name.strip(), want.strip()
    got = params.get(name)
    if got is None:  # omitted parameter -- never matched, including by '*'
        return False
    return _glob(want, str(got))


def _glob(pattern, text):
    """'*' matches any run of characters. Iterative, so a star-heavy pattern
    cannot blow the stack."""
    parts = pattern.split("*")
    if len(parts) == 1:
        return pattern == text
    if not text.startswith(parts[0]):
        return False
    pos = len(parts[0])
    for part in parts[1:-1]:
        found = text.find(part, pos)
        if found < 0:
            return False
        pos = found + len(part)
    return text.endswith(parts[-1]) and pos <= len(text) - len(parts[-1])


def cost(model, in_tokens, out_tokens):
    rate_in, rate_out = RATES[ALIASES.get(model, model)]
    return in_tokens / 1e6 * rate_in + out_tokens / 1e6 * rate_out


# --- the demonstration -------------------------------------------------------

SPAWNS = [
    #        agent            param              frontmatter     in       out
    Spawn("repo-search", None, "opus", 220_000, 9_000),
    Spawn("code-reviewer", None, "sonnet", 180_000, 12_000),
    Spawn("doc-summarizer", None, None, 140_000, 6_000),
    Spawn("deep-debugger", "claude-opus-5", "sonnet", 260_000, 18_000),
    Spawn("test-writer", "opus", None, 95_000, 14_000),
]

DENY_RULES = ["Agent(model:opus)", "Agent(model:fable)"]
ENV_MODEL = "haiku"        # the cost cap you exported months ago
SESSION_MODEL = "claude-opus-5"


def main():
    print(f"CLAUDE_CODE_SUBAGENT_MODEL={ENV_MODEL}   session={SESSION_MODEL}")
    print(f"deny rules: {DENY_RULES}\n")
    header = f"{'agent':<16}{'was':<17}{'now':<17}{'via':<12}{'denied':<8}{'$ now':>8}"
    print(header + "\n" + "-" * len(header))
    old_total = new_total = 0.0
    caught = changed = 0
    for s in SPAWNS:
        was, _ = resolve_subagent_model(s, ENV_MODEL, SESSION_MODEL, legacy=True)
        now, layer = resolve_subagent_model(s, ENV_MODEL, SESSION_MODEL)
        params = {} if s.param is None else {"model": s.param}
        denied = any(rule_matches(r, "Agent", params) for r in DENY_RULES)
        old_total += cost(was, s.in_tokens, s.out_tokens)
        new_total += cost(now, s.in_tokens, s.out_tokens)
        caught += denied
        changed += was != now
        mark = "BLOCKED" if denied else ("-" if was == now else "escaped")
        print(f"{s.agent:<16}{was:<17}{now:<17}{layer:<12}{mark:<8}"
              f"{cost(now, s.in_tokens, s.out_tokens):>8.3f}")

    print(f"\nfan-out cost under the old order: ${old_total:.3f}")
    print(f"fan-out cost under the new order: ${new_total:.3f}"
          f"   ({new_total / old_total:.1f}x)")
    print(f"\nspawns that changed model: {changed}/{len(SPAWNS)}"
          f"   caught by a deny rule: {caught}/{len(SPAWNS)}")

    print("\nwhy the rules miss:")
    print(f"  Agent(model:opus) vs literal 'claude-opus-5' -> "
          f"{rule_matches('Agent(model:opus)', 'Agent', {'model': 'claude-opus-5'})}")
    print(f"  Agent(model:*)    vs an omitted parameter    -> "
          f"{rule_matches('Agent(model:*)', 'Agent', {})}")
    print(f"  Agent(model:*)    vs literal 'opus'          -> "
          f"{rule_matches('Agent(model:*)', 'Agent', {'model': 'opus'})}")


if __name__ == "__main__":
    main()
