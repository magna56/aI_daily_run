"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const DEFAULT_VOICE = process.env.VIDEO_VOICE || "coral";
const TTS_MODEL = process.env.VIDEO_TTS_MODEL || "gpt-4o-mini-tts";
const TTS_SPEED = Number(process.env.VIDEO_TTS_SPEED) || 1.05;
const TTS_INSTRUCTIONS = process.env.VIDEO_TTS_INSTRUCTIONS
  || "You are a sharp software engineer explaining a production gotcha to a teammate. Warm, wry, clearly into it — not a newscaster and not a commercial. Vary pitch and emphasis. Stress numbers and the punchline. Conversational. Never flat, never rushed.";

const BEAT_INSTRUCTIONS = {
  cold_open: "Spark of recognition. Like 'you've already done this.' Slight smile in the voice. Stress 'before.'",
  frame: "Mapping old names to new ones. Clear, engaged. Stress 'while in your process.'",
  mechanism: "This is the punchline. Lean into 'seven times' and 'never wrote the line.' Wry, not angry.",
  demo: "Pointing at a screen. Helpful, still energetic.",
  cta: "Friendly close. Invite, don't hard-sell.",
};

const MODEL_FALLBACKS = [
  TTS_MODEL,
  "gpt-4o-mini-tts-2025-03-20",
  "gpt-4o-mini-tts",
  "tts-1-hd",
];

function supportsInstructions(model) {
  return /gpt-4o|mini-tts/i.test(model) && !/^tts-1/.test(model);
}

async function synthesize(text, outPath, opts = {}) {
  const apiKey = opts.apiKey || process.env.OPENAI_API_KEY;
  if (!apiKey) return { ok: false, reason: "no OPENAI_API_KEY" };

  const voice = opts.voice || DEFAULT_VOICE;
  const speed = opts.speed ?? TTS_SPEED;
  const beatId = opts.beatId || "";
  const models = [...new Set(MODEL_FALLBACKS.filter(Boolean))];

  let lastErr = "";
  for (const model of models) {
    const body = {
      model,
      voice,
      input: text,
      response_format: "mp3",
    };
    if (supportsInstructions(model)) {
      const extra = BEAT_INSTRUCTIONS[beatId] || "";
      body.instructions = `${TTS_INSTRUCTIONS} ${extra}`.trim();
    } else {
      body.speed = speed;
    }

    const res = await fetch("https://api.openai.com/v1/audio/speech", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      lastErr = `TTS ${model} HTTP ${res.status}: ${(await res.text()).slice(0, 180)}`;
      continue;
    }

    const buf = Buffer.from(await res.arrayBuffer());
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, buf);
    return { ok: true, path: outPath, bytes: buf.length, model, voice };
  }

  return { ok: false, reason: lastErr || "all TTS models failed" };
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
  const pad = opts.beatPadSec ?? 0.3;
  const timed = [];
  let usedModel = null;

  for (const beat of beats) {
    const partPath = path.join(audioDir, `beat-${beat.id}.mp3`);
    const r = await synthesize(beat.text, partPath, { ...opts, beatId: beat.id });
    if (!r.ok) return r;
    usedModel = r.model;
    const dur = audioDurationSec(partPath);
    const extra = beat.id === "mechanism" ? 0.2 : 0;
    timed.push({
      id: beat.id,
      path: partPath,
      durationSec: dur ? dur + pad + extra : null,
    });
  }

  const wavs = [];
  for (const t of timed) {
    const wav = path.join(audioDir, `beat-${t.id}.wav`);
    toWav(t.path, wav);
    wavs.push(wav);
    const sil = path.join(audioDir, `sil-${t.id}.wav`);
    const silDur = t.id === "mechanism" ? pad + 0.2 : pad;
    execFileSync("ffmpeg", [
      "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
      "-t", String(silDur), sil,
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
    model: usedModel,
    voice: opts.voice || DEFAULT_VOICE,
  };
}

module.exports = {
  synthesize,
  synthesizeBeats,
  audioDurationSec,
  DEFAULT_VOICE,
  TTS_SPEED,
};
