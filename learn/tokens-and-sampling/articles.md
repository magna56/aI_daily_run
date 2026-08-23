# Further Reading: Temperature Is a Knob, Not a Personality

## Primary Sources

### 1. [OpenAI tokenizer playground](https://platform.openai.com/tokenizer)
**Source**: platform.openai.com | **Read time**: ~5 min
> Paste a string, see the tokens and IDs. The fastest way to internalize that words are not tokens — try a long identifier, a UUID, and the same word with and without a leading space.

### 2. [tiktoken](https://github.com/openai/tiktoken)
**Source**: github.com/openai | **Read time**: ~10 min
> OpenAI's BPE tokenizer library. The README is enough to encode a string and count tokens for the model you actually call. Use this in CI if you need a budget check without an API round-trip.

### 3. [Understanding GPT tokenizers (Simon Willison)](https://simonwillison.net/2023/Jun/8/gpt-tokenizers/)
**Source**: simonwillison.net | **Read time**: ~12 min
> A practitioner's tour of what tokenizers do to code, Unicode, and surprising English. Written for people who ship features, not for people who train models.

## Background & Ecosystem

### 4. [The Illustrated Word2vec](https://jalammar.github.io/illustrated-word2vec/)
**Source**: jalammar.github.io | **Read time**: ~20 min
> Embeddings as vectors you can add and compare, with pictures. Older than today's language-model embedding tables, but the right intuition: discrete IDs become coordinates so "nearby" means something.

### 5. [The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751)
**Source**: arXiv | **Read time**: ~30 min
> Holtzman et al. on why greedy and high-likelihood decoding go stale, and why nucleus (top-p) sampling exists. The paper behind the API checkbox you have been toggling without a name.

## The one-line takeaway
Tokens are the codec and the bill. Softmax turns scores into a die. Temperature, top-k, and top-p only change how that die is loaded — they never add a fact the logits did not already contain.
