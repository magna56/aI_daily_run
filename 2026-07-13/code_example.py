#!/usr/bin/env python3
"""
Rebuild the `llm` CLI's plugin architecture from scratch: a minimal pluggy.

Simon Willison's `llm` (and pytest, tox, Datasette) all extend themselves the
same way: the CORE defines named extension points ("hook specs"); PLUGINS ship
functions with matching names ("hook impls") marked @hookimpl; a plugin manager
DISCOVERS plugins via setuptools entry points and calls EVERY implementation of
each hook, aggregating results. New models/tools/commands appear without editing
the core.

This file implements that mechanism in pure Python -- no pluggy, no llm, no
network -- then uses it to build a tiny `llm`-like core that two plugins extend
without touching a line of core code.

Run:  python3 code_example.py
"""

from functools import wraps

# ---------------------------------------------------------------------------
# 1. The plugin machinery (this is ~all of pluggy's core idea).
# ---------------------------------------------------------------------------
def hookspec(fn):
    """Marks a function as a HOOK SPECIFICATION: it defines the contract
    (name + signature) but has no body worth running."""
    fn._is_hookspec = True
    return fn


def hookimpl(fn):
    """Marks a plugin function as a HOOK IMPLEMENTATION. Matching to a spec is
    by function NAME -- not by import, not by explicit registration."""
    fn._is_hookimpl = True
    return fn


class PluginManager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.specs = {}          # hook name -> spec function
        self.impls = {}          # hook name -> [impl functions]

    def add_hookspecs(self, namespace):
        for name in dir(namespace):
            fn = getattr(namespace, name)
            if getattr(fn, "_is_hookspec", False):
                self.specs[name] = fn
                self.impls.setdefault(name, [])

    def register(self, plugin):
        """Register one plugin object/module: scan it for @hookimpl functions
        whose names match a known spec."""
        for name in dir(plugin):
            fn = getattr(plugin, name)
            if getattr(fn, "_is_hookimpl", False) and name in self.specs:
                self.impls[name].append(fn)

    def hook(self, name, **kwargs):
        """Call EVERY implementation of `name`, collect non-None results.
        This aggregation (not override) is what lets plugins compose."""
        results = []
        for fn in self.impls.get(name, []):
            r = fn(**kwargs)
            if r is not None:
                results.append(r)
        return results

    def discover(self, entry_points):
        """Simulated setuptools entry-point discovery. In real llm, this reads
        installed-package metadata for the `llm` group; here we pass the map in
        so the demo stays self-contained. The point: the core imports plugins
        it was never told about by name."""
        for ep_name, plugin in entry_points.get(self.project_name, {}).items():
            print(f"  discovered plugin: {ep_name}")
            self.register(plugin)


# ---------------------------------------------------------------------------
# 2. The CORE. It defines extension points and knows about NO concrete model.
# ---------------------------------------------------------------------------
class HookSpecs:
    @hookspec
    def register_models(register):
        """Plugins call register(model, aliases=(...)) once per model."""

    @hookspec
    def register_tools(register):
        """Plugins call register(fn) once per tool (a typed callable)."""


class Core:
    def __init__(self):
        self.pm = PluginManager("llm")
        self.pm.add_hookspecs(HookSpecs)
        self.models, self.aliases, self.tools = {}, {}, {}

    def load_plugins(self, entry_points):
        print("Loading plugins via entry points...")
        self.pm.discover(entry_points)
        # Fire register_* hooks, handing each impl a `register` callable.
        self.pm.hook("register_models", register=self._register_model)
        self.pm.hook("register_tools", register=self._register_tool)
        print(f"Registered models: {list(self.models)}")
        print(f"Model aliases:     {self.aliases}")
        print(f"Registered tools:  {list(self.tools)}\n")

    def _register_model(self, model, aliases=()):
        self.models[model.model_id] = model
        for a in aliases:
            self.aliases[a] = model.model_id

    def _register_tool(self, fn):
        self.tools[fn.__name__] = fn

    def prompt(self, model_ref, text):
        model_id = self.aliases.get(model_ref, model_ref)
        model = self.models[model_id]
        return model.execute(text)


class Model:
    """Base class plugins subclass -- mirrors llm.Model.execute()."""
    model_id = "base"
    def execute(self, prompt):  # pragma: no cover
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 3. TWO PLUGINS. In reality each is a separate pip package with a pyproject
#    [project.entry-points.llm] table. Neither imports the other; neither edits
#    the core. They only agree on the hook NAMES and the base classes.
# ---------------------------------------------------------------------------
class EchoModel(Model):
    model_id = "echo-1"
    def execute(self, prompt):
        return f"[echo-1] you said: {prompt!r} ({len(prompt)} chars)"

class ShoutModel(Model):
    model_id = "shout-1"
    def execute(self, prompt):
        return f"[shout-1] {prompt.upper()}!!!"

class ModelsPlugin:
    @hookimpl
    def register_models(register):
        register(EchoModel(), aliases=("echo",))
        register(ShoutModel(), aliases=("shout", "loud"))

class ToolsPlugin:
    @hookimpl
    def register_tools(register):
        def word_count(text: str) -> int:
            """A tool is just a typed callable the core can dispatch."""
            return len(text.split())
        register(word_count)


if __name__ == "__main__":
    # This dict stands in for setuptools entry-point metadata across pip pkgs.
    ENTRY_POINTS = {"llm": {"llm-models-demo": ModelsPlugin,
                            "llm-tools-demo":  ToolsPlugin}}

    core = Core()
    core.load_plugins(ENTRY_POINTS)

    print("Dispatching prompts to plugin-provided models:")
    print("  ", core.prompt("echo",  "hello plugin world"))
    print("  ", core.prompt("loud",  "ship it"))          # alias -> shout-1
    print("  ", core.prompt("shout-1", "direct by id"))   # full id works too

    print("\nCalling a plugin-provided tool:")
    wc = core.tools["word_count"]
    print("   word_count('the quick brown fox') =", wc("the quick brown fox"))

    print("\nWhy this matters:")
    print(" * Core never imported EchoModel/ShoutModel/word_count by name.")
    print(" * Adding a model family = ship a new package; core is untouched.")
    print(" * Hooks AGGREGATE (all impls run) -> plugins compose, not override.")
    print(" * Same pattern as pytest, Datasette, and llm; same lib: pluggy.")
    print(" * MCP is this idea across processes; pluggy is the in-process form.")
