# Further Reading: The `llm` CLI & Plugin Architecture

## Primary Sources

### 1. [LLM plugin hooks reference](https://llm.datasette.io/en/stable/plugins/plugin-hooks.html)
**Source**: llm.datasette.io | **Read time**: ~10 min
> The authoritative list of every hook: `register_models`, `register_commands`, `register_tools`, `register_embedding_models`, `register_template_loaders`, `register_fragment_loaders`. Shows the `@hookimpl` decorator and the `register(...)` callable pattern each hook uses.

### 2. [Writing a plugin to support a new model](https://llm.datasette.io/en/stable/plugins/tutorial-model-plugin.html)
**Source**: llm.datasette.io | **Read time**: ~15 min
> Hands-on tutorial: subclass `llm.Model`, implement `execute()`, wire up the `register_models` hook, and add the `[project.entry-points.llm]` table so `pip install` makes the model discoverable. The real-world version of `code_example.py`.

### 3. [pluggy documentation](https://pluggy.readthedocs.io/)
**Source**: pluggy.readthedocs.io | **Read time**: ~20 min
> The plugin library underneath `llm`, pytest, tox, and Datasette. Covers hook specs vs impls, `firstresult` hooks, `tryfirst`/`trylast` ordering, and hook wrappers — the parts the minimal from-scratch demo intentionally omits.

## Background & Ecosystem

### 4. [LLM: A CLI utility and Python library for interacting with LLMs](https://llm.datasette.io/)
**Source**: llm.datasette.io | **Read time**: ~8 min
> Project home. Prompts, SQLite logging of every request/response, embeddings, fragments/attachments, templates, tool calling, and a plugin directory listing dozens of community model/tool plugins.

### 5. [How I use LLM and its plugins (Simon Willison's weblog)](https://simonwillison.net/tags/llm/)
**Source**: simonwillison.net | **Read time**: browse
> The author's running commentary on the tool and its plugin ecosystem — practical patterns, new plugins (`llm-anthropic`, `llm-gemini`, `llm-ollama`, `llm-coding-agent`), and design rationale straight from the maintainer.

## The one-line takeaway
Publish an interface (named hooks), discover implementers at runtime (entry points), call them all and aggregate — and your tool grows an ecosystem instead of a merge queue. It's dependency inversion as a distribution strategy; MCP is the same idea across process boundaries.
