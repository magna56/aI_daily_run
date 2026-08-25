# How Vision Models Turn Pixels Into Tokens

**Category**: Multimodal Engineering
**Tags**: multimodal, cost, inference-serving
**Date**: 2026-08-21
**Level**: Building
**For**: How models work
**Hook**: Before your prompt runs, the image is already cut into tokens — and you often pay for blank space.
**Time to read**: ~10 minutes

## Explain Like I'm 5

Imagine mailing someone a photo, but the post office only ships square boxes of one fixed size.
Your photo is tall and thin, so it goes into three boxes with a lot of empty space — and you pay
for all three boxes, air included. Worse, the post office trims any photo bigger than a set size
before packing, so mailing a sharper photo gets you the exact same blurry one at the other end.
The other post office in town cuts your photo into small squares that follow its real shape, so
you pay only for what's actually there — but now every parcel is a different size, and the
loading dock has to figure out how to stack them.

## For a Software Engineer

**This is a padding-and-quantization problem, and you already know it from tensors.** When you
pad a batch to its longest member you burn compute on cells holding nothing. A vision model does
exactly this with pixels: the popular approach chops your image onto a fixed grid of 512×512
squares and rounds *up* on both axes, so you're billed for grid cells that are mostly empty. On
a plain A4 page that's 47% air. On a perfectly square photo — the shape you'd assume is safest —
it's 43.8%, because the image lands at 768×768 and a 512 grid needs 1024×1024 to cover it.

**The part that should change what you do on Monday is a silent ceiling.** Before any of that
tiling happens there's a resize step you didn't write and can't turn off: the shorter side of
your image gets pulled down to 768 pixels. I ran a 200 dpi, a 300 dpi, and a 600 dpi scan of the
same A4 page through it. All three came out **byte-identical** — 768×1086, ~93 dpi, 1105 tokens
every time. So if your document pipeline misreads small print and someone suggests re-scanning
the corpus at higher quality, that work is guaranteed to change nothing. Same input, same cost,
same errors. Verify the ceiling before you buy the scanner.

**The alternative moves the cost rather than deleting it** — the same trade as any
variable-length-record system. Newer models size the image to its own shape (one token per 28×28
pixel block) and cap *total* pixels instead of forcing a grid. That gives you an actual dial:
spend more tokens, get more detail, up to the source resolution and no further. It also makes
small images genuinely cheap — a 96×96 icon costs 9 tokens instead of 255. But now every request
is a different length, which is a scheduling problem, not a modelling one. In my simulation naive
batching wasted 63.8% on padding; sorting by size first dropped that to 2.2%, at the cost of
serving requests out of arrival order.

**And watch the config you paste in.** The most-copied setup line for these models sets a
*minimum* image size. It's good advice for documents and quietly catastrophic for small UI
screenshots: it upscales that 9-token icon to 256 tokens — 28× — to add detail that was never
captured in the first place.

## What It Is

Every VLM has a function that turns an image into a token sequence, and almost nobody reads it.
It runs before your prompt, it is not in your code, and it silently fixes two things you probably
believe you control: **how much the image costs** and **how much of the image the model can
actually see**. There are two families of that function in production today, and they fail in
opposite directions.

**Fixed tiling** (OpenAI GPT-4o/4.1/o-series, LLaVA-NeXT AnyRes, InternVL) normalizes the image
onto a grid of fixed-size squares. OpenAI's documented high-detail path is: scale to fit inside
2048×2048, then scale so the *shortest* side is 768, then count 512×512 squares and bill
`85 + 170 × tiles`. InternVL 1.5 does the same shape differently — 1 to 40 tiles of 448×448
chosen by aspect-ratio match, plus a downscaled thumbnail for global context. The grid is the
unit of both computation and billing.

**Native resolution** (Qwen2-VL, NaViT, and August 2026's Cohere North Micro Vision) deletes the
grid. Qwen2-VL uses a patch size of 14 and a `spatial_merge_size` of 2, so one visual token is
exactly one 28×28 pixel block. `smart_resize` rounds both dimensions to multiples of 28 and
rescales only to keep total pixels inside `[min_pixels, max_pixels]`, preserving aspect ratio.
Token count is then just `(H/28) × (W/28)` — the image's own shape, quantized at 28px, with no
grid to pad against. North Micro Vision (2.4B, released this month) pushes the same idea to a
document-shaped ceiling: 1654×2339, "an A4 page at 200 dpi," with 2D RoPE plus interpolated 1D
embeddings (C-RoPE) to keep position encoding coherent when every input is a different shape.

The trade is not "one is more efficient." It is **where the variance lives**. Tiling gives you a
predictable, quantized cost and an unadvertised resolution ceiling. Native resolution gives you
faithful pixels and a variable-length sequence — which is now your scheduler's problem.

## Why It Matters

I computed both pipelines exactly over a corpus of realistic input shapes. Three results are
worth changing your code over.

**1. The padding tax is never zero, and it is worst on the shapes you'd assume are safe.**

| Input | Tile grid | Tiles | Tokens | Grid area wasted |
|---|---|---|---|---|
| A4 doc @200dpi (1654×2339) | 2×3 | 6 | 1105 | **47.0%** |
| Laptop screenshot (2880×1800) | 3×2 | 6 | 1105 | 40.0% |
| Phone screenshot (1170×2532) | 2×4 | 8 | 1445 | 39.1% |
| **Square photo (1024×1024)** | 2×2 | 4 | 765 | **43.8%** |
| Small icon (96×96) | 1×1 | 1 | 255 | 96.5% |

A perfect square wastes 43.8%, because the shortest-side-768 rule lands it at 768×768 and a 512
grid needs 2×2=1024×1024 to cover that. There is no "well-behaved" aspect ratio. The ceil on
each axis means the *only* zero-waste inputs are exact multiples of the tile size after two
chained rescales you don't control.

**2. Fixed tiling has a hard resolution ceiling, and it is far lower than anyone assumes.**

This is the finding that should change behavior:

```
200dpi scan  1654x2339  -> 768x1086 = 92.9 dpi, 1105 tokens
300dpi scan  2480x3508  -> 768x1086 = 92.9 dpi, 1105 tokens
600dpi scan  4960x7016  -> 768x1086 = 92.9 dpi, 1105 tokens
```

**All three collapse to byte-identical inputs.** The shortest-side-768 rule caps an A4 portrait
page at ~93 dpi no matter what you upload. Re-scanning your document corpus at 600 dpi to fix
OCR misses on small print does exactly nothing — same pixels, same cost, same errors. 6pt text at
93 dpi is roughly 8 pixels tall. That's the ceiling, and `detail: "high"` is already on the other
side of it.

Native resolution turns that ceiling into a dial you own:

```
Qwen max_pixels=1280 tok ->  840x1176 = 101.6 dpi, 1260 tok
Qwen max_pixels=2560 tok -> 1176x1680 = 142.2 dpi, 2520 tok
Qwen max_pixels=4096 tok -> 1484x2128 = 179.4 dpi, 4028 tok
Qwen max_pixels=8192 tok -> 1652x2352 = 199.8 dpi, 4956 tok
```

Note the last row: you asked for 8192 tokens and got 4956. The budget is a **cap, not a target** —
it saturates at the source resolution and stops charging you. That's the correct semantics, and
it's the opposite of the tiling path, where the floor (`85 + 170`) is charged even for a 96×96
icon.

**3. The most-copied Qwen config snippet is wrong for small images.**

The recipe everywhere in the docs and tutorials — `min_pixels = 256*28*28` to "ensure each image
gets 256–1024 tokens" — is a **floor**, and it silently upscales small assets to pay for pixels
that were never captured:

| Input | Qwen default | Qwen w/ 256-recipe | OpenAI tiling |
|---|---|---|---|
| icon 96×96 | **9 tok** | 256 tok | 255 tok |
| button 240×64 | **18 tok** | 279 tok | 255 tok |
| toolbar 800×48 | **58 tok** | 264 tok | 425 tok |

A UI-automation agent screenshotting small elements pays **28× more** under a config line that
was pasted in to improve document quality. Native resolution's biggest structural win — cheap
small images — is exactly what that line throws away. The default (`min_pixels = 56*56`) is right
for anything UI-shaped.

## Key Technical Details

**Background first.** A vision model can't read pixels directly, so a *vision encoder* cuts the
image into small fixed squares called **patches**, reads each one, and often **merges**
neighbouring patches to cut the count down. Whatever survives that merge is a **visual token** —
the same unit of cost and context the language model spends on words. So the entire cost question
reduces to two numbers: how big is one patch, and how many patches collapse into one token. The
bullets below are the real settings behind those two numbers, ordered from the ones that set the
price to the ones that shape the architecture.

- **One Qwen2-VL visual token is a 28×28 pixel block.** That's the two numbers above:
  `patch_size=14` (each patch is 14×14 px) and `spatial_merge_size=2` (a 2×2 group of patches
  becomes one token) — 14 × 2 = 28. This is why every token count in this session is a multiple
  of a 28px grid.
- **Video is cheaper than you'd guess**: `temporal_patch_size=2` pairs frames up, so a 2-frame
  clip costs the same as a single frame.
- **`smart_resize` is the whole native-resolution algorithm**, and it's four lines: round height
  and width to the nearest multiple of 28; if that exceeds `max_pixels`, scale down by
  `β = sqrt(H·W / max_pixels)` and *floor* to the grid; if it falls under `min_pixels`, scale up
  and *ceil*. Aspect ratio survives to within one 28px quantum.
- **OpenAI's tiling constants**, for comparison: 85 base + 170 per tile (GPT-4o/4.1/4.5), 75 + 150
  (o1/o3). The trap is GPT-4o-mini at 2833 + 5667 — that is a *different token unit*, not a more
  expensive model, so you cannot scale mini's image cost from its text price.
- **Extreme aspect ratios get treated better than moderate ones under tiling**, which is
  backwards from intuition. A 3000×500 banner is so wide that the shortest-side rule never fires
  (341 < 768), so it keeps a full 2048px on its long axis. A near-square photo gets aggressively
  downscaled. Worth knowing before you "normalize" input shapes.
- **NaViT's patch-n-pack** (packing several images into one sequence) is the fix for native
  resolution's batching problem: concatenate patches from *differently-sized images* into one
  fixed-length sequence, then use a block-diagonal **attention mask** — a rule stopping tokens of
  one image from looking at another — to keep them separate. It is exactly the sequence-packing
  trick from language-model pretraining, moved to the vision encoder.
- **DeepStack projection** (feeding the encoder's output in at several depths), used by North
  Micro Vision: inject patch embeddings from several vision-encoder layers into the corresponding
  *early layers* of the language model, rather than concatenating one flat projection at the
  input. You get multi-scale detail without multiplying the token count.

## How It Connects to What You Know

This is a **quantization problem wearing a computer-vision costume**, and the same reasoning you
already apply to numeric formats transfers directly. Fixed tiling is a uniform grid quantizer:
simple, hardware-friendly, and wasteful whenever the signal doesn't fill the grid — the 43.8%
square-photo waste is the visual equivalent of padding a tensor to a tile boundary. Native
resolution is a shape-adaptive quantizer with a global budget constraint, which is the same
structure as the per-block scaling in the NVFP4 session (2026-07-04-s2): match the representation
to the data instead of forcing the data into the representation.

The cost doesn't vanish, it **relocates** — and it relocates into the exact place the 2026-08-18
P-PAS session was about. Variable-length visual prefills are the worst possible input to a
continuous-batching scheduler: prefill cost is paid once per request but lengthens the iteration
that every decoding sequence is waiting on. A native-resolution VLM under load is a machine for
generating prefill-pressure variance. `max_pixels` is therefore not an image-quality setting, it
is **an admission-control parameter** — the same category of knob as `max_num_batched_tokens`, and
subject to the same finding: there is no right constant, only a right policy.

And the framing from 2026-08-20 applies unchanged: a mitigation that works can move a cost rather
than remove it. Tiling doesn't eliminate the padding waste, it makes it *invisible and uniform*,
which is why nobody optimizes it. Native resolution makes it visible and variable, which is why
it feels harder — but visible-and-variable is the only version you can actually schedule against.

## Try It Yourself

`code_example.py` implements both pipelines exactly — the OpenAI two-stage rescale and tile ceil,
and Qwen2-VL's `smart_resize` with the real constants (factor 28, `min_pixels=56²`,
`max_pixels=28²·1280`) — with zero dependencies. It runs four experiments:

1. **Cost/waste table** over 8 realistic input shapes, reproducing the 20–96% padding tax.
2. **The DPI ceiling**: 200/300/600 dpi A4 scans producing identical outputs under tiling, and
   the `max_pixels` dial that escapes it (including the saturation at source resolution).
3. **The `min_pixels` trap**: same UI corpus under default vs. the 256-token recipe, showing the
   28× inflation.
4. **Batch packing**: the mitigation ladder for the variance native resolution hands your
   scheduler, on a 600-image UI-agent workload (mean 455 tok, median 9 tok — a few full pages
   dominate the bill):

   | Strategy | Padding waste |
   |---|---|
   | naive pad-to-max, batch=4 | 56.8% |
   | naive pad-to-max, batch=16 | 63.8% |
   | length-bucketed, batch=8 | **2.2%** |
   | patch-n-pack, seq=2048 | 36.8% |
   | patch-n-pack, seq=4096 | **6.0%** |

   Two things fall out. Sorting by length before batching is a three-word change that recovers
   almost all of it — but it reorders arrivals, so you pay in tail latency. And **pack length
   must clear roughly 2× your largest single item**: at seq=2048 two 1260-token pages can't
   share a pack, so every pack strands a large tail and packing does *worse* than a 4096 pack.
   The same "no right constant, only a right policy" shape as the P-PAS session.

## Glossary

- **VLM** (Vision-Language Model) — a model that accepts images *and* text in the same prompt,
  like GPT-4o or Qwen2-VL. Internally it has no notion of an image: something must first convert
  pixels into the same kind of units the language model already consumes. That converter is what
  this whole session is about.
- **Token** — the unit a language model reads, bills, and budgets in. For text it's roughly a
  word-piece. For images it's a fixed patch of pixels. Everything downstream — cost, context
  limit, latency — is counted in these, which is why "how many tokens is my image" is the whole
  question.
- **Visual token** — one token that stands for a small square of the image. In Qwen2-VL it is
  exactly a 28×28 pixel block, so a 840×1176 image is 30 × 42 = 1260 visual tokens.
- **Patch** — the small square the vision encoder actually reads (14×14 pixels here). Several
  patches get merged into one visual token; patches are the encoder's unit, tokens are the
  language model's.
- **Tiling / AnyRes / dynamic tiling** — the strategy of cutting an image into fixed-size squares
  (512×512 for OpenAI, 448×448 for InternVL) and charging per square. Simple and predictable, but
  it rounds up on both axes, so partly-empty edge tiles are billed in full.
- **DPI** (dots per inch) — how much detail survives, not just a scanner setting. It's what
  decides whether small text is readable: at the ~93 dpi ceiling measured here, 6-point print is
  about 8 pixels tall, which is roughly the point where character recognition starts guessing.
  Doubling your scanner's dpi is worthless if the pipeline caps it back down.
- **Aspect ratio** — width divided by height. It matters because a fixed square grid fits some
  shapes far better than others, and the mismatch is billed to you as empty grid area.
- **`max_pixels` / `min_pixels`** — the total-pixel budget on native-resolution models.
  `max_pixels` is a ceiling that trades tokens for detail and stops charging once it reaches the
  source resolution; `min_pixels` is a *floor* that upscales small images, which is why it
  quietly inflates the cost of icons and UI screenshots.
- **Prefill** — the one-time pass a model makes over your entire input before it writes a single
  word of output. Images land here, so a large image is paid for up front, in full, on every
  request. Contrast with *decode*, the per-output-token phase.
- **Continuous batching / scheduler** — the server component that packs many users' requests
  through the GPU together. It assumes requests are roughly comparable in size; images of wildly
  varying token counts are precisely what breaks that assumption.
- **Padding waste** — compute you pay for that holds no data, because something had to be rounded
  up to a fixed size. It shows up twice here: in the image tile grid, and again when batching
  variable-length requests.
- **Patch n' Pack** — the fix for the second one: stuff several differently-sized images into a
  single fixed-length sequence and use a mask so they can't "see" each other. Same idea as packing
  short training examples together to avoid padding.
- **Attention mask** — a rule saying which parts of the input may look at which other parts. Used
  here to keep two images packed in one sequence from bleeding into each other.
- **OCR** (Optical Character Recognition) — reading text out of an image. The practical task most
  affected by the dpi ceiling above.
- **RoPE / 2D RoPE / M-RoPE** — the scheme that tells a model *where* each token sits. Text needs
  one dimension (position in the sentence); images need two (row and column); video needs three.
  Native-resolution models need a version of this that still works when every input is a
  different shape.
