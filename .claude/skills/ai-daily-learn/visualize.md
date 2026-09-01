# visualize.html — the required interactive artifact

**The test, same as every other artifact:** does the reader leave able to build something?
A visualizer earns its place by building *intuition for a mechanism they are about to
implement* — the reader should change an input, watch the article's claim emerge, and
understand the trade-off well enough to reason about their own numbers. Decoration that
merely restates the write-up fails this, however nice it looks.

This is not optional and not a decorated summary. The reader lazy-loads this file in an
iframe with `sandbox="allow-scripts"` (no same-origin, no popups, no forms, no storage).
If the file is missing there is no visualizer at all — neither the inline figure nor the tab.

**Before writing, open the newest `YYYY-MM-DD/visualize.html` in this repo and match that
quality bar.** Recent gold: `2026-08-23/visualize.html` (RAG grid heatmap) and
`2026-08-23-s2/visualize.html` (memory-headroom lab). Both: one mechanism, live numbers
from `code_example.py`, labelled controls, Reset, dark chrome, height postMessage.

## Where it goes

**In the reading flow, not in a tab.** From 2026-09-01, `topic.md` places a line reading exactly
`[[visualize]]` at the point of difficulty the artifact resolves, and the reader splices it into
the Overview prose there. When a session does that, the Visualize tab disappears — the artifact is
identical, only where the reader meets it has changed.

Put it immediately after the paragraph that raises the question it answers. A visualizer at the
end of the article is a visualizer nobody opens; one sitting under the sentence that just confused
someone is the thing that rescues them. `--check` warns when a session ships `visualize.html` and
never places the marker.

## What it must do

The reader changes one or two inputs and watches the article's claim appear. Pull constants
and headline results from `topic.md` and `code_example.py`. Never invent data to make it
dramatic.

Pick the interaction that fits the mechanism:

- **Pipeline/budget** — sliders change flow, tokens, latency, cost, or failure rate
- **Matrix/representation** — heatmap, quantization grid, bit counts, compression
- **Decision/eval** — toggles change accepted/rejected, score, or confound
- **Search/serving** — sweep a threshold or load; show the winner / inversion
- **Agent/tool system** — enable pieces and trace dispatch or validation

A static infographic, a restatement of the Excalidraw diagram, or a page of prose in a
pretty box is a failed visualizer. If the claim cannot be interacted with, the topic is
not ready.

## Hard contract (`build.js --check` enforces these)

- Complete standalone HTML: `<!doctype html>`, `<html>`, a non-empty `<title>`, viewport meta
- Root marker: `data-visualizer="<session-id>"` on `<main>` or the wrap — the value is the
  folder name (`2026-08-25`, `frontier-2026-08-25`), so a file that has drifted out of its
  session is traceable. A bare `data-visualizer` now warns.
- Restrictive CSP, no exceptions:

  `default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'`

- **No** `<script src>`, `<link href>`, `fetch(`, `XMLHttpRequest`, `WebSocket`, CDN, webfont,
  external image, API key, or network of any kind
- Inline CSS + vanilla JS only. No React/JSX, no build step
- JavaScript must parse (`node` / `vm.Script` syntax check). Wrap in an IIFE
- Height handshake, on load and on every layout change:

```javascript
function reportHeight() {
  parent.postMessage({
    type: "adl-visualize-height",
    height: document.documentElement.scrollHeight
  }, "*");
}
addEventListener("load", reportHeight);
new ResizeObserver(reportHeight).observe(document.documentElement);
```

## Design (match the reader, stay topic-specific)

- Dark page (`color-scheme: dark`). Background near `#0a0d18` / `#090b10` so the iframe
  does not flash light inside the reader's shell
- System UI + ui-monospace only — no Google Fonts
- Clear mechanism, live numerical readout, one-sentence state explanation
- Meaningful labelled controls (keyboard accessible) and a **Reset** button that returns every
  input to the article's own numbers — a reader who drags a slider into nonsense must have a way
  back without reloading the page
- Works at phone width; honor `prefers-reduced-motion`; cap timers and clean them up
- Deterministic / seeded data if you simulate

Canvas is fine if it stays self-contained (see `2026-08-23/visualize.html`).

## After writing

```bash
# syntax: build.js --check already compiles every <script>
node build.js --check
```

Today's id must not warn `no visualize.html`, `no data-visualizer`, `does not report its
height`, `references external resources`, or `invalid JavaScript`.

**Four of the rules above are now build warnings, not honour-system items:** the CSP meta, the
session id on `data-visualizer`, `documentElement.scrollHeight` + `ResizeObserver`, and the Reset
control. They are the parts of the contract that are invisible in a screenshot, which is exactly
why they were the parts that shipped missing. A visualizer that looks finished and warns is not
finished.
