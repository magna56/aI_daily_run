# How to Run the Agent Loop OpenAI Used to Run for You

**Category**: New Models & APIs
**Tags**: agents, production, cost
**Date**: 2026-08-28
**Level**: Building
**For**: Building agents
**Hook**: OpenAI's Assistants API stopped answering two days ago, and its replacement will not run your tool-calling loop for you — your own code has to.
**Time to read**: ~8 minutes

## Explain Like I'm 5

You used to order at a restaurant by telling the waiter and then waiting. If the cook needed to know how spicy you wanted it, the waiter walked over, asked, and walked back. That restaurant has switched to counter service. Now you carry your own plate, you walk over yourself every time the cook has a question, and you have to remember what is already on your table.

## The Problem

What stopped working on August 26 was not an endpoint. It was a loop.

If you built on the Assistants API, your code created a thread, posted a message, started a run, then polled that run's status. It went `queued`, `in_progress`, and eventually `requires_action`, at which point you handed back tool outputs and polled again. Your process was a client to a state machine somebody else was running.

The replacement, the Responses API, has no run object at all. Nothing polls because nothing is running: a response comes back complete, and if the model wants a tool called, that request is just one of the items in the reply.

The loop is a `while` in your process now — which is why a find-and-replace on the URL leaves you with an agent that answers the first question and forgets the second.

## How the Responses API Handles a Tool Call

### Everything Is an Item

Chat Completions handed you `choices[0].message`. A response hands you `output`, a typed list, deliberately mixed:

```json
"output": [
  {"type": "reasoning", "summary": [], "content": []},
  {"id": "fc_12345xyz", "call_id": "call_12345xyz", "type": "function_call",
   "name": "get_weather", "arguments": "{\"location\":\"Paris, France\"}"}
]
```

An **item** is one unit of model context — a message, a reasoning trace, a tool call, a tool result. The old shape crammed all of them into one message object's optional fields; this one gives each its own type. Note that `arguments` is a JSON *string*, so it needs parsing.

### The Round Trip

You run the function and send the result back as its own item, matched by `call_id`:

```json
{"type": "function_call_output", "call_id": "call_12345xyz", "output": "25C and clear"}
```

Then comes the part that catches people: you must append **the model's original `function_call` item as well**, not just your output. Send back the output alone and the model receives an answer to a question it has no record of asking.

The same goes for `reasoning` items: filter them out of the replay and the model loses its own train of thought across the tool call.

### Where the Conversation Lives

Three options, not interchangeable:

- **Replay the items yourself** — keep a list and append `response.output` after every call.
- **`previous_response_id`** — send the previous response's id and let the server stitch.
- **The Conversations API** — `POST /v1/conversations`, then pass `conversation` on each request.

None makes the history cheaper: the docs are explicit that all previous input tokens in a chain are billed as input tokens. `previous_response_id` saves you a data structure, not money.

The one real difference is retention: response objects live 30 days, conversation objects are not subject to that TTL. That alone picks the third option if your product shows a chat from last quarter.

## For a Software Engineer

You have done this migration before. It is the move from sticky sessions to a stateless service: the server stops holding your session, and state either rides along in every request or lives in a store you address explicitly. Threads were sticky sessions; Conversations are the store.

The tool loop is the second half of the same change: an asynchronous job API — submit, poll, supply input when it asks — replaced by a synchronous call you put in a loop.

What is genuinely new is the billing shape. The loop is yours, but its cost has nothing to do with how cleverly you write it: every tool call is a fresh request that re-sends the whole conversation, so an agent taking six tool calls to answer one question pays for that question's context seven times. This was equally true under Assistants. You just never wrote the line of code that made it obvious.

## What This Means for You

**When this matters.** You have code calling the assistants or threads endpoints and it is failing right now — or you are on Chat Completions, deciding whether to move at all.

**How it affects you.** Only Assistants sunset, so Chat Completions is no emergency. If you were on Assistants the outage is live, and no automated thread migration exists: old history must be read out and rewritten as conversation items — user turns as `input_text`, assistant turns as `output_text`. On every path, prior turns are re-billed on each call.

**What to do about it.** Two things. Write the loop below with an assertion that every `function_call` gets a `function_call_output` carrying a matching `call_id` — that one check catches the most common migration bug before a user sees it. Then log input tokens per *user question*, not per API call: the ratio between them is your tool-call count, and it is usually higher than people guess.

## Implementing It

**The change**

Four pieces move. Take them in this order, because nothing else matters until requests are accepted at all.

**1. The request builder.** The tool definition loses its nested `function` wrapper, and structured outputs move from `response_format` to `text.format`:

```python
# before — Chat Completions
tools = [{"type": "function",
          "function": {"name": "get_weather", "parameters": SCHEMA}}]
response_format = {"type": "json_schema",
                   "json_schema": {"name": "weather", "schema": SCHEMA}}

# after — Responses
tools = [{"type": "function", "name": "get_weather",
          "parameters": SCHEMA, "strict": True}]
text = {"format": {"type": "json_schema", "name": "weather", "schema": SCHEMA}}
```

The schema object itself is untouched; only the path wrapping it changes. A leftover `response_format` is one of the mistakes the migration guide names explicitly — your schema simply is not where the API looks for it.

**2. The loop owner.** This is the code that used to be a poll:

```python
input_list = [{"role": "user", "content": question}]
while True:
    resp = client.responses.create(model=MODEL, tools=tools, input=input_list)
    input_list += resp.output      # keeps reasoning AND function_call items
    calls = [i for i in resp.output if i.type == "function_call"]
    if not calls:
        return resp.output_text
    for call in calls:
        input_list.append({
            "type": "function_call_output",
            "call_id": call.call_id,
            "output": dispatch(call.name, json.loads(call.arguments)),
        })
```

The line that appends `resp.output` comes *before* the dispatch loop. That ordering is what keeps each `function_call` sitting ahead of its own output in the list.

**3. The state layer.** If you were on threads, nothing carries over on its own. Create the conversation and replay the old turns into it:

```http
POST /v1/conversations
{"items": [
  {"type": "message", "role": "user",
   "content": [{"type": "input_text",  "text": "...previous user turn..."}]},
  {"type": "message", "role": "assistant",
   "content": [{"type": "output_text", "text": "...previous reply..."}]}
]}
```

Then pass the id instead of carrying the list: `client.responses.create(model=MODEL, conversation=conv_id, input=question)`. Migrate threads lazily — new conversations onto the new object, old ones only when a user opens them.

**4. The streaming consumer.** The old handler read `delta` off every chunk. Responses emits typed events and text is only one of them:

```python
for event in stream:
    if event.type == "response.output_text.delta":
        ui.append(event.delta)
    elif event.type == "response.function_call_arguments.delta":
        tool_buf.append(event.delta)   # tool args stream here, not in output_text
    elif event.type == "response.completed":
        finalize(event.response)
```

A handler still branching on `delta` alone will quietly render an empty answer every time the model's reply is a tool call rather than text.

**How you know it worked**

Three signals, cheapest first.

- **Assert the pairing.** Before each `responses.create`, check that the set of `call_id`s on your `function_call` items equals the set on your `function_call_output` items. Unequal means you dropped one, and the assertion fires in development rather than the model apologising in production.
- **Count what you replay.** Log how many `reasoning` items are in `input_list`. It should grow as the conversation does; flat at zero means you are filtering them out, and the symptom is an agent that reasons well on the first tool call and badly on the third.
- **Measure input tokens per question, not per call.** Take one question that needs three tools. Input tokens summed across those four requests should be roughly four times your base context, not one. If you expected one, the re-billing rule is the thing you had not priced in.

## When Owning the Loop Is the Wrong Tool

Chat Completions did not sunset. If your feature is one request and one answer with no tools, migrating buys typed items you do not need and a loop you never enter.

The costs arrive with the loop. Every tool call is now a network round trip from *your* machine; under Assistants that hop happened inside OpenAI's network and never appeared in your traces. Managed `file_search` and `code_interpreter` orchestration was doing real work you may now be rebuilding yourself.

Three questions before you move anything:

1. Are you actually broken, or just on the older-but-supported path? Only one of those is urgent.
2. How many tool calls does your median question take? That number multiplies your context cost — measure it before you commit.
3. Do you need history older than 30 days? That answer alone picks between replaying items yourself and the Conversations API.
