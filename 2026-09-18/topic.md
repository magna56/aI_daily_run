# How to Decide What Falls Out of Your Prompt First

**Category**: Building Agents & MCP
**Tags**: context-engineering, prompt-engineering, cost
**Date**: 2026-09-18
**Level**: Building
**For**: Building agents
**Hook**: Give every part of your prompt a priority number and the biggest number can still lose, because the ranking only applies between siblings.
**Engineer's view**: This is z-index with stacking contexts. You set a piece of your prompt to priority 200 and it is still dropped before something set to 0, because priorities only rank siblings inside one branch of the tree. The number you chose never competed with the number you were comparing it to.
**TLDR**: Prompt priorities rank siblings, not the whole prompt. What survives a token budget is decided by where a piece sits in the tree, not by how big its number is.
**Time to read**: ~11 minutes

## Explain Like I'm 5

Imagine packing a suitcase using packing cubes. Inside each cube you rank what matters most, so if that cube has to lose something, the lowest-ranked thing goes first.

Now the suitcase will not close. You do not compare every item to every other item. You pick a cube, and take from the bottom of that one.

So a "must take" item in a cube you rated low can leave before a "whatever" item in a cube you rated high. The rank inside a cube only ever competes with that same cube.

## The Problem

You have shipped this bug before, and it was in CSS. You set `z-index: 9999` on the thing that has to sit on top. It renders behind an element set to `1`. You add more nines. Nothing moves.

An hour later you learn about stacking contexts. Your 9999 was only ever competing with its own siblings, and the parent it lives in was already behind the other element. The number was never in the race you thought it was in.

Prompt assembly has the same shape, with a worse failure mode. Every piece of a prompt gets a priority, and when the whole thing overflows the model's context window, the lowest priority is dropped to make room. So far so obvious.

The part that bites is that the priorities are **local to the tree**. A number of 200 in one branch does not outrank a 0 in another. What actually decides the order is the path from the root, and the numbers only break ties between siblings along it.

When it goes wrong you do not get an error. You get a model that answers as though it never saw an instruction, because it did not. The prompt was assembled, it fit the budget, and the piece you cared about was quietly the cheapest thing to cut.

The fix is to stop reading the numbers and start reading the tree. Set priorities on the parents that actually compete. Then use `passPriority` to flatten any wrapper that should not have formed a scope of its own.

```figure
{ "kind": "system",
  "title": "The whole argument: the number loses to the path",
  "lanes": [
    { "t": "you wrote", "nodes": [
        { "id": "a", "t": "priority 200, deep in a low branch", "s": "bad" },
        { "id": "b", "t": "priority 0, in a high branch", "s": "ok" } ] },
    { "t": "the renderer ranks", "nodes": [
        { "id": "path", "t": "by path from the root", "s": "new" } ] },
    { "t": "over budget, so it drops", "nodes": [
        { "id": "drop", "t": "your 200", "s": "bad" },
        { "id": "keep", "t": "keeps the 0", "s": "ok" } ] }
  ],
  "edges": [
    { "from": "a", "to": "path", "s": "bad" },
    { "from": "b", "to": "path", "s": "ok" },
    { "from": "path", "to": "drop", "t": "lowest branch first", "s": "bad" },
    { "from": "path", "to": "keep", "s": "ok" } ],
  "note": "Numbers only break ties between siblings. They never compete across branches." }
```

## The Fix: Set Priorities on the Parents That Actually Compete

Microsoft ships this renderer as `@vscode/prompt-tsx`, MIT licensed, and it is the one Copilot Chat itself uses. You declare a prompt as a tree of components, each with a `priority`, and call `renderPrompt` with the model's token budget. Anything that does not fit is pruned lowest-first, keeping declaration order.

The README compares `priority` to a z-index. That is exactly right, and it is exactly the trap. Z-index brings stacking contexts with it, and the docs do not spell that part out.

### Why doesn't 200 beat 0?

Take this tree, which is the README's own example:

```jsx
<UserMessage priority={1}>
  <TextChunk priority={100}>A</TextChunk>
  <TextChunk priority={0}>B</TextChunk>
</UserMessage>
<SystemMessage priority={2}>
  <TextChunk priority={200}>C</TextChunk>
  <TextChunk priority={20}>D</TextChunk>
</SystemMessage>
```

Pruning order is **B, A, D, C**. The whole `UserMessage` branch empties before the `SystemMessage` branch loses anything, because 1 is less than 2. `A` at 100 goes before `D` at 20. The hundred never met the twenty.

### What happens when two branches tie?

It gets less intuitive, and this is worth knowing before you debug it at midnight. Drop the parent priorities from that example and the order becomes **B, D, A, C**.

```figure
{ "kind": "route",
  "title": "Same four elements, same four numbers, two different prune orders",
  "source": "two sibling branches",
  "parts": [
    { "t": "parents ranked 1 and 2", "to": 0, "via": "priority decides", "s": "ok" },
    { "t": "parents left unranked", "to": 1, "via": "lookahead decides", "s": "new" }
  ],
  "dests": [
    { "t": "B, A, D, C — one branch empties first", "s": "ok" },
    { "t": "B, D, A, C — the branches take turns", "s": "new" }
  ],
  "note": "A is 100 and D is 20. Which one survives depends only on whether the parents carry a number." }
```

With the parents tied, the renderer looks ahead at each one's direct children and picks whichever branch holds the lowest-priority child. So the branches take turns. Adding one low-priority child deep inside a branch changes which branch gets cut first. That is action at a distance, and it is hard to spot if you are not expecting it.

### How do I lose part of something instead of all of it?

Wholesale pruning is usually too blunt for a long user query or a big retrieved document. `TextChunk` with `flexGrow` renders after its siblings. It takes whatever budget they left, and fits as much text as it can on a delimiter you choose:

```jsx
<UserMessage priority={100}>
  <TextChunk breakOn=" ">{this.props.userQuery}</TextChunk>
</UserMessage>
```

`TokenLimit max={1000}` caps a subtree, which is pruned before the prompt as a whole is.

## What This Means for You

**When this matters.** It matters as soon as your prompt is assembled from parts rather than written as one string, which is every agent. Conversation history, retrieved files, tool results and system instructions all compete. The ones that grow without bound are the ones that push everything else out.

**How it affects you.** The failure is silent and it looks like a model problem. Your agent ignores a rule you are certain you sent. You re-read it. You make it more emphatic. None of it helps, because the text never arrived. Silent truncation is the most expensive class of prompt bug for that reason: the thing you would change is not the thing that is wrong.

**What to do about it.** Start by finding out whether you are truncating at all, which costs one line and needs no library:

```python
# does the assembled prompt even fit? do this before you tune any priorities
print(sum(len(m["content"]) // 4 for m in messages), "approx tokens vs", model_limit)
```

If that number is near your limit, something is already being dropped.

Then draw your prompt as a tree on paper and mark which pieces are siblings. The pieces you thought were competing usually are not. That drawing is the whole fix more often than any code change, because the bug is almost never the number you picked. It is the branch you picked it in.

## Implementing It

**The change.** Three roles touch this, and the first is the one people skip.

*Role 1: whoever owns the prompt's shape.* Priorities belong on the elements that actually compete, which means the parents. Setting them only on leaves is the mistake that produces the z-index confusion:

```jsx
// before: leaves ranked, parents unranked, so branches take turns
<UserMessage><History priority={10} /></UserMessage>
<SystemMessage><Rules priority={900} /></SystemMessage>

// after: the branches themselves are ranked, so Rules cannot lose to History
<UserMessage priority={10}><History /></UserMessage>
<SystemMessage priority={900}><Rules /></SystemMessage>
```

When a wrapper component exists for code organization rather than for ranking, give it `passPriority` so its children compete in the parent's scope instead of forming their own:

```jsx
<UserMessage>
  <MyContainer passPriority>
    <ChildA priority={1} /><ChildB priority={3} />
  </MyContainer>
  <ChildC priority={2} />
</UserMessage>
// prune order becomes ChildA, ChildC, ChildB — one flat ranking
```

*Role 2: whoever writes a component that has to fit a budget.* Implement `prepare(sizing)` and trim against `sizing.tokenBudget` rather than assuming you get everything. The budget handed to you is what your siblings left:

```tsx
class SimpleTextChunk extends PromptElement<{ text: string }, string> {
  prepare(sizing: PromptSizing) {
    const words = this.props.text.split(' ');
    let str = '';
    for (const word of words) {
      if (tokenizer.tokenLength(str + ' ' + word) > sizing.tokenBudget) break;
      str += ' ' + word;
    }
    return str;
  }
  render(content: string) { return <>{content}</>; }
}
```

*Role 3: whoever pairs a tool call with its result.* This one is a real bug rather than a tidiness point. If a tool response is pruned and its request survives, you have sent the model a call with no answer. `useKeepWith` ties them, so pruning the response removes the request too:

```tsx
const KeepWith = useKeepWith();
<KeepWith priority={2}><ToolCallRequest>...</ToolCallRequest></KeepWith>
<KeepWith priority={1}><ToolCallResponse>...</ToolCallResponse></KeepWith>
```

Note this is not `Chunk`. `Chunk` refuses to prune the group at all, which is the wrong answer here: a large tool result should be droppable. `KeepWith` lets the response go and takes the request with it, so the transcript stays coherent either way.

**How you know it worked.** Do not infer this from output quality, because a truncated prompt and a confused model look identical from there. The library ships a tracer that reports what it allocated and what it cut:

```js
const renderer = new PromptRenderer(/* ... */);
renderer.tracer = new HTMLTracer();
await renderer.render(/* ... */);
```

Serve it and read which elements were dropped. Before the change, the piece you care about appears in the pruned set. After it, it does not, and something you marked as expendable does instead. If nothing is pruned in either run your budget was never tight and you have not tested the thing you changed — shrink `modelMaxPromptTokens` until something gives, then compare.

## When a Priority Tree Is the Wrong Tool

It is the wrong tool when your prompt always fits. A fixed system prompt and one user turn will never overflow a modern context window. A priority tree there is machinery guarding a door nobody walks through. Concatenate the strings.

It is also the wrong answer to a prompt that is too big on purpose. Pruning decides what to lose once you have already built something oversized. It will drop the same context every turn while you wonder why answers got worse. If one element is always the thing pruned, that is not a ranking problem. Retrieve less, summarize earlier, or move it out of the prompt entirely.

And it binds you to a rendering model. Prompts become components with a compile step, `jsx` set to `react` and a `jsxFactory` of `vscpp` in your `tsconfig.json`. That is a reasonable trade inside a VS Code extension, where this library already lives. It is a heavy one if your prompt assembly is thirty lines of Python.

Three questions before you adopt it:

- Does my prompt actually overflow today, with real conversation history in it?
- Can I name which two pieces should lose to each other, and are they siblings?
- Would summarizing the biggest element beat ranking it?

## Glossary

- **priority** — a number ranking an element against its siblings only, not against the whole prompt
- **pruning** — dropping the lowest-priority elements until the prompt fits the token budget
- **token budget** — how much of the model's context window this prompt is allowed to use
- **passPriority** — marks a wrapper as transparent so its children compete in the parent's scope
- **flexGrow** — renders an element after its siblings so it can use whatever budget they left
- **useKeepWith** — ties elements together so pruning one removes the others

