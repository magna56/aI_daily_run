"""
The Responses-API agent loop, implemented against a fake server.

Implements the loop that OpenAI's Assistants API used to run for you: typed items in,
typed items out, function_call paired with function_call_output by call_id, and the
whole list re-sent on every turn. `run_agent_loop` and `assert_call_pairing` are the
liftable parts -- swap FakeResponsesClient for the real SDK and they work unchanged.

Prints the token accounting the write-up claims: a question needing 3 tools costs
roughly 4x its base context, because every tool call re-sends the conversation.

Run: python3 code_example.py
"""

import json

# --- knobs -------------------------------------------------------------------
# Raise TOOL_CALLS_NEEDED and watch the cost multiple track it exactly: N tools
# means N+1 requests, and request k re-sends everything from requests 1..k-1.
TOOL_CALLS_NEEDED = 3
BASE_CONTEXT_CHARS = 4000       # system prompt + tool schemas, sent every single time


# --- the liftable core -------------------------------------------------------

def assert_call_pairing(input_list):
    """Every function_call must have a function_call_output with the same call_id.

    This is the check worth keeping in your own loop. The most common migration bug
    is appending your tool result but not the model's original call, and the model's
    only symptom is answering a question it has no record of being asked.
    """
    calls = {i["call_id"] for i in input_list if i.get("type") == "function_call"}
    outs = {i["call_id"] for i in input_list if i.get("type") == "function_call_output"}
    missing, orphan = calls - outs, outs - calls
    if missing or orphan:
        raise AssertionError(f"unpaired call_ids: missing={missing} orphaned={orphan}")


def run_agent_loop(client, question, tools, dispatch, keep_reasoning=True,
                   keep_call_items=True):
    """Drive a Responses-style conversation to a final text answer.

    keep_reasoning / keep_call_items exist to demonstrate the two ways this loop is
    commonly written wrong. In real code both are simply always True -- you append
    resp["output"] wholesale and never filter it.
    """
    input_list = [{"role": "user", "content": question}]
    billed_input_chars = 0

    while True:
        billed_input_chars += BASE_CONTEXT_CHARS + len(json.dumps(input_list))
        resp = client.create(input_list)

        for item in resp["output"]:
            if item["type"] == "reasoning" and not keep_reasoning:
                continue                      # bug 2: model loses its own chain
            if item["type"] == "function_call" and not keep_call_items:
                continue                      # bug 1: unpaired call_id
            input_list.append(item)

        calls = [i for i in resp["output"] if i["type"] == "function_call"]
        if not calls:
            return resp["output_text"], input_list, billed_input_chars

        for call in calls:
            # append the OUTPUT after the call item, so the pair stays ordered
            input_list.append({
                "type": "function_call_output",
                "call_id": call["call_id"],
                "output": dispatch(call["name"], json.loads(call["arguments"])),
            })


# --- a fake server so this runs with no API key ------------------------------

class FakeResponsesClient:
    """Emits the item shapes the real API emits: reasoning, function_call, message."""

    def __init__(self, tool_calls_needed):
        self.remaining = tool_calls_needed
        self.n = 0

    def create(self, _input_list):
        self.n += 1
        reasoning = [{"type": "reasoning", "summary": [],
                      "content": [{"text": f"step {self.n}: deciding what to look up"}]}]
        if self.remaining > 0:
            self.remaining -= 1
            cid = f"call_{self.n:05d}"
            return {"output": reasoning + [{
                "id": f"fc_{self.n:05d}", "call_id": cid, "type": "function_call",
                "name": "get_weather",
                "arguments": json.dumps({"location": f"city-{self.n}"}),
            }], "output_text": None}
        return {"output": reasoning + [{"type": "message", "role": "assistant",
                                        "content": [{"type": "output_text",
                                                     "text": "It is 25C and clear."}]}],
                "output_text": "It is 25C and clear."}


def dispatch(name, args):
    assert name == "get_weather", name
    return f"25C and clear in {args['location']}"


# --- what it proves ----------------------------------------------------------

def main():
    tools = [{"type": "function", "name": "get_weather",
              "parameters": {"type": "object",
                             "properties": {"location": {"type": "string"}},
                             "required": ["location"], "additionalProperties": False},
              "strict": True}]

    text, items, billed = run_agent_loop(
        FakeResponsesClient(TOOL_CALLS_NEEDED), "What's the weather?", tools, dispatch)
    assert_call_pairing(items)

    base = BASE_CONTEXT_CHARS
    print(f"answer: {text}")
    print(f"requests sent:        {TOOL_CALLS_NEEDED + 1} "
          f"({TOOL_CALLS_NEEDED} tool calls + 1 final)")
    print(f"items replayed:       {len(items)} "
          f"({sum(1 for i in items if i.get('type') == 'reasoning')} reasoning kept)")
    print(f"billed input chars:   {billed:,}  vs base context {base:,}")
    print(f"cost multiple:        {billed / base:.1f}x base context for ONE question")

    print("\n-- bug 1: appending the output but not the model's call item --")
    _, bad, _ = run_agent_loop(FakeResponsesClient(TOOL_CALLS_NEEDED),
                               "What's the weather?", tools, dispatch,
                               keep_call_items=False)
    try:
        assert_call_pairing(bad)
        print("   assertion did NOT fire (unexpected)")
    except AssertionError as e:
        print(f"   assertion fired in dev, not in prod: {e}")

    print("\n-- bug 2: filtering reasoning items out of the replay --")
    _, thin, _ = run_agent_loop(FakeResponsesClient(TOOL_CALLS_NEEDED),
                                "What's the weather?", tools, dispatch,
                                keep_reasoning=False)
    kept = sum(1 for i in thin if i.get("type") == "reasoning")
    print(f"   reasoning items replayed: {kept} (should grow with the conversation)")


if __name__ == "__main__":
    main()
