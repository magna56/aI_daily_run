"""
Minimal Coding Agent Loop — from scratch in pure Python.

Demonstrates the core architecture of a coding agent (like Claude Code or
llm-coding-agent) without any API calls. Uses a simulated LLM that makes
deterministic tool calls to show the dispatch loop, approval gating, path
sandboxing, and chain limiting in action.

Run:
    python3 ~/ai_learning/2026-07-05/code_example.py

No dependencies beyond Python 3.10+ stdlib.
"""

from __future__ import annotations
import json
import os
import re
import tempfile
import textwrap
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


# ---------------------------------------------------------------------------
# 1. Tool definitions — JSON Schema style, matching Claude Code conventions
# ---------------------------------------------------------------------------

TOOLS = {
    "read_file": {
        "description": "Read a file with line numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "offset": {"type": "integer", "default": 0},
                "limit": {"type": "integer", "default": 2000},
            },
            "required": ["file_path"],
        },
        "read_only": True,
    },
    "edit_file": {
        "description": "Replace exact string match in a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
            },
            "required": ["file_path", "old_string", "new_string"],
        },
        "read_only": False,
    },
    "execute_command": {
        "description": "Run a shell command.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "default": 120},
            },
            "required": ["command"],
        },
        "read_only": False,
    },
}


# ---------------------------------------------------------------------------
# 2. Sandbox — path containment (prevents traversal and symlink escape)
# ---------------------------------------------------------------------------

def resolve_safe(root: Path, rel_path: str) -> Path:
    """Resolve a path safely within the sandbox root."""
    candidate = (root / rel_path).resolve()
    root_resolved = root.resolve()
    if not str(candidate).startswith(str(root_resolved)):
        raise PermissionError(f"Path escape blocked: {rel_path}")
    return candidate


# ---------------------------------------------------------------------------
# 3. Tool implementations
# ---------------------------------------------------------------------------

def tool_read_file(root: Path, file_path: str, offset: int = 0, limit: int = 2000) -> str:
    path = resolve_safe(root, file_path)
    if not path.exists():
        return f"Error: {file_path} not found"
    lines = path.read_text().splitlines()
    selected = lines[offset:offset + limit]
    return "\n".join(f"{i + offset + 1:4d}\t{line}" for i, line in enumerate(selected))


def tool_edit_file(root: Path, file_path: str, old_string: str, new_string: str) -> str:
    path = resolve_safe(root, file_path)
    if not path.exists():
        return f"Error: {file_path} not found"
    content = path.read_text()
    count = content.count(old_string)
    if count == 0:
        return f"Error: old_string not found in {file_path}"
    if count > 1:
        return f"Error: old_string matches {count} locations — must be unique"
    new_content = content.replace(old_string, new_string, 1)
    path.write_text(new_content)
    return f"OK: replaced 1 occurrence in {file_path}\n-{old_string}\n+{new_string}"


def tool_execute_command(root: Path, command: str, timeout: int = 120) -> str:
    # In a real agent this runs subprocess — we simulate it
    return f"[simulated] $ {command}\nCommand executed successfully."


DISPATCH = {
    "read_file": tool_read_file,
    "edit_file": tool_edit_file,
    "execute_command": tool_execute_command,
}


# ---------------------------------------------------------------------------
# 4. Approval policies
# ---------------------------------------------------------------------------

class ApprovalPolicy(Enum):
    YOLO = "yolo"               # approve everything
    READ_ONLY_AUTO = "default"  # auto-approve reads, gate writes
    LOCKED = "locked"           # approve nothing without explicit ok


def check_approval(tool_name: str, policy: ApprovalPolicy) -> bool:
    if policy == ApprovalPolicy.YOLO:
        return True
    if policy == ApprovalPolicy.LOCKED:
        return False
    # Default: auto-approve read-only tools
    return TOOLS[tool_name].get("read_only", False)


# ---------------------------------------------------------------------------
# 5. Simulated LLM — deterministic "model" that returns canned tool calls
# ---------------------------------------------------------------------------

@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]
    id: str = ""

@dataclass
class ModelResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)

def simulated_llm(turn: int, observations: list[str], root: Path) -> ModelResponse:
    """A fake LLM that follows a scripted plan to fix a bug."""
    if turn == 0:
        return ModelResponse(
            text="I'll read the file first to understand the bug.",
            tool_calls=[ToolCall("read_file", {"file_path": "app.py"}, "tc_0")],
        )
    elif turn == 1:
        return ModelResponse(
            text="Found the bug — off-by-one in the loop. Fixing it.",
            tool_calls=[ToolCall("edit_file", {
                "file_path": "app.py",
                "old_string": "for i in range(len(items)):",
                "new_string": "for i in range(len(items) - 1):",
            }, "tc_1")],
        )
    elif turn == 2:
        return ModelResponse(
            text="Running the tests to verify the fix.",
            tool_calls=[ToolCall("execute_command", {"command": "python -m pytest tests/"}, "tc_2")],
        )
    elif turn == 3:
        return ModelResponse(text="Bug fixed. The off-by-one error in app.py is resolved.")
    return ModelResponse(text="Done.")


# ---------------------------------------------------------------------------
# 6. Agent loop — the core dispatch cycle
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    text: str
    tool_calls_executed: int
    turns: int
    blocked_calls: list[str] = field(default_factory=list)

def run_agent(
    root: Path,
    task: str,
    policy: ApprovalPolicy = ApprovalPolicy.READ_ONLY_AUTO,
    chain_limit: int = 10,
) -> AgentResult:
    """
    The core agent loop:
      1. Send prompt + observations to LLM
      2. If LLM returns tool calls, dispatch them (with approval check)
      3. Collect results as observations for next turn
      4. If LLM returns only text (no tool calls), we're done
      5. Enforce chain_limit to prevent runaway loops
    """
    observations: list[str] = []
    total_tool_calls = 0
    blocked: list[str] = []

    print(f"\n{'='*60}")
    print(f"  AGENT LOOP — policy: {policy.value}, chain_limit: {chain_limit}")
    print(f"  Task: {task}")
    print(f"  Sandbox: {root}")
    print(f"{'='*60}\n")

    for turn in range(chain_limit):
        response = simulated_llm(turn, observations, root)

        # Print the model's reasoning
        if response.text:
            print(f"  [{turn}] Model: {response.text}")

        # No tool calls = agent is done
        if not response.tool_calls:
            return AgentResult(response.text, total_tool_calls, turn + 1, blocked)

        # Dispatch each tool call
        turn_observations = []
        for tc in response.tool_calls:
            approved = check_approval(tc.name, policy)
            status = "APPROVED" if approved else "BLOCKED"
            print(f"  [{turn}] Tool: {tc.name}({json.dumps(tc.arguments, indent=None)}) -> {status}")

            if approved:
                fn = DISPATCH[tc.name]
                result = fn(root, **tc.arguments)
                turn_observations.append(f"[{tc.name}] {result}")
                total_tool_calls += 1
                # Show truncated result
                preview = result[:120] + "..." if len(result) > 120 else result
                print(f"         Result: {preview}")
            else:
                blocked.append(tc.name)
                turn_observations.append(f"[{tc.name}] BLOCKED by approval policy")
                print(f"         (tool call blocked by {policy.value} policy)")

        observations.extend(turn_observations)

    return AgentResult("Chain limit reached", total_tool_calls, chain_limit, blocked)


# ---------------------------------------------------------------------------
# 7. Tool Schema Trap demo — show how schema design affects behavior
# ---------------------------------------------------------------------------

def demo_schema_trap():
    """
    Demonstrates the "Better Models: Worse Tools" paradox.

    When a model is RL-trained on Schema A (Claude Code style), it may inject
    Schema A fields when calling Schema B (third-party style).
    """
    print("\n" + "="*60)
    print("  TOOL SCHEMA TRAP DEMO")
    print("="*60)

    # Schema A: Claude Code style (flat parameters)
    schema_a = {
        "name": "edit_file",
        "parameters": ["file_path", "old_string", "new_string"],
    }

    # Schema B: Pi style (batched edits array)
    schema_b = {
        "name": "apply_edits",
        "parameters": ["file_path", "edits"],  # edits is [{old, new}, ...]
    }

    # What an RL-trained model might generate for Schema B
    # (leaking Schema A fields into Schema B's structure)
    correct_call = {
        "file_path": "app.py",
        "edits": [
            {"old": "foo()", "new": "bar()"},
        ],
    }

    malformed_call = {
        "file_path": "app.py",
        "edits": [
            {"old": "foo()", "new": "bar()", "old_string": "foo()", "new_string": "bar()"},
            #                                  ^^^^^^^^^^           ^^^^^^^^^^
            #                          leaked from Claude Code's schema!
        ],
    }

    print(f"\n  Schema A (Claude Code): {schema_a['parameters']}")
    print(f"  Schema B (Pi/3rd-party): {schema_b['parameters']}")
    print(f"\n  Correct Schema B call:")
    print(f"    {json.dumps(correct_call, indent=4)}")
    print(f"\n  Malformed call (RL training leak):")
    print(f"    {json.dumps(malformed_call, indent=4)}")

    # Strict schema validation catches this
    expected_keys = {"old", "new"}
    for i, edit in enumerate(malformed_call["edits"]):
        extra = set(edit.keys()) - expected_keys
        if extra:
            print(f"\n  Validation ERROR in edit[{i}]: unexpected fields {extra}")
            print(f"  -> This is the 'Better Models: Worse Tools' paradox.")
            print(f"  -> The model's RL training on Schema A leaked field names")
            print(f"     into Schema B calls. The edit content is correct,")
            print(f"     but the schema violation breaks the framework.")

    # Mitigation strategies
    print(f"\n  Mitigation strategies:")
    strategies = [
        ("Match the provider's schema", "Use old_string/new_string if targeting Claude"),
        ("Lenient validation", "Strip unknown fields instead of rejecting"),
        ("Provider-specific adapters", "Detect model family, swap tool schemas"),
        ("Schema normalization", "Map all edit schemas to a canonical form"),
    ]
    for name, desc in strategies:
        print(f"    - {name}: {desc}")


# ---------------------------------------------------------------------------
# 8. Main — run both demos
# ---------------------------------------------------------------------------

def main():
    # Create a temp sandbox with a buggy file
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        app_file = root / "app.py"
        app_file.write_text(textwrap.dedent("""\
            def process(items):
                results = []
                for i in range(len(items)):
                    results.append(items[i] + items[i + 1])
                return results
        """))

        # Demo 1: Agent loop with default approval (reads auto, writes gated)
        print("\n" + "#"*60)
        print("# DEMO 1: Default approval policy")
        print("#"*60)
        result = run_agent(root, "Fix the off-by-one bug in app.py")
        print(f"\n  Result: {result.turns} turns, {result.tool_calls_executed} tools executed")

        # Reset the file
        app_file.write_text(textwrap.dedent("""\
            def process(items):
                results = []
                for i in range(len(items)):
                    results.append(items[i] + items[i + 1])
                return results
        """))

        # Demo 2: Same task but LOCKED policy — only reads succeed
        print("\n" + "#"*60)
        print("# DEMO 2: Locked approval policy (all mutations blocked)")
        print("#"*60)
        result = run_agent(root, "Fix the off-by-one bug in app.py", ApprovalPolicy.LOCKED)
        print(f"\n  Result: {result.turns} turns, {result.tool_calls_executed} tools executed")
        print(f"  Blocked: {result.blocked_calls}")

    # Demo 3: Tool schema trap
    print("\n" + "#"*60)
    print("# DEMO 3: Tool Schema Trap (Better Models: Worse Tools)")
    print("#"*60)
    demo_schema_trap()

    # Summary
    print("\n" + "="*60)
    print("  KEY TAKEAWAYS")
    print("="*60)
    print("""
  1. The agent loop is simple: prompt -> tool calls -> observe -> repeat
  2. Value is in tool design, approval policy, and sandboxing
  3. RL training creates implicit coupling to specific tool schemas
  4. When building agent tools, consider matching your model provider's
     schema conventions (old_string/new_string for Claude, apply_patch
     for OpenAI) to benefit from their RL training
  5. Use lenient validation + schema normalization as a safety net
    """)


if __name__ == "__main__":
    main()
