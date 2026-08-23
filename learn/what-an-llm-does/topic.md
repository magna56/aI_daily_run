# The Model Only Ever Picks the Next Token

**Category**: New Models & APIs
**Tags**: transformers, training
**Date**: 2026-08-23
**Level**: Start here
**For**: How models work
**Hook**: A language model only ever picks the next word. Training teaches it which pick looks right.
**Kind**: Learn
**Time to read**: ~10 minutes

## Explain Like I'm 5
Imagine a friend who has read every book in the library, but who can only ever say one word at a time. You say a sentence. They guess the single most likely next word. You add that word to the sentence. They guess again. They are not looking up an answer, and they are not planning a paragraph in their head. They are playing an extremely well-practiced version of "finish this sentence." The more books they have read, and the more times a teacher has said "that reply was better than this one," the more useful their next-word guesses become.

## The Problem
Most engineers meet these models as a chat box that "answers questions." That framing hides the machine. If you think of the model as a search engine, you will be shocked when it invents a function that does not exist. If you think of it as a reasoner with a plan, you will be shocked when it agrees with a wrong premise and then writes three confident paragraphs about it. The actual machine is narrower and more useful once you see it: it is a next-token predictor that has been trained, in three different stages, to make those next-token picks look like helpful assistant text.

## For a Software Engineer
This is an autocomplete problem taken to an extreme, not a database lookup and not a compiler. A phone keyboard already does next-word prediction from a tiny local history. A language model does the same job with a much richer history — your prompt, the system instructions, and every token it has already emitted in this reply — and a much larger statistical model of "what usually comes next."

The surprising number is how little the *runtime* does. At inference time there is no separate "thinking engine" underneath the words. The model scores every token in its vocabulary, picks one, appends it, and repeats. A 400-word answer is about 400 of those picks (more or less, because tokens are not always whole words — that is the next chapter). If a fact was never in the training data, or was rare, the model still has to pick *something*. That is why it can sound fluent while being wrong.

Monday-morning action: when an output is bad, ask "what prefix made this next token likely?" before you ask "why doesn't it understand?" A missing file, a vague spec, or a contradictory earlier sentence is a prefix problem. The model is completing what it can see.

## What This Means for You
**When this matters**: you are about to trust a generated answer, write a prompt, or decide whether a coding agent "knows" your codebase.

**How it affects you**: the model does not retrieve a stored answer. It generates a continuation. That is why it can write a plausible-looking API that your repo does not have, why it can flip a boolean and keep going, and why extra context in the prompt changes the next-token distribution more than any amount of wishing.

**What to do about it**: treat the prompt plus the files you attach as the *only* state the model has. Put the constraint in the prefix ("do not invent endpoints; if the handler is missing, say so"). Prefer a coding agent that can *read* the repo over a chat box you paste into. And when you hear "the model was trained to…", map that sentence onto one of the three stages below — pretraining, supervised fine-tuning, or preference training — instead of treating "trained" as a synonym for "understands."

## What It Is
A large language model is a neural network that, given a sequence of tokens, outputs a score for every token in its vocabulary. The highest-scoring tokens are the ones that, in its training, most often followed similar prefixes. Sampling turns those scores into an actual next token. The new token is appended, and the network runs again.

That is the whole runtime loop. Everything people call "the model" — ChatGPT, Claude, Gemini, a local Llama — is this loop plus a tokenizer, a context window, and a serving stack. The differences you feel in product (it answers questions, it refuses some requests, it writes in a helpful tone) are almost entirely differences in *training data and training stages*, not a different machine at inference time.

The architecture that made this scale is the transformer: a stack of layers that lets every position in the sequence attend to earlier positions, so the guess for token 200 can use tokens 1 through 199. You do not need the matrix math to use the product. You do need the implication: there is no scratchpad unless the model *writes* one into the token stream (a chain of thought is still just tokens), and there is no memory of last Tuesday's chat unless that text is in this request.

## Why It Matters
Once you see next-token prediction, three product mysteries stop being mysteries.

First, fluency is cheap and correctness is not. The pretraining objective rewards text that looks like the internet. "Looks like a good answer" and "is a good answer" are different losses. That is why a model can write a beautiful, wrong unit test.

Second, the assistant personality is not native. A base model trained only on internet text will continue a Stack Overflow thread, a recipe, or a rant — whatever the prefix looks like. The helpful "Sure, here's a patch" voice is painted on in later stages.

Third, "alignment" and "instruction following" are training, not a system prompt you can fully fake. A system prompt steers the prefix. Supervised fine-tuning and preference training change the weights so that, given a user request, the likely continuation *is* an assistant reply rather than a blog post. That is why the same architecture can be a raw completer in one checkpoint and a product chatbot in another.

## Key Technical Details

**Background first.** A *token* is a chunk of text the model can emit — a word, a piece of a word, or punctuation. A *vocabulary* is the fixed list of those chunks (often around 30,000 to 200,000). *Logits* are the raw scores the network assigns to each vocabulary item before they are turned into probabilities. *Pretraining* is the first, longest training stage: predict the next token on a huge unlabeled text corpus. *Supervised fine-tuning* (SFT) is the second stage: train on labeled (prompt, ideal reply) pairs so the model learns the assistant format. *Reinforcement learning from human feedback* (RLHF) is a common third stage: humans (or a model standing in for them) rank replies, a reward model learns those rankings, and the language model is updated to make high-reward replies more likely.

- **The inference loop is pick, append, repeat.** There is no second network that "checks the answer" unless a product team added one outside the model (a tool, a linter, a verifier). The model you called only ever produced the next token.
- **Pretraining is compression plus prediction.** On a trillion-plus tokens of text, the model is trained to minimize next-token surprise. That is enough to absorb grammar, idioms, a lot of factual associations, and a lot of *wrong but common* text. A base checkpoint completes text; it is not trying to be useful.
- **Supervised fine-tuning is the format change.** Teams collect conversations that look like the product they want: a user message, then a good assistant message. Training on those pairs shifts probability mass from "continue the user's sentence" to "start a helpful reply." This is ordinary supervised learning — labeled examples — applied on top of the pretrained weights. It is also where a lot of "the model knows how to use tools" comes from: the examples include tool calls.
- **Preference training is the taste change.** SFT can only show one "right" reply per prompt. Humans often disagree, and many prompts have many acceptable replies. RLHF (and nearby methods such as Direct Preference Optimization) take *pairs*: reply A is better than reply B. The model is updated so A-like continuations become more likely. This is why a product model refuses some requests, hedges on medical advice, or writes in a particular tone — those behaviors were preferred in the ranking data, not deduced at runtime.
- **The three stages share one mechanism.** After all of that training, serving still does next-token prediction. Pretraining, SFT, and RLHF change *which* token is likely, not *whether* the model is picking a token.
- **A transformer is a parallelizable sequence model.** Older recurrent nets guessed the next token after reading the prefix one step at a time, which is hard to train at this scale. A transformer lets every position look at earlier positions in parallel during training. That is an engineering reason this generation of models exists, not a claim that the model "pays attention" in the everyday sense.
- **Context is the working set, not long-term memory.** The model can only condition on tokens that fit in the current context window. A coding agent that "remembers" your repo is re-reading files (or a summary) into that window, not consulting a hidden database of your company.

## How It Connects to What You Know
You already ship systems that look like this. A compiler takes a prefix (source) and emits the next valid construct according to a grammar — except the grammar is exact and the model’s "grammar" is statistical. Autocomplete in your IDE is the same job at 20 candidates; the model is autocomplete with a 100,000-wide candidate list and a much longer prefix. A cache is not a brain: if the key is missing, you recompute. If the file is not in the prompt, the model does not have it.

This page is a chapter in the Learn track — the evergreen curriculum. The daily lab (the dated cards on the homepage) is the case-study feed. Later daily posts will assume you know that the runtime is next-token prediction and that "the model was trained" means one of the three stages above. Read this first; then a paper about a new preference method, or a changelog about a new coding model, is an application of this chapter rather than a new kind of machine.

## Try It Yourself
`code_example.py` builds a tiny next-token table from a handful of sentences — no neural net, no API. It then applies the three stages as data operations: more unlabeled text (pretrain), labeled (prompt, reply) pairs (supervised fine-tuning), and "prefer this continuation over that one" (a stand-in for preference training). It prints the next-token distribution after each stage so you can see the *same* pick-the-next-token machine produce a raw completer, then an assistant, then a preferred tone.

## Glossary
- **Token** — a chunk of text the model reads and writes; sometimes a word, often a piece of a word. The next chapter is about how text is cut into tokens.
- **Vocabulary** — the fixed list of tokens the model is allowed to emit.
- **Next-token prediction** — the only job the model has at runtime: given the tokens so far, score every vocabulary item and pick one.
- **Logits** — the raw scores the network assigns to each vocabulary item, before they become probabilities.
- **Context window** — the maximum number of tokens the model can condition on in one request (prompt plus reply so far).
- **Transformer** — the neural-network architecture used by modern language models; it lets each position in the sequence use information from earlier positions.
- **Base model** — a checkpoint trained mostly or only with next-token prediction on unlabeled text; it completes text rather than answering as an assistant.
- **Pretraining** — the first training stage: next-token prediction on a huge unlabeled corpus.
- **SFT** (Supervised Fine-Tuning) — the second stage: training on labeled (prompt, ideal reply) pairs so the model learns the assistant format.
- **RLHF** (Reinforcement Learning from Human Feedback) — a third-stage family of methods: humans rank replies, a reward signal is derived, and the model is updated to make preferred replies more likely.
- **Reward model** — a model trained to score how much a human would like a reply; used as a stand-in for a human during preference training.
- **DPO** (Direct Preference Optimization) — a preference-training method that updates the language model from chosen/rejected pairs without a separate reinforcement-learning loop.
- **Inference** — running a trained model to produce tokens; no weights are being learned.
- **LLM** (Large Language Model) — a transformer language model trained at large scale; in this chapter it means the next-token machine described above.
- **API** (Application Programming Interface) — the request/response contract you call; here, usually a completion endpoint that returns the next tokens.
- **IDE** (Integrated Development Environment) — the editor you already use, whose autocomplete is the small version of next-token prediction.
- **Chain of thought** — tokens the model writes as intermediate reasoning; still next-token prediction, not a hidden scratchpad.
