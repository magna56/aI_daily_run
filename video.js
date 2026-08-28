#!/usr/bin/env node
/* =============================================================================
   video.js — short 9:16 explainer from a daily session folder (first-draft lock).

     node video.js                  newest YYYY-MM-DD session
     node video.js 2026-08-28
     node video.js 2026-08-28 --media   also copy to media/videos/
     node video.js --script|--dry-run|--no-tts|--no-capture|--capture
   ============================================================================= */

"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const { loadSession, newestSessionId, slugify } = require("./lib/video/session");
const { buildScript } = require("./lib/video/script");
const { buildStoryboard } = require("./lib/video/storyboard");
const { slideForBeat } = require("./lib/video/slides");
const { synthesizeBeats, audioDurationSec } = require("./lib/video/tts");
const { assemble } = require("./lib/video/assemble");
const { writeSrt } = require("./lib/video/captions");
const { captureVisualize } = require("./lib/video/capture");

const ROOT = __dirname;
const args = process.argv.slice(2).filter((a) => a !== "--");
const flags = new Set(args.filter((a) => a.startsWith("-")));
const idArg = args.find((a) => !a.startsWith("-"));
const scriptOnly = flags.has("--script");
const dryRun = flags.has("--dry-run");
const skipTts = flags.has("--no-tts");
const skipCapture = flags.has("--no-capture");
const forceCapture = flags.has("--capture");
const copyMedia = flags.has("--media");

function resolveApiKey() {
  if (process.env.OPENAI_API_KEY) return process.env.OPENAI_API_KEY;
  try {
    const key = execFileSync("security", [
      "find-generic-password", "-a", "theaicommit",
      "-s", "openai-api-key-theaicommit", "-w",
    ], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    if (key) process.env.OPENAI_API_KEY = key;
    return key || "";
  } catch {
    return "";
  }
}

if (!idArg && flags.has("--help")) {
  console.error("Usage: node video.js [session-id] [--media] [--script] [--dry-run] [--no-tts] [--capture]");
  process.exit(0);
}

async function main() {
  const id = idArg || newestSessionId();
  if (!id) {
    console.error("No session id and no YYYY-MM-DD folders found.");
    process.exit(1);
  }

  resolveApiKey();

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
      console.log(`==> TTS: ${tts.path} (${tts.bytes} bytes, ${tts.voice || "alloy"} / ${tts.model || "tts-1-hd"})`);
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

  if (copyMedia && fs.existsSync(result.outPath)) {
    const mediaDir = path.join(ROOT, "media", "videos");
    fs.mkdirSync(mediaDir, { recursive: true });
    const dest = path.join(mediaDir, `${session.slug}-short.mp4`);
    fs.copyFileSync(result.outPath, dest);
    console.log(`==> media: ${dest}`);
  }
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
