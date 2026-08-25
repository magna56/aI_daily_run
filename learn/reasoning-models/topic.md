# How Reasoning Models Work

**Category**: New Models & APIs
**Tags**: training, cost
**Date**: 2026-08-23
**Level**: Building
**For**: How models work
**Hook**: A reasoning model is the same weights spending extra tokens before it answers — you buy quality with time and money.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5

Sometimes you ask a friend a hard question and they sit quietly scribbling on scratch paper before they speak. They did not become a different person. They spent more time. The scratch paper still counts as talking — you wait, and you pay for the paper. "Think harder" in these products is that extra scribbling, not a new brain in the box.

## The Problem

Vendors ship a "reasoning" or "thinking" SKU next to a fast one. Teams treat the thinking SKU as strictly smarter and route everything to it. Bills jump. Latency jumps. Easy tickets get a three-page inner monologue. Hard tickets still fail if the prefix is missing the file. You did not buy a new capability class. You bought test-time compute — more tokens before the user-visible answer — and you applied it with a blunt default.

## For a Software Engineer

This is the same trade as turning on `-O3` or running a fuzzer longer: extra work at *request* time, same program. A reasoning model is usually the same (or sibling) weights with a training recipe that makes long scratchpad tokens likely, plus a product that hides those tokens or bills them on a different meter.

The number worth feeling: if the hidden chain is 2,000 tokens and the answer is 200, you paid for ~10× the generation of a direct reply — every time, including "rename this variable." That can be worth it on a gnarly proof or a multi-file root cause. It is waste on a format conversion.

Monday morning: split your traffic. Fast model / no thinking for tool routing, classify, commit messages, "what does this error mean?" Thinking SKU for tasks you would be willing to wait 30–60 seconds on and review. Cap thinking tokens if the API has a knob. Do not A/B "smarter" without measuring both quality *and* p95 latency.

## What This Means for You

**When this matters**: you are picking a default model in Cursor or an API router, and one option says it "thinks."

**How it affects you**: quality per dollar is a product choice. A reasoning default on a high-QPS agent will dominate the bill and still not read a file you never fetched (lesson 4).

**What to do about it**: make thinking an explicit mode, like "run the slow tests." Log thinking tokens separately. If the vendor hides the scratchpad, you still pay for it — read the usage fields.

## What It Is

At runtime it is still next-token prediction (lesson 1). The difference is *what tokens come first*. A reasoning model is trained (often with reinforcement on graded tasks) so that a long intermediate trace is a likely continuation. The product may stream that trace, hide it, or summarize it.

Test-time compute means: spend more inference to get a better answer from the same weights — sample longer, search, vote, or think. Training-time compute is a bigger or longer-trained model. They are not interchangeable. A small model thinking longer can beat a large model answering immediately on some math and code benches. It will not invent your private API.

"Extended thinking" sliders are usually a token budget on that scratchpad. They are temperature's cousin: a knob with a real cost, not a personality.

## Why It Matters

If you do not name the trade, someone will set the org default to the thinking SKU because the eval chart went up. Eval charts rarely include your p95 or your tool-call format. Reasoning is a different *product* — slower, pricier, sometimes better on hard items. Treat it like reserved instances vs on-demand, not like "the smart one."

## Key Technical Details

**Background first.** *Test-time compute* is extra inference per request. *Chain of thought* is intermediate tokens. *Reasoning model* is a checkpoint + product behavior that makes those tokens likely and (often) hidden.

- **Hidden tokens still bill.** Check `output_tokens` / thinking-specific fields, not just the visible reply.
- **Thinking does not replace tools.** A long scratchpad about a missing file is still a missing file.
- **Stop sequences and JSON mode still apply.** A reasoning model that rambles before `{` will break your parser unless you constrain it (lesson 2).
- **Caps exist for a reason.** Unlimited thinking is an unbounded loop with a nicer name.

## How It Connects to What You Know

You already buy latency with more CPU on a request. This is that, billed per token. Speculative decoding and cascades (cheaper model first) are the other side of the same budget.

Previous: [How the Agent Loop Works](#learn/the-agent-loop). Next: [How the Forward Pass Runs](#learn/how-the-forward-pass-runs).

## Try It Yourself

`code_example.py` pretends two decoders — "answer now" vs "scratch then answer" — on the same tiny task and prints token counts and a fake latency so the 10× generation cost is visible.

## Glossary

- **Test-time compute** — extra inference spent on one request.
- **Chain of thought** — intermediate tokens before the final answer.
- **Reasoning model** — a product/checkpoint that spends those tokens on purpose.
- **Thinking budget** — a cap on how many scratchpad tokens you will buy.
