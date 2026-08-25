# Further Reading: How Self-Attention Works

## Primary Sources

### 1. [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
**Source**: arXiv | **Read time**: ~40 min
> Vaswani et al., 2017. Scaled dot-product attention, multi-head, and the `1/√d` term. §3.2 is the whole mechanism.

### 2. [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)
**Source**: jalammar.github.io | **Read time**: ~25 min
> Pictures for Q, K, V and the residual block. Use this if the matrix multiply in the primer is clear but you want it drawn.

### 3. [The Illustrated GPT-2](https://jalammar.github.io/illustrated-gpt2/)
**Source**: jalammar.github.io | **Read time**: ~20 min
> Causal masking and the decoder-only stack — the shape behind every chat API.

## Background & Ecosystem

### 4. [Formal Algorithms for Transformers](https://arxiv.org/abs/2207.09238)
**Source**: arXiv | **Read time**: ~25 min
> Phuong & Hutter. Attention written as algorithms, not prose. Handy when you want the shapes without the 2017 experiments.

### 5. [How the forward pass runs](https://theaicommit.com/#learn/how-the-forward-pass-runs)
**Source**: theaicommit.com | **Read time**: ~10 min
> The KV cache is stored keys and values so the next token does not rebuild the past. This primer is the table; that lesson is the receipt.

## The one-line takeaway
Each token scores the others, softmax turns scores into a competition, and the mix is a weighted sum of values — not a search engine.
