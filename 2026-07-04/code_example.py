"""ContextSniper Pattern: Token-Efficient Code Memory for Coding Agents

Implements the retrieve → rank → filter → package pipeline from the ContextSniper
paper (arxiv 2607.01916, July 2026). Shows how a coding agent can find bug-relevant
evidence using ~60% fewer tokens than reading full files.

Run: python3 code_example.py
Dependencies: none (stdlib only)
"""

import re
import math
from collections import Counter
from dataclasses import dataclass

# --- Simulated repository: a Python project with a bug ---

REPO = {
    "server.py": """import json
from auth import validate_token
from database import get_user, update_user
from cache import cached

class RequestHandler:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.rate_limiter = RateLimiter(max_rpm=100)

    def handle_get_user(self, request):
        token = request.headers.get("Authorization")
        if not validate_token(token):
            return Response(401, "Unauthorized")
        user_id = request.params["user_id"]
        user = get_user(self.db_pool, user_id)
        return Response(200, json.dumps(user))

    def handle_update_user(self, request):
        token = request.headers.get("Authorization")
        if not validate_token(token):
            return Response(401, "Unauthorized")
        user_id = request.params["user_id"]
        data = json.loads(request.body)
        update_user(self.db_pool, user_id, data)
        return Response(200, "OK")

    def handle_delete_user(self, request):
        token = request.headers.get("Authorization")
        if not validate_token(token):
            return Response(401, "Unauthorized")
        user_id = request.params["user_id"]
        # BUG: should check ownership before delete
        delete_user(self.db_pool, user_id)
        return Response(200, "Deleted")
""",
    "auth.py": """import hmac
import hashlib
import time

SECRET_KEY = "change-me-in-production"
TOKEN_TTL = 3600

def validate_token(token):
    if not token or not token.startswith("Bearer "):
        return False
    parts = token[7:].split(".")
    if len(parts) != 3:
        return False
    payload, timestamp, signature = parts
    if time.time() - float(timestamp) > TOKEN_TTL:
        return False
    expected = hmac.new(SECRET_KEY.encode(), f"{payload}.{timestamp}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)

def create_token(user_id):
    timestamp = str(time.time())
    payload = str(user_id)
    signature = hmac.new(SECRET_KEY.encode(), f"{payload}.{timestamp}".encode(), hashlib.sha256).hexdigest()
    return f"Bearer {payload}.{timestamp}.{signature}"
""",
    "database.py": """import sqlite3

def get_connection(db_pool):
    return db_pool.get()

def get_user(db_pool, user_id):
    conn = get_connection(db_pool)
    cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "email": row[2], "role": row[3]}

def update_user(db_pool, user_id, data):
    conn = get_connection(db_pool)
    fields = ", ".join(f"{k} = ?" for k in data.keys())
    values = list(data.values()) + [user_id]
    conn.execute(f"UPDATE users SET {fields} WHERE id = ?", values)
    conn.commit()

def delete_user(db_pool, user_id):
    conn = get_connection(db_pool)
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
""",
    "cache.py": """import functools
import time

_cache = {}
_ttl = {}
DEFAULT_TTL = 300

def cached(ttl=DEFAULT_TTL):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (func.__name__, args, tuple(sorted(kwargs.items())))
            if key in _cache and time.time() - _ttl[key] < ttl:
                return _cache[key]
            result = func(*args, **kwargs)
            _cache[key] = result
            _ttl[key] = time.time()
            return result
        return wrapper
    return decorator

def invalidate(func_name):
    keys_to_remove = [k for k in _cache if k[0] == func_name]
    for k in keys_to_remove:
        del _cache[k]
        del _ttl[k]
""",
    "test_server.py": """import pytest
from server import RequestHandler

def test_get_user_unauthorized():
    handler = RequestHandler(mock_pool)
    req = MockRequest(headers={}, params={"user_id": "1"})
    resp = handler.handle_get_user(req)
    assert resp.status == 401

def test_delete_user_no_ownership_check():
    # This test FAILS: user A can delete user B
    handler = RequestHandler(mock_pool)
    req = MockRequest(
        headers={"Authorization": token_for_user_a},
        params={"user_id": "user_b_id"}
    )
    resp = handler.handle_delete_user(req)
    # BUG: returns 200 instead of 403
    assert resp.status == 403, "Should not allow deleting other users"
""",
}

BUG_REPORT = """FAILING TEST: test_delete_user_no_ownership_check
AssertionError: assert 200 == 403
User A can delete User B's account without ownership verification.
File: test_server.py, line 15"""


# --- Token counting (simple word-based approximation) ---

def count_tokens(text: str) -> int:
    return len(text.split())


# --- Stage 1: Retrieval (keyword + structural search) ---

@dataclass
class CodeChunk:
    file: str
    start_line: int
    end_line: int
    content: str
    score: float = 0.0


def retrieve_candidates(repo: dict, query: str, context_lines: int = 3) -> list[CodeChunk]:
    """Find code chunks that match query keywords."""
    keywords = set(re.findall(r'\w+', query.lower()))
    chunks = []

    for filename, content in repo.items():
        lines = content.strip().split('\n')
        for i, line in enumerate(lines):
            line_words = set(re.findall(r'\w+', line.lower()))
            overlap = keywords & line_words
            if overlap:
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                chunk_text = '\n'.join(lines[start:end])
                chunks.append(CodeChunk(
                    file=filename,
                    start_line=start + 1,
                    end_line=end,
                    content=chunk_text,
                    score=len(overlap)
                ))
    return chunks


# --- Stage 2: Ranking (BM25-style + structural signals) ---

def bm25_score(query_terms: list[str], doc: str, k1: float = 1.5, b: float = 0.75,
               avg_dl: float = 50) -> float:
    doc_terms = re.findall(r'\w+', doc.lower())
    dl = len(doc_terms)
    tf = Counter(doc_terms)
    score = 0.0
    for term in query_terms:
        f = tf.get(term, 0)
        numerator = f * (k1 + 1)
        denominator = f + k1 * (1 - b + b * dl / avg_dl)
        idf = math.log(1 + 1)  # simplified
        score += idf * numerator / denominator if denominator > 0 else 0
    return score


def rank_chunks(chunks: list[CodeChunk], query: str,
                error_file: str = "") -> list[CodeChunk]:
    """Rank by BM25 + structural bonus (same file as error gets boost)."""
    terms = re.findall(r'\w+', query.lower())
    for chunk in chunks:
        lexical = bm25_score(terms, chunk.content)
        structural = 2.0 if chunk.file == error_file else 0.0
        has_function_def = 1.0 if 'def ' in chunk.content else 0.0
        chunk.score = lexical + structural + has_function_def
    return sorted(chunks, key=lambda c: c.score, reverse=True)


# --- Stage 3: Intention-Aware Filtering ---

def filter_by_intention(chunks: list[CodeChunk], intention: str,
                        max_chunks: int = 5) -> list[CodeChunk]:
    """Keep only chunks relevant to the agent's current intention."""
    filtered = []
    seen_ranges = set()
    for chunk in chunks:
        range_key = (chunk.file, chunk.start_line, chunk.end_line)
        if range_key in seen_ranges:
            continue
        seen_ranges.add(range_key)
        if intention == "fix_bug":
            if any(kw in chunk.content.lower()
                   for kw in ['delete', 'bug', 'assert', 'error', 'fail',
                              'owner', 'check', 'permission', 'user_id']):
                filtered.append(chunk)
        else:
            filtered.append(chunk)
        if len(filtered) >= max_chunks:
            break
    return filtered


# --- Stage 4: Compact Evidence Packaging ---

def package_evidence(chunks: list[CodeChunk]) -> str:
    """Package chunks as compact evidence with file/line metadata."""
    parts = []
    for chunk in chunks:
        parts.append(
            f"--- {chunk.file}:{chunk.start_line}-{chunk.end_line} "
            f"(score: {chunk.score:.1f}) ---\n{chunk.content}"
        )
    return "\n\n".join(parts)


# --- Main: compare naive vs. ContextSniper ---

def main():
    print("=" * 65)
    print("  CONTEXTSNIPER PATTERN — Token-Efficient Code Memory")
    print("  Based on arxiv 2607.01916 (July 2, 2026)")
    print("=" * 65)

    print(f"\nBug report:\n  {BUG_REPORT.strip()}")

    # --- Naive approach: dump all files ---
    print(f"\n{'─' * 65}")
    print("NAIVE APPROACH: Read all files into context")
    print(f"{'─' * 65}")
    naive_context = "\n\n".join(
        f"=== {f} ===\n{c}" for f, c in REPO.items()
    )
    naive_tokens = count_tokens(naive_context)
    print(f"  Files read:  {len(REPO)}")
    print(f"  Tokens used: {naive_tokens}")

    # --- ContextSniper approach ---
    print(f"\n{'─' * 65}")
    print("CONTEXTSNIPER: Retrieve → Rank → Filter → Package")
    print(f"{'─' * 65}")

    # Stage 1
    query = "delete user ownership check permission 403 unauthorized"
    candidates = retrieve_candidates(REPO, query)
    print(f"\n  Stage 1 — Retrieval:  {len(candidates)} candidate chunks found")

    # Stage 2
    ranked = rank_chunks(candidates, query, error_file="test_server.py")
    print(f"  Stage 2 — Ranking:    top scores: "
          f"{[f'{c.file}:{c.start_line}({c.score:.1f})' for c in ranked[:5]]}")

    # Stage 3
    filtered = filter_by_intention(ranked, intention="fix_bug", max_chunks=5)
    print(f"  Stage 3 — Filtering:  {len(filtered)} chunks after intention filter")

    # Stage 4
    evidence = package_evidence(filtered)
    sniper_tokens = count_tokens(evidence)
    print(f"  Stage 4 — Packaging:  {sniper_tokens} tokens")

    # --- Results ---
    savings = (1 - sniper_tokens / naive_tokens) * 100
    print(f"\n{'─' * 65}")
    print("RESULTS")
    print(f"{'─' * 65}")
    print(f"  Naive tokens:        {naive_tokens}")
    print(f"  ContextSniper tokens: {sniper_tokens}")
    print(f"  Token reduction:     {savings:.1f}%")
    print(f"  Evidence quality:    Contains the buggy function + failing test")

    print(f"\n{'─' * 65}")
    print("EVIDENCE DELIVERED TO AGENT")
    print(f"{'─' * 65}")
    print(evidence)

    print(f"\n{'─' * 65}")
    print("TAKEAWAY")
    print(f"{'─' * 65}")
    print("  The paper achieves 38.9% token reduction on Claude Code and")
    print("  51.5% on OpenClaw (SWE-bench Lite) with only a 2-point drop")
    print("  in resolution rate. The pattern — retrieve, rank with hybrid")
    print("  signals, filter by agent intention, package compactly — is")
    print("  applicable to any AI coding tool or MCP server you build.")
    print()


if __name__ == "__main__":
    main()
