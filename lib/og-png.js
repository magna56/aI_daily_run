/* =============================================================================
   og-png.js — 1200×630 Open Graph card, no native deps.
   -----------------------------------------------------------------------------
   Session pages used to share one site-wide og-image.png, so Google/social
   crawlers saw the same picture for every article. This draws a dark branded
   card (title + date + category) as a real PNG so each URL has its own image.
   ============================================================================= */

"use strict";

const zlib = require("zlib");

const W = 1200;
const H = 630;

// 5×7 glyphs for printable ASCII. Each row is a 5-bit mask, MSB = left pixel.
const FONT = {
  " ": [0,0,0,0,0,0,0],
  "!": [4,4,4,4,0,4,0],
  "\"": [10,10,0,0,0,0,0],
  "#": [10,31,10,31,10,0,0],
  "%": [17,2,4,8,17,0,0],
  "&": [4,10,4,10,17,14,0],
  "'": [4,4,0,0,0,0,0],
  "(": [2,4,4,4,4,2,0],
  ")": [8,4,4,4,4,8,0],
  "*": [4,14,4,0,0,0,0],
  "+": [0,4,14,4,0,0,0],
  ",": [0,0,0,0,4,4,8],
  "-": [0,0,14,0,0,0,0],
  ".": [0,0,0,0,0,4,0],
  "/": [1,2,4,8,16,0,0],
  "0": [14,17,19,21,25,14,0],
  "1": [4,12,4,4,4,14,0],
  "2": [14,17,1,6,8,31,0],
  "3": [14,17,2,1,17,14,0],
  "4": [2,6,10,18,31,2,0],
  "5": [31,16,30,1,17,14,0],
  "6": [14,16,30,17,17,14,0],
  "7": [31,1,2,4,8,8,0],
  "8": [14,17,14,17,17,14,0],
  "9": [14,17,17,15,1,14,0],
  ":": [0,4,0,0,4,0,0],
  ";": [0,4,0,0,4,4,8],
  "<": [2,4,8,4,2,0,0],
  "=": [0,14,0,14,0,0,0],
  ">": [8,4,2,4,8,0,0],
  "?": [14,17,2,4,0,4,0],
  "@": [14,17,21,21,16,14,0],
  A: [14,17,17,31,17,17,0],
  B: [30,17,30,17,17,30,0],
  C: [14,17,16,16,17,14,0],
  D: [30,17,17,17,17,30,0],
  E: [31,16,30,16,16,31,0],
  F: [31,16,30,16,16,16,0],
  G: [14,17,16,19,17,14,0],
  H: [17,17,31,17,17,17,0],
  I: [14,4,4,4,4,14,0],
  J: [1,1,1,1,17,14,0],
  K: [17,18,28,18,17,17,0],
  L: [16,16,16,16,16,31,0],
  M: [17,27,21,17,17,17,0],
  N: [17,25,21,19,17,17,0],
  O: [14,17,17,17,17,14,0],
  P: [30,17,17,30,16,16,0],
  Q: [14,17,17,21,18,13,0],
  R: [30,17,17,30,18,17,0],
  S: [14,17,8,2,17,14,0],
  T: [31,4,4,4,4,4,0],
  U: [17,17,17,17,17,14,0],
  V: [17,17,17,17,10,4,0],
  W: [17,17,17,21,21,10,0],
  X: [17,17,14,17,17,17,0],
  Y: [17,17,14,4,4,4,0],
  Z: [31,1,2,4,8,31,0],
  "[": [14,8,8,8,8,14,0],
  "]": [14,2,2,2,2,14,0],
  "_": [0,0,0,0,0,31,0],
  a: [0,14,1,15,17,15,0],
  b: [16,16,30,17,17,30,0],
  c: [0,14,16,16,17,14,0],
  d: [1,1,15,17,17,15,0],
  e: [0,14,17,31,16,14,0],
  f: [6,8,28,8,8,8,0],
  g: [0,15,17,15,1,14,0],
  h: [16,16,30,17,17,17,0],
  i: [4,0,12,4,4,14,0],
  j: [2,0,2,2,18,12,0],
  k: [16,18,20,24,20,18,0],
  l: [12,4,4,4,4,14,0],
  m: [0,26,21,21,21,21,0],
  n: [0,30,17,17,17,17,0],
  o: [0,14,17,17,17,14,0],
  p: [0,30,17,30,16,16,0],
  q: [0,15,17,15,1,1,0],
  r: [0,22,24,16,16,16,0],
  s: [0,15,16,14,1,30,0],
  t: [8,28,8,8,8,6,0],
  u: [0,17,17,17,17,15,0],
  v: [0,17,17,17,10,4,0],
  w: [0,17,17,21,21,10,0],
  x: [0,17,10,4,10,17,0],
  y: [0,17,17,15,1,14,0],
  z: [0,31,2,4,8,31,0],
  "{": [6,8,8,16,8,8,6],
  "|": [4,4,4,4,4,4,0],
  "}": [12,2,2,1,2,2,12],
  "~": [0,8,21,2,0,0,0],
};

function crc32(buf) {
  let c = ~0;
  for (let i = 0; i < buf.length; i++) {
    c ^= buf[i];
    for (let k = 0; k < 8; k++) c = (c >>> 1) ^ (0xEDB88320 & -(c & 1));
  }
  return (~c) >>> 0;
}

function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const td = Buffer.concat([Buffer.from(type), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(td));
  return Buffer.concat([len, td, crc]);
}

function hex(s) {
  const n = parseInt(s.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function fill(px, x0, y0, x1, y1, rgb) {
  const xA = Math.max(0, x0 | 0), xB = Math.min(W, x1 | 0);
  const yA = Math.max(0, y0 | 0), yB = Math.min(H, y1 | 0);
  for (let y = yA; y < yB; y++) {
    let i = (y * W + xA) * 3;
    for (let x = xA; x < xB; x++) {
      px[i++] = rgb[0]; px[i++] = rgb[1]; px[i++] = rgb[2];
    }
  }
}

function glyph(ch) {
  return FONT[ch] || FONT[ch.toUpperCase()] || FONT["?"];
}

function textWidth(s, scale, tracking) {
  return s.length * (5 * scale + tracking) - tracking;
}

function drawText(px, s, x, y, scale, rgb, tracking) {
  for (const ch of s) {
    const rows = glyph(ch);
    for (let r = 0; r < 7; r++) {
      const bits = rows[r] || 0;
      for (let c = 0; c < 5; c++) {
        if (bits & (16 >> c)) {
          fill(px, x + c * scale, y + r * scale, x + (c + 1) * scale, y + (r + 1) * scale, rgb);
        }
      }
    }
    x += 5 * scale + tracking;
  }
}

function wrap(s, maxChars) {
  const words = String(s || "").split(/\s+/).filter(Boolean);
  const lines = [];
  let cur = "";
  for (const w of words) {
    const next = cur ? cur + " " + w : w;
    if (next.length <= maxChars) cur = next;
    else {
      if (cur) lines.push(cur);
      if (w.length > maxChars) {
        for (let i = 0; i < w.length; i += maxChars) lines.push(w.slice(i, i + maxChars));
        cur = "";
      } else cur = w;
    }
  }
  if (cur) lines.push(cur);
  return lines.slice(0, 4);
}

function encodePng(px) {
  const raw = Buffer.alloc((W * 3 + 1) * H);
  for (let y = 0; y < H; y++) {
    const dest = y * (W * 3 + 1);
    raw[dest] = 0;
    px.copy(raw, dest + 1, y * W * 3, (y + 1) * W * 3);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(W, 0);
  ihdr.writeUInt32BE(H, 4);
  ihdr[8] = 8;   // bit depth
  ihdr[9] = 2;   // truecolor
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr),
    chunk("IDAT", zlib.deflateSync(raw, { level: 9 })),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

function renderOgPng({ title, kicker, date }) {
  const px = Buffer.alloc(W * H * 3);
  const bg = hex("#111217");
  const ink = hex("#e7e2d8");
  const muted = hex("#9a9488");
  const accent = hex("#a78bfa");
  fill(px, 0, 0, W, H, bg);
  fill(px, 0, 0, 16, H, accent);

  const brand = "THE AI COMMIT";
  drawText(px, brand, 64, 72, 3, accent, 4);

  const titleScale = 6;
  const tracking = 6;
  const maxPx = W - 64 - 64;
  const maxChars = Math.floor((maxPx + tracking) / (5 * titleScale + tracking));
  const lines = wrap(title, Math.max(18, maxChars));
  let y = 180;
  for (const line of lines) {
    drawText(px, line, 64, y, titleScale, ink, tracking);
    y += 7 * titleScale + 18;
  }

  const bits = [date, kicker].filter(Boolean).join("  |  ");
  if (bits) drawText(px, bits, 64, H - 90, 3, muted, 4);

  return encodePng(px);
}

module.exports = { renderOgPng };
