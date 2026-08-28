#!/usr/bin/env node
/* =============================================================================
   video.js — short vertical explainer from a daily session folder.
   ============================================================================= */

"use strict";

const fs = require("fs");
const path = require("path");

const { loadSession } = require("./lib/video/session");
const { buildScript } = require("./lib/video/script");
const { buildStoryboard } = require("./lib/video/storyboard");
const { slideForBeat } = require("./lib/video/slides");
const { synthesizeBeats, audioDurationSec } = require("./lib/video/tts");
const { assemble } = require("./lib/video/assemble");
const { writeSrt } = require("./lib/video/captions");
const { captureVisualize } = require("./lib/video/capture");

const ROOT = __dirname;
const args = process.argv.slice(2).filter((a) => a !== "--");
const id = args.find((a) => !a.startsWith("-"));
const scriptOnly = args.includes("--script");
const dryRun = args.includes("--dry-run");
const skipTts = args.includes("--no-tts");
const skipCapture = args.includes("--no-capture");
const forceCapture = args.includes("--capture");

if (!id) {
  console.error("Usage: node video.js <session-id> [--script] [--dry-run] [--no-tts] [--capture]");
  process.exit(1);
}

async function main() {
  const session = loadSession(id);
  const outDir = path.join(ROOT, "videos", id);
  fs.mkdirSync(outDir, { recursive: true });

  const script = buildScript(session);
  fs.writeFileSync(path.join(outDir, "script.json"), JSON.stringify(script, null, 2));
  fs.writeFileSync(path.join(outDir, "narration.txt"), script.narration + "\n");
  console.log(`==> script: ${outDir}/script.json (${script.wordCount} words)`);
  if (scriptOnly) return;

  const capturePath = path.join(outDir, "capture", "demo.mp4");
  let demoCapture = fs.existsSync(capturePath);
  if (session.hasVisualize && (!demoCapture || forceCapture) && !skipCapture) {
    try {
      console.log("==> capture: recording visualize.html …");
      const cap = await captureVisualize(session, outDir);
      if (cap.ok) {
        demoCapture = true;
        console.log(`==> capture: ${cap.path}`);
      }
    } catch (err) {
      console.log(`==> capture failed (${err.message})`);
    }
  }

  let beatDurations = {};
  if (!skipTts) {
    const tts = await synthesizeBeats(script.beats, outDir);
    if (tts.ok) {
      beatDurations = Object.fromEntries(
        tts.beats.filter((b) => b.durationSec).map((b) => [b.id, b.durationSec]),
      );
      console.log(`==> TTS: ${tts.path} (${tts.bytes} bytes, ${process.env.VIDEO_VOICE || "nova"} @ ${process.env.VIDEO_TTS_SPEED || "1.0"}x)`);
    } else {
      console.log(`==> TTS skipped (${tts.reason})`);
    }
  }

  if (demoCapture && beatDurations.demo) {
    const demoLen = audioDurationSec(capturePath);
    if (demoLen) {
      beatDurations.demo = Math.min(14, Math.max(beatDurations.demo, Math.min(demoLen, 12)));
    }
  }

  const storyboard = buildStoryboard(session, script, { outDir, hasDemoCapture: demoCapture, beatDurations });
  fs.writeFileSync(path.join(outDir, "storyboard.json"), JSON.stringify(storyboard, null, 2));
  console.log(`==> storyboard: ${outDir}/storyboard.json`);

  const slidesDir = path.join(outDir, "slides");
  fs.mkdirSync(slidesDir, { recursive: true });
  for (let i = 0; i < storyboard.beats.length; i++) {
    const beat = storyboard.beats[i];
    const n = String(i + 1).padStart(2, "0");
    fs.writeFileSync(
      path.join(slidesDir, `beat-${n}-${beat.id}.png`),
      slideForBeat(session, { ...beat, ...script.beats[i] }),
    );
  }
  console.log(`==> slides: ${slidesDir}/ (${storyboard.beats.length} PNGs)`);

  const srtPath = writeSrt(storyboard, path.join(outDir, "captions.srt"));
  console.log(`==> captions: ${srtPath}`);

  if (dryRun) return;

  const audioPath = path.join(outDir, storyboard.audioFile);
  const result = assemble(storyboard, outDir, {
    audioDurationSec: fs.existsSync(audioPath) ? audioDurationSec(audioPath) : null,
    srtPath,
  });
  console.log(`==> video: ${result.outPath}${result.hasAudio ? " (with audio)" : " (silent)"}`);
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
