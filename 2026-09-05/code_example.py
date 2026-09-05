"""Typed tool results: one call, two readers, and what inlining costs.

Builds MCP tool results the way the core spec allows -- typed content blocks with
audience annotations -- and routes them the way a client should. No network, no
SDK, no extension: every shape here is core protocol.

Three things it shows:
  * a result that answers with a file path leaves the model nothing to reason
    about and the user nothing to look at
  * a typed result carries the picture for the person and the fact for the model,
    and each side gets only its own copy
  * inlining is not a one-off charge -- an embedded blob is re-sent on every turn
    for the rest of the session

Run: python3 code_example.py

Raise ARTIFACT_KB past INLINE_LIMIT_KB and watch deliver() switch to a link.
"""

import base64

# --- knobs: edit these ---------------------------------------------------
ARTIFACT_KB = 180          # the chart you just rendered
INLINE_LIMIT_KB = 256      # inline below this, link above it
TURNS_AFTER = 8            # how many more turns the session runs
BASE64_OVERHEAD = 4 / 3    # base64 costs about a third extra
BYTES_PER_TOKEN = 4        # rough, and only used to price context


def text_block(text, audience=("assistant",), priority=0.6):
    return {"type": "text", "text": text,
            "annotations": {"audience": list(audience), "priority": priority}}


def image_block(png, mime="image/png", audience=("user",), priority=0.9):
    return {"type": "image", "data": base64.b64encode(png).decode(), "mimeType": mime,
            "annotations": {"audience": list(audience), "priority": priority}}


def deliver(name, payload, mime, limit_kb=INLINE_LIMIT_KB):
    """Inline what is small, link what is not. The whole size policy, one place.

    An embedded blob lands in the conversation and is re-sent on every later
    turn; a link is a URI the client fetches only if it needs to.
    """
    if len(payload) <= limit_kb * 1024:
        return {"type": "resource",
                "resource": {"uri": "file:///tmp/" + name, "mimeType": mime,
                             "blob": base64.b64encode(payload).decode()}}
    return {"type": "resource_link", "uri": "file:///tmp/" + name,
            "name": name, "mimeType": mime}


def route(content):
    """The client side. A missing audience means BOTH, never one or the other.

    Defaulting to "user" silently hides results from the model, which looks like
    the model being stupid rather than like a bug in your client.
    """
    to_screen, to_model = [], []
    for block in content:
        who = (block.get("annotations") or {}).get("audience") or ["user", "assistant"]
        if "user" in who:
            to_screen.append(block)
        if "assistant" in who:
            to_model.append(block)
    return to_screen, to_model


def context_tokens(blocks):
    """What the model's context pays for these blocks, this turn."""
    total = 0
    for b in blocks:
        if b["type"] == "text":
            total += len(b["text"])
        elif b["type"] in ("image", "audio"):
            total += len(b["data"])
        elif b["type"] == "resource":
            r = b["resource"]
            total += len(r.get("blob") or r.get("text") or "")
        elif b["type"] == "resource_link":
            total += len(b["uri"]) + len(b.get("name", ""))
    return round(total / BYTES_PER_TOKEN)


def describe(blocks):
    out = []
    for b in blocks:
        if b["type"] == "text":
            out.append("text(%d chars)" % len(b["text"]))
        elif b["type"] == "image":
            out.append("image(%s, %dkB)" % (b["mimeType"], len(b["data"]) // 1024))
        elif b["type"] == "resource":
            out.append("resource(inline %dkB)" % (len(b["resource"]["blob"]) // 1024))
        elif b["type"] == "resource_link":
            out.append("resource_link(%s)" % b["name"])
    return ", ".join(out) or "nothing"


def can_answer(to_model, question_needs):
    """Could the model answer from what it was actually given?"""
    return any(b["type"] == "text" and question_needs in b["text"] for b in to_model)


def main():
    png = b"\x89PNG" + b"\x00" * (ARTIFACT_KB * 1024 - 4)

    # 1. What most tools return today.
    naive = {"content": [{"type": "text", "text": "Chart saved to /tmp/plot.png"}]}
    # 2. What the protocol has always allowed.
    typed = {"content": [
        image_block(png),
        text_block("Revenue by region. Peak: EU at $288k across 5 regions."),
    ]}

    print("Two results for the same tool call\n")
    for label, result in (("answers with a path", naive), ("typed blocks", typed)):
        screen, model = route(result["content"])
        print("  %-20s" % label)
        print("     user sees      %s" % describe(screen))
        print("     model receives %s" % describe(model))
        print("     model can name the peak region: %s\n"
              % ("yes" if can_answer(model, "EU") else "no"))

    # 3. Inlining is charged again on every later turn.
    print("What the picture costs the conversation (%dkB artifact)\n" % ARTIFACT_KB)
    inline = deliver("plot.png", png, "image/png", limit_kb=10_000)   # force inline
    linked = deliver("plot.png", png, "image/png", limit_kb=1)        # force link
    print("  %-16s %10s %14s %16s" % ("delivery", "this turn", "after %d turns" % TURNS_AFTER, "what arrives"))
    for label, block in (("embedded", inline), ("resource_link", linked)):
        first = context_tokens([block])
        print("  %-16s %9s %13s   %s"
              % (label, "{:,}".format(first), "{:,}".format(first * (TURNS_AFTER + 1)),
                 describe([block])))

    chosen = deliver("plot.png", png, "image/png")
    print("\n  at INLINE_LIMIT_KB=%d, deliver() chose: %s" % (INLINE_LIMIT_KB, describe([chosen])))
    print("\n  Base64 adds about a third before any of this, and an embedded blob")
    print("  is re-sent with the whole transcript on every turn that follows it.")


if __name__ == "__main__":
    main()
