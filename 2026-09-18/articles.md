# Further Reading: How to Decide What Falls Out of Your Prompt First

## Articles

### 1. [@vscode/prompt-tsx](https://github.com/microsoft/vscode-prompt-tsx)
**Source**: microsoft/vscode-prompt-tsx (MIT) | **Read time**: ~25 min
> The primary source, and the README is the documentation. Read the Prioritization section twice: the four-element example and its two prune orders are the whole mechanism, and the sentence that matters is "priorities are local in the element tree." Then read Flex Behavior for `flexGrow` and the `SimpleTextChunk` implementation, which is the shortest useful illustration of writing a component that trims itself against the budget it was handed rather than the budget it wanted.

### 2. [Chat extensions guide](https://code.visualstudio.com/api/extension-guides/chat)
**Source**: VS Code extension docs | **Read time**: ~20 min
> The surrounding machinery, and the reference to keep open while you implement. It covers chat participants, `vscode.lm.selectChatModels`, and the request/response flow that `renderPrompt` sits inside. Read it if you are actually shipping an extension; skip it if you only came for the pruning idea, which transfers to any language.

### 3. [chat-sample extension](https://github.com/microsoft/vscode-extension-samples/tree/main/chat-sample)
**Source**: microsoft/vscode-extension-samples (MIT) | **Read time**: ~15 min
> The one to open in an editor. A working participant with the `tsconfig.json` already configured for `vscpp`, so you can change a priority, run it, and watch a different element disappear. Faster than reading about the compile setup, and the `jsxFactory` configuration is the part people get wrong on the first try.

### 4. [The stacking context](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_positioned_layout/Stacking_context)
**Source**: MDN | **Read time**: ~10 min
> Worth ten minutes even though it is a CSS page, because it is the same bug with better diagrams and twenty more years of people writing about it. If the priority-is-local idea has not clicked yet, this is where it clicks. The list of properties that silently create a stacking context is a good reminder that scope boundaries are usually invisible at the call site.

### 5. [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
**Source**: Anthropic Engineering | **Read time**: ~20 min
> The wider argument, and the one to read before deciding you need any of this. It treats the context window as a budget to be spent deliberately, which reframes pruning as the last resort it should be: a prompt that is always cutting the same element every turn has a retrieval problem, not a ranking problem.
