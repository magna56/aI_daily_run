# Further Reading: How an MCP Tool Sends Back an Image, a File, or Audio

## Articles

### 1. [Tools — the tool result section](https://modelcontextprotocol.io/specification/latest/server/tools)
**Source**: Model Context Protocol specification | **Date**: current | **Read time**: ~20 min
> The primary source, and the section to jump to is "Tool Result". Every block shape in this session
> is written out there with a worked JSON example: `text`, `image`, `audio`, `resource_link`, and
> embedded `resource`. Read it once and the thing that stands out is how ordinary it is — none of
> this is new, none of it is negotiated, and the note that all five types accept annotations is a
> single sentence most people scroll past.

### 2. [Resources — annotations, and text against blob](https://modelcontextprotocol.io/specification/latest/server/resources)
**Source**: Model Context Protocol specification | **Date**: current | **Read time**: ~15 min
> Where `audience` and `priority` are actually defined, with their allowed values, and the reason to
> read it even though this session is about tools: the annotation format is shared, so what you
> learn here applies to resources, prompts and tool results alike. It also settles `text` against
> `blob`, and carries the `https://` rule worth knowing before you pick a URI scheme — use it only
> when the client can fetch the thing without coming back through you.

### 3. [MCP Apps: interactive UI applications](https://modelcontextprotocol.io/extensions/apps/overview)
**Source**: Model Context Protocol specification | **Date**: current | **Read time**: ~15 min
> The contrast, and worth reading to see where the boundary sits. Apps is an opt-in extension for
> results a user *interacts* with — a form, a map you drill into — and both sides have to support
> it. Everything in today's session is core protocol that needs no negotiation at all. Read this
> when a picture is genuinely not enough, and note how much more machinery that costs you.

### 4. [Example servers, including media](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples)
**Source**: Model Context Protocol on GitHub | **Date**: current | **Read time**: ~20 min
> The one to open in an editor. `qr-server` and `pdf-server` are the shortest way to see a real
> server hand back something that is not prose, and `say-server` does the audio case end to end.
> They are built on the Apps extension rather than plain content blocks, so read them for the
> delivery shape rather than as a template — the core-protocol version is strictly less code.
