# Further Reading: Don't Skip the Boring Tokens

## Articles

### 1. [TileMix full paper (HTML)](https://arxiv.org/html/2608.17336)
**Source**: arXiv | **Date**: 18 August 2026 | **Read time**: ~35 min
> The primary source, and the version to read rather than the abstract — the abstract does not tell you the routing is static and data-free, which is the most interesting thing about the method. Go to the experiments section for the tile sizes (`BLOCK_M=128`, `BLOCK_N=64`), the grouping constraint that keeps the routing map inside one 64-bit word, and the coverage sweeps at 25/50/75%. The reference to keep open while implementing.

### 2. [Big Bird: Transformers for Longer Sequences](https://arxiv.org/abs/2007.14062)
**Source**: arXiv (Zaheer et al.) | **Date**: 2020 | **Read time**: ~30 min
> Where the routing templates come from. Read this to understand what the spatial prior actually encodes — local band, global tokens, random blocks — because TileMix inherits it wholesale, including its blind spots. Read first if you have not met structured sparse attention; the templates are the part TileMix reuses unchanged.

### 3. [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135)
**Source**: arXiv (Dao et al.) | **Date**: 2022 | **Read time**: ~40 min
> The online-softmax tiling that TileMix modifies, and the baseline it is measured against. Section 3.1 is the one that matters here: it is where the running max and running sum are derived, which is exactly the state both precision paths have to share. If the rescale step in the code example looked arbitrary, this is why it is not.

### 4. [LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale](https://arxiv.org/abs/2208.07339)
**Source**: arXiv (Dettmers et al.) | **Date**: 2022 | **Read time**: ~30 min
> The counterpoint worth holding in mind: it argues that a small number of outlier features must stay in higher precision, and handles them by *splitting the matmul* rather than by spatial routing. Two different answers to "not all of this deserves 16 bits" — reading them together is what makes the design space visible.

### 5. [Transformer Circuits Thread](https://transformer-circuits.pub/)
**Source**: Anthropic | **Date**: ongoing | **Read time**: varies
> Not about this paper. Included because the honest limitation of TileMix — a static template cannot know that *your* prompt hid something important in a region it calls boring — is fundamentally a question about what attention patterns mean, and this is where that question is being worked on. Skip unless the "not adaptive" critique is the part you want to pull on.
