#!/usr/bin/env node
/* =============================================================================
   video.js — short vertical explainer from a daily session folder.
   -----------------------------------------------------------------------------
   Dependency-free (plus ffmpeg on PATH). Optional OPENAI_API_KEY for TTS.

     node video.js <id>              full pipeline
     node video.js <id> --script     script.json + narration.txt only
     node video.js <id> --dry-run    stop before ffmpeg assembly
   ============================================================================= */

"use strict";

const fs = require("fs");
const path = require("path");

const { loadSession } = require("./lib/video/session");
const { buildScript } = require("./lib/video/script");
const { buildStoryboard } = require("./lib/video/storyboard");
const { slideForBeat } = require("./lib/video/slides");
const { synthesize, audioDurationSec } = require("./lib/video/tts");
const { assemble } = require("./lib/video/assemble");
const { captureVisualize } = require("./lib/video/capture");

const ROOT = __dirname;
const args = process.argv.slice(2).filter((a) => a !== "--");
const id = args.find((a) => !a.startsWith("-"));
const scriptOnly = args.includes("--script");
const dryRun = args.includes("--dry-run");
const skipTts = args.includes("--no-tts");
const skipCapture = args.includes("--no-capture");
const forceCapture = args.includes("--capture");

function usage() {
  console.error(`Usage: node video.js <session-id> [--script] [--dry-run] [--no-tts]
Example: node video.js 2026-08-28`);
  process.exit(1);
}

if (!id) usage();

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
  if (session.hasVisualize && !demoCapture && !skipCapture) {
    try {
      console.log("==> capture: recording visualize.html …");
      const cap = await captureVisualize(session, outDir);
      if (cap.ok) {
        demoCapture = true;
        console.log(`==> capture: ${cap.path}`);
      } else {
        console.log(`==> capture skipped (${cap.reason})`);
      }
    } catch (err) {
      console.log(`==> capture failed (${err.message}) — continuing with slides only`);
    }
  } else if (forceCapture && session.hasVisualize) {
    const cap = await captureVisualize(session, outDir);
    if (!cap.ok) throw new Error(cap.reason || "capture failed");
    demoCapture = true;
    console.log(`==> capture: ${cap.path}`);
  }

  const storyboard = buildStoryboard(session, script, { outDir, hasDemoCapture: demoCapture });
  fs.writeFileSync(path.join(outDir, "storyboard.json"), JSON.stringify(storyboard, null, 2));
  console.log(`==> storyboard: ${outDir}/storyboard.json`);

  const slidesDir = path.join(outDir, "slides");
  fs.mkdirSync(slidesDir, { recursive: true });
  for (let i = 0; i < storyboard.beats.length; i++) {
    const beat = storyboard.beats[i];
    const n = String(i + 1).padStart(2, "0");
    const file = path.join(slidesDir, `beat-${n}-${beat.id}.png`);
    const png = slideForBeat(session, { ...beat, ...script.beats[i] });
    fs.writeFileSync(file, png);
  }
  console.log(`==> slides: ${slidesDir}/ (${storyboard.beats.length} PNGs)`);

  if (!skipTts) {
    const audioPath = path.join(outDir, storyboard.audioFile);
    const tts = await synthesize(script.narration, audioPath);
    if (tts.ok) {
      console.log(`==> TTS: ${audioPath} (${tts.bytes} bytes)`);
    } else {
      console.log(`==> TTS skipped (${tts.reason}) — use narration.txt or set OPENAI_API_KEY`);
    }
  }

  if (dryRun) {
    console.log("==> dry run — skipping ffmpeg assembly");
    if (!demoCapture && session.hasVisualize) {
      console.log(`    tip: record visualize.html -> ${outDir}/capture/demo.mp4 then re-run`);
    }
    return;
  }

  const audioPath = path.join(outDir, storyboard.audioFile);
  const dur = fs.existsSync(audioPath) ? audioDurationSec(audioPath) : null;
  const result = assemble(storyboard, outDir, { audioDurationSec: dur });
  console.log(`==> video: ${result.outPath}${result.hasAudio ? " (with audio)" : " (silent — add TTS or mux manually)"}`);
  if (!demoCapture && session.hasVisualize) {
    console.log(`    tip: re-run without --no-capture, or add ${capturePath}`);
  }
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
