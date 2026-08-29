"""
MCP Tasks (io.modelcontextprotocol/tasks), both halves, in one file.

TaskStore is the server half: it returns CreateTaskResult and serves tasks/get
and tasks/update. poll() is the client half: it handles either result shape,
polls at pollIntervalMs, answers input_required, and resumes from a persisted
taskId. Lift either one straight out. The clock is simulated, so the
twenty-minute job finishes instantly.

Run: python3 code_example.py
Spec: https://github.com/modelcontextprotocol/ext-tasks (revision 2026-07-28)
"""

import json
import secrets

# --- knobs ------------------------------------------------------------------
JOB_SECONDS = 20 * 60      # how long the tool really runs. Raise it: the poll
                           # count grows, the model-token cost stays at zero.
POLL_INTERVAL_MS = 5000    # what the server suggests in pollIntervalMs
TTL_MS = 3_600_000         # server may delete the task after this
CONVERSATION_TOKENS = 8000 # size of the agent's context, for the comparison below


class TaskStore:
    """Server side. Swap the dict for Redis or a table and nothing else here
    changes: the point is that task state lives where every replica can read it."""

    def __init__(self):
        self._tasks = {}

    def create(self, needs_input_at, finishes_at, now):
        # A taskId is a bearer token for server-side state: real entropy, never
        # a counter. And the spec forbids returning the handle before tasks/get
        # would resolve, so the row is written before the caller sees the id.
        task_id = secrets.token_urlsafe(24)
        self._tasks[task_id] = {
            "status": "working", "createdAt": now, "lastUpdatedAt": now,
            "needs_input_at": needs_input_at, "finishes_at": finishes_at,
            "answered": False, "inputRequests": {},
        }
        return {"resultType": "task", "taskId": task_id, "status": "working",
                "statusMessage": "Deploy queued.", "createdAt": iso(now),
                "lastUpdatedAt": iso(now), "ttlMs": TTL_MS, "pollIntervalMs": POLL_INTERVAL_MS}

    def get(self, task_id, now):
        t = self._tasks.get(task_id)
        if t is None:                       # purged after TTL, or never existed
            raise JsonRpcError(-32602, "Failed to retrieve task: Task not found")
        self._advance(t, now)
        out = {"resultType": "complete", "taskId": task_id, "status": t["status"],
               "createdAt": iso(t["createdAt"]), "lastUpdatedAt": iso(now),
               "ttlMs": TTL_MS, "pollIntervalMs": POLL_INTERVAL_MS}
        if t["status"] == "input_required":
            out["inputRequests"] = t["inputRequests"]
        if t["status"] == "completed":
            # A tool that ran fine but failed its own business logic is completed
            # with isError inside result — NOT status "failed".
            out["result"] = {"content": [{"type": "text", "text": "Deployed rev 41a9."}], "isError": False}
        return out

    def update(self, task_id, input_responses, now):
        t = self._tasks[task_id]
        # Ignore responses for keys that are not outstanding: unknown, already
        # answered, or superseded. This is what makes client retries safe.
        for key in list(t["inputRequests"]):
            if key in input_responses:
                t["answered"] = True
                del t["inputRequests"][key]
        if not t["inputRequests"]:
            t["status"] = "working"
        return {"resultType": "complete"}

    def _advance(self, t, now):
        if t["status"] in ("completed", "failed", "cancelled"):
            return
        if not t["answered"] and now >= t["needs_input_at"]:
            t["status"] = "input_required"
            schema = {"type": "object", "properties": {"ok": {"type": "boolean"}},
                      "required": ["ok"]}
            t["inputRequests"] = {"confirm_prod": {
                "method": "elicitation/create",
                "params": {"mode": "form", "message": "Deploy to production?",
                           "requestedSchema": schema}}}
        elif t["answered"] and now >= t["finishes_at"]:
            t["status"] = "completed"


class JsonRpcError(Exception):
    def __init__(self, code, message):   # code travels to the client verbatim
        super().__init__(message)
        self.code = code


def iso(seconds):
    s = int(seconds)
    return f"2026-08-29T12:{s // 60:02d}:{s % 60:02d}Z"


def call_tool(store, on_input, clock):
    """The server decides per request whether to return a task, so every
    tools/call site must handle both shapes."""
    res = store.create(clock[0] + 300, clock[0] + JOB_SECONDS, clock[0])
    if res.get("resultType") != "task":
        return res, 0, 0                       # ordinary CallToolResult
    return poll(store, res["taskId"], on_input, clock)  # persist taskId first


def poll(store, task_id, on_input, clock):
    """Resumable: hand it a taskId read back from disk after a restart."""
    polls, wire_bytes, seen = 0, 0, set()
    while True:
        clock[0] += POLL_INTERVAL_MS / 1000
        task = store.get(task_id, clock[0])
        polls += 1
        wire_bytes += len(json.dumps({"method": "tasks/get", "params": {"taskId": task_id}}))
        wire_bytes += len(json.dumps(task))
        if task["status"] == "input_required":
            # Dedupe on the key: the same request reappears on every poll until
            # you answer it, and showing a user the same prompt twice is a bug.
            fresh = {k: v for k, v in task["inputRequests"].items() if k not in seen}
            seen.update(fresh)
            if fresh:
                store.update(task_id, {k: on_input(v) for k, v in fresh.items()}, clock[0])
        elif task["status"] in ("completed", "failed", "cancelled"):
            return task, polls, wire_bytes


def main():
    clock = [0.0]
    task, polls, wire_bytes = call_tool(
        TaskStore(), lambda req: {"action": "accept", "content": {"ok": True}}, clock)

    print(f"final status      {task['status']}  after {clock[0] / 60:.0f} simulated minutes")
    print(f"tasks/get polls   {polls}")
    print(f"protocol traffic  {wire_bytes / 1024:.1f} KB")
    print(f"model turns spent 0\n")

    # The alternative most servers ship today: return "job 7f2a started" as text
    # and let the model remember to call check_job. Every check is a model turn,
    # and every turn re-reads the whole conversation.
    checks = JOB_SECONDS // 30
    print(f"text-handle baseline: {checks} model turns to notice it finished")
    print(f"  context re-read     {checks * CONVERSATION_TOKENS:,} tokens")
    print("  and the deploy is lost entirely if the agent restarts")


if __name__ == "__main__":
    main()
