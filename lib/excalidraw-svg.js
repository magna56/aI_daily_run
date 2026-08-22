/* =============================================================================
   excalidraw-svg.js — renders a .excalidraw scene to a standalone SVG string.
   -----------------------------------------------------------------------------
   Dependency-free, deterministic (same scene in => byte-identical SVG out), and
   sized for exactly the diagrams that scripts/generate_excalidraw.py emits:
   rectangle + text + arrow, all at roughness 0 (no hand-drawn jitter to fake).

   Anything outside that set is skipped rather than approximated — a wrong shape
   reads as a bug in the diagram, a missing one reads as a gap in this renderer.

     const { renderExcalidrawSVG } = require("./lib/excalidraw-svg");
     const { svg, width, height, skipped } = renderExcalidrawSVG(scene);

   Geometry notes (mirroring the generator, which pre-computes final positions):
     - text.x/.y is the TOP-LEFT of the text block; centre/middle alignment is
       already baked in by the generator, so no container math is needed here.
     - text.height is lines * fontSize * 1.25 + 4, i.e. 2px of padding per side.
     - arrow.x/.y is the start point and `points` are relative to it.
     - Array order is z-order. The generator's `index` ("a3", "a10", ...) is NOT
       a valid fractional index — sorting by it would put a10 before a9 — so it
       is deliberately ignored.
   ============================================================================= */

"use strict";

const PADDING = 20;          // breathing room around the scene bounding box
const LINE_HEIGHT = 1.25;    // generator hard-codes this; used when absent
const TEXT_PAD_Y = 2;        // half of the generator's +4 height padding

// Excalidraw font ids -> a stack we can actually serve. Excalifont/Virgil are
// not embedded (that would mean shipping a webfont), so the hand-drawn faces
// fall back to the system sans. Our stack runs ~5% narrower per glyph than the
// generator's 0.55*fontSize estimate, so labels sit inside their boxes.
const FONTS = {
  1: '"Excalifont", "Virgil", "Segoe UI", ui-sans-serif, system-ui, sans-serif',
  2: '"Helvetica Neue", Helvetica, Arial, sans-serif',
  3: 'ui-monospace, "Cascadia Code", SFMono-Regular, Menlo, Consolas, monospace',
  5: '"Excalifont", "Segoe UI", ui-sans-serif, system-ui, -apple-system, sans-serif',
  6: '"Nunito", ui-sans-serif, system-ui, sans-serif',
  7: '"Lilita One", ui-sans-serif, system-ui, sans-serif',
  8: '"Comic Shanns", ui-monospace, monospace',
};
const DEFAULT_FONT = FONTS[5];

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"]/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]
  ));
}

// Trim float noise so rebuilds produce identical bytes and the SVG stays small.
function n(v) {
  const r = Math.round(Number(v) * 100) / 100;
  return Object.is(r, -0) ? 0 : r;
}

function isTransparent(c) {
  return !c || c === "transparent" || c === "none";
}

/* ---- text measurement ----------------------------------------------------- */

// Approximate advance widths, in em, for a Helvetica/Segoe-class sans. Exact
// metrics would need the font file; these land within a few percent, which is
// all the wrapper needs to break lines where Excalidraw breaks them.
const NARROW = "iljtfrI.,'\"`:;!|()[]{}";
const WIDE = "mwMW@%";
const EM = (() => {
  const t = Object.create(null);
  for (const c of NARROW) t[c] = 0.29;
  for (const c of WIDE) t[c] = 0.86;
  for (const c of "ABCDEFGHJKLNOPQRSTUVXYZ") t[c] = 0.68;
  for (const c of "0123456789") t[c] = 0.56;
  t[" "] = 0.27; t["-"] = 0.34; t["_"] = 0.5;
  return t;
})();

function measure(str, fontSize) {
  let em = 0;
  for (const ch of String(str)) em += EM[ch] === undefined ? 0.52 : EM[ch];
  return em * fontSize;
}

// Greedy word wrap, matching how Excalidraw reflows text bound to a container.
// Words wider than the line are hard-broken so nothing escapes the shape.
function wrapText(str, maxWidth, fontSize) {
  const out = [];
  for (const paragraph of String(str).split("\n")) {
    if (!paragraph) { out.push(""); continue; }
    let line = "";
    for (const word of paragraph.split(/(\s+)/)) {
      if (!word) continue;
      const candidate = line + word;
      if (line && measure(candidate, fontSize) > maxWidth) {
        out.push(line.trimEnd());
        line = /^\s+$/.test(word) ? "" : word;
      } else {
        line = candidate;
      }
      while (measure(line, fontSize) > maxWidth && line.length > 1) {
        let cut = line.length - 1;
        while (cut > 1 && measure(line.slice(0, cut), fontSize) > maxWidth) cut--;
        out.push(line.slice(0, cut));
        line = line.slice(cut);
      }
    }
    out.push(line.trimEnd());
  }
  return out;
}

function alive(el) {
  return el && !el.isDeleted && el.type;
}

/* ---- geometry ------------------------------------------------------------ */

const BOUND_PAD = 5; // Excalidraw's BOUND_TEXT_PADDING

/**
 * One pass that resolves every text element's real geometry, because the saved
 * file does not carry it:
 *
 *   1. Wrap each text to its declared width. The generator always passes width
 *      as a box constraint (a column, a shape's inner width), never as a
 *      measurement, so treating it as a wrap boundary is what it meant. This is
 *      also what Excalidraw does for text bound to a shape.
 *   2. Re-derive text height from the wrapped line count.
 *   3. Grow any shape whose label now needs more room — Excalidraw re-runs this
 *      on load, so a file can legitimately carry a too-short box (the generator
 *      sizes flow steps before it knows how their labels wrap).
 *
 * Without step 1 long descriptions run off the canvas; without step 3 labels
 * spill out the bottom of their shape.
 */
function layout(elements) {
  const out = elements.map((el) => {
    if (el.type !== "text") return el;
    const size = el.fontSize || 16;
    const lh = (el.lineHeight || LINE_HEIGHT) * size;
    const lines = el.width > 0
      ? wrapText(el.text, el.width, size)
      : String(el.text == null ? "" : el.text).split("\n");
    let widest = 0;
    for (const line of lines) widest = Math.max(widest, measure(line, size));
    return Object.assign({}, el, {
      _lines: lines,
      // Keep the declared width (it anchors centred text) but never let the
      // bounding box crop a line that renders wider than the estimate did.
      _inkWidth: Math.max(el.width || 0, widest),
      height: lines.length * lh + TEXT_PAD_Y * 2,
    });
  });

  // containerId on the label is the authoritative link (boundElements on the
  // shape is only a convenience index, and is sometimes absent).
  const needed = new Map();
  for (const el of out) {
    if (el.type !== "text" || !el.containerId) continue;
    const want = el.height + BOUND_PAD * 2;
    needed.set(el.containerId, Math.max(needed.get(el.containerId) || 0, want));
  }
  return out.map((el) => {
    const want = needed.get(el.id);
    return want > el.height ? Object.assign({}, el, { height: Math.ceil(want) }) : el;
  });
}

// Arrows can run right-to-left or bottom-to-top, in which case el.width is the
// absolute delta and x/y is still the START — so the true extent has to come
// from the points, not from x..x+width.
function extent(el) {
  if ((el.type === "arrow" || el.type === "line") && Array.isArray(el.points) && el.points.length) {
    const xs = el.points.map((p) => el.x + p[0]);
    const ys = el.points.map((p) => el.y + p[1]);
    return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
  }
  // _inkWidth (set by layout) is how wide the text actually renders, which can
  // exceed the declared width the generator reserved for it.
  const w = el.type === "text" && el._inkWidth != null ? el._inkWidth : (el.width || 0);
  // Centred text is anchored on its box centre, so extra ink spreads both ways.
  const slack = el.type === "text" && el.textAlign === "center" ? (w - (el.width || 0)) / 2 : 0;
  return [el.x - Math.max(0, slack), el.y, el.x + w - Math.max(0, slack), el.y + (el.height || 0)];
}

function bounds(elements) {
  let x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
  for (const el of elements) {
    const [a, b, c, d] = extent(el);
    if (a < x1) x1 = a;
    if (b < y1) y1 = b;
    if (c > x2) x2 = c;
    if (d > y2) y2 = d;
  }
  if (!isFinite(x1)) return { x1: 0, y1: 0, x2: 100, y2: 100 };
  return { x1, y1, x2, y2 };
}

/* ---- element renderers --------------------------------------------------- */

// Excalidraw's ADAPTIVE_RADIUS (roundness.type 3) caps at 32px; PROPORTIONAL
// (type 2, used on arrows) never applies to a rect here.
function cornerRadius(el) {
  if (!el.roundness) return 0;
  if (el.roundness.type === 3) return Math.min(32, Math.min(el.width, el.height) * 0.25);
  return Math.min(el.width, el.height) * 0.25;
}

function renderRect(el) {
  const fill = isTransparent(el.backgroundColor) ? "none" : el.backgroundColor;
  const r = n(cornerRadius(el));
  return (
    `<rect x="${n(el.x)}" y="${n(el.y)}" width="${n(el.width)}" height="${n(el.height)}"` +
    (r ? ` rx="${r}" ry="${r}"` : "") +
    ` fill="${esc(fill)}" stroke="${esc(el.strokeColor)}" stroke-width="${n(el.strokeWidth || 1)}"` +
    opacityAttr(el) +
    ` />`
  );
}

function renderEllipse(el) {
  const fill = isTransparent(el.backgroundColor) ? "none" : el.backgroundColor;
  return (
    `<ellipse cx="${n(el.x + el.width / 2)}" cy="${n(el.y + el.height / 2)}"` +
    ` rx="${n(el.width / 2)}" ry="${n(el.height / 2)}"` +
    ` fill="${esc(fill)}" stroke="${esc(el.strokeColor)}" stroke-width="${n(el.strokeWidth || 1)}"` +
    opacityAttr(el) +
    ` />`
  );
}

function renderDiamond(el) {
  const fill = isTransparent(el.backgroundColor) ? "none" : el.backgroundColor;
  const { x, y, width: w, height: h } = el;
  const pts = [
    [x + w / 2, y], [x + w, y + h / 2], [x + w / 2, y + h], [x, y + h / 2],
  ].map(([a, b]) => `${n(a)},${n(b)}`).join(" ");
  return (
    `<polygon points="${pts}" fill="${esc(fill)}" stroke="${esc(el.strokeColor)}"` +
    ` stroke-width="${n(el.strokeWidth || 1)}"${opacityAttr(el)} />`
  );
}

function opacityAttr(el) {
  const o = el.opacity == null ? 100 : el.opacity;
  return o >= 100 ? "" : ` opacity="${n(o / 100)}"`;
}

function renderText(el, byId) {
  const size = el.fontSize || 16;
  const lh = (el.lineHeight || LINE_HEIGHT) * size;
  const family = FONTS[el.fontFamily] || DEFAULT_FONT;
  const align = el.textAlign || "left";
  const container = el.containerId && byId ? byId.get(el.containerId) : null;
  const lines = el._lines || String(el.text == null ? "" : el.text).split("\n");

  // Horizontal anchor. el.width is the box the generator reserved, not the
  // measured glyph width, so anchoring (rather than stretching) is what keeps
  // labels centred in their rectangles.
  let anchorX = el.x;
  let anchor = "start";
  if (align === "center") { anchorX = el.x + (el.width || 0) / 2; anchor = "middle"; }
  else if (align === "right") { anchorX = el.x + (el.width || 0); anchor = "end"; }

  // Wrapping changes the line count, so the block has to be re-centred against
  // the container rather than against el.height (computed for the unwrapped text).
  const block = lines.length * lh;
  let top;
  if (container && el.verticalAlign === "middle") top = container.y + (container.height - block) / 2;
  else if (el.verticalAlign === "middle") top = el.y + ((el.height || block) - block) / 2;
  else top = el.y + TEXT_PAD_Y;

  const out = [];
  lines.forEach((line, i) => {
    if (!line) return; // nothing to paint, but the line still advances y
    // Centre each line inside its own line box: matches how Excalidraw lays
    // text out, and keeps single-line labels optically centred in a shape.
    const y = top + (i + 0.5) * lh;
    out.push(
      `<text x="${n(anchorX)}" y="${n(y)}" text-anchor="${anchor}"` +
      ` dominant-baseline="central" font-family='${family}' font-size="${n(size)}"` +
      ` fill="${esc(el.strokeColor)}"${opacityAttr(el)}` +
      ` style="white-space:pre">${esc(line)}</text>`
    );
  });
  return out.join("");
}

function renderPath(el, markers) {
  const pts = Array.isArray(el.points) && el.points.length
    ? el.points
    : [[0, 0], [el.width || 0, el.height || 0]];
  const abs = pts.map((p) => [el.x + p[0], el.y + p[1]]);

  let d;
  if (abs.length === 2 || !el.roundness) {
    d = "M " + abs.map(([x, y]) => `${n(x)} ${n(y)}`).join(" L ");
  } else {
    // Smooth multi-point arrows: quadratic curves through segment midpoints,
    // which is what Excalidraw's PROPORTIONAL_RADIUS curve looks like.
    d = `M ${n(abs[0][0])} ${n(abs[0][1])}`;
    for (let i = 1; i < abs.length - 1; i++) {
      const [cx, cy] = abs[i];
      const [nx, ny] = abs[i + 1];
      d += ` Q ${n(cx)} ${n(cy)} ${n((cx + nx) / 2)} ${n((cy + ny) / 2)}`;
    }
    const last = abs[abs.length - 1];
    d += ` L ${n(last[0])} ${n(last[1])}`;
  }

  const color = el.strokeColor || "#1e1e1e";
  let attrs = "";
  if (el.endArrowhead) attrs += ` marker-end="url(#${markers.get(color)})"`;
  if (el.startArrowhead) attrs += ` marker-start="url(#${markers.get(color)})"`;
  return (
    `<path d="${d}" fill="none" stroke="${esc(color)}" stroke-width="${n(el.strokeWidth || 1)}"` +
    ` stroke-linecap="round" stroke-linejoin="round"${opacityAttr(el)}${attrs} />`
  );
}

/* ---- arrowhead markers ---------------------------------------------------- */

// One marker per stroke colour. `orient="auto-start-reverse"` lets the same
// forward-pointing triangle serve marker-start and marker-end, so no separate
// mirrored shape is needed. Ids carry a per-render uid so several diagrams can
// coexist in one document without their defs colliding.
function markerRegistry(uid) {
  const seen = new Map();
  return {
    get(color) {
      if (!seen.has(color)) seen.set(color, `adl-${uid}-ah${seen.size}`);
      return seen.get(color);
    },
    defs() {
      const out = [];
      for (const [color, id] of seen) {
        out.push(
          `<marker id="${id}" viewBox="0 0 10 7" refX="10" refY="3.5"` +
          ` markerWidth="8" markerHeight="5.6" orient="auto-start-reverse">` +
          `<path d="M 0 0 L 10 3.5 L 0 7 z" fill="${esc(color)}" /></marker>`
        );
      }
      return out.join("");
    },
  };
}

/* ---- entry point ---------------------------------------------------------- */

/**
 * @param {object} scene  parsed .excalidraw JSON
 * @param {object} [opts] { uid, padding, title, background }
 * @returns {{svg:string,width:number,height:number,skipped:string[]}}
 */
function renderExcalidrawSVG(scene, opts) {
  const o = opts || {};
  const uid = o.uid || "d";
  const pad = o.padding == null ? PADDING : o.padding;
  const elements = layout(
    (scene && Array.isArray(scene.elements) ? scene.elements : []).filter(alive)
  );

  const { x1, y1, x2, y2 } = bounds(elements);
  const width = Math.max(1, Math.ceil(x2 - x1 + pad * 2));
  const height = Math.max(1, Math.ceil(y2 - y1 + pad * 2));

  const bg = o.background
    || (scene && scene.appState && scene.appState.viewBackgroundColor)
    || "#ffffff";

  const markers = markerRegistry(uid);
  const byId = new Map(elements.map((el) => [el.id, el]));
  const skipped = [];
  const body = [];

  for (const el of elements) {
    switch (el.type) {
      case "rectangle": body.push(renderRect(el)); break;
      case "ellipse": body.push(renderEllipse(el)); break;
      case "diamond": body.push(renderDiamond(el)); break;
      case "text": body.push(renderText(el, byId)); break;
      case "arrow":
      case "line": body.push(renderPath(el, markers)); break;
      default: skipped.push(el.type);
    }
  }

  // Title comes from the first text element so screen readers get something
  // better than "image"; the generator always leads with the topic title.
  const firstText = elements.find((e) => e.type === "text" && e.text);
  const title = o.title || (firstText ? String(firstText.text).split("\n")[0] : "Diagram");

  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${n(x1 - pad)} ${n(y1 - pad)} ${width} ${height}"` +
    ` width="${width}" height="${height}" role="img" aria-label="${esc(title)}">` +
    `<title>${esc(title)}</title>` +
    (markers.defs() ? `<defs>${markers.defs()}</defs>` : "") +
    `<rect x="${n(x1 - pad)}" y="${n(y1 - pad)}" width="${width}" height="${height}" fill="${esc(bg)}" />` +
    body.join("") +
    `</svg>`;

  return { svg, width, height, skipped: [...new Set(skipped)] };
}

module.exports = { renderExcalidrawSVG };
