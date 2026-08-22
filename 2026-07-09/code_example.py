"""
Deterministic Verification Gates for Tool-Using Agents
=======================================================
Demonstrates the "Reason Less, Verify More" pattern from arXiv:2607.07405.

Simulates an airline booking agent that makes tool calls, some of which
silently violate business policies. Shows how lightweight deterministic
gates catch violations that the agent's own reasoning misses.

Run: python3 ~/ai_learning/2026-07-09/code_example.py
Requirements: none (pure stdlib)
"""

import json
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

# --- Domain Model ---

class BookingStatus(Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    PENDING = "pending"

@dataclass
class Booking:
    id: str
    passengers: int
    fare_class: str  # "economy", "business", "first"
    status: BookingStatus
    departure_day: int  # day of year
    changes_remaining: int = 3

@dataclass
class SystemState:
    bookings: dict[str, Booking] = field(default_factory=dict)
    current_day: int = 180  # mid-year

    def snapshot(self) -> dict:
        return {bid: (b.status.value, b.passengers, b.fare_class)
                for bid, b in self.bookings.items()}

# --- Tools (policy-permissive: they execute any well-formed call) ---

def tool_change_passengers(state: SystemState, booking_id: str, new_count: int) -> str:
    b = state.bookings[booking_id]
    old = b.passengers
    b.passengers = new_count
    return f"Changed {booking_id} passengers: {old} -> {new_count}"

def tool_cancel_booking(state: SystemState, booking_id: str) -> str:
    b = state.bookings[booking_id]
    b.status = BookingStatus.CANCELLED
    b.changes_remaining = 0
    return f"Cancelled {booking_id}"

def tool_change_fare(state: SystemState, booking_id: str, new_fare: str) -> str:
    b = state.bookings[booking_id]
    old = b.fare_class
    b.fare_class = new_fare
    b.changes_remaining -= 1
    return f"Changed {booking_id} fare: {old} -> {new_fare}"

TOOLS = {
    "change_passengers": tool_change_passengers,
    "cancel_booking": tool_cancel_booking,
    "change_fare": tool_change_fare,
}

# --- Verification Gates (the core pattern from the paper) ---

@dataclass
class GateResult:
    allowed: bool
    violation: str = ""

Gate = Callable[[SystemState, str, dict], GateResult]

def gate_passenger_count(state: SystemState, tool_name: str, args: dict) -> GateResult:
    """Passenger count must be >= 1 after any modification."""
    if tool_name == "change_passengers":
        # A gate reads whatever the model emitted, so it cannot assume the call
        # is well formed. Indexing args[...] here would turn a malformed call
        # into a crash inside the very check meant to stop it.
        new_count = args.get("new_count")
        if new_count is None:
            return GateResult(False, "POLICY: change_passengers requires new_count")
        if new_count < 1:
            return GateResult(False, f"POLICY: passenger count must be >= 1 (got {new_count})")
    return GateResult(True)

def gate_booking_status(state: SystemState, tool_name: str, args: dict) -> GateResult:
    """Cannot modify a cancelled booking."""
    if tool_name in ("change_passengers", "change_fare"):
        b = state.bookings.get(args["booking_id"])
        if b and b.status == BookingStatus.CANCELLED:
            return GateResult(False, f"POLICY: cannot modify cancelled booking {args['booking_id']}")
    return GateResult(True)

def gate_change_limit(state: SystemState, tool_name: str, args: dict) -> GateResult:
    """Max 3 fare changes per booking."""
    if tool_name == "change_fare":
        b = state.bookings.get(args["booking_id"])
        if b and b.changes_remaining <= 0:
            return GateResult(False, f"POLICY: no fare changes remaining on {args['booking_id']}")
    return GateResult(True)

def gate_departure_window(state: SystemState, tool_name: str, args: dict) -> GateResult:
    """Cannot cancel within 1 day of departure."""
    if tool_name == "cancel_booking":
        b = state.bookings.get(args["booking_id"])
        if b and (b.departure_day - state.current_day) <= 1:
            return GateResult(False,
                f"POLICY: cannot cancel {args['booking_id']} within 1 day of departure "
                f"(departs day {b.departure_day}, today is day {state.current_day})")
    return GateResult(True)

ALL_GATES: list[Gate] = [
    gate_passenger_count,
    gate_booking_status,
    gate_change_limit,
    gate_departure_window,
]

# --- Simulated Agent (generates plausible but sometimes policy-violating calls) ---

@dataclass
class AgentAction:
    tool: str
    args: dict
    reasoning: str

def generate_scenario_actions(state: SystemState) -> list[AgentAction]:
    """Simulates an agent generating a sequence of tool calls.
    Some are valid, some silently violate policies."""
    actions = []
    bookings = list(state.bookings.keys())
    b1 = bookings[0]
    b2 = bookings[1] if len(bookings) > 1 else b1

    actions.append(AgentAction(
        "change_passengers", {"booking_id": b1, "new_count": 3},
        "Customer wants to add a traveler"))
    actions.append(AgentAction(
        "cancel_booking", {"booking_id": b1},
        "Customer changed mind, wants to cancel"))
    # VIOLATION: modifying a just-cancelled booking
    actions.append(AgentAction(
        "change_fare", {"booking_id": b1, "new_fare": "business"},
        "Upgrade cancelled booking per loyalty status"))
    # VIOLATION: setting passengers to 0
    actions.append(AgentAction(
        "change_passengers", {"booking_id": b2, "new_count": 0},
        "Remove all passengers before rebooking"))
    # Valid action
    actions.append(AgentAction(
        "change_fare", {"booking_id": b2, "new_fare": "first"},
        "Upgrade to first class"))
    # Exhaust change limit then try again
    actions.append(AgentAction(
        "change_fare", {"booking_id": b2, "new_fare": "economy"},
        "Customer wants economy instead"))
    actions.append(AgentAction(
        "change_fare", {"booking_id": b2, "new_fare": "business"},
        "Actually, go business"))
    # VIOLATION: 4th change when limit is 3
    actions.append(AgentAction(
        "change_fare", {"booking_id": b2, "new_fare": "first"},
        "No wait, first class"))

    return actions

# --- Execution Engine ---

def execute_without_gates(state: SystemState, actions: list[AgentAction]) -> list[dict]:
    results = []
    for a in actions:
        try:
            msg = TOOLS[a.tool](state, **a.args)
            results.append({"action": a.tool, "args": a.args, "result": "SUCCESS",
                           "message": msg, "reasoning": a.reasoning})
        except Exception as e:
            results.append({"action": a.tool, "args": a.args, "result": "ERROR",
                           "message": str(e), "reasoning": a.reasoning})
    return results

def execute_with_gates(state: SystemState, actions: list[AgentAction],
                       gates: list[Gate]) -> list[dict]:
    results = []
    for a in actions:
        # Run all gates before execution
        blocked = False
        for gate in gates:
            gr = gate(state, a.tool, a.args)
            if not gr.allowed:
                results.append({"action": a.tool, "args": a.args, "result": "GATE_BLOCKED",
                               "message": gr.violation, "reasoning": a.reasoning})
                blocked = True
                break
        if not blocked:
            try:
                msg = TOOLS[a.tool](state, **a.args)
                results.append({"action": a.tool, "args": a.args, "result": "SUCCESS",
                               "message": msg, "reasoning": a.reasoning})
            except Exception as e:
                results.append({"action": a.tool, "args": a.args, "result": "ERROR",
                               "message": str(e), "reasoning": a.reasoning})
    return results

# --- Analysis ---

def make_fresh_state() -> SystemState:
    state = SystemState()
    state.bookings["BK-001"] = Booking("BK-001", 2, "economy", BookingStatus.CONFIRMED, 195)
    state.bookings["BK-002"] = Booking("BK-002", 1, "economy", BookingStatus.CONFIRMED, 210,
                                        changes_remaining=3)
    return state

def print_results(label: str, results: list[dict], final_state: SystemState):
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    for i, r in enumerate(results, 1):
        status_icon = {"SUCCESS": "+", "GATE_BLOCKED": "X", "ERROR": "!"}[r["result"]]
        print(f"\n  [{status_icon}] Step {i}: {r['action']}({r['args']})")
        print(f"      Reasoning: {r['reasoning']}")
        print(f"      Result:    {r['result']} — {r['message']}")

    print(f"\n  Final state:")
    for bid, b in final_state.bookings.items():
        print(f"    {bid}: status={b.status.value}, pax={b.passengers}, "
              f"fare={b.fare_class}, changes_left={b.changes_remaining}")

def run_monte_carlo(n_trials: int = 500):
    """Run randomized scenarios to measure gate effectiveness across many cases."""
    random.seed(42)
    violations_ungated = 0
    violations_gated = 0
    total_actions = 0
    gate_catches = {g.__name__: 0 for g in ALL_GATES}

    for _ in range(n_trials):
        state = make_fresh_state()
        # Randomize: sometimes make bookings near departure or already changed
        for b in state.bookings.values():
            if random.random() < 0.3:
                b.departure_day = state.current_day + random.choice([0, 1])
            if random.random() < 0.3:
                b.changes_remaining = random.choice([0, 1])
            if random.random() < 0.2:
                b.status = BookingStatus.CANCELLED

        # Give each call the arguments its own tool takes. Sampling the args
        # independently of the tool would measure how often the generator emits
        # nonsense, not how often a well-formed call violates policy.
        def random_action() -> AgentAction:
            tool = random.choice(list(TOOLS.keys()))
            args = {"booking_id": random.choice(list(state.bookings.keys()))}
            if tool == "change_passengers":
                args["new_count"] = random.choice([-1, 0, 1, 2, 3])
            elif tool == "change_fare":
                args["new_fare"] = random.choice(["economy", "business", "first"])
            return AgentAction(tool, args, "random test")

        actions = [random_action() for _ in range(5)]

        # Count gate blocks
        for a in actions:
            total_actions += 1
            any_violation = False
            for gate in ALL_GATES:
                gr = gate(state, a.tool, a.args)
                if not gr.allowed:
                    gate_catches[gate.__name__] += 1
                    any_violation = True
                    break
            if any_violation:
                violations_gated += 1

        # For ungated, check if actions would have been violations
        # (same count since we're measuring the actions, not execution)
        violations_ungated += sum(1 for a in actions
            for g in ALL_GATES if not g(state, a.tool, a.args).allowed)

    print(f"\n{'='*70}")
    print(f"  Monte Carlo Analysis ({n_trials} trials, {total_actions} total actions)")
    print(f"{'='*70}")
    print(f"\n  Actions that would violate policy: {violations_ungated}")
    print(f"  Actions caught by gates:           {violations_gated}")
    print(f"  Catch rate:                        {violations_gated/max(violations_ungated,1)*100:.1f}%")
    print(f"\n  Gate fire breakdown:")
    for name, count in sorted(gate_catches.items(), key=lambda x: -x[1]):
        print(f"    {name:30s}  fired {count:4d} times")

# --- Main ---

if __name__ == "__main__":
    print("Deterministic Verification Gates for Tool-Using Agents")
    print("Based on: 'Reason Less, Verify More' (arXiv:2607.07405)\n")

    # Scenario 1: Without gates
    state1 = make_fresh_state()
    actions = generate_scenario_actions(state1)
    results1 = execute_without_gates(state1, actions)
    print_results("WITHOUT GATES (policy-permissive tools)", results1, state1)

    # Scenario 2: With gates
    state2 = make_fresh_state()
    actions = generate_scenario_actions(state2)
    results2 = execute_with_gates(state2, actions, ALL_GATES)
    print_results("WITH GATES (deterministic verification)", results2, state2)

    # Comparison
    ungated_success = sum(1 for r in results1 if r["result"] == "SUCCESS")
    gated_success = sum(1 for r in results2 if r["result"] == "SUCCESS")
    gated_blocked = sum(1 for r in results2 if r["result"] == "GATE_BLOCKED")

    print(f"\n{'='*70}")
    print(f"  Comparison")
    print(f"{'='*70}")
    print(f"  Without gates: {ungated_success}/{len(results1)} calls 'succeeded' "
          f"(including silent violations)")
    print(f"  With gates:    {gated_success}/{len(results2)} calls succeeded, "
          f"{gated_blocked} blocked")
    print(f"  Silent violations prevented: {gated_blocked}")

    # Monte Carlo
    run_monte_carlo()
