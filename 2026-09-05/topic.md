# How an MCP Tool Puts a Clickable App Inside the Chat

**Category**: Building Agents & MCP
**Tags**: security, production, from-scratch
**Date**: 2026-09-05
**Level**: Building
**For**: Building agents
**Hook**: A tool can now hand back a small web page that renders in the conversation, and the page can call your server itself when someone clicks it.
**Time to read**: ~10 minutes
**Engineer's view**: This is the endpoint you wrote for your own frontend, then found strangers calling with curl. Your tool assumed the model decided to call it. Now a button inside a rendered page calls it too, and every check you wrote about why the model wanted this is checking the wrong thing.
**TLDR**: Today a tool sends back text for the model to read. Now it can send back a small web page that appears in the chat, and when the user clicks it, that page calls your server without the model involved.

## Explain Like I'm 5

Imagine a help desk that can only read answers out loud. You ask which flights are available, and
someone reads you a list. You want a different date, so you ask again, and they read a new list.

Now imagine they slide a paper form across the counter instead. You tick the boxes yourself, and the
form goes straight back to the office without anyone reading anything aloud.

That is the change. The desk can hand you something you use directly, rather than words that have to
be read to you.

## The Problem

You have shipped this before, and it had nothing to do with AI. A report was too big to read in an
email, so you built a small web page for it. That page needed its own login, its own session, its
own deploy, and its own copy of the query. Six months later the report changed and you fixed it
twice, because there were two places to fix.

A tool on an agent server is still at the email stage.

A tool returns text. That is the whole contract, and for most tools it is the right one. But some
results are not for reading. Sales by region wants a map you click. A deployment config wants a form
with every option visible at once. A pull request wants a diff you can scroll. Hand those back as
text and the model narrates them to the user one question at a time, while the user answers in
sentences.

Both escapes are bad. Send a link and the user leaves the conversation, and you are back to building
that separate page with its own login. Keep talking and you spend twenty turns rebuilding a form out
of prose.

**The fix is to let the tool return a small web page, rendered inside the conversation, that can
call your tools itself.** That last clause is the one that changes your server, because it means the
model stops being the only thing calling in.

## The Fix: Return a Page the Host Renders in the Conversation

This is the MCP Apps extension. It is opt-in, both sides have to support it, and it combines two
primitives you already have: a tool, and a resource.

### What does the server actually declare?

Two things, and the link between them is one field. The tool carries
`_meta.ui.resourceUri` pointing at a `ui://` address. That address resolves to a resource whose
contents are an HTML page, usually bundled with its own script and styles into a single file.

The host can fetch that resource *before* the tool is called, so the page is already on screen when
the result lands.

### How does the page talk back?

Through a sandboxed iframe, over `postMessage`, speaking its own dialect of the protocol. Some
methods are shared with core MCP, notably `tools/call`. Others are new and carry a `ui/` prefix,
starting with `ui/initialize`.

The sandbox is the part worth reading twice. The page cannot touch the parent document, read the
host's cookies or storage, or navigate the page around it. Its content security policy is
deny-by-default, so loading anything from another origin means declaring it in `_meta.ui.csp`, and
capabilities like the microphone have to be requested in `_meta.ui.permissions`.

Inside that box the page can do three useful things: call a tool on your server, open a link, and
push structured data back into the model's context.

### What happens on a client that has never heard of this?

Both sides advertise. The client declares the extension in its per-request capabilities, the server
declares it in its discovery response, and if either side is missing it, nothing renders.

So the extension makes a rule out of something that is easy to forget: **your tool still has to
return text that means something on its own.** One result now serves two audiences. The page is for
the person, and the text is for the model and for every host that cannot draw the page.

## What This Means for You

**When this matters.** As soon as a tool result is something a user acts on rather than reads.
Picking from a list, filling in a config, approving items one at a time, scrubbing through a
document. If your tool's output is a fact the model reasons over, none of this applies and you
should stay with text.

**How it affects you.** The interesting cost is not the UI work. It is that a tool you wrote with
one caller now has two, and the second one is a button. Any handler that decided what to allow by
reasoning about why the model asked is now deciding on the wrong evidence, because a user clicking
`Refund` is not the model choosing to refund.

**What to do about it.**

1. Open your tool handlers and find the ones that authorize nothing themselves, because the host
   asks the user to approve each call. That is a ten-minute read and it is worth doing whether or
   not you ever ship a UI.
2. For each of those, write down who is allowed to make that call and on what data. If the answer
   is "whoever the host let through", you have found the gap.
3. Return text worth reading from every tool, even the ones you plan to give a UI. That text is
   your fallback, your logs, and what the model sees.
4. Then build one small app for the tool with the worst back-and-forth. `Implementing It` has the
   server side, the page side, and the guard.

## Implementing It

**The change.** Three roles plus a guard, and the guard is the one nobody writes.

*The server author.* A tool declaration and a resource, joined by the `ui://` address:

```typescript
const resourceUri = "ui://pick-region/mcp-app.html";

registerAppTool(server, "pick-region", {
  title: "Pick a region",
  description: "Shows regional sales and lets the user drill in.",
  inputSchema: {},
  _meta: { ui: { resourceUri } },          // the whole link to the UI
}, async () => ({
  content: [{ type: "text", text: summarizeRegions() }],   // still text, always
}));

registerAppResource(server, resourceUri, resourceUri,
  { mimeType: RESOURCE_MIME_TYPE },
  async () => ({ contents: [{ uri: resourceUri,
                              mimeType: RESOURCE_MIME_TYPE,
                              text: await readFile("dist/mcp-app.html", "utf-8") }] }));
```

Notice what the tool still returns: text. The page is declared in metadata, never in the result, so
a host that ignores `_meta` sees an ordinary tool and gets an ordinary answer. That is the whole
compatibility story, and it costs you nothing as long as the text stays real.

*The page author.* Connect, take the first result the host pushes, and call back on interaction:

```typescript
const app = new App({ name: "Region Picker", version: "1.0.0" });
app.connect();

app.ontoolresult = (result) => render(result);   // the initial call's result

button.addEventListener("click", async () => {
  const fresh = await app.callServerTool({ name: "pick-region",
                                           arguments: { region: selected } });
  render(fresh);            // note: a real round trip, so show a pending state
});
```

*The guard.* This is the new work. The handler can no longer infer permission from the fact that it
was called, so check inside it:

```typescript
async function handler(args, ctx) {
  if (!allowed(ctx.userId, "pick-region", args.region)) {
    throw new Error("not permitted for this user");   // fails the same either way
  }
  return { content: [{ type: "text", text: summarizeRegions(args.region) }] };
}
```

Write it so the answer does not depend on whether a model or a button made the call. If the two
paths need different rules, that is a decision to make deliberately rather than inherit.

**How you know it worked.** Three checks, cheapest first.

Call the tool from a host without the extension and read what comes back. If the text is a stub
like `see the app`, the fallback is broken and every client that cannot render your page gets
nothing. That is also what the model sees.

Then log the caller on every invocation and watch the split. A tool with a UI should show both
kinds of traffic within a day. If you only ever see model-initiated calls, the page is not wired up;
if you only see app-initiated ones, the model is not being told what the tool is for.

Finally, try to break the sandbox on purpose. Load an external script the page never declared and
confirm the content security policy blocks it. A page that loads anything you did not put in
`_meta.ui.csp` means the policy is not doing its job, and you would rather learn that from your own
test than from someone else's.

## When an MCP App Is the Wrong Tool

Most tools should stay text, and that is not a limitation. A model cannot see your page. Anything
the model needs to reason over, chain into the next call, or quote back to the user has to arrive as
text regardless, so a UI adds work without removing any.

It is also a web app you now ship inside a server, with everything that implies: a bundle step, a
content security policy, and a fresh place for a cross-site scripting bug to live. Before this, a
compromised tool returned bad text. Now it can return bad markup that runs in the user's session.
The sandbox is why that is survivable, and it is also why you should not fight it.

Latency is easy to miss. Every click that calls a tool is a real round trip to your server, so a
page that felt instant while you developed it against localhost will not feel that way over a
tunnel. Design the pending states before you need them.

And be honest about the evidence here. This is a specification with an implementation, not a result:
there are no published numbers on whether users complete tasks faster this way. The design argument
is strong and the measurement does not exist yet.

Three questions before you build one:

1. Does the user act on this result, or only read it?
2. If a button calls this tool, is my handler still right?
3. What does a host that cannot render the page get?

## Glossary

- **tool** — a function an MCP server exposes, which until now always returned text or data
- **resource** — an addressable thing a server serves, here the bundled HTML page itself
- **host** — the application the user is talking to, which renders the page and brokers every call
- **sandbox** — the restricted iframe the page runs in, with no access to the surrounding document
- **extension** — an opt-in addition to the protocol that both sides must advertise before it is used
- **fallback** — the plain text the tool returns for clients and models that cannot use the page
