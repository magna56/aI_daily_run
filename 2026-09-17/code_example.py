"""
How an agent decides a web page is safe to read.

Implements the two-phase URL approval an agent needs before it fetches a page
and before that page's text enters the model's context: pattern derivation,
the credential-in-host trust gate, and separate request/response checks.

`UrlApprovalPolicy` is the part to lift. Point it at your own allowlist and
call it on both sides of your fetch.

Run: python3 code_example.py
"""
# REQUIRES: none (standard library only)

import fnmatch
from urllib.parse import urlsplit, urlunsplit

# ---------------------------------------------------------------- knobs ----
# Flip this to True to see what a single bare `*` does to every check below.
ALLOW_EVERYTHING = False

ALLOWLIST = {
    # specific rules first: the lookup takes the FIRST match with a value set,
    # which is settings-file order, not most-specific-first
    "https://docs.python.org": True,
    "*.mycompany.com": {"approveRequest": True, "approveResponse": False},
    "https://github.com": {"approveRequest": True, "approveResponse": False},
}


# ------------------------------------------------------ the liftable core ----
def is_url_safe_for_trust(url: str) -> bool:
    """A URL may be pattern-matched only if it has a host and that host has no
    credentials. `https://github.com@evil.com/` really goes to evil.com, so it
    is excluded from matching entirely and only a bare `*` can approve it."""
    host = urlsplit(url).netloc
    return len(host) > 0 and "@" not in host


def extract_patterns(url: str) -> list:
    """Derive approval patterns, most specific first. Never yields `*.com`."""
    if not is_url_safe_for_trust(url):
        return []
    parts = urlsplit(url)
    scheme, host, path = parts.scheme, parts.netloc, parts.path
    out = []

    def add(p):
        p = p.rstrip("/")
        if p and p not in out:
            out.append(p)

    add(urlunsplit((scheme, host, path, "", "")))   # full URL, query dropped
    add(urlunsplit((scheme, host, "", "", "")))     # domain only

    labels = host.split(".")
    is_ipv4 = len(labels) == 4 and all(s.isdigit() for s in labels)
    is_ipv6 = ":" in host
    # wildcards only when there are real subdomains, so `*.com` is unreachable
    if not (is_ipv4 or is_ipv6) and len(labels) > 2:
        for i in range(len(labels) - 2):
            add(urlunsplit((scheme, "*." + ".".join(labels[i + 1:]), "", "", "")))

    segments = [s for s in path.split("/") if s]
    for i in range(len(segments) - 1, -1, -1):        # walk the path back up
        add(urlunsplit((scheme, host, "/" + "/".join(segments[:i]), "", "")))
    return out


class UrlApprovalPolicy:
    """Two-phase approval. `check_request` gates the fetch; the response side
    gates whether the fetched text is allowed into the model's context."""

    def __init__(self, allowlist: dict):
        self.allowlist = allowlist

    def _value(self, settings, check_request: bool):
        if isinstance(settings, bool):
            return settings
        return settings.get("approveRequest" if check_request else "approveResponse")

    def is_approved(self, url: str, check_request: bool) -> bool:
        if not is_url_safe_for_trust(url):
            # only the bare wildcard reaches a URL carrying credentials
            v = self._value(self.allowlist.get("*", False), check_request)
            return bool(v)
        target = urlunsplit(urlsplit(url)[:3] + ("", ""))
        for pattern, settings in self.allowlist.items():   # first match wins
            if pattern == "*" or fnmatch.fnmatch(target, pattern + "*"):
                v = self._value(settings, check_request)
                if v is not None:
                    return v
        return False

    def approve_call(self, urls: list, check_request: bool) -> bool:
        """A tool call is auto-approved only when EVERY url in it is approved.
        Per-call rather than per-url is what stops a batch smuggling one host."""
        return all(self.is_approved(u, check_request) for u in urls)


# ------------------------------------------------------------------ demo ----
CASES = [
    ("https://docs.python.org/3/library/asyncio.html", "your own docs bookmark"),
    ("https://wiki.mycompany.com/onboarding?token=s3cr3t", "internal wiki, with a token"),
    ("https://github.com/microsoft/vscode/issues/1", "issue text strangers wrote"),
    ("https://github.com@evil.com/pwn", "looks like github, goes to evil.com"),
    ("https://blog.unknown.dev/post", "never approved anything here"),
]


def main():
    allowlist = dict(ALLOWLIST)
    if ALLOW_EVERYTHING:
        allowlist["*"] = True

    policy = UrlApprovalPolicy(allowlist)
    print(f"allowlist has {len(allowlist)} entries"
          f"{'  (including a bare *)' if ALLOW_EVERYTHING else ''}\n")

    print(f"{'url':<52}{'fetch?':>8}{'into context?':>15}")
    print("-" * 75)
    for url, why in CASES:
        req = policy.is_approved(url, check_request=True)
        res = policy.is_approved(url, check_request=False)
        print(f"{url[:50]:<52}{('auto' if req else 'ASK'):>8}{('auto' if res else 'ASK'):>15}")
        print(f"  {why}")
    print()

    u = "https://docs.corp.example.com/api/v2/auth?k=1"
    print(f"patterns offered when you approve {u}")
    for i, p in enumerate(extract_patterns(u)):
        print(f"  {i + 1}. {p}" + ("   <- top 2 shown in the picker" if i == 1 else ""))
    print("  note: the query string is gone, and no pattern is ever *.com\n")

    evil = "https://github.com@evil.com/pwn"
    print(f"patterns for {evil}: {extract_patterns(evil) or 'none - excluded from matching'}")
    print(f"  approved for context? {policy.is_approved(evil, False)}"
          f"   (only a bare * can ever approve it)\n")

    batch = ["https://docs.python.org/3/", "https://blog.unknown.dev/post"]
    print(f"one call fetching {len(batch)} urls, one of them unapproved:")
    print(f"  every url approved? {policy.approve_call(batch, check_request=True)}"
          "  -> the whole call stops, not just the unknown url")


if __name__ == "__main__":
    main()
