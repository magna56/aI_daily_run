"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const DEFAULT_VOICE = process.env.VIDEO_VOICE || "onyx";
const TTS_MODEL = process.env.VIDEO_TTS_MODEL || "tts-1";

async function synthesize(text, outPath, opts = {}) {
  const apiKey = opts.apiKey || process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return { ok: false, reason: "no OPENAI_API_KEY" };
  }

  const voice = opts.voice || DEFAULT_VOICE;
  const res = await fetch("https://api.openai.com/v1/audio/speech", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: TTS_MODEL,
      voice,
      input: text,
      response_format: "mp3",
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    return { ok: false, reason: `TTS HTTP ${res.status}: ${err.slice(0, 200)}` };
  }

  const buf = Buffer.from(await res.arrayBuffer());
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, buf);
  return { ok: true, path: outPath, bytes: buf.length };
}

function audioDurationSec(mp3Path) {
  try {
    const out = execFileSync("ffprobe", [
      "-v", "error",
      "-show_entries", "format=duration",
      "-of", "default=noprint_wrappers=1:nokey=1",
      mp3Path,
    ], { encoding: "utf8" });
    const n = parseFloat(out.trim());
    return Number.isFinite(n) ? n : null;
  } catch {
    return null;
  }
}

module.exports = { synthesize, audioDurationSec, DEFAULT_VOICE };
