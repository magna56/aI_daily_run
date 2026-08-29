# How an Agent Calls a Tool That Takes Twenty Minutes

**Category**: Building Agents & MCP
**Tags**: mcp, reliability, production, latency
**Date**: 2026-08-29
**Level**: Building
**For**: Building agents
**Hook**: A tool call that runs for twenty minutes gets cut off somewhere in the middle, so the tool protocol now lets the server hand back a numbered ticket instead of an answer.
**Time to read**: ~8 minutes

## Explain Like I'm 5

You drop your shoes at the repair shop. The cobbler does not make you wait at the counter for three hours — he gives you a numbered ticket and says come back after lunch. If he needs to know whether you want black laces or brown, he writes the question on the ticket, and you answer it next time you stop by. If your phone dies and you come back tomorrow instead, the ticket still works. That number is the whole trick: it turns waiting into checking.

## The Problem

Write an agent tool that deploys a service or reindexes a corpus, and nothing between the agent and your server wants to hold a connection open for twelve minutes. The load balancer has an idle timeout. So does the reverse proxy, the client's HTTP library, and the phone network the user is on.

So people route around the protocol. The tool returns a string — `"started job 7f2a, call check_job to see if it finished"` — and now the *model* must remember to poll. Usually it does. Sometimes it reports the deploy succeeded, because the text said "started" and that was close enough.

And when the agent restarts halfway through, there is nothing to go back to. The work is still running on your server; the only pointer to it was a sentence in a conversation that no longer exists.

## How a Task Handle Replaces the Blocking Call

The Model Context Protocol — the JSON-RPC dialect agents use to call tools — shipped an extension for this: `io.modelcontextprotocol/tasks`, stable in its `2026-07-28` revision. Three methods, one new result shape. New to this? Start at AI basics → [The agent loop](#learn/the-agent-loop).

### The Two Result Shapes

A client opts in by naming the extension in the `_meta` of every request — per-request, because MCP no longer keeps a session. After that the **server** decides, call by call, whether a `tools/call` returns a normal `CallToolResult` or a handle:

```json
{"resultType": "task", "taskId": "786512e2-9e0d-44bd-8f29-789f320fe840",
 "status": "working", "statusMessage": "Deploy queued.",
 "ttlMs": 3600000, "pollIntervalMs": 5000}
```

There is no `deploy_async` beside `deploy`, and no flag on the call. One tool sometimes answers with a receipt, so `resultType` is the discriminator and every call site must read it.

### The Poll Loop

The client calls `tasks/get` with the id and honours `pollIntervalMs`; servers may rate-limit anyone faster. What makes this more than a retry loop is `ttlMs` — a deadline, not a hint. After it elapses the server may mark the task `failed` and delete it, so expiry is an outcome your client handles, not an edge case.

### Mid-Flight Input

When the job needs a human, the task turns `input_required` and `tasks/get` carries an `inputRequests` map: keys the server picked, values that are ordinary `elicitation/create` requests. You answer with `tasks/update` and an `inputResponses` map under the same keys. The request reappears on every poll until you answer, so deduplicate on the key or the user is asked the same question forty times.

### Failed Versus isError

`failed` means a JSON-RPC fault during execution. A tool that ran perfectly and returned a business error is `completed`, with `isError: true` inside `result`. Backwards, and your retry logic hammers a deploy that will never succeed.

## For a Software Engineer

This is `202 Accepted`, and you have shipped it: the POST returns a location, the client polls it, one poll finally returns the answer. Your instincts about TTLs, idempotency and resumable clients transfer intact.

One thing genuinely differs: in the HTTP version the *client* picks the async endpoint. Here the server picks, so a client that assumes `tools/call` returns a result crashes the day your server decides one call is slow.

The number that makes the case: a twenty-minute job at the suggested five-second interval is **240 `tasks/get` round trips and 69 KB of traffic — and zero model turns**, because the loop lives in your client, not in the conversation. The string-handle workaround, checked every thirty seconds, spends 40 model turns; at an 8,000-token context that is **320,000 tokens re-read** to learn that a deploy finished.

**Monday:** find the slowest tool on your server and compare its worst case against your gateway's idle timeout.

## What This Means for You

**When this matters.** You maintain an MCP server with a tool that can exceed your proxy's idle timeout — a deploy, a batch import, an approval gate — or a client that just met a shape it does not recognise.

**How it affects you.** On the server, the timeout is not a transport bug; it is a result shape you were not using. On the client it is a breaking-shaped change delivered as an opt-in: nothing moves until you declare the capability, and then *every* `tools/call` can return either shape. Declaring support without handling it is worse than staying silent.

**What to do about it.** Add the poll branch to your client before you add tasks to your server, then convert exactly one slow tool and watch it. If you own neither side, measure the gap between your longest tool call and your shortest idle timeout — that is the size of the problem coming.

## Implementing It

**The change.** Both halves move, in a specific order: the client learns to read the discriminator first, because a server returning tasks to a client that ignores `resultType` has broken every long call in a new way.

*Server — in your `tools/call` handler.* Three branches: fast tool, slow tool with a capable client, slow tool with an incapable one. Do not skip the third; silence there is how a client ends up parsing a receipt as an answer.

```python
CAPS = "io.modelcontextprotocol/clientCapabilities"
TASKS = "io.modelcontextprotocol/tasks"

def handle_call_tool(req):
    caps = req["params"].get("_meta", {}).get(CAPS, {})
    if req["params"]["name"] not in SLOW_TOOLS:
        return run_now(req)                    # unchanged: answer inline

    if TASKS not in caps.get("extensions", {}):
        return error(-32021, "Missing required client capability", data={
            "requiredCapabilities": {"extensions": {TASKS: {}}}})

    task_id = tasks.create(req)                # durable BEFORE you reply
    return {"resultType": "task", "taskId": task_id, "status": "working",
            "ttlMs": 3_600_000, "pollIntervalMs": 5000,
            "createdAt": now_iso(), "lastUpdatedAt": now_iso()}
```

`tasks.create` writing durably *before* the response is the requirement people miss. If your store is eventually consistent, wait for consistency inside `create`: a client that polls an id it was just handed and gets "not found" has no correct way to read that.

*Client — at every `tools/call` site.* Declaring the capability is one line in `_meta`; the branch after it is the actual work.

```python
res = session.request("tools/call", {
    "name": name, "arguments": args,
    "_meta": {CAPS: {"extensions": {TASKS: {}}}}})

if res.get("resultType") != "task":
    return res                                 # CallToolResult, exactly as before

save_task_id(conversation_id, res["taskId"])   # so a restart can resume
return poll_until_terminal(res["taskId"], res["pollIntervalMs"])
```

That `save_task_id` line is what buys crash resilience, and it is the one most easily left as a to-do.

Inside `poll_until_terminal`, the branch worth writing carefully is the input one, because the server re-sends the same request until you answer:

```python
if task["status"] == "input_required":
    fresh = {k: v for k, v in task["inputRequests"].items() if k not in answered}
    answered |= fresh.keys()                   # the same key repeats every poll
    if fresh:
        session.request("tasks/update",
                        {"taskId": task_id, "inputResponses": ask_user(fresh)})
```

Treat each entry with the same suspicion as a direct elicitation: a task is not a higher-trust channel, so that prompt earns the confirmation UI a standalone `elicitation/create` would get. The full loop, with terminal-state handling and the byte accounting behind the numbers above, is in `code_example.py`.

**How you know it worked.** Log `resultType` at every `tools/call` return site and count the two values over a day: the ratio tells you which tools your server actually decided were slow, and a flat zero means your capability declaration never reached `_meta`. Then kill your client mid-job and restart it — the run should resume from the persisted `taskId` and reach `completed`, not start a second deploy. Finally, grep for `-32021`: every hit is a client of yours that opted out and can no longer call that tool at all.

## When a Task Is the Wrong Tool

Under about five seconds, blocking is simply better: you would trade one round trip for three plus a durable write, and add a state machine to save nothing.

The bigger constraint is who is on the other end. The published extension support matrix does not list tasks yet, so most hosts your server meets have not opted in — which means the synchronous path stays in your code indefinitely rather than getting deleted after the migration.

The durable store is a real operational surface: task IDs are bearer tokens, so they need genuine entropy, an authorization check on every `tasks/get`, and a TTL sweeper you now own.

Three questions before adopting it: does any tool actually exceed a timeout you do not control, do the clients you care about declare the capability, and do you have somewhere to put task state that survives a pod restart? If the first answer is no, recognise the pattern and move on.
