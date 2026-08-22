"""
Blast-Radius Gating for Agent-Driven Diffs
============================================
Demonstrates the practice described in topic.md: instead of gating merges on
"who wrote this" or "how many lines changed", score each diff by how much it
crosses architectural boundaries (modules, public interfaces, ownership,
symbol fan-in) and only require a human "explain-back" checkpoint when that
score is high. Everything below threshold fast-tracks.

No dependencies — pure stdlib. Run with:
    python3 code_example.py
"""

from dataclasses import dataclass, field
from collections import defaultdict

# ---------------------------------------------------------------------------
# 1. A tiny synthetic codebase: modules, symbols, ownership, and a call graph
#    (fan-in = how many OTHER modules' symbols call into this symbol)
# ---------------------------------------------------------------------------

OWNERS = {
    "billing": "team-payments",
    "billing.invoice_api": "team-payments",
    "storage": "team-platform",
    "storage.blob_client": "team-platform",
    "storage.schema": "team-platform",
    "notifications": "team-comms",
}

# symbol -> module it lives in
SYMBOL_MODULE = {
    "Invoice.total": "billing",
    "InvoiceAPI.charge": "billing.invoice_api",
    "BlobClient.put": "storage.blob_client",
    "BlobClient.get": "storage.blob_client",
    "StorageSchema.RecordV2": "storage.schema",
    "Notifier.send": "notifications",
}

# who calls whom, across the whole (simulated) codebase -- used to compute fan-in
CALL_GRAPH = {
    "InvoiceAPI.charge": ["BlobClient.put", "Notifier.send"],
    "Invoice.total": ["StorageSchema.RecordV2"],
    "ReportingJob.run": ["BlobClient.get", "StorageSchema.RecordV2"],
    "AuditJob.run": ["StorageSchema.RecordV2"],
    "ReconciliationJob.run": ["BlobClient.get"],
}

PUBLIC_SYMBOLS = {"InvoiceAPI.charge", "BlobClient.put", "BlobClient.get", "StorageSchema.RecordV2"}


def fan_in(symbol: str) -> int:
    """Count distinct callers of `symbol` across the call graph."""
    callers = {caller for caller, callees in CALL_GRAPH.items() if symbol in callees}
    return len(callers)


# ---------------------------------------------------------------------------
# 2. A diff = the symbols an agent touched, plus which ones changed *shape*
#    (signature/schema, not just body) -- shape changes are what break callers.
# ---------------------------------------------------------------------------

@dataclass
class Diff:
    name: str
    author: str                      # "agent" or a human handle
    touched_symbols: list = field(default_factory=list)
    shape_changed: set = field(default_factory=set)  # subset of touched_symbols


DIFFS = [
    Diff(
        name="PR-4821: retry backoff tuning",
        author="agent",
        touched_symbols=["InvoiceAPI.charge"],
        shape_changed=set(),  # internal-only change, no signature/schema touch
    ),
    Diff(
        name="PR-4822: add checksum field to storage record",
        author="agent",
        touched_symbols=["StorageSchema.RecordV2", "BlobClient.put", "BlobClient.get"],
        shape_changed={"StorageSchema.RecordV2"},
    ),
    Diff(
        name="PR-4823: swap blob client for streaming charge flow",
        author="agent",
        touched_symbols=["InvoiceAPI.charge", "BlobClient.put", "Notifier.send"],
        shape_changed={"BlobClient.put"},
    ),
    Diff(
        name="PR-4824: fix notification typo",
        author="agent",
        touched_symbols=["Notifier.send"],
        shape_changed=set(),
    ),
]

# ---------------------------------------------------------------------------
# 3. Blast-radius scoring
# ---------------------------------------------------------------------------

WEIGHTS = {
    "cross_module": 2,      # touches symbols in >1 module
    "cross_owner": 3,       # touches symbols owned by >1 team
    "public_shape_change": 4,   # changes the *shape* of a public symbol
    "fan_in": 1,            # per distinct external caller of a shape-changed symbol
}
GATE_THRESHOLD = 6


def score_diff(diff: Diff) -> dict:
    modules = {SYMBOL_MODULE[s] for s in diff.touched_symbols}
    owners = {OWNERS[m] for m in modules}

    reasons = []
    score = 0

    if len(modules) > 1:
        score += WEIGHTS["cross_module"]
        reasons.append(f"crosses {len(modules)} modules ({', '.join(sorted(modules))})")

    if len(owners) > 1:
        score += WEIGHTS["cross_owner"]
        reasons.append(f"crosses {len(owners)} ownership boundaries ({', '.join(sorted(owners))})")

    public_shape_changes = diff.shape_changed & PUBLIC_SYMBOLS
    for sym in public_shape_changes:
        score += WEIGHTS["public_shape_change"]
        callers = fan_in(sym)
        score += WEIGHTS["fan_in"] * callers
        reasons.append(f"changes shape of public symbol '{sym}' (fan-in={callers} external callers)")

    return {"score": score, "reasons": reasons, "modules": modules, "owners": owners}


def gate(diff: Diff) -> dict:
    result = score_diff(diff)
    result["requires_explain_back"] = result["score"] >= GATE_THRESHOLD
    return result


# ---------------------------------------------------------------------------
# 4. Run the gate over all diffs and report
# ---------------------------------------------------------------------------

def main():
    print("Blast-Radius Gate — threshold = %d\n" % GATE_THRESHOLD)
    fast_tracked, sync_required = [], []

    for diff in DIFFS:
        result = gate(diff)
        verdict = "SYNC CHECKPOINT REQUIRED" if result["requires_explain_back"] else "fast-track (agent+CI merge)"
        (sync_required if result["requires_explain_back"] else fast_tracked).append(diff.name)

        print(f"{diff.name}  [author={diff.author}]")
        print(f"  score = {result['score']}  ->  {verdict}")
        if result["reasons"]:
            for r in result["reasons"]:
                print(f"    - {r}")
        else:
            print("    - single-module, no public shape change")
        if result["requires_explain_back"]:
            print("  >> ACTION: a human must write a 2-3 sentence explain-back before merge:")
            print("     'What invariant changed, and why is it still safe for existing callers?'")
        print()

    print("=" * 60)
    print(f"Fast-tracked ({len(fast_tracked)}): {fast_tracked}")
    print(f"Sync required ({len(sync_required)}): {sync_required}")
    print()
    print("Note what got flagged: not the biggest diff, and not by author identity —")
    print("PR-4822 (3 lines conceptually, one field) trips the gate because it reshapes")
    print("a public schema with 3 external callers; PR-4823 touches 3 modules across")
    print("2 teams. PR-4821 is agent-authored AND behavior-changing but stays internal")
    print("to one module, so it fast-tracks — friction is spent only where it buys sync.")


if __name__ == "__main__":
    main()
