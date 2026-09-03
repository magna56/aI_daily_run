"""What a coding agent's prompt cache actually charges you.

Implements the prefix cache the API applies to every turn: a request is a list of
blocks, the server matches from the front, and everything from the first mismatch
onward is re-processed and written. Two things outside the prompt text -- the model
and the effort level -- are part of the cache key, which is why switching either
one re-reads content that did not change.

Run: python3 code_example.py

Change SWITCH_MODEL_AT_TURN and watch the session total move. That is the whole
article in one number.
"""

from collections import namedtuple

# --- knobs: edit these ---------------------------------------------------
SWITCH_MODEL_AT_TURN = 20    # None keeps one model all session
TTL = "1h"                   # "5m" or "1h" -- sets the cache-write multiplier
IDLE_GAP_SECONDS = 45        # how long you think between turns
TURNS = 40

# Claude Opus 5 list price, per million input tokens.
INPUT_PER_TOKEN = 5.00 / 1_000_000
READ_MULTIPLIER = 0.10                        # a cache read is ~10% of input
WRITE_MULTIPLIER = {"5m": 1.25, "1h": 2.00}   # a write costs more than input
TTL_SECONDS = {"5m": 300, "1h": 3600}

Block = namedtuple("Block", "name text tokens")


class PrefixCache:
    """The server side of prompt caching. Lift this to reason about your own runs.

    One entry per cache key. The key is not just the prompt: it carries the model
    and the effort level, so two otherwise identical requests on different models
    never see each other's entry.
    """

    def __init__(self, ttl="1h"):
        self.ttl = ttl
        self.entries = {}  # key -> (blocks, last_touched_seconds)

    def submit(self, key, blocks, now):
        """Return (read_tokens, write_tokens) for one request."""
        entry = self.entries.get(key)
        # The lifetime runs from the START of the request that last touched the
        # entry, so a long generation eats into the window before the next turn.
        if entry is not None and now - entry[1] > TTL_SECONDS[self.ttl]:
            entry = None
        cached = entry[0] if entry is not None else []

        matched = 0
        for old, new in zip(cached, blocks):
            if old.text != new.text:
                break  # the match is exact -- nothing after this point counts
            matched += 1

        read = sum(b.tokens for b in blocks[:matched])
        write = sum(b.tokens for b in blocks[matched:])
        self.entries[key] = (list(blocks), now)
        return read, write

    def price(self, read, write):
        return (read * READ_MULTIPLIER + write * WRITE_MULTIPLIER[self.ttl]) * INPUT_PER_TOKEN


TURN_TOKENS = 7_000


def build_request(turn, tools="base"):
    """The three layers, stablest first.

    The conversation is one block per turn rather than one block overall, because
    that is what makes it cacheable: turn 40's request repeats turns 1-39 byte for
    byte and appends one new block at the end.
    """
    blocks = [
        Block("system prompt", f"instructions+tools:{tools}", 12_000),
        Block("project context", "CLAUDE.md+memory", 8_000),
    ]
    blocks += [Block(f"turn {i}", f"turn:{i}", TURN_TOKENS) for i in range(1, turn + 1)]
    return blocks


def run_session(switch_at, ttl, gap):
    cache = PrefixCache(ttl)
    model, effort, now, total, rebuilds = "opus-5", "high", 0.0, 0.0, 0
    for turn in range(1, TURNS + 1):
        if switch_at is not None and turn == switch_at:
            model = "sonnet-5"  # a different cache key: nothing carries over
        blocks = build_request(turn)
        read, write = cache.submit((model, effort), blocks, now)
        if turn > 1 and write > TURN_TOKENS:  # wrote more than the new turn
            rebuilds += 1
        total += cache.price(read, write)
        now += gap
    return total, rebuilds


def main():
    ctx = 300_000
    cache = PrefixCache(TTL)
    replay = cache.price(ctx, 0)
    rebuild = cache.price(0, ctx)

    print(f"One {ctx:,}-token context, {TTL} cache, Claude Opus 5 list price")
    print(f"  replayed from cache   ${replay:>6.2f}")
    print(f"  rebuilt from scratch  ${rebuild:>6.2f}   ({rebuild / replay:.0f}x)")

    print("\nWhat the multipliers do (relative to the uncached input rate)")
    print(f"  cache read            {READ_MULTIPLIER:.2f}x")
    for ttl, mult in WRITE_MULTIPLIER.items():
        n = 2 if ttl == "5m" else 3
        print(f"  cache write, {ttl:<3}      {mult:.2f}x   break-even at {n} requests")

    print(f"\nA {TURNS}-turn session, {IDLE_GAP_SECONDS}s between turns, {TTL} cache")
    clean, clean_rb = run_session(None, TTL, IDLE_GAP_SECONDS)
    dirty, dirty_rb = run_session(SWITCH_MODEL_AT_TURN, TTL, IDLE_GAP_SECONDS)
    print(f"  one model all session         ${clean:>6.2f}   {clean_rb} rebuild(s)")
    print(f"  /model at turn {SWITCH_MODEL_AT_TURN:<3}            ${dirty:>6.2f}   {dirty_rb} rebuild(s)")
    print(f"  cost of that one keystroke    ${dirty - clean:>6.2f}")

    print("\nThe same session, priced against how long you pause between turns")
    print(f"  {'gap':>7}   {'5m cache':>9}   {'1h cache':>9}   cheaper")
    for gap in (45, 240, 600, 3000):
        five, _ = run_session(None, "5m", gap)
        hour, _ = run_session(None, "1h", gap)
        winner = "5m" if five <= hour else "1h"
        label = f"{gap // 60}m{gap % 60:02d}s"
        print(f"  {label:>7}   ${five:>8.2f}   ${hour:>8.2f}   {winner}")
    print("\n  Under five minutes every turn refreshes the short entry, so the")
    print("  hour buys nothing but its doubled write price. Past it, the hour wins.")


if __name__ == "__main__":
    main()
