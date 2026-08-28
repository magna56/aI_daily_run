"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

// Neutral, consistent voice. gpt-4o-mini-tts + "personality" instructions
// read as theatrical or condescending; tts-1-hd alloy is even and factual.
const DEFAULT_VOICE = process.env.VIDEO_VOICE || "alloy";
const TTS_MODEL = process.env.VIDEO_TTS_MODEL || "tts-1-hd";
const TTS_SPEED = Number(process.env.VIDEO_TTS_SPEED) || 1.0;

async function synthesize(text, outPath, opts = {}) {
  const apiKey = opts.apiKey || process.env.OPENAI_API_KEY;
  if (!apiKey) return { ok: false, reason: "no OPENAI_API_KEY" };

  const voice = opts.voice || DEFAULT_VOICE;
  const model = opts.model || TTS_MODEL;
  const speed = opts.speed ?? TTS_SPEED;

  const res = await fetch("https://api.openai.com/v1/audio/speech", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
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
  return { ok: true, path: outPath, bytes: buf.length, model, voice };
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

function toWav(mp3Path, wavPath) {
  execFileSync("ffmpeg", [
    "-y", "-i", mp3Path,
    "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le",
    wavPath,
  ], { stdio: "pipe" });
}

async function synthesizeBeats(beats, outDir, opts = {}) {
  const audioDir = path.join(outDir, "audio");
  fs.mkdirSync(audioDir, { recursive: true });
  const pad = opts.beatPadSec ?? 0.28;
  const timed = [];
  let used = { model: null, voice: null };

  for (const beat of beats) {
    const partPath = path.join(audioDir, `beat-${beat.id}.mp3`);
    const r = await synthesize(beat.text, partPath, opts);
    if (!r.ok) return r;
    used = { model: r.model, voice: r.voice };
    const dur = audioDurationSec(partPath);
    timed.push({
      id: beat.id,
      path: partPath,
      durationSec: dur ? dur + pad : null,
    });
  }

  const wavs = [];
  for (const t of timed) {
    const wav = path.join(audioDir, `beat-${t.id}.wav`);
    toWav(t.path, wav);
    wavs.push(wav);
    const sil = path.join(audioDir, `sil-${t.id}.wav`);
    execFileSync("ffmpeg", [
      "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
      "-t", String(pad), sil,
    ], { stdio: "pipe" });
    wavs.push(sil);
  }

  const narrationPath = path.join(audioDir, "narration.mp3");
  const listPath = path.join(audioDir, "concat.txt");
  fs.writeFileSync(
    listPath,
    wavs.map((p) => `file '${p.replace(/'/g, "'\\''")}'`).join("\n"),
  );
  execFileSync("ffmpeg", [
    "-y", "-f", "concat", "-safe", "0", "-i", listPath,
    "-c:a", "libmp3lame", "-q:a", "4",
    narrationPath,
  ], { stdio: "pipe" });
  fs.unlinkSync(listPath);

  return {
    ok: true,
    path: narrationPath,
    beats: timed,
    bytes: fs.statSync(narrationPath).size,
    model: used.model,
    voice: used.voice,
  };
}

module.exports = {
  synthesize,
  synthesizeBeats,
  audioDurationSec,
  DEFAULT_VOICE,
  TTS_SPEED,
};
