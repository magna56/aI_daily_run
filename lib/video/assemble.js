"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

function run(cmd, args, opts = {}) {
  execFileSync(cmd, args, { stdio: opts.inherit ? "inherit" : "pipe", ...opts });
}

function exists(p) {
  try { fs.accessSync(p); return true; } catch { return false; }
}

/**
 * Build a vertical MP4 from storyboard beats (slides + optional demo clip + audio).
 * Slide beats are stitched in one ffmpeg pass via the concat demuxer.
 */
function assemble(storyboard, rootDir, opts = {}) {
  const size = storyboard.size || { w: 1080, h: 1920 };
  const fps = storyboard.fps || 30;
  const tmpDir = path.join(rootDir, ".assemble-tmp");
  fs.mkdirSync(tmpDir, { recursive: true });

  const audioPath = path.join(rootDir, storyboard.audioFile);
  const hasAudio = exists(audioPath);
  const totalAudioSec = hasAudio ? opts.audioDurationSec : null;

  const beatDur = storyboard.beats.map((b) => b.durationSec);
  if (hasAudio && totalAudioSec && totalAudioSec > 0 && !storyboard.meta?.syncedToAudio) {
    const sum = beatDur.reduce((a, b) => a + b, 0);
    const scale = totalAudioSec / sum;
    for (let i = 0; i < storyboard.beats.length; i++) {
      storyboard.beats[i].durationSec = Math.max(2, beatDur[i] * scale);
    }
  }

  const parts = [];
  for (let i = 0; i < storyboard.beats.length; i++) {
    const beat = storyboard.beats[i];
    const dur = beat.durationSec;

    if (beat.visual.type === "video") {
      const vid = path.join(rootDir, beat.visual.file);
      if (exists(vid)) {
        const segPath = path.join(tmpDir, `clip-${String(i + 1).padStart(2, "0")}.mp4`);
        run("ffmpeg", [
          "-y", "-i", vid,
          "-vf", `scale=${size.w}:${size.h}:force_original_aspect_ratio=decrease,pad=${size.w}:${size.h}:(ow-iw)/2:(oh-ih)/2,setsar=1`,
          "-t", String(dur),
          "-r", String(fps),
          "-an",
          "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
          segPath,
        ]);
        parts.push({ type: "video", path: segPath, durationSec: dur });
        continue;
      }
    }

    const slide = path.resolve(rootDir, beat.visual.file);
    if (!exists(slide)) throw new Error(`Missing slide: ${slide}`);
    parts.push({ type: "slide", path: slide, durationSec: dur });
  }

  let silentVideo;
  if (parts.every((p) => p.type === "slide")) {
    silentVideo = slideshowFromSlides(parts, tmpDir, size, fps);
  } else {
    silentVideo = mixedParts(parts, tmpDir, size, fps);
  }

  const outPath = path.join(rootDir, storyboard.outFile);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });

  if (hasAudio) {
    run("ffmpeg", [
      "-y", "-i", silentVideo, "-i", audioPath,
      "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
      "-shortest",
      outPath,
    ], { inherit: true });
  } else {
    fs.copyFileSync(silentVideo, outPath);
  }

  if (!opts.keepTmp) {
    for (const f of fs.readdirSync(tmpDir)) {
      fs.unlinkSync(path.join(tmpDir, f));
    }
    fs.rmdirSync(tmpDir);
  }

  return { outPath, hasAudio, segmentCount: parts.length };
}

function slideshowFromSlides(parts, tmpDir, size, fps) {
  const listPath = path.join(tmpDir, "slides.txt");
  const lines = [];
  for (const p of parts) {
    lines.push(`file '${p.path.replace(/'/g, "'\\''")}'`);
    lines.push(`duration ${p.durationSec}`);
  }
  lines.push(`file '${parts[parts.length - 1].path.replace(/'/g, "'\\''")}'`);
  fs.writeFileSync(listPath, lines.join("\n"));

  const out = path.join(tmpDir, "video-only.mp4");
  run("ffmpeg", [
    "-y", "-f", "concat", "-safe", "0", "-i", listPath,
    "-vf", `scale=${size.w}:${size.h},setsar=1,fps=${fps}`,
    "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
    "-pix_fmt", "yuv420p",
    out,
  ]);
  return out;
}

function mixedParts(parts, tmpDir, size, fps) {
  const segs = [];
  for (let i = 0; i < parts.length; i++) {
    const p = parts[i];
    const segPath = path.join(tmpDir, `seg-${String(i + 1).padStart(2, "0")}.mp4`);
    if (p.type === "video") {
      fs.copyFileSync(p.path, segPath);
    } else {
      run("ffmpeg", [
        "-y", "-loop", "1", "-i", p.path,
        "-t", String(p.durationSec),
        "-vf", `scale=${size.w}:${size.h},setsar=1`,
        "-r", "1",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        segPath,
      ]);
    }
    segs.push(segPath);
  }

  const listPath = path.join(tmpDir, "concat.txt");
  fs.writeFileSync(listPath, segs.map((p) => `file '${p.replace(/'/g, "'\\''")}'`).join("\n"));
  const out = path.join(tmpDir, "video-only.mp4");
  run("ffmpeg", [
    "-y", "-f", "concat", "-safe", "0", "-i", listPath,
    "-c", "copy",
    out,
  ]);
  return out;
}

module.exports = { assemble };
