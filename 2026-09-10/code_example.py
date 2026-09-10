"""What "required approvals" actually asserts, and what it does not.

Models a merge gate the way branch protection does -- as rules evaluated
against a list of reviews -- then runs the same pull requests through four
rule sets. The point is to see a configuration that passes for the wrong
reason, which is the failure a count cannot detect.

No network, no GitHub token. The review objects have the same shape the REST
API returns, so the predicate that decides is the one you would ship.

Run: python3 code_example.py

Add a rule to RULESETS and it is evaluated against every case.
"""

# Reviews as GET /repos/{owner}/{repo}/pulls/{n}/reviews returns them.
def review(login, kind, state="APPROVED", commit="c2"):
    return {"user": {"login": login, "type": kind}, "state": state,
            "commit_id": commit}


HUMAN, BOT = "User", "Bot"
OWNERS = {"@payments-team": {"dana", "sam"}}          # from CODEOWNERS
HEAD = "c2"                                            # the most recent push


# --- the rules, each a predicate over (reviews, pr) -----------------------
def approvals(reviews):
    return [r for r in reviews if r["state"] == "APPROVED"]


def count_at_least(n):
    """required_approving_review_count. Counts. Asks nothing about who."""
    return lambda rv, pr: len(approvals(rv)) >= n


def code_owner_review():
    """require_code_owner_review. Names accounts, so a bot cannot satisfy it.

    Applies only where a path HAS an owner. An unowned path passes vacuously,
    which is what makes a deliberately unowned generated directory the case
    this feature is good at rather than a hole in the gate.
    """
    def rule(rv, pr):
        owners = set()
        for team in pr["owners"]:
            owners |= OWNERS.get(team, set())
        if not owners:
            return True
        return any(r["user"]["login"] in owners for r in approvals(rv))
    return rule


def last_push_approval():
    """require_last_push_approval. About independence, not humanity."""
    return lambda rv, pr: any(
        r["commit_id"] == HEAD and r["user"]["login"] != pr["last_pusher"]
        for r in approvals(rv))


def human_approval():
    """Not a GitHub rule -- the CI check from Implementing It."""
    return lambda rv, pr: any(r["user"]["type"] == HUMAN for r in approvals(rv))


RULESETS = {
    "count>=1": [count_at_least(1)],
    "count>=2": [count_at_least(2)],
    "+owner": [count_at_least(1), code_owner_review()],
    "+owner+push": [count_at_least(1), code_owner_review(), last_push_approval()],
    "+human(CI)": [count_at_least(1), human_approval()],
}

CASES = [
    ("teammate approved",
     [review("dana", HUMAN)], {"owners": ["@payments-team"], "last_pusher": "rio"}),
    ("AI reviewer approved",
     [review("copilot", BOT)], {"owners": ["@payments-team"], "last_pusher": "rio"}),
    ("AI reviewer, twice",
     [review("copilot", BOT), review("copilot-secondary", BOT)],
     {"owners": ["@payments-team"], "last_pusher": "rio"}),
    ("AI + a non-owner human",
     [review("copilot", BOT), review("rio", HUMAN)],
     {"owners": ["@payments-team"], "last_pusher": "rio"}),
    ("owner approved an old commit",
     [review("dana", HUMAN, commit="c1")],
     {"owners": ["@payments-team"], "last_pusher": "rio"}),
    ("unowned path, AI approved",
     [review("copilot", BOT)], {"owners": [], "last_pusher": "rio"}),
]


def main():
    names = list(RULESETS)
    print("Does the pull request merge?\n")
    print("  %-30s%s" % ("case", "".join("%-13s" % n for n in names)))
    for label, reviews, pr in CASES:
        cells = []
        for n in names:
            ok = all(rule(reviews, pr) for rule in RULESETS[n])
            cells.append("%-13s" % ("merge" if ok else "blocked"))
        print("  %-30s%s" % (label, "".join(cells)))

    print("\n  Row 2 is the whole point. One AI approval merges under a plain count,")
    print("  and the configuration is the one you wrote before AI reviewers existed.")
    print("\n  Row 3 shows why raising the number does not help: two bot approvals")
    print("  satisfy a rule asking for two. The count was never the property.")
    print("\n  Row 4 is the subtle one. A human approved, so the CI check passes —")
    print("  but rio is not an owner and is the last pusher, so only the columns")
    print("  that name accounts catch it. 'A human looked' is weaker than 'the")
    print("  person responsible for this code agreed'.")
    print("\n  Row 6 is the case the feature is genuinely good at: nobody owns the")
    print("  path, so the owner rule passes vacuously and the AI approval is enough.")
    print("  Note the last column blocks it anyway — the CI check as written is")
    print("  repo-wide, so it undoes the feature exactly where it earns its place.")
    print("  Scope the check to the same paths CODEOWNERS covers, or it becomes the")
    print("  blunt instrument you were trying to replace.")


if __name__ == "__main__":
    main()
