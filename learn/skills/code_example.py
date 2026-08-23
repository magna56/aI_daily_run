#!/usr/bin/env python3
"""
A skill is a lazy-loaded instruction pack, not a smaller model.

Tiny harness: four SKILL.md files in memory. Only frontmatter sits in the
catalog. A keyword matcher stands in for "the model decided this description
fits." Compare that bill to dumping every body into the always-on file, to a
hook (zero prompt tokens), and to a sub-agent (new setup, summary returns).

Run:  python3 code_example.py
"""

from textwrap import dedent

SKILLS = [
    {
        "name": "review-pr",
        "triggers": ("review", "pull request", "pr"),
        "description": "Reviews a pull request. Use when the user asks to review a PR or diff.",
        "body": "Checklist: scope, tests, error paths, secrets. Comment on the diff, not the vibe.",
    },
    {
        "name": "commit-msg",
        "triggers": ("commit", "commit message"),
        "description": "Writes a commit message. Use when the user asks for a commit message.",
        "body": "Format: type(scope): summary. Body says why. No trailing period on the subject.",
    },
    {
        "name": "deploy-web",
        "triggers": ("deploy", "ship", "release"),
        "description": "Deploys the web app. Use when the user asks to deploy, ship, or release.",
        "body": "Run tests, bump the tag, deploy the already-built folder, then smoke-check /health.",
    },
    {
        "name": "sql-style",
        "triggers": ("sql", "query", "postgres"),
        "description": "Applies warehouse SQL style. Use when the user writes SQL or a query.",
        "body": "Lowercase keywords, explicit column lists, no SELECT *. Filter in WHERE, not HAVING.",
    },
]


def words(text):
    return len(text.split())


def catalog():
    return [{"name": s["name"], "description": s["description"]} for s in SKILLS]


def load(phrase):
    q = phrase.lower()
    for s in SKILLS:
        if any(t in q for t in s["triggers"]):
            return s
    return None


def main():
    cat = catalog()
    cat_words = sum(words(c["name"]) + words(c["description"]) for c in cat)
    bodies = sum(words(s["body"]) for s in SKILLS)
    dumped = cat_words + bodies
    hook_words = 0
    child_setup, summary = 400, 40

    print("CATALOG (always in the prefix — frontmatter only)")
    for c in cat:
        print(f"  /{c['name']}: {c['description']}")
    print(f"  catalog words: {cat_words}")
    print(f"  all bodies dumped into always-on file: {dumped}")
    print()

    phrases = [
        "review this pull request please",
        "write me a commit message",
        "how does postgres nest loops work?",
    ]
    print("LOAD ON TRIGGER (body arrives only when the phrase matches)")
    for phrase in phrases:
        skill = load(phrase)
        if skill:
            loaded = cat_words + words(skill["body"])
            print(f"  {phrase!r}")
            print(f"    loaded /{skill['name']}  →  {loaded} words in prefix")
            print(f"    body: {skill['body']}")
        else:
            print(f"  {phrase!r}  →  catalog only ({cat_words} words), no body")
    print()

    print("SAME TASK, FOUR PRIMITIVES  ('review this pull request')")
    skill = load("review this pull request")
    loaded = cat_words + words(skill["body"])
    rows = [
        ("skill (on demand)", loaded, "catalog + one body"),
        ("dump every SKILL.md into CLAUDE.md", dumped, "all bodies every turn"),
        ("hook (PreToolUse linter)", hook_words, "runs outside the model"),
        ("sub-agent (child + summary)", child_setup + summary, f"{child_setup} in child, {summary} back"),
    ]
    for name, n, note in rows:
        print(f"  {n:4d} words  {name:42s}  {note}")
    print()
    print("A skill is not a smaller model. It is a file the harness loads.")
    print("A hook is not a skill. A sub-agent is not a skill.")


if __name__ == "__main__":
    main()
