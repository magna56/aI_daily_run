# hud-lite — the pipeline, in ~700 lines of stdlib Python

A working implementation of the mechanism described in
[`../research/02-architecture.md`](../research/02-architecture.md):

```
hook (auto-instrument)  ->  aggregate + forensics  ->  issues  ->  MCP  ->  agent  ->  GitHub PR
```

No dependencies. No `pip install`. Python 3.8+.

This exists because the interesting question about Hud is not *what does the marketing say* but
*what has to be true for this to work at all* — and the fastest way to find that out is to build
it. Several of the design claims in the research only became legible after implementing them; two
of them changed a conclusion.

## Run it

```bash
cd prototype

python3 demo_app.py                                              # 1. replay traffic through the sensor
python3 -m hud_lite.mcp_server --data .hud-demo/runtime.json --demo   # 2. see what an agent sees
python3 -m unittest test_prototype -v                            # 3. 18 self-checks
```

## What you get

Step 1 runs a small checkout service 250 times under the sensor. One tenant, `initech`, was
configured through a legacy admin panel that writes `discount_bps` as a **string** instead of an
int. It is 5% of traffic. Nothing in the repo looks wrong and no test catches it.

Step 2 prints the four things the agent would call:

```
1. list_issues()
  [high    ] EXC-78aafbd4                    TypeError in demo_app.py:apply_discount
  [high    ] RATE-demo_app.py-apply_discount demo_app.py:apply_discount fails 8.4% of the time (21/250)
  [medium  ] PERF-demo_app.py-checkout       demo_app.py:checkout averages 32.3ms over 250 calls
  [medium  ] PERF-...build_recommendations   demo_app.py:build_recommendations averages 34.5ms over 229 calls

2. get_issue('EXC-78aafbd4')   -- forensics from the moment of failure
  TypeError: unsupported operand type(s) for //: 'str' and 'int'  (seen 21 times)
    demo_app.py:43  in demo_app.py:apply_discount
      discount = price_cents * config["discount_bps"] // 10000
        price_cents    = 53452
        config         = {'tenant': 'initech', 'currency': 'USD', 'discount_bps': '150'}
```

**That last line is the whole product.** Not the stack trace — the *value*. `'150'` in quotes.
An agent reading the repo sees `config["discount_bps"]` and has no way to know it is sometimes a
string. An agent reading this fixes it in one pass and knows which tenant to check.

Step 2 then prints the generated **Prompt to Fix**, which ends by handing the PR to GitHub MCP.

## Wire it into a real agent

```bash
claude mcp add hud-lite -- python3 -m hud_lite.mcp_server \
  --data /absolute/path/to/prototype/.hud-demo/runtime.json
```

Then, with the GitHub MCP server also connected, ask your agent:
*"Call list_issues, then get_fix_prompt on the top issue, and follow it."*
It will investigate through the sensor's tools and open a PR. That is the one click.

## The five tools

| Tool | Returns | Why an agent needs it |
|---|---|---|
| `list_issues` | Detected problems, most severe first | Entry point; without it the agent has a data dump, not a task |
| `get_issue` | Full forensics: frames, source lines, **local variable values** | The part a log file and a repo checkout cannot give you |
| `get_function_stats` | Calls, mean/max duration, error rate | Distinguishes always-broken from rarely-broken — different fixes |
| `get_call_graph` | Real callers and callees with production counts | Blast radius. Grep finds callers; this finds the ones that *execute* |
| `get_fix_prompt` | The ready-to-run instruction | The "one click" |

## Files

| File | What it demonstrates |
|---|---|
| `hud_lite/hook.py` | Auto-instrumentation: app-code-only filtering, memoized per-file decisions, incremental duration sampling, **unsampled** exception capture with locals |
| `hud_lite/store.py` | Aggregation (O(functions), not O(requests)), secret redaction, crash fingerprinting |
| `hud_lite/issues.py` | Telemetry → a short list of named problems, ranked for triage |
| `hud_lite/prompts.py` | Prompt to Fix — MCP-referencing rather than context-inlining, and why |
| `hud_lite/mcp_server.py` | JSON-RPC 2.0 over stdio; the five tools |
| `demo_app.py` | A bug that is invisible in source and obvious at runtime |
| `test_prototype.py` | 18 checks, including a full MCP handshake |

## Three things building it actually taught

**1. Unsampled exceptions are not a nice-to-have, they are the product.**
Everything else in the sensor can be sampled aggressively — and is. Exceptions cannot be, because
the crash you dropped is the crash the agent needed. Once you see that asymmetry in code, Hud's
"forensics at the moment of failure" stops being a slogan and becomes the one constraint the
architecture is built around.

**2. Filtering is the whole performance story.**
The difference between plausible overhead and unusable overhead is deciding *cheaply* whether a
frame is yours. Memoizing that per file turns the hot path into one dict lookup
(`hook.py:_resolve`). Hud's stated exclusion of `node_modules` and `site-packages` is not a
convenience feature — it is the thing that makes 1–2% arithmetically possible.

**3. Ranking issues is harder than detecting them, and the naive version is wrong.**
The first version of `issues.detect` sorted by severity then by count, and a merely-slow function
outranked a live crash — because `count` means *failures* for an exception and *invocations* for a
latency outlier, and comparing them is meaningless. A test caught it (`issues.py` now ranks by kind
before count). Any real version of this product has the same trap, and getting it wrong means the
agent confidently fixes the wrong thing first.

## What this is not

Honest scope, so nobody mistakes this for a clone:

- `sys.setprofile` is used because it is stdlib and legible. It is **slower** than what a real
  sensor does (import-time rewriting, or eBPF — which is what Hud's "Runtime Internals" hiring
  points at). Do not benchmark this and conclude anything about Hud's 1–2% claim.
- In-memory store, JSON snapshot on exit. Hud streams to ClickHouse Cloud continuously.
- No deploy correlation, no rollback, no baseline-versus-current regression detection.
- Python only. Hud ships Node/TS, Python and Java.
- The issue thresholds are constants. Real detection is statistical.
