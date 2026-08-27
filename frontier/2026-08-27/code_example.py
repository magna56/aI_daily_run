"""
Why an agent's tool schemas never hit the prefix cache, and what makes them
cacheable. Implements the core idea from ReCache (arXiv:2608.19662, Fang, Wei,
Hu & Shen, 20 Aug 2026): give every tool schema *resource-local* positions
instead of global ones, and a tool's KV block becomes identical no matter where
it lands in the prompt.

The KV function here is a stand-in, not a transformer -- but it keeps the one
property that causes the real problem: a token's KV state depends on its
POSITION, so the same schema text at offset 300 and offset 40 are different
tensors and cannot be reused for each other.

Run: python3 code_example.py
"""
import random

# Turn this up and the prefix cache gets worse, not better: more tools means
# more ways to order them, and every ordering is a different global layout.
N_TOOLS = 8
N_REQUESTS = 200
TOOLS_PER_REQUEST = 4
SEED = 7

SYSTEM_PROMPT_TOKENS = 40  # the shared prefix every request starts with

# name -> how many tokens that tool's JSON schema costs
TOOLS = {
    "search_web":     52, "read_file":     38, "write_file":   44,
    "run_sql":        61, "send_email":    47, "list_dir":     29,
    "get_weather":    33, "create_ticket": 56,
}

def kv_state(tool: str, local_index: int, position: int) -> tuple:
    """Stand-in for one token's (K,V). The only property that matters here is
    that POSITION is part of the state -- which is exactly why a schema moved
    down the prompt cannot reuse the KV it had higher up."""
    return (tool, local_index, position)

# ---- The reusable core: a cache keyed on what actually identifies a block ----
class ResourceKVCache:
    """Caches one KV block per tool. The key deliberately excludes the tool's
    offset in the prompt -- that is the whole point. Lift this and swap
    kv_state() for your serving stack's real KV computation."""

    def __init__(self, resource_local_positions: bool):
        # False = today's behaviour: a block is only valid at the offset it was
        # built at, so the key must include that offset.
        self.resource_local = resource_local_positions
        self.store = {}
        self.hits = 0
        self.misses = 0

    def key(self, tool: str, offset: int):
        return tool if self.resource_local else (tool, offset)

    def block(self, tool: str, offset: int) -> list:
        k = self.key(tool, offset)
        if k in self.store:
            self.hits += 1
            return self.store[k]
        self.misses += 1
        # Resource-local: positions restart at 0 inside every tool block, so the
        # block is composition-invariant. Global: positions carry the offset in.
        base = 0 if self.resource_local else offset
        blk = [kv_state(tool, i, base + i) for i in range(TOOLS[tool])]
        self.store[k] = blk
        return blk

    def tokens_stored(self) -> int:
        return sum(len(b) for b in self.store.values())

def prefix_cache_reusable_tokens(prev: list, cur: list) -> int:
    """Standard prefix caching: reuse stops at the first tool that differs.
    Everything after it shifts position and must be recomputed."""
    reusable = SYSTEM_PROMPT_TOKENS
    for a, b in zip(prev, cur):
        if a != b:
            break
        reusable += TOOLS[a]
    return reusable

def main():
    rng = random.Random(SEED)
    requests = [rng.sample(list(TOOLS), TOOLS_PER_REQUEST) for _ in range(N_REQUESTS)]

    total_tool_tokens = sum(sum(TOOLS[t] for t in r) for r in requests)

    # --- Today: prefix caching over a dynamically composed tool list ---
    reused = 0
    prev = None
    for r in requests:
        if prev is not None:
            reused += prefix_cache_reusable_tokens(prev, r) - SYSTEM_PROMPT_TOKENS
        prev = r
    prefix_hit_rate = 100 * reused / total_tool_tokens

    # --- Same traffic, two cache designs ---
    global_cache = ResourceKVCache(resource_local_positions=False)
    local_cache = ResourceKVCache(resource_local_positions=True)
    for r in requests:
        offset = SYSTEM_PROMPT_TOKENS
        for tool in r:
            global_cache.block(tool, offset)
            local_cache.block(tool, offset)
            offset += TOOLS[tool]

    print(f"{N_REQUESTS} requests, {TOOLS_PER_REQUEST} of {N_TOOLS} tools each, "
          f"{total_tool_tokens} tool tokens sent in total\n")

    print("--- prefix caching (what you have today) ---")
    print(f"tool tokens reused: {prefix_hit_rate:.1f}%  "
          f"-- reuse stops at the first tool that moved\n")

    def report(name, c):
        n = c.hits + c.misses
        print(f"{name:<34}{100*c.hits/n:>6.1f}% hit   "
              f"{len(c.store):>4} blocks   {c.tokens_stored():>6} tokens stored")

    print("--- per-resource KV cache ---")
    report("global positions (cache per site)", global_cache)
    report("resource-local positions", local_cache)

    saved = 100 * (1 - local_cache.tokens_stored() / global_cache.tokens_stored())
    print(f"\nresource-local stores {saved:.1f}% fewer KV tokens than caching "
          f"each tool at each offset it appears at.")
    print(f"Blocks needed collapses to exactly one per tool: "
          f"{len(local_cache.store)} for {N_TOOLS} tools.")

if __name__ == "__main__":
    main()
