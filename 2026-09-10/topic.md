# Why Copilot's Approval Counts as a Required Review

**Category**: AI Engineering Practices
**Tags**: coding-agents, reliability, security
**Date**: 2026-09-10
**Level**: Building
**For**: Shipping AI
**Hook**: Branch protection asks for a number of approvals, and it never asked who supplied them. An AI reviewer can now supply one, so the rule you wrote to mean "a person read this" quietly stopped meaning that.
**Engineer's view**: You once required two approvals on a deploy, then added a service account to the reviewers team so automation could unblock itself. The rule still passed and the guarantee was gone. This is that, and the account is a code reviewer.
**TLDR**: GitHub can now let Copilot submit an approval that counts toward a repository's required-approvals rule. The count was always a proxy for human review, and it is worth encoding the property you actually wanted instead.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine a door that opens once two people sign a sheet. The rule is not really about
people, it is about two signatures. For years only people could hold the pen, so nobody
noticed the difference. Now a very fast helper can sign too. The door still opens on two
signatures, exactly as designed. What changed is that "two signatures" and "two people
looked" are no longer the same sentence.

## The Problem

You have shipped this bug, and it had nothing to do with AI. You required two approvals on
production deploys. Then automation needed to unblock its own release, so someone added a
service account to the reviewers team. The rule still passed on every deploy. The property
you wanted — that a second person had looked — was gone, and nothing failed to tell you.

Branch protection has the same shape. The setting is a number: require this many approving
reviews before merge. It counts approvals. It has never asked what kind of account
supplied them, because for years only one kind could.

That assumption has expired. An AI reviewer can now submit an approval that counts toward
the required approving reviews, instead of leaving an advisory comment. So a repository
with `required_approving_review_count: 1` may now merge code that no person read.

Nothing broke, and nothing in your repository changed. The rule does exactly what it always
did, the configuration looks identical to the day you wrote it, and the guarantee you
believed it carried is the only thing that moved.

**The fix is to stop using a count as a proxy for a property**, and to say the thing you
meant.

## The Fix: Require the Property, Not the Number

The change landed in GitHub's changelog on 1 September 2026, in public preview, and the
important detail is that it is opt-in and path-scoped. Two settings already exist that
describe a person rather than a tally, and those are the lever.

```figure
{ "kind": "system",
  "title": "The whole argument: the same rule, before and after a new reviewer exists",
  "lanes": [
    { "t": "the rule says", "nodes": [
        { "id": "count", "t": "1 approving review" } ] },
    { "t": "satisfied by", "nodes": [
        { "id": "human", "t": "a teammate", "s": "ok" },
        { "id": "bot",   "t": "an AI reviewer", "s": "new" } ] },
    { "t": "what you get", "nodes": [
        { "id": "read", "t": "someone read it", "s": "ok" },
        { "id": "merge", "t": "a merge, and no reader", "s": "bad" } ] }
  ],
  "edges": [
    { "from": "count", "to": "human" },
    { "from": "count", "to": "bot",  "t": "admin enables", "s": "new" },
    { "from": "human", "to": "read" },
    { "from": "bot",   "to": "merge", "s": "bad" } ],
  "note": "The rule is unchanged and still passes. Only the set of principals that can satisfy it grew." }
```

### Which setting actually names a person?

`Require review from Code Owners`. A code owner is an entry in your `CODEOWNERS` file — a
user or a team you wrote down. Copilot is not in that file, so a code-owner requirement
cannot be satisfied by it. The requirement points at named accounts rather than at a
number, which is exactly the difference this change exposes.

The second is `Require approval of the most recent reviewable push`, which demands an
approval from someone other than the last person to push. That one is about independence
rather than humanity, and it is worth having for a separate reason: it stops an author
approving their own final commit.

```figure
{ "kind": "route",
  "title": "What each rule is really asserting",
  "source": "a pull request, ready to merge",
  "parts": [
    { "t": "required approvals: 1", "to": 0, "via": "a tally", "s": "bad" },
    { "t": "code owner review", "to": 1, "via": "named accounts", "s": "ok" },
    { "t": "not the last pusher", "to": 1, "via": "independence", "s": "ok" }
  ],
  "dests": [
    { "t": "any principal can satisfy it", "s": "bad" },
    { "t": "only who you listed can", "s": "ok" }
  ],
  "note": "Only the second kind survives a new type of reviewer appearing, because it names who rather than how many." }
```

### So should the feature just stay off?

That is one answer and it is not the best one. Copilot review catches real things, and the
approval is dismissed automatically when new commits are pushed, so a stale sign-off does
not linger.

The useful posture is narrower. Let it approve where its judgment is worth as much as a
person's and the downside is bounded — generated clients, lockfiles, translations, docs —
and keep a named human owner on everything else. That is what the file-path restriction is
for, and it is the part of the announcement most worth using.

## What This Means for You

**When this matters.** You have branch protection expressed as a count, and someone in your
organization can enable this. Note the levels: an **enterprise** or **organization** admin
can turn it on, so a repository owner may not be the person who decides. If you are subject
to an audit that says "all changes are peer reviewed", the sentence in your policy and the
rule enforcing it have just drifted apart.

**How it affects you.** It turns a settings question into a design question. The honest
version of what you want is rarely "one approval" — it is closer to "a person who owns this
code agreed to it, and it was not the author". Those are different rules, and only one of
them survives the arrival of a new kind of reviewer.

It also gives you a useful habit for everything else. Any rule expressed as a count of
principals is a rule that will change meaning when the set of principals changes. That is
worth checking wherever you have one.

**What to do about it.**

1. Find out whether it is enabled above you. Check the organization setting first, because
   the repository view will not tell you an enterprise turned it on.
2. Add a `CODEOWNERS` entry and a code-owner requirement to the paths where a human
   genuinely has to look. That is the change with the most effect for the least work.
3. Then decide the paths where an AI approval is genuinely enough, and restrict it to those
   rather than leaving it repository-wide.
4. If you are audited, reconcile the policy text with the rule. "Peer reviewed" now needs
   to say what a peer is.

## Implementing It

**The change.** Three places, and each is a different owner.

*The ruleset.* Say what you mean, in the rule itself:

```json
{
  "name": "protect main",
  "target": "branch",
  "conditions": { "ref_name": { "include": ["refs/heads/main"], "exclude": [] } },
  "rules": [{
    "type": "pull_request",
    "parameters": {
      "required_approving_review_count": 1,
      "require_code_owner_review": true,
      "require_last_push_approval": true,
      "dismiss_stale_reviews_on_push": true
    }
  }]
}
```

`require_code_owner_review` is the line that does the work. The count stays at one, and
that one now has to come from an account you listed in `CODEOWNERS`.

*The ownership file.* The rule above is inert without it, and this is where you decide
which paths need a person:

```
# CODEOWNERS — a human owner on the paths where review is the point
/src/billing/       @payments-team
/infra/             @platform-team
/.github/workflows/ @platform-team

# No owner here on purpose: generated, and cheap to get wrong
/src/api/generated/
/locales/
```

*The check that catches it anyway.* Settings drift and admins above you change things, so
assert the property in CI rather than trusting the configuration:

```python
import os, urllib.request, json

repo, pr = os.environ["GITHUB_REPOSITORY"], os.environ["PR_NUMBER"]
req = urllib.request.Request(
    f"https://api.github.com/repos/{repo}/pulls/{pr}/reviews",
    headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
             "Accept": "application/vnd.github+json"})
reviews = json.load(urllib.request.urlopen(req))

human = [r for r in reviews
         if r["state"] == "APPROVED" and (r.get("user") or {}).get("type") == "User"]
if not human:
    raise SystemExit("no approval from a human account — approvals: %d"
                     % sum(1 for r in reviews if r["state"] == "APPROVED"))
```

The field that matters is `user.type`, which is `"User"` for a person and `"Bot"` for a
bot account. Make this a required status check and the property is enforced by something
you own, rather than by a setting someone above you can flip.

Note what the check deliberately does not do: it never counts approvals. Counting is the
mistake that got you here, so it asserts that at least one human approval exists and stays
silent about how many there are in total.

Scope it to the paths `CODEOWNERS` covers, though. Run repo-wide it will also block the
generated directories you deliberately left unowned, which is the one place the AI approval
was earning its keep.

**How you know it worked.** Open a pull request touching an owned path, get only a Copilot
approval, and confirm the merge button stays disabled. That is the test, and it takes two
minutes. Then push a commit to an already-approved PR and confirm the approval is
dismissed, which is stale review dismissal doing its job.

The slower signal is worth setting up if you are audited. Count merges to `main` whose
approvals were all bot accounts, monthly. You are looking for zero on owned paths, and the
number is only meaningful if you were measuring it before you changed anything.

**When not to.** Do not put a code owner on a path nobody wants to own. An unowned
generated directory that merges on an AI approval is the case this feature is good at, and
forcing a human there just teaches people to rubber-stamp.

## When an AI Approval Is the Wrong Gate

The narrow version of this feature is genuinely useful, so it is worth being clear about
where it is not.

Anything where the reviewer needs context that is not in the diff. A change that is
correct in isolation and wrong for a reason living in a design document, a customer
commitment, or last week's incident is exactly what a human owner is for. The diff looks
fine, which is the problem.

Anything you are audited on, until the policy text is updated. The risk there is not a bad
merge; it is a control you claim to have and cannot evidence. Fix the sentence before you
change the setting, not afterwards.

And it is a public preview. Behavior can move, and a control you rely on should be one you
can assert yourself — which is why the CI check above matters more than the settings page.

Three questions before you enable it anywhere:

- Is it already on above me, and who can turn it off?
- Which paths would I genuinely accept a machine sign-off on?
- If the setting changed tomorrow without telling me, what would fail?

## Glossary

- **Branch protection** — rules that must pass before a commit reaches a protected branch.
  Expressed as a ruleset on modern repositories.
- **Required approving reviews** — the count of approving reviews a pull request needs. A
  number, with no statement about who supplied it.
- **CODEOWNERS** — a file listing users or teams that own given paths. It names accounts,
  which is why a code-owner requirement behaves differently from a count.
- **Ruleset** — the newer form of branch protection, defined as JSON and manageable through
  the API, so the rule can live in review alongside the code.
- **Stale review dismissal** — automatically withdrawing approvals when new commits land,
  so a sign-off always refers to the diff that was actually read.
- **Bot account** — a non-human principal on GitHub. The reviews API reports it as
  `user.type` of `"Bot"`, which is the field a check can assert on.
