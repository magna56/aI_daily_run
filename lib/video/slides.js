"use strict";

const zlib = require("zlib");

const W = 1080;
const H = 1920;

// 5×7 bitmap font (same glyphs as lib/og-png.js).
const FONT_FULL = {
  " ": [0,0,0,0,0,0,0],
  "!": [4,4,4,4,0,4,0],
  "\"": [10,10,0,0,0,0,0],
  "#": [10,31,10,31,10,0,0],
  "$": [4,15,20,14,5,30,4],
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
  K: [17,18,20,24,18,17,0],
  L: [16,16,16,16,16,31,0],
  M: [17,27,21,17,17,17,0],
  N: [17,25,21,19,17,17,0],
  O: [14,17,17,17,17,14,0],
  P: [30,17,30,16,16,16,0],
  Q: [14,17,17,21,10,13,0],
  R: [30,17,30,20,18,17,0],
  S: [14,17,16,14,1,30,0],
  T: [31,4,4,4,4,4,0],
  U: [17,17,17,17,17,14,0],
  V: [17,17,17,17,10,4,0],
  W: [17,17,17,21,21,10,0],
  X: [17,17,10,4,10,17,17,0],
  Y: [17,17,10,4,4,4,0],
  Z: [31,1,2,4,8,31,0],
  "[": [14,8,8,8,8,14,0],
  "\\": [16,8,4,2,1,0,0],
  "]": [14,2,2,2,2,14,0],
  "^": [4,10,17,0,0,0,0],
  _: [0,0,0,0,0,31,0],
  "`": [8,4,0,0,0,0,0],
  a: [0,0,14,1,15,15,0],
  b: [16,16,30,17,17,30,0],
  c: [0,0,14,16,16,14,0],
  d: [1,1,15,17,17,15,0],
  e: [0,0,14,31,16,14,0],
  f: [6,8,16,30,8,8,0],
  g: [0,15,17,15,1,14,0],
  h: [16,16,30,17,17,17,0],
  i: [4,0,4,4,4,4,0],
  j: [2,0,2,2,2,18,12,0],
  k: [16,16,18,20,18,17,0],
  l: [4,4,4,4,4,4,0],
  m: [0,0,21,21,21,21,0],
  n: [0,0,22,17,17,17,0],
  o: [0,0,14,17,17,14,0],
  p: [0,30,17,17,30,16,16,0],
  q: [0,15,17,17,15,1,1,0],
  r: [0,0,22,16,16,16,0],
  s: [0,0,14,16,14,1,30,0],
  t: [4,16,30,4,4,2,0],
  u: [0,0,17,17,17,15,0],
  v: [0,0,17,17,17,10,0],
  w: [0,0,17,17,21,10,0],
  x: [0,0,17,10,4,10,17,0],
  y: [0,0,17,17,15,1,14,0],
  z: [0,0,31,2,4,8,31,0],
  "{": [6,4,4,24,4,4,6,0],
  "|": [4,4,4,4,4,4,4,0],
  "}": [6,4,4,6,4,4,6,0],
  "~": [8,21,2,0,0,0,0],
};

function hex(h) {
  const n = parseInt(h.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function fill(px, x, y, w, hgt, rgb) {
  for (let row = y; row < y + hgt; row++) {
    for (let col = x; col < x + w; col++) {
      const i = (row * W + col) * 3;
      px[i] = rgb[0];
      px[i + 1] = rgb[1];
      px[i + 2] = rgb[2];
    }
  }
}

function drawText(px, text, x, y, scale, rgb, tracking = 4) {
  let cx = x;
  for (const ch of String(text)) {
    const g = FONT_FULL[ch] || FONT_FULL[ch.toUpperCase?.() ? ch.toUpperCase() : " "] || FONT_FULL[" "];
    for (let row = 0; row < 7; row++) {
      let bits = g[row] || 0;
      for (let col = 0; col < 5; col++) {
        if (bits & (16 >> col)) {
          fill(px, cx + col * scale, y + row * scale, scale, scale, rgb);
        }
      }
    }
    cx += 5 * scale + tracking;
  }
}

function asciify(s) {
  return String(s || "")
    .replace(/[—–]/g, "-")
    .replace(/[''']/g, "'")
    .replace(/[""]/g, '"')
    .replace(/…/g, "...")
    .replace(/[^\x20-\x7E]/g, "");
}

function wrap(s, maxChars, maxLines = 8) {
  const words = asciify(s).split(/\s+/).filter(Boolean);
  const lines = [];
  let cur = "";
  for (const w of words) {
    const next = cur ? `${cur} ${w}` : w;
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
  return lines.slice(0, maxLines);
}

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
  ihdr[8] = 8;
  ihdr[9] = 2;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr),
    chunk("IDAT", zlib.deflateSync(raw, { level: 9 })),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

function renderSlide({ kicker, headline, body, footer }) {
  const px = Buffer.alloc(W * H * 3);
  const bg = hex("#090b10");
  const panel = hex("#141821");
  const ink = hex("#f4f6fb");
  const muted = hex("#929db1");
  const accent = hex("#818cf8");
  const warn = hex("#facc15");

  fill(px, 0, 0, W, H, bg);
  fill(px, 0, 0, 12, H, accent);
  fill(px, 48, 320, W - 96, H - 640, panel);

  if (kicker) {
    drawText(px, asciify(kicker).toUpperCase(), 72, 120, 4, warn, 6);
  }

  const scale = 7;
  const tracking = 8;
  const maxChars = Math.floor((W - 144 + tracking) / (5 * scale + tracking));
  const lines = wrap(headline, Math.max(12, maxChars), 5);
  let y = 400;
  for (const line of lines) {
    drawText(px, line, 72, y, scale, ink, tracking);
    y += 7 * scale + 24;
  }

  if (body) {
    const bScale = 5;
    const bTrack = 6;
    const bMax = Math.floor((W - 144 + bTrack) / (5 * bScale + bTrack));
    const bodyLines = wrap(body, Math.max(16, bMax), 10);
    y += 40;
    for (const line of bodyLines) {
      drawText(px, line, 72, y, bScale, muted, bTrack);
      y += 7 * bScale + 18;
    }
  }

  if (footer) {
    const fScale = 4;
    const fLines = wrap(footer, 40, 2);
    let fy = H - 200;
    for (const line of fLines) {
      drawText(px, line, 72, fy, fScale, accent, 5);
      fy += 36;
    }
  }

  drawText(px, "THE AI COMMIT", 72, H - 80, 3, muted, 4);
  return encodePng(px);
}

function slideForBeat(session, beat) {
  if (beat.id === "cold_open") {
    return renderSlide({
      kicker: "If you build on OpenAI agents",
      headline: beat.onScreen || beat.text,
      footer: session.meta.Category || session.id,
    });
  }
  if (beat.id === "frame") {
    return renderSlide({
      kicker: "What changed",
      headline: beat.onScreen || beat.text,
      footer: session.id,
    });
  }
  if (beat.id === "mechanism") {
    return renderSlide({
      kicker: "The part people miss",
      headline: beat.onScreen || beat.text,
      body: beat.onScreen && beat.onScreen !== beat.text ? beat.text : null,
      footer: session.title,
    });
  }
  if (beat.id === "hook") {
    return renderSlide({
      kicker: session.meta.Category || "Daily lab",
      headline: session.meta.Hook || session.title,
      footer: session.id,
    });
  }
  if (beat.id === "cta") {
    return renderSlide({
      kicker: "Read the full article",
      headline: beat.title || session.title,
      footer: (beat.url || session.url).replace(/^https?:\/\//, ""),
    });
  }
  if (beat.id === "demo") {
    return renderSlide({
      kicker: "Interactive demo",
      headline: session.hasVisualize ? "See the billing multiplier" : "See the code",
      body: beat.text,
      footer: session.hasVisualize
        ? "Record visualize.html -> capture/demo.mp4"
        : null,
    });
  }
  return renderSlide({
    kicker: beat.label,
    headline: beat.text,
    footer: session.title,
  });
}

module.exports = { renderSlide, slideForBeat, W, H };
