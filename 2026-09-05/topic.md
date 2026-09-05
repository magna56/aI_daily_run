# How an MCP Tool Sends Back an Image, a File, or Audio

**Category**: Building Agents & MCP
**Tags**: multimodal, production, from-scratch
**Date**: 2026-09-05
**Level**: Building
**For**: Building agents
**Hook**: A tool result is not one string. It can carry a picture the person sees and a summary the model reads, addressed separately.
**Time to read**: ~10 minutes
**Engineer's view**: This is a Content-Type you never set. You have been packing a chart into a text field and hoping the model describes it, when the protocol has a typed image block the client renders. An audience field lets one result send the picture to the person and the numbers to the model.
**TLDR**: A tool does not have to answer in text. It can hand back a picture, a sound file, or a link to a document, and mark each part for the person, the model, or both.

## Explain Like I'm 5

Imagine posting someone a parcel, but the only thing the post office accepts is a written note. You
want to send a photograph, so you describe the photograph in words and hope they picture it.

Then you find out parcels were allowed the whole time. You can post the photograph itself. You can
even put two things in one parcel, with a label saying which is for them and which is for their
assistant to file.

Nothing about the post office changed. You had just never read that page.

## The Problem

You have shipped this before, and it had nothing to do with AI. An endpoint had to return a
generated chart, and the response schema said `message: string`. So you base64'd the image into the
message field and told the client to look for a data URI. It worked.

Then the logs filled with megabytes of base64. The error tracker truncated the field. A year later
somebody added a length check and the chart quietly stopped arriving.

The bug was not the encoding. It was putting typed data into a field that was typed for something
else, because that field was the one already there.

Tool results have the same shape and the same temptation. A tool that renders a chart writes a file
and returns `"saved to /tmp/plot.png"`. A tool that transcribes audio returns a paragraph about the
audio. The result is a string, so everything becomes a string, and the person on the other end gets
a description of a picture instead of the picture.

**The fix is to use the typed content block the protocol already has, and to say who each part is
for.** A tool result is a list, not a string. It can hold an image, an audio clip, a link to a file,
or all three, and each block can be addressed to the person, the model, or both.

## The Fix: Return Typed Blocks and Address Each One

This is core protocol, not an extension. Nothing to negotiate, no opt-in on either side: a tool
result has carried these types all along, and most servers only ever use the first.

### What can a block actually be?

Five types, and the first is the only one most tools use:

| Type | Shape | Use it for |
| --- | --- | --- |
| `text` | `{ type, text }` | Anything the model must read |
| `image` | `{ type, data, mimeType }` | A chart, a screenshot, a rendered page |
| `audio` | `{ type, data, mimeType }` | Speech, an alert tone, a clip you generated |
| `resource_link` | `{ type, uri, name, mimeType }` | Something too big to inline |
| `resource` | `{ type, resource: { uri, mimeType, text or blob } }` | Something small enough to inline |

`image` and `audio` carry base64 in `data`. An embedded `resource` uses `text` or `blob` depending
on whether it is text or binary.

```figure
{
 "kind": "anatomy",
 "title": "What one typed block actually looks like",
 "lines": [
  "{",
  "  \"type\": \"image\",",
  "  \"data\": \"iVBORw0KGgo…\",",
  "  \"mimeType\": \"image/png\",",
  "  \"annotations\": {",
  "    \"audience\": [\"user\"],",
  "    \"priority\": 0.9",
  "  }",
  "}"
 ],
 "callouts": [
  {
   "line": 1,
   "t": "The typed block the client renders. Core protocol, nothing negotiated.",
   "s": "new"
  },
  {
   "line": 5,
   "t": "Who this block is for. Leave it out and it goes to both readers.",
   "s": "ok"
  }
 ]
}
```

### How does one result serve both the person and the model?

This is the part worth the read, and it is three words of metadata. Every block takes an
`annotations` object:

```json
{ "type": "image", "data": "iVBORw0…", "mimeType": "image/png",
  "annotations": { "audience": ["user"], "priority": 0.9 } }
```

`audience` is an array of `"user"`, `"assistant"`, or both. `priority` runs 0.0 to 1.0, where 1 is
effectively required and 0 is entirely optional.

That solves the problem the whole topic circles. **A model cannot see your chart.** It can see a
sentence about the chart. So return both: the image marked for the user, the numbers marked for the
assistant. One tool call, one result, two readers, and neither gets the other's copy.

```figure
{
 "kind": "route",
 "title": "One result, two readers, neither carrying the other's copy",
 "source": "one tool result",
 "parts": [
  {
   "t": "image block, 240 kB encoded",
   "via": "audience: [\"user\"]",
   "to": 0,
   "s": "new"
  },
  {
   "t": "text block, “Peak: EU at $288k”",
   "via": "audience: [\"assistant\"]",
   "to": 1,
   "s": "ok"
  }
 ],
 "dests": [
  {
   "t": "the person's screen",
   "s": "new"
  },
  {
   "t": "the model's context",
   "s": "ok"
  }
 ],
 "note": "The annotation is the whole mechanism. Drop it and both blocks travel to both places, so the model pays for pixels it cannot read."
}
```

### When do I link instead of embed?

Size decides it. Base64 inflates by about a third and every byte lands in the conversation, so a
40 MB video embedded in a result is 53 MB of context nobody asked for. Return a `resource_link`
instead and the client fetches it only if it needs it.

One rule on the `https://` scheme: use it only when the client can fetch the thing itself without
going back through your server.

## What This Means for You

**When this matters.** Any tool whose real output is not prose. Chart and diagram generators,
screenshot tools, anything producing a PDF or a spreadsheet, transcription and speech tools, and
anything that currently answers with a file path.

**How it affects you.** Two things change. Your users stop reading descriptions of things and start
seeing the things, which needs no model cooperation at all. And your context bill drops, because a
picture marked for the user does not have to be narrated into the transcript in order to reach them.

The interactive-page extension covered elsewhere is a different tool for a different job. That one
needs both sides to opt in and support is still uneven. This is core protocol and has been for a
long time, so it works on far more clients today.

**What to do about it.**

1. Grep your tool handlers for `"saved to"`, `"see the file at"`, and any path you return as prose.
   Each hit is a result that should be typed. This takes five minutes and needs no code change.
2. Pick the one whose output a person actually looks at, and return an `image` block instead.
3. Then add the annotations. Mark the picture for the user and add a short text block for the
   assistant, so the model can still reason about what it just produced.
4. Check the size before you inline anything. `Implementing It` has the threshold and the link form.

## Implementing It

**The change.** Three roles, and the third is the one that keeps your context bill down.

*The tool author.* Return a list, not a sentence. The typed block and the model's copy are two
entries in the same result:

```python
def render_chart(args):
    png = plot(args["rows"])                      # bytes
    return {"content": [
        {"type": "image",
         "data": base64.b64encode(png).decode(),
         "mimeType": "image/png",
         "annotations": {"audience": ["user"], "priority": 0.9}},
        {"type": "text",
         "text": f"Revenue by region, {len(args['rows'])} rows. Peak: EU at $288k.",
         "annotations": {"audience": ["assistant"], "priority": 0.6}},
    ]}
```

The text block is not a caption for the human. It is the only thing the model will ever know about
that image, so write it as the fact you want reasoned over, not as alt text.

*The size check.* Inline small, link large. Pick a threshold and enforce it in one place:

```python
INLINE_LIMIT = 256 * 1024        # base64 adds ~33% on top of this

def deliver(path, mime):
    if os.path.getsize(path) <= INLINE_LIMIT:
        blob = base64.b64encode(open(path, "rb").read()).decode()
        return {"type": "resource",
                "resource": {"uri": f"file://{path}", "mimeType": mime, "blob": blob}}
    return {"type": "resource_link", "uri": f"file://{path}",
            "name": os.path.basename(path), "mimeType": mime}
```

*The client author.* Read the annotations rather than rendering everything. A block marked
`["assistant"]` is not for the screen, and one marked `["user"]` should not be pushed into the
model's context as base64:

```python
for block in result["content"]:
    who = (block.get("annotations") or {}).get("audience") or ["user", "assistant"]
    if "user" in who:      render(block)
    if "assistant" in who: to_model.append(block)
```

Note the default when `audience` is absent: both. Treating a missing annotation as "user only"
silently hides results from the model, which is a bug that looks like the model being stupid.

**How you know it worked.** Three checks, cheapest first.

Call the tool and read the raw result rather than the rendered one. You are looking for a `content`
array with more than one entry and a `mimeType` that is not `text/plain`. If it is a single text
block containing a path, nothing has changed yet.

Then watch your input tokens on a call that returns an image. If they jump by roughly a third more
than the file size, you inlined something that should have been a link, and the size check above is
not being hit.

Finally, ask the model a question that only the text block can answer — "which region peaked?" — and
confirm it answers without the image. If it cannot, your assistant-facing block is missing or is
alt text rather than content, and the model has been guessing from the filename.

## When Sending Media Is the Wrong Tool

A model cannot see pixels the way your user can. Some can read an image, many cannot, and none
should be relied on to extract a number from a chart you could have sent as a number. If the value
matters, send the value as text. The picture is for the person.

Inlining has a real cost and it is worse than it looks: base64 adds about a third, and every byte
sits in the conversation for the rest of the session, re-sent on every subsequent turn. A large
embedded file is not a one-off charge. That is what `resource_link` exists to avoid.

Client support is uneven for the display half. Every client can technically receive these blocks,
but whether a picture is shown, downloaded, or quietly dropped depends on the host. Your text block
is what makes the result survive a client that renders nothing, so it is not optional politeness.

And binary from a tool is a security surface. The spec is blunt about validating URIs and sanitizing
file paths against directory traversal, because a `file://` link is a request for the client to open
something you named.

Three questions before you return media:

1. Does a person look at this output, or only the model?
2. How big is it, and will it be re-sent on every turn after this one?
3. If the client shows nothing, does my text block still answer the question?

## Glossary

- **content block** — one entry in a tool result's list, carrying a type and its data
- **audience** — an annotation naming who a block is for: the user, the assistant, or both
- **priority** — an annotation from 0.0 to 1.0 saying how important a block is to include
- **embedded** — data sent inline in the result itself, rather than referred to by address
- **base64** — the text encoding used for binary here, which costs about a third in extra size
