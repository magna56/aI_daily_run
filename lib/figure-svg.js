"use strict";
/* Inline article figures.
 *
 * Two problems are being fixed here, and the second one matters more.
 *
 * 1. SIZE. The Diagram tab renders one 1200x1700 poster carrying every visual a
 *    session has, then scales it into a pane. At that scale a 13px label lands
 *    at about six pixels. So a figure here is deliberately small: one claim,
 *    720px wide, no type under 11px, read at 1:1 and never zoomed.
 *
 * 2. CONTENT. The old generator could only express `concepts` (a definition
 *    grid), `flow` (a strip of labels), `rows` (a table) and `bars` (a chart).
 *    None of those can draw a MECHANISM -- they can only arrange labels. So
 *    every session drew a picture of its own sentences, which is exactly what
 *    SKILL.md forbids, and the rule was unobeyable because the tool had no way
 *    to obey it.
 *
 * Hence this vocabulary. Every kind here draws STRUCTURE the prose cannot hand
 * you in one glance:
 *
 *   anatomy  a real specimen -- JSON, a request, a config -- with callouts
 *            pointing at the exact lines that carry the argument
 *   route    one thing splitting into parts that go to different places, with
 *            the field that DECIDES the split drawn on the connector
 *   bars     genuine quantities, and nothing else
 *
 * If a figure you want is really a list of definitions, it is not a figure. It
 * is the glossary, and it already exists.
 *
 * Colour lives in index.html: the SVG emits class names and the site supplies
 * the palette, so figures follow the reader's light/dark theme.
 */

const W = 720;                 // the reading column, and the only width there is
const PAD = 16;
const TITLE = 15, LABEL = 12.5, MONO = 12, NOTE = 11.5;
const MONO_ADV = 0.6;          // advance width of the mono stack, per px of size

const esc = (s) => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function textW(s, size) { return String(s).length * size * 0.545; }

function wrap(s, size, max, maxLines) {
  const words = String(s).split(/\s+/).filter(Boolean);
  const lines = [];
  let line = "";
  for (const w of words) {
    const next = line ? line + " " + w : w;
    if (textW(next, size) > max && line) { lines.push(line); line = w; }
    else line = next;
  }
  if (line) lines.push(line);
  if (maxLines && lines.length > maxLines) {
    const cut = lines.slice(0, maxLines);
    cut[maxLines - 1] = cut[maxLines - 1].replace(/.{0,2}$/, "…");
    return cut;
  }
  return lines;
}

const txt = (x, y, s, size, cls, anchor) =>
  `<text x="${(+x).toFixed(1)}" y="${(+y).toFixed(1)}" class="${cls}" font-size="${size}"` +
  (anchor ? ` text-anchor="${anchor}"` : "") + `>${esc(s)}</text>`;

/* ---- anatomy -----------------------------------------------------------
 * A specimen on the left, callouts on the right, a leader line from each
 * callout to the line it is about. This is the one that teaches: the reader
 * sees the real shape, and the annotation says which part is load-bearing.  */
function anatomy(spec) {
  const lines = spec.lines || [];
  const callouts = spec.callouts || [];
  const lineH = MONO * 1.55;
  const specW = Math.min(392, Math.max(...lines.map((l) => textW(l, MONO) * 1.1), 240) + 26);
  const specX = PAD, calloutX = specX + specW + 58;
  const calloutW = W - PAD - calloutX;

  let y = PAD + (spec.title ? 30 : 0);
  const specY = y;
  const specH = lines.length * lineH + 18;
  const parts = [
    `<rect x="${specX}" y="${specY}" width="${specW.toFixed(1)}" height="${specH.toFixed(1)}" rx="8" class="fig-spec"/>`,
  ];

  // Which specimen lines are called out — those get a highlight band.
  const marked = new Set(callouts.map((c) => c.line));
  lines.forEach((ln, i) => {
    const ly = specY + 13 + i * lineH;
    if (marked.has(i)) {
      parts.push(`<rect x="${specX + 4}" y="${(ly - MONO + 1).toFixed(1)}" width="${(specW - 8).toFixed(1)}" height="${(lineH - 1).toFixed(1)}" rx="4" class="fig-specmark"/>`);
    }
    parts.push(`<text x="${specX + 12}" y="${(ly + 3).toFixed(1)}" class="fig-mono${marked.has(i) ? " on" : ""}" font-size="${MONO}" xml:space="preserve">${esc(ln)}</text>`);
  });

  // Callouts, stacked, each with a leader back to its line.
  let cy = specY + 2;
  for (const c of callouts) {
    const body = wrap(c.t || "", LABEL, calloutW - 26, 3);
    const h = body.length * LABEL * 1.35 + 16;
    const anchorY = specY + 13 + (c.line || 0) * lineH - 1;
    const midY = cy + h / 2;
    parts.push(
      `<path d="M${(specX + specW + 4).toFixed(1)} ${anchorY.toFixed(1)} C${(specX + specW + 30).toFixed(1)} ${anchorY.toFixed(1)}, ${(calloutX - 26).toFixed(1)} ${midY.toFixed(1)}, ${(calloutX - 6).toFixed(1)} ${midY.toFixed(1)}" class="fig-leader fig-${c.s || "neutral"}"/>`,
      `<circle cx="${(specX + specW + 4).toFixed(1)}" cy="${anchorY.toFixed(1)}" r="2.6" class="fig-dot fig-${c.s || "neutral"}"/>`,
      `<rect x="${calloutX}" y="${cy.toFixed(1)}" width="${calloutW}" height="${h.toFixed(1)}" rx="7" class="fig-callout fig-${c.s || "neutral"}"/>`,
      body.map((l, i) => txt(calloutX + 12, cy + 14 + i * LABEL * 1.35, l, LABEL, "fig-celltext")).join(""));
    cy += h + 9;
  }
  return { body: parts.join(""), height: Math.max(specY + specH, cy) + PAD };
}

/* ---- route -------------------------------------------------------------
 * One object splits, and each part goes somewhere different. The field that
 * DECIDES where it goes is drawn on the connector, because that field is the
 * mechanism and everything else is scenery. */
function route(spec) {
  const parts = spec.parts || [], dests = spec.dests || [];
  const srcW = 196, destW = 190;
  const midX = PAD + srcW + 62, destX = W - PAD - destW;
  let y = PAD + (spec.title ? 30 : 0);

  const partH = 44, partGap = 12;
  const srcH = parts.length * partH + (parts.length - 1) * partGap + 34;
  const destH = 46, destGap = 18;
  const destsH = dests.length * destH + (dests.length - 1) * destGap;
  const top = y, height = Math.max(srcH, destsH);
  const srcY = top + (height - srcH) / 2, destY = top + (height - destsH) / 2;

  const out = [
    `<rect x="${PAD}" y="${srcY.toFixed(1)}" width="${srcW}" height="${srcH.toFixed(1)}" rx="9" class="fig-frame"/>`,
    txt(PAD + 12, srcY + 19, spec.source || "one tool result", LABEL, "fig-framelabel"),
  ];

  dests.forEach((d, i) => {
    const dy = destY + i * (destH + destGap);
    const body = wrap(typeof d === "string" ? d : d.t, LABEL, destW - 20, 2);
    out.push(`<rect x="${destX}" y="${dy.toFixed(1)}" width="${destW}" height="${destH}" rx="8" class="fig-cell fig-${(d && d.s) || "neutral"}"/>`);
    out.push(body.map((l, k) => txt(destX + destW / 2, dy + destH / 2 - (body.length - 1) * LABEL * 0.68 + k * LABEL * 1.35 + 4, l, LABEL, "fig-celltext", "middle")).join(""));
  });

  parts.forEach((p, i) => {
    const py = srcY + 26 + i * (partH + partGap);
    const body = wrap(p.t || "", LABEL, srcW - 24, 2);
    out.push(`<rect x="${PAD + 10}" y="${py.toFixed(1)}" width="${srcW - 20}" height="${partH}" rx="6" class="fig-cell fig-${p.s || "neutral"}"/>`);
    out.push(body.map((l, k) => txt(PAD + srcW / 2, py + partH / 2 - (body.length - 1) * LABEL * 0.68 + k * LABEL * 1.35 + 4, l, LABEL, "fig-celltext", "middle")).join(""));

    const toIdx = Math.min(p.to || 0, Math.max(dests.length - 1, 0));
    const y1 = py + partH / 2, y2 = destY + toIdx * (destH + destGap) + destH / 2;
    const x1 = PAD + srcW - 6;
    out.push(
      `<path d="M${x1} ${y1.toFixed(1)} C${(x1 + 40)} ${y1.toFixed(1)}, ${(destX - 44)} ${y2.toFixed(1)}, ${(destX - 7)} ${y2.toFixed(1)}" class="fig-leader fig-${p.s || "neutral"}"/>`,
      `<path d="M${destX - 7} ${y2.toFixed(1)} l-6 -4 v8 z" class="fig-arrowhead fig-${p.s || "neutral"}"/>`);
    if (p.via) {
      const vy = (y1 + y2) / 2 - 7, vw = textW(p.via, NOTE) + 14;
      out.push(
        `<rect x="${(midX - vw / 2).toFixed(1)}" y="${vy.toFixed(1)}" width="${vw.toFixed(1)}" height="16" rx="8" class="fig-via"/>`,
        txt(midX, vy + 11.5, p.via, NOTE, "fig-viatext", "middle"));
    }
  });
  return { body: out.join(""), height: top + height + PAD };
}

/* ---- bars: genuine quantities, nothing else ---------------------------- */
function bars(spec) {
  const items = spec.bars || [];
  const labelW = 176, valueW = 84;
  const trackW = W - PAD * 2 - labelW - valueW - 16;
  const max = Math.max(...items.map((b) => Math.abs(b.v) || 0), 1);
  let y = PAD + (spec.title ? 30 : 0);
  const out = [];
  for (const b of items) {
    const h = 26, bw = Math.max(2, trackW * (Math.abs(b.v) || 0) / max);
    out.push(
      ...wrap(b.label || "", LABEL, labelW - 8, 2).map((l, i, all) =>
        txt(PAD, y + h / 2 - (all.length - 1) * LABEL * 0.68 + i * LABEL * 1.35 + 4, l, LABEL, "fig-rowlabel")),
      `<rect x="${PAD + labelW}" y="${y}" width="${trackW}" height="${h}" rx="5" class="fig-track"/>`,
      `<rect x="${PAD + labelW}" y="${y}" width="${bw.toFixed(1)}" height="${h}" rx="5" class="fig-bar fig-${b.s || "neutral"}"/>`,
      txt(W - PAD, y + h / 2 + 4, b.d != null ? b.d : b.v, LABEL, "fig-value", "end"));
    y += h + 10;
  }
  return { body: out.join(""), height: y - 10 + PAD };
}

/* ---- system: an actual block diagram ----------------------------------
 * Lanes are columns (server | host | destination), nodes stack inside a lane,
 * and edges carry the label that explains WHY the arrow exists. This is the one
 * that answers "draw me the thing" -- containment and direction do the
 * explaining, and the labels only name what is already visible in the shape.  */
function system(spec) {
  const lanes = spec.lanes || [], edges = spec.edges || [];
  /* The gutter between lanes is sized to the widest edge label, not fixed. With
     a fixed 46px gap the labels ("user", "assistant") were wider than the space
     they sat in and collided with the boxes on either side. */
  const widestEdge = Math.max(0, ...edges.map((e) => (e.t ? textW(e.t, NOTE) + 18 : 0)));
  const laneGap = Math.max(56, Math.min(140, widestEdge + 22));
  const laneW = (W - PAD * 2 - laneGap * (lanes.length - 1)) / (lanes.length || 1);
  const nodeH = 46, nodeGap = 16;
  const top = PAD + (spec.title ? 30 : 0);
  const headH = lanes.some((l) => l.t) ? 22 : 0;
  const rows = Math.max(...lanes.map((l) => (l.nodes || []).length), 1);
  const bodyH = rows * nodeH + (rows - 1) * nodeGap;

  const at = {};                       // id -> box, so edges can find their ends
  const boxes = [], labels = [];
  lanes.forEach((lane, li) => {
    const lx = PAD + li * (laneW + laneGap);
    if (lane.t) {
      labels.push(txt(lx + laneW / 2, top + 13, lane.t, NOTE, "fig-lane", "middle"));
    }
    const nodes = lane.nodes || [];
    const stackH = nodes.length * nodeH + (nodes.length - 1) * nodeGap;
    const ny0 = top + headH + (bodyH - stackH) / 2;
    nodes.forEach((n, ni) => {
      const y = ny0 + ni * (nodeH + nodeGap);
      at[n.id] = { x: lx, y, w: laneW, h: nodeH };
      const lines = wrap(n.t || "", LABEL, laneW - 16, 2);
      boxes.push(
        `<rect x="${lx.toFixed(1)}" y="${y.toFixed(1)}" width="${laneW.toFixed(1)}" height="${nodeH}" rx="8" class="fig-cell fig-${n.s || "neutral"}"/>`,
        lines.map((l, k) => txt(lx + laneW / 2,
          y + nodeH / 2 - (lines.length - 1) * LABEL * 0.68 + k * LABEL * 1.35 + 4,
          l, LABEL, "fig-celltext", "middle")).join(""));
    });
  });

  const wires = [];
  /* Two edges crossing the same gutter at similar heights put their labels in
     the same place, which is how "a file path" ended up printed on top of
     "user". Remember every label box and nudge a colliding one clear. */
  const placed = [];
  function freeY(x, y, w) {
    let ty = y;
    for (let guard = 0; guard < 24; guard++) {
      const hit = placed.some((r) => Math.abs(r.y - ty) < 17 && Math.abs(r.x - x) < (r.w + w) / 2);
      if (!hit) break;
      ty += 18;
    }
    placed.push({ x, y: ty, w });
    return ty;
  }
  for (const e of edges) {
    const a = at[e.from], b = at[e.to];
    if (!a || !b) continue;
    const x1 = a.x + a.w + 2, y1 = a.y + a.h / 2;
    const x2 = b.x - 8, y2 = b.y + b.h / 2;
    const mx = (x1 + x2) / 2;
    wires.push(
      `<path d="M${x1.toFixed(1)} ${y1.toFixed(1)} C${mx.toFixed(1)} ${y1.toFixed(1)}, ${mx.toFixed(1)} ${y2.toFixed(1)}, ${x2.toFixed(1)} ${y2.toFixed(1)}" class="fig-leader fig-${e.s || "neutral"}"/>`,
      `<path d="M${x2.toFixed(1)} ${y2.toFixed(1)} l-6 -4 v8 z" class="fig-arrowhead fig-${e.s || "neutral"}"/>`);
    if (e.t) {
      const vw = Math.min(textW(e.t, NOTE) + 12, laneGap - 8);
      const vy = freeY(mx, (y1 + y2) / 2 - 8, vw);
      wires.push(
        `<rect x="${(mx - vw / 2).toFixed(1)}" y="${vy.toFixed(1)}" width="${vw.toFixed(1)}" height="16" rx="8" class="fig-via"/>`,
        txt(mx, vy + 11.5, e.t, NOTE, "fig-viatext", "middle"));
    }
  }
  // Wires under boxes, so a curve never crosses a label.
  return { body: labels.join("") + wires.join("") + boxes.join(""),
           height: top + headH + bodyH + PAD };
}

const KINDS = { anatomy, route, bars, system };

function renderFigure(spec) {
  const make = KINDS[spec && spec.kind];
  if (!make) throw new Error("unknown figure kind: " + (spec && spec.kind) +
    " (want anatomy, route, bars or system)");
  const { body, height } = make(spec);
  const head = spec.title ? txt(PAD, PAD + 14, spec.title, TITLE, "fig-title") : "";
  const noteLines = spec.note ? wrap(spec.note, NOTE, W - PAD * 2, 2) : [];
  const foot = noteLines.map((l, i) => txt(PAD, height + 4 + i * NOTE * 1.32, l, NOTE, "fig-note")).join("");
  const total = height + (noteLines.length ? noteLines.length * NOTE * 1.32 + 6 : 0);

  /* No width/height attributes: the figure scales to its container and never
     needs a pan/zoom viewport, which is the point of this whole file. */
  return `<svg class="fig" viewBox="0 0 ${W} ${total.toFixed(0)}" role="img" ` +
    `aria-label="${esc(spec.title || spec.kind)}" preserveAspectRatio="xMidYMin meet">` +
    head + body + foot + "</svg>";
}

module.exports = { renderFigure, FIGURE_WIDTH: W, FIGURE_KINDS: Object.keys(KINDS) };
