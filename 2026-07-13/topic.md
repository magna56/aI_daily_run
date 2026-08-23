# The `llm` CLI & Its Plugin Architecture: pluggy Hooks as an Extensibility Pattern

**Category**: Building Agents & MCP
**Date**: 2026-07-13
**Time to read**: ~10 minutes

## What It Is

Simon Willison's [`llm`](https://llm.datasette.io/) is a small, wildly popular open-source CLI + Python library for talking to language models. `llm "explain this"` runs a prompt; everything — every prompt, response, token count, and tool call — is logged to a local SQLite database you can query later. It supports prompts, streaming, embeddings, fragments/attachments, templates, and tool calling, all from one binary you `pip install llm` (or `uvx llm`) and run offline against local models or remote APIs.

The reason it's worth studying as an *engineering artifact* is not the LLM part — it's the **plugin architecture**. The `llm` core knows nothing about OpenAI, Anthropic, Gemini, Ollama, or any specific model. Those all live in *plugins* (`llm-openai`, `llm-anthropic`, `llm-gemini`, `llm-ollama`, …). New model families, new CLI commands, new tools, and new embedding models are all added *without editing the core package*. This is the same pattern that powers pytest, tox, and Datasette, and it's built on the exact same library: **[pluggy](https://pluggy.readthedocs.io/)**, pytest's plugin framework.

Concretely, `llm` defines a set of **hook specifications** (named extension points). A plugin ships **hook implementations** decorated with `@hookimpl` whose function *name matches* a spec. At startup, `llm` uses a plugin manager to discover installed plugins via **setuptools entry points** (the `[project.entry-points.llm]` table in a plugin's `pyproject.toml`), then calls every registered implementation of each hook and collects the results. That's the whole trick: name-matched functions, auto-discovered, called in aggregate.

## Why It Matters

- **Zero-core-change extensibility.** Adding Anthropic support is `pip install llm-anthropic` — no fork, no PR to the core, no version coupling. For a platform team, this is the difference between a bottleneck and an ecosystem.
- **It's the standard Python plugin idiom.** pytest fixtures/plugins, Datasette, `llm`, and plenty of internal company tooling use this exact pattern. Understanding pluggy once transfers everywhere.
- **Entry-point discovery decouples install from import.** The host never imports plugins by name; it asks the installed-package metadata "who registered under group `llm`?" This is how a tool discovers code it has never heard of.
- **Aggregation semantics matter.** Because *all* implementations of a hook run and results are collected into a list, plugins compose rather than override. Contrast with subclassing or monkey-patching, where the last writer wins.

## Key Technical Details

- **Hook specs** (the contract the core defines): `register_models(register, model_aliases)`, `register_commands(cli)`, `register_tools(register)`, `register_embedding_models(register)`, `register_template_loaders(register)`, `register_fragment_loaders(register)`.
- **`@hookimpl`** marks a plugin function as an implementation; matching happens by **function name**, not by import or registration call.
- **The `register` callable pattern.** Several hooks pass in a `register(...)` function; the plugin calls it once per thing it contributes (e.g. `register(MyModel(), aliases=("myshort",))`). This lets one hook contribute many models/tools.
- **Models subclass `llm.Model`** (or `AsyncModel`) and implement `execute()`; **embedding models subclass `llm.EmbeddingModel`** and implement `embed_batch()`; **tools** are plain functions with type hints *or* `llm.Toolbox` subclasses (invoked with `-T ToolboxName`).
- **Discovery** is via setuptools entry points under the `llm` group; `llm plugins` lists what's loaded. No central registry, no config file listing plugins.
- **Ordering & first-result hooks.** pluggy supports `tryfirst`/`trylast` and `firstresult` hooks (stop at first non-None) — useful when you want override rather than aggregate semantics.

## How It Connects to What You Know

You already build agents with tool schemas and dispatch loops. This is the *host-side* mirror of that: instead of a hard-coded tool table, the host publishes an interface (hook specs) and lets independently-shipped packages populate it at runtime. It's dependency inversion — the core depends on an abstraction (the hook name + signature), and plugins depend on that same abstraction, so neither depends on the other. If you've wired MCP servers into Claude, the mental model is identical: MCP is a *cross-process* plugin protocol (JSON-RPC + capability discovery); pluggy is the *in-process* version (Python entry points + name-matched callables). `register_tools` in `llm` and "list tools" in MCP are the same idea at different layers.

## Try It Yourself

`code_example.py` implements a **minimal pluggy-style plugin framework from scratch** in ~130 lines of pure Python — `@hookspec`, `@hookimpl`, a `PluginManager` that name-matches and aggregates, and *simulated entry-point discovery*. It then builds a mini `llm`-like core with `register_models` and `register_tools` hooks, and ships **two plugins** that add a model and a tool **without touching the core**. Running it shows the core discovering, registering, and dispatching to code it was never compiled against.
