# The Loop Is Cheap. Serving and Checks Are the Job.

**Category**: AI in Production
**Tags**: agents, production, cost
**Date**: 2026-08-23
**Level**: Building
**For**: Building agents
**Hook**: An agent is a loop around tools. Production is the cache, the bill, and the check the model cannot talk past.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

A kid with a walkie-talkie can ask a grown-up to open a door, look in a box, or write a note. That is the loop: think, ask, look, think again. The dangerous part is not the walkie-talkie. It is the kid who can open *every* door, the phone bill when they ask a hundred times, and the grown-up who believes "I already locked it" without checking the latch.

## The Problem

A demo agent is a while-loop: model, parse a tool call, run it, append the result, repeat. That fits in an afternoon. Production is the part the demo skips: prefix caching so you do not re-pay the system prompt, timeouts so a hung tool does not hold a worker, a verifier so "I migrated the table" is not accepted on vibe, and a bill that does not explode when one user pastes a repo.

## For a Software Engineer

Treat the model as a CPU that only emits tokens. Tools are syscalls. Your harness is the kernel: schema, allowlist, retries, and policy. Prompt cache helps when the *prefix* is stable — system prompt, tool list, and long static context. If you mutate the prefix every turn (new timestamp at the top, shuffled tools), you miss the cache and pay full prefill.

Scale is not "more agents." It is stateless request handling where you can, sticky sessions where you must, and a hard cap on loop steps. Serving many users means the same rules as any API: idempotent tools, bounded work, and an eval that fails the build when the loop starts deleting the wrong thing.

Monday morning: write down the prefix that should stay frozen. Put a step budget on the loop. Wrap every write tool in a check the model cannot rewrite.

## What This Means for You

**When this matters**: you are moving an agent from a laptop demo to something other people can hit.

**How it affects you**: the model will call the wrong tool, call it twice, or claim success. Cost will hide in uncached prefills and retries. A missing verifier is an incident, not a polish item.

**What to do about it**: freeze the cacheable prefix. Log every tool call with arguments and result hashes. Cap steps. Put deterministic checks on writes. Load-test the loop, not the single completion.

## What It Is

An agent in production is four layers:

1. **Loop** — sample, parse, act, append.
2. **Tools** — typed, allowlisted, timeouted, preferably idempotent.
3. **Serving** — batching, cache hits, queue limits, isolation per tenant.
4. **Checks** — evals, blast-radius gates, human review on the writes that can hurt.

Interviews like to stay on layer 1. Outages live on 2–4.

## Why It Matters

This is why a "working" agent still cannot ship. The loop is a few hundred lines. The production surface is the same as a payment API plus a model that will improvise. If you only optimize the prompt, you will miss the cache, the retry storm, and the tool that has no rollback.

It is also why MCP, skills, and subagents are not a personality upgrade. They are more prefix and more syscalls. Each one must inherit the same budget and the same checks.

## Key Technical Details

**Background first.** *Prefill* is processing the prompt. *Decode* is emitting new tokens. *Prompt cache* reuses the KV state of a repeated prefix. *Blast radius* is how far a successful tool call can reach.

- **Cache the static prefix.** Tools and policy belong there if they do not change every call.
- **Cap the loop.** A runaway tool-call storm is a cost and a safety bug.
- **Idempotency keys on writes.** The model will double-submit.
- **Verify outside the model.** Parse, lint, migrate --dry-run, row counts — the model does not get a vote.
- **Isolate tenants.** One user's repo is not another's prompt.

## How It Connects to What You Know

A web worker that calls Stripe is not "done" when the happy-path handler works. You still need retries, idempotency, and a reconciliation job. An agent is that worker with a nondeterministic planner. You already know not to trust `res.ok` without checking the ledger. Do the same for "the model said it finished."

That is the last primer. The daily lab is a different pile — today's paper or changelog, not this shelf.

## Try It Yourself

`code_example.py` runs a tiny agent loop with a cached prefix, a write tool, and a verifier. Toggle cache-busting and the verifier to see the bill and the lie.

## Glossary

- **Agent loop** — sample, tool, observe, repeat.
- **Prefill** — the expensive pass over the prompt.
- **Prompt cache** — reuse of a stable prefix's compute.
- **Blast radius** — how much a tool can change if it succeeds.
- **Verifier** — a check the model cannot talk its way around.
- **Idempotent tool** — running it twice does not double the damage.
