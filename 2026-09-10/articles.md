# Further Reading: Why Copilot's Approval Counts as a Required Review

## Articles

### 1. [Copilot code review can now approve pull requests](https://github.blog/changelog/2026-09-01-copilot-code-review-can-now-approve-pull-requests/)
**Source**: GitHub Changelog | **Date**: 1 September 2026 | **Read time**: ~5 min
> The change itself, and short enough that there is no excuse not to read the primary source. The
> sentence that matters is that Copilot "can submit an approval that counts toward the repository's
> required-approvals rule" — not an advisory comment, a binding one. Note the three facts the
> secondary coverage tends to drop: it is off by default, it is enabled at the enterprise,
> organization or repository level, and the paths it may approve can be restricted.

### 2. [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
**Source**: GitHub Docs | **Date**: current | **Read time**: ~20 min
> The reference for the fix. Read the pull-request rules section and notice which rules name
> accounts and which only count: `require_code_owner_review` and `require_last_push_approval`
> describe a principal, while `required_approving_review_count` describes a number. That
> distinction is the whole article, and it was in the docs before any of this happened.

### 3. [About code owners](https://docs.github.com/en/repositories/managing-your-repos-settings-and-features/customizing-your-repository/about-code-owners)
**Source**: GitHub Docs | **Date**: current | **Read time**: ~15 min
> Worth reading properly before you rely on it as a gate, because the path-matching rules surprise
> people: the last matching pattern wins, and a path with no matching entry has no owner at all. The
> second half is what makes a deliberately unowned generated directory a design choice rather than
> an oversight, which is the posture this session ends on.

### 4. [List reviews for a pull request](https://docs.github.com/en/rest/pulls/reviews)
**Source**: GitHub REST API documentation | **Date**: current | **Read time**: ~10 min
> The endpoint the CI check in this session calls, and the field that makes it possible. Each review
> carries a `user` object whose `type` is `"User"` for a person and `"Bot"` otherwise, so "was this
> approved by a human" is one request and one predicate. Read it if you want the check to assert
> anything more specific than the version here.

### 5. [Copilot code review: resolution reasons and expanded capabilities](https://github.blog/changelog/2026-08-27-copilot-code-review-resolution-reasons-and-expanded-capabilities/)
**Source**: GitHub Changelog | **Date**: 27 August 2026 | **Read time**: ~5 min
> The entry a week earlier, and useful context for judging how much weight the approval deserves.
> It describes what the reviewer now covers and how it reports why a comment was resolved — which
> is the evidence you would actually use to decide which paths you are willing to let it sign off
> on, rather than deciding from the announcement alone.
