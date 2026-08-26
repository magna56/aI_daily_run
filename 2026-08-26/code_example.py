#!/usr/bin/env python3
"""
Same 3 candidate findings, reported two shapes: prose (a terminal reply)
and the typed shape ReportFindings uses (file/line, failure_scenario,
category, verdict) -- only one of them a CI script can act on without
reading a sentence. verify() checks each against real source text before
it earns a verdict, filtering the false positive rather than downgrading
it, then re-reports fixed/skipped/no_change_needed after a fix.

Run:  python3 code_example.py
"""

import json
from dataclasses import dataclass

# Two files with real bugs, as the review sees them. Edit to try your own
# false positive / real bug pair.
REPO_SOURCE = {
    "src/auth/session.ts": (
        "async function refreshToken(session) {\n"
        "  const next = await issueToken(session.userId);\n"
        "  session.token = next;  // logout() can null session mid-await, above\n"
        "}\n"
    ),
    "src/auth/expiry.ts": (
        "function parseExpiry(raw) {\n"
        "  const n = parseInt(raw, 10);\n"
        "  if (Number.isNaN(n)) return 0;  // silently treats bad input as expired-now\n"
        "  return n;\n"
        "}\n"
    ),
}

@dataclass
class Finding:
    file: str
    summary: str
    failure_scenario: str          # concrete inputs -> wrong output, never a guess
    line: int | None = None
    category: str = "correctness"  # "correctness"->normal/Important, "style"->nit
    verdict: str | None = None     # set by verify(), never by the finder
    outcome: str | None = None     # set on re-report: fixed|skipped|no_change_needed

CANDIDATES = [
    Finding(
        file="src/auth/session.ts", line=142,
        summary="Token refresh races with logout, leaving stale sessions active",
        failure_scenario="logout() nulls session between issueToken() returning and "
                          "session.token = next landing; the stale token is then used",
    ),
    Finding(
        file="src/auth/expiry.ts", line=88, category="style",
        summary="parseExpiry silently returns 0 on malformed input",
        failure_scenario="parseExpiry('not-a-number') returns 0 instead of raising, "
                          "so a corrupt expiry field is read as 'already expired'",
    ),
    Finding(  # false positive: claims something the source doesn't do
        file="src/auth/session.ts", line=142,
        summary="Raw session.userId is interpolated into a SQL query without escaping",
        failure_scenario="a userId containing a quote character breaks out of the "
                          "query string and injects arbitrary SQL",
    ),
]

def _text_supports(f: Finding, repo_source: dict[str, str]) -> str | None:
    """None = source contradicts the claim (false positive, filtered out).
    'weak' = plausible but the exact mechanism isn't visible in this slice.
    'strong' = the source literally shows the failure mechanism."""
    src = repo_source.get(f.file, "")
    if not src:
        return None
    if "sql" in f.summary.lower() and "SELECT" not in src and "query" not in src.lower():
        return None                      # claims SQL; there is no query in this file at all
    if "race" in f.summary.lower() and "acquireLock" not in src and "await" in src:
        return "strong"                  # the actual unguarded-await pattern is right there
    if "malformed" in f.failure_scenario.lower() and "NaN" in src:
        return "strong"
    return "weak"

def verify(candidates: list[Finding], repo_source: dict[str, str]) -> list[Finding]:
    """Only CONFIRMED or PLAUSIBLE survive -- same two verdicts ReportFindings
    uses. A claim the source flatly contradicts is dropped, not demoted; an
    empty result is a valid, checkable report, not a missing one."""
    kept = []
    for f in candidates:
        support = _text_supports(f, repo_source)
        if support is None:
            continue                     # false positive: filtered, not kept
        f.verdict = "CONFIRMED" if support == "strong" else "PLAUSIBLE"
        kept.append(f)
    return sorted(kept, key=lambda f: {"CONFIRMED": 0, "PLAUSIBLE": 1}[f.verdict])

def render_prose(findings: list[Finding]) -> str:
    """What a terminal /code-review reply looks like: one paragraph."""
    if not findings:
        return "No issues found."
    parts = [f"{f.summary.rstrip('.')} at {f.file}:{f.line}." for f in findings]
    return " Also, ".join(parts).replace("Also, ", "Also, ", 1)

def render_typed(findings: list[Finding]) -> str:
    """What a host app asking for ReportFindings gets: a checkable list."""
    if not findings:
        return "[] -- nothing survived verification"
    lines = []
    for f in findings:
        outcome = f" outcome={f.outcome}" if f.outcome else ""
        lines.append(f"  [{f.verdict:9}] {f.file}:{f.line}  {f.summary}{outcome}")
    return "\n".join(lines)

def ci_gate_line(findings: list[Finding]) -> str:
    """The same embeddable line the real check run writes -- see docs:
    gh api ... --jq '.output.text | split("bughunter-severity: ")[1] ...'"""
    counts = {"normal": 0, "nit": 0, "pre_existing": 0}
    for f in findings:
        counts["normal" if f.category != "style" else "nit"] += 1
    return f"bughunter-severity: {json.dumps(counts)} -->"

def should_block_merge(findings: list[Finding]) -> bool:
    return any(f.verdict == "CONFIRMED" and f.category != "style" for f in findings)

def main():
    confirmed = verify(CANDIDATES, REPO_SOURCE)
    rejected = len(CANDIDATES) - len(confirmed)
    print(f"{len(confirmed)} of {len(CANDIDATES)} survived verify(); "
          f"{rejected} filtered out (no source support)\n")

    print("--- prose shape (what a terminal reply looks like) ---")
    print(render_prose(confirmed))
    print("\n--- typed shape (what ReportFindings-style output looks like) ---")
    print(render_typed(confirmed))
    print("\n--- CI-parseable line (embedded in the real check run's output.text) ---")
    print(ci_gate_line(confirmed))
    print(f"should_block_merge() -> {should_block_merge(confirmed)}")

    print("\nNow the author fixes the race condition and asks for a re-review.")
    FIXED_SOURCE = dict(REPO_SOURCE)
    FIXED_SOURCE["src/auth/session.ts"] = (
        "const lock = await acquireLock(session.userId); ... lock.release();"
    )
    for f in confirmed:
        if "race" in f.summary.lower():
            f.outcome = "fixed" if "acquireLock" in FIXED_SOURCE[f.file] else "skipped"
        else:
            f.outcome = "no_change_needed"

    print("\n--- typed shape, re-reported after the fix ---")
    print(render_typed(confirmed))

if __name__ == "__main__":
    main()
