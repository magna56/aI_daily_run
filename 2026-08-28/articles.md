# Further Reading: How to Run the Agent Loop OpenAI Used to Run for You

Read these in order. The first two decide *what* you have to change; the third and fourth
are the ones to keep open while you change it.

## Articles

### 1. [Migrate to the Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)
**Source**: OpenAI API docs | **Date**: 2026 | **Read time**: ~12 min
> The field-by-field mapping, including the two renames that break silently rather than
> loudly: tool definitions losing their nested `function` wrapper, and `response_format`
> becoming `text.format`. Its "common mistakes" list is the fastest code review you can
> run against your own diff. Read this first whichever API you are coming from.

### 2. [Assistants migration guide](https://developers.openai.com/api/docs/assistants/migration)
**Source**: OpenAI API docs | **Date**: 2026 | **Read time**: ~8 min
> The concept mapping — Assistant becomes Prompt, Thread becomes Conversation, Run becomes
> Response, run steps become Items — plus the confirmation that there is no automated tool
> for moving existing threads. Read it only if you were on Assistants; if you were on Chat
> Completions it tells you nothing you need.

### 3. [Function calling](https://developers.openai.com/api/docs/guides/function-calling)
**Source**: OpenAI API docs | **Date**: 2026 | **Read time**: ~15 min
> The loop itself, with the exact item shapes: `function_call` with its `call_id` and
> JSON-string `arguments`, and the `function_call_output` you send back. This is the page to
> have open in a second window while you write the `while` loop — it is the only one that
> states outright that you must append the model's own call item, not just your result.

### 4. [Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)
**Source**: OpenAI API docs | **Date**: 2026 | **Read time**: ~7 min
> The three ways to carry history, and the two facts that actually decide between them:
> every prior input token is re-billed on every call regardless of which you pick, and
> response objects expire after 30 days while conversation objects do not. Read this
> *before* you choose, not after your first invoice.

### 5. [New release of LLM adds support for reasoning traces, OpenAI Responses, and server-side tools](https://simonwillison.net/2026/Aug/4/new-release-of-llm/)
**Source**: Simon Willison's Weblog | **Date**: 4 Aug 2026 | **Read time**: ~10 min
> A working open-source client that had to absorb this exact migration — typed items,
> reasoning traces that have to survive a round trip, server-side tools. The most useful
> thing here is not the prose but the repository behind it: somebody else's answer to the
> design questions you are about to hit, in code you can read rather than a spec you have
> to interpret.
