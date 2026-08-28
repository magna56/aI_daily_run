"use strict";

const fs = require("fs");
const path = require("path");

function srtTime(sec) {
  const s = Math.max(0, Number(sec) || 0);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const rest = s % 60;
  const whole = Math.floor(rest);
  const ms = Math.round((rest - whole) * 1000);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(whole).padStart(2, "0")},${String(ms).padStart(3, "0")}`;
}

function wrapCaption(text, max = 42) {
  const words = String(text || "").replace(/\s+/g, " ").trim().split(" ");
  const lines = [];
  let cur = "";
  for (const w of words) {
    const next = cur ? `${cur} ${w}` : w;
    if (next.length <= max) cur = next;
    else {
      if (cur) lines.push(cur);
      cur = w;
    }
  }
  if (cur) lines.push(cur);
  return lines.slice(0, 3).join("\n");
}

function writeSrt(storyboard, outPath) {
  let t = 0;
  const blocks = [];
  storyboard.beats.forEach((beat, i) => {
    const start = t;
    const end = t + beat.durationSec;
    t = end;
    blocks.push(
      `${i + 1}\n${srtTime(start)} --> ${srtTime(end)}\n${wrapCaption(beat.text)}\n`,
    );
  });
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, blocks.join("\n"));
  return outPath;
}

module.exports = { writeSrt, srtTime };
