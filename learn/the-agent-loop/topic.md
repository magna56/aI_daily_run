# Observe / Think / Act; Tool Names Are the Contract

**Category**: Building Agents & MCP
**Tags**: agents, mcp
**Date**: 2026-08-23
**Level**: Start here
**For**: Building agents
**Hook**: An agent is a loop that looks, decides, and calls a named tool. The name is the API.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5
Imagine a kitchen where every drawer has a label: "knife," "pot," "oven." You look at the counter (observe), decide what to do (think), and open the drawer whose label matches (act). You do not invent a new drawer in the moment. If someone peels the "knife" label off and writes "blade," a cook who only ever learned "knife" will stand there confused — or open the wrong drawer and jam the handle. The labels *are* the kitchen. The cook is not magic. They are a loop: look, decide, open.

## The Problem
"Agent" gets used to mean a new kind of intelligence. Under the API it is a while-loop: take the latest observations, ask the model what to do next, if the answer is a tool call then run that tool and append the result, repeat. The loop is a few dozen lines. What actually breaks in production is the *contract* — the tool names and JSON schemas the model was trained to emit versus the ones your harness accepts. People spend weeks on orchestration graphs and skip the part where renaming `edit_file` silently tanks the success rate.

## For a Software Engineer
This is **a request loop over a typed API**. Observe is reading the last responses. Think is one model call. Act is dispatch on a function name plus JSON arguments. You have written this as a game loop, a REPL, or an HTTP worker: poll, decide, call, append.

The tool list you send is not documentation. It is the **surface area of the API** the model can call. Names matter the way route paths matter. Models are trained — sometimes with reinforcement learning on a vendor's own coding agent — to emit `edit_file(path, old_string, new_string)` or `apply_patch` with a unified diff. If your schema uses `mutate_buffer` with a different shape, two things happen: the model is worse at filling it, and it may *invent* fields from the schema it was trained on. The daily case study on 2026-07-05 (*Building Coding Agents from Scratch — and the Tool Schema Trap*) is that failure in the wild: newer Claude models injected extra keys into a third-party edit array because Claude Code's schema had leaked into their reflexes.

MCP (Model Context Protocol) is **HTTP for tools**. A server exposes `tools/list` and `tools/call` over JSON-RPC, the way a web service exposes `GET /routes` and `POST /routes/:name`. Any harness that speaks MCP can use any server. The protocol is not the loop. The loop still observe / think / act; MCP is how act is transported across a process boundary.

Monday-morning action: print every tool name your agent advertises. If you are not matching a well-known schema for edits and file reads, treat that as an API change — and expect a compatibility tax.

## What This Means for You
**When this matters**: you are writing an agent loop, wrapping tools for a coding model, or adding an MCP server so Cursor or Claude Code can call your system.

**How it affects you**: a clever planner with a sloppy schema will lose to a boring loop with names the model already knows. A hundred MCP tools stuffed into the prefix make every turn more expensive before the user has asked a question. A renamed tool is a broken contract, not a refactor.

**What to do about it**: keep the loop visible (one function, a max-iteration cap, tool results appended as observations). Name tools after the verbs models already emit (`read_file`, `edit_file`, or the provider's `apply_patch`). When you cannot match, write a thin adapter. Use MCP to *expose* tools, not to replace the loop. Then read 2026-07-05 for the schema-trap details.

## What It Is
An agent is this loop:

1. **Observe.** The harness collects the user message and any tool results sitting on the transcript.
2. **Think.** It sends the full prefix to the model. The model returns either text (stop) or one or more tool calls: a name plus arguments that should match a JSON Schema.
3. **Act.** The harness looks up the name, validates arguments, runs the function (or denies it), and appends the result as the next observation.
4. Repeat until the model stops calling tools, the user interrupts, or a turn cap fires.

That is the architecture. Planner/executor graphs, multi-agent swarms, and "cognitive architectures" are extra loops or extra prefixes. They still reduce to observe / think / act.

A **tool schema** is the contract: `name`, `description`, and a JSON Schema for `parameters`. The model never imports your Python. It fills in JSON that claims to match that schema. Your dispatcher is a `switch` on `name`.

**MCP** standardizes discovery and invocation. A client (the harness) connects to a server, lists tools, and calls one by name. Resources and prompts are sibling surfaces. For this lesson, treat MCP as "tools over a socket" — the HTTP analogy holds: list is GET, call is POST, the schema is the OpenAPI operation.

## Why It Matters
Simon Willison's `llm-coding-agent` (~500 lines) made the loop boring on purpose. The interesting software is the tool implementations (sandbox paths, approval gates, diffs) and the schemas those tools advertise. Once the loop is commodity, competition moves to the contract: whose names the frontier models have practiced, and whether your server speaks a protocol other harnesses already connect to.

MCP matters because it turns "I wrote a Python callback" into "any client can call this." It does not make the model better at your names. If anything it makes the prefix problem worse: each connected server dumps its catalog at the front of every turn. The protocol and the loop are orthogonal — you can have a perfect MCP server and a loop that never validates arguments.

Keep the loop in one function you can print. When someone asks "why did it call `execute_command` twice?", the answer should be a log line: observe, think (this JSON), act (this result), observe. If that trace lives inside a framework callback maze, you will debug the framework. The 2026-07-05 `llm-coding-agent` write-up is ~500 lines because the authors refused to hide the cycle.

## Key Technical Details
**Background first.** A *tool call* is structured output: the model emits a name and a JSON object instead of (or before) assistant prose. A *schema* is the JSON Schema that object should satisfy. The *dispatcher* is your code that maps name → function. *MCP* is a JSON-RPC protocol whose tool methods are `tools/list` and `tools/call`.

- **The loop is the program.** Cap iterations. Log each think/act pair. If you cannot draw the cycle on a whiteboard, you do not have an agent you can debug — you have a framework.
- **Names are the API.** Prefer `read_file`, `write_file`, `edit_file` (exact-string replace), `execute_command` — the set `llm-coding-agent` and Claude Code both speak. OpenAI-oriented stacks may want `apply_patch`. Adapters beat unique names.
- **Descriptions steer, schemas constrain.** A vague description gets the tool called for the wrong job. A loose schema (`additionalProperties` implicit, missing `required`) lets the model invent keys. Validate *before* execution; treat extras as errors, not as "helpful."
- **The schema trap is real.** Models reinforced on one vendor's tools leak that vendor's field names into yours. The 2026-07-05 write-up is the case study: extra keys in a nested `edits[]` array that the third-party schema never defined. Matching the trained shape is compatibility, not taste.
- **MCP is transport plus discovery.** `tools/list` returns the catalog the harness will put in the prefix. `tools/call` is act. HTTP-shaped thinking helps: do not expose a hundred routes if the client pays for the whole OpenAPI document on every request. Progressive discovery (few tools first) is the protocol's answer; your server still has to offer a small surface.
- **Act is where policy lives.** Read-only tools can auto-approve. Mutations need a gate. Path traversal (`..`, absolute paths) is a dispatcher bug, not a model bug. The loop should not trust the model to sandbox itself.
- **Cap the cycle.** A missing stop condition is an infinite `think` → `act` → `observe` on a confused model. `llm-coding-agent` exposes a chain limit; you want the same integer, logged when it fires. "The agent ran away" is an uncapped loop, not a personality.
- **Parallel tool calls are still this loop.** A think step may emit three names. Act runs them (or a subset), observe appends three results, think runs again. Do not invent a second architecture for "it called two tools." Validate each name independently — one miss should not silently drop the others.

## How It Connects to What You Know
This is a REPL with side effects, or a message worker that calls other services by name. MCP is the part that looks like microservices: a standard request/response so the IDE is not hard-wired to your functions. The 2026-07-05 session is the next page — the loop is easy, the schema is where models have been silently trained onto one vendor's kitchen labels. This page is the kitchen. That page is what happens when the labels do not match the cook.

## Try It Yourself
`code_example.py` runs a fake model through observe / think / act. The trained policy knows `edit_file`. Point the same policy at a matching schema and the edit lands. Rename the tool to `mutate_buffer` and the call misses the dispatcher. A third run speaks MCP-shaped `list` / `call`. Pure Python, no API key, no network.

## Glossary
- **Agent loop** — observe (inputs and tool results), think (one model call), act (run a named tool), repeat.
- **Observe** — collect the latest user text and tool results onto the transcript.
- **Think** — the model call that produces text or tool calls.
- **Act** — the harness executing a named tool and appending the result.
- **Tool schema** — name, description, and JSON Schema for arguments. The contract the model fills in.
- **Dispatcher** — code that maps a tool name to a function and validates arguments.
- **JSON-RPC** — the request/response format MCP uses (method name plus params, id for correlation).
- **MCP** (Model Context Protocol) — an open protocol so a harness can list and call tools on another process. HTTP for tools.
- **`tools/list` / `tools/call`** — MCP methods for discovery and invocation.
- **Schema trap** — a model trained on one tool shape emitting that shape against a different schema.
