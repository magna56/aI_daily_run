# Further Reading: How an Agent Decides a Web Page Is Safe to Read

## Articles

### 1. [chatUrlFetchingPatterns.ts](https://github.com/microsoft/vscode/blob/main/src/vs/workbench/contrib/chat/common/tools/builtinTools/chatUrlFetchingPatterns.ts)
**Source**: microsoft/vscode (MIT) | **Read time**: ~10 min
> The primary source, and 170 lines you can read end to end. `extractUrlPatterns` is the function to study: it shows exactly which rules an approval can become, in specificity order, and the two guards that keep it sane — wildcards only when the host has more than two labels, and a separate exclusion for hosts that are addresses rather than names. Read `isUrlApproved` next and notice it returns the first matching entry, not the most specific one.

### 2. [chatUrlFetchingConfirmation.ts](https://github.com/microsoft/vscode/blob/main/src/vs/workbench/contrib/chat/common/tools/builtinTools/chatUrlFetchingConfirmation.ts)
**Source**: microsoft/vscode (MIT) | **Read time**: ~12 min
> The other half, and the one to copy if you are building a fetching tool. `getPreConfirmAction` and `getPostConfirmAction` are the whole two-phase idea in two methods, and `canUseDefaultApprovals = false` is the line that opts your tool out of the generic yes-or-no path. Open it in an editor beside your own agent loop and find the place you should have a post-fetch checkpoint.

### 3. [Language Model Tools API](https://code.visualstudio.com/api/extension-guides/ai/tools)
**Source**: VS Code extension docs | **Read time**: ~15 min
> Read this before you write a tool, not after. It covers registration, the confirmation flow and how a result is returned, which is the surrounding machinery the two files above plug into. The reference to keep open while you implement; skip it if you are only tuning your own settings.

### 4. [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
**Source**: OWASP | **Read time**: ~20 min
> The bug class under its industry name. Prompt injection is LLM01 and indirect prompt injection — instructions arriving inside content the model was asked to read — is exactly what the response-side approval exists to interrupt. Useful for arguing the case to someone who wants a standard cited rather than a code file.

### 5. [chat code organization](https://github.com/microsoft/vscode/blob/main/src/vs/workbench/contrib/chat/chatCodeOrganization.md)
**Source**: microsoft/vscode (MIT) | **Read time**: ~5 min
> A map written by the team, worth five minutes before you go exploring. It tells you which folder owns the tools infrastructure, the participant model and the built-in tools, which is how you find the next file worth reading. Note the split it implies: core holds the tool plumbing, while the model calls and prompts live in the extension.
