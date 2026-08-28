"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const DEFAULT_VOICE = process.env.VIDEO_VOICE || "nova";
const TTS_MODEL = process.env.VIDEO_TTS_MODEL || "tts-1";
const TTS_SPEED = Number(process.env.VIDEO_TTS_SPEED) || 1.0;

async function synthesize(text, outPath, opts = {}) {
  const apiKey = opts.apiKey || process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return { ok: false, reason: "no OPENAI_API_KEY" };
  }

  const voice = opts.voice || DEFAULT_VOICE;
  const speed = opts.speed ?? TTS_SPEED;
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
      speed,
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

/** Synthesize each beat separately, concat, return per-beat durations for tight sync. */
async function synthesizeBeats(beats, outDir, opts = {}) {
  const audioDir = path.join(outDir, "audio");
  fs.mkdirSync(audioDir, { recursive: true });
  const pad = opts.beatPadSec ?? 0.35;
  const timed = [];

  for (const beat of beats) {
    const partPath = path.join(audioDir, `beat-${beat.id}.mp3`);
    const r = await synthesize(beat.text, partPath, opts);
    if (!r.ok) return r;
    const dur = audioDurationSec(partPath);
    const extra = beat.id === "mechanism" ? 0.25 : 0;
    timed.push({
      id: beat.id,
      path: partPath,
      durationSec: dur ? dur + pad + extra : null,
    });
  }

  const silencePath = path.join(audioDir, "silence.mp3");
  execFileSync("ffmpeg", [
    "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
    "-t", String(pad), "-q:a", "9", silencePath,
  ], { stdio: "pipe" });
  const silenceMech = path.join(audioDir, "silence-mech.mp3");
  execFileSync("ffmpeg", [
    "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
    "-t", String(pad + 0.25), "-q:a", "9", silenceMech,
  ], { stdio: "pipe" });

  const concatEntries = [];
  for (const t of timed) {
    concatEntries.push(t.path);
    concatEntries.push(t.id === "mechanism" ? silenceMech : silencePath);
  }

  const narrationPath = path.join(audioDir, "narration.mp3");
  const listPath = path.join(audioDir, "concat.txt");
  fs.writeFileSync(
    listPath,
    concatEntries.map((p) => `file '${p.replace(/'/g, "'\\''")}'`).join("\n"),
  );
  execFileSync("ffmpeg", [
    "-y", "-f", "concat", "-safe", "0", "-i", listPath,
    "-c", "copy", narrationPath,
  ], { stdio: "pipe" });
  fs.unlinkSync(listPath);

  return {
    ok: true,
    path: narrationPath,
    beats: timed,
    bytes: fs.statSync(narrationPath).size,
  };
}

module.exports = {
  synthesize,
  synthesizeBeats,
  audioDurationSec,
  DEFAULT_VOICE,
  TTS_SPEED,
};
