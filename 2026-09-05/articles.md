# Further Reading: How an MCP Tool Puts a Clickable App Inside the Chat

## Articles

### 1. [MCP Apps: interactive UI applications](https://modelcontextprotocol.io/extensions/apps/overview)
**Source**: Model Context Protocol specification | **Date**: current | **Read time**: ~15 min
> The primary source, and read the security section twice rather than once. It sets out exactly what
> the sandbox does and does not stop — no parent document, no cookies, no navigating the page around
> it — which is the boundary every other decision in this session rests on. The sequence diagram
> partway down is the clearest statement anywhere of the thing this write-up is about: the arrow
> from the app back to the server that never passes through the model.

### 2. [Build an MCP App](https://modelcontextprotocol.io/extensions/apps/build)
**Source**: Model Context Protocol documentation | **Date**: current | **Read time**: ~25 min
> The one to follow with an editor open. It walks the complete loop — `registerAppTool` with the
> `_meta.ui.resourceUri` field, `registerAppResource` serving the bundled HTML, then the page side
> with `app.connect()`, `ontoolresult` and `callServerTool`. The bundling advice matters more than
> it looks: the iframe's content policy is deny-by-default, so either you inline your assets or you
> declare every origin, and finding that out at the end of a build is a bad afternoon.

### 3. [ext-apps: eighteen example servers](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples)
**Source**: Model Context Protocol on GitHub | **Date**: current | **Read time**: ~20 min
> Read two of these before writing your own, and pick them from opposite ends. `qr-server` is about
> as small as an app gets and shows the shape without ceremony. `system-monitor-server` is the
> push-updates case, where the page keeps changing without the user asking. The repository also
> holds `basic-host`, which is the fastest way to see your own app render without wiring up a real
> client first.

### 4. [MCP extensions: negotiation and graceful degradation](https://modelcontextprotocol.io/extensions/overview)
**Source**: Model Context Protocol specification | **Date**: current | **Read time**: ~10 min
> The half of the contract that is easy to skip and expensive to skip. It gives the exact shape of
> how both sides advertise support, and it states the rule this session leans on — a server offering
> UI-enhanced tools still owes meaningful text to clients that cannot render them. Worth reading
> even if you never ship an app, because the same negotiation governs every extension, including the
> Tasks one.
