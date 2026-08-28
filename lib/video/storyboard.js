"use strict";

const path = require("path");

const WPM = Number(process.env.VIDEO_WPM) || 150;

function words(s) {
  return String(s || "").split(/\s+/).filter(Boolean).length;
}

function durationFromWords(wc, min = 4, max = 30) {
  const sec = Math.ceil((wc / WPM) * 60);
  return Math.min(max, Math.max(min, sec));
}

/**
 * Turn script beats into a timed storyboard for assembly.
 */
function buildStoryboard(session, script, opts = {}) {
  const outDir = opts.outDir;
  const beats = script.beats.map((beat, i) => {
    const n = String(i + 1).padStart(2, "0");
    const wc = words(beat.text);
    let visual = {
      type: "slide",
      file: path.join("slides", `beat-${n}-${beat.id}.png`),
    };

    if (beat.id === "demo") {
      const demoMp4 = path.join("capture", "demo.mp4");
      if (opts.hasDemoCapture) {
        visual = { type: "video", file: demoMp4 };
      } else if (session.hasVisualize) {
        visual = {
          type: "slide",
          file: path.join("slides", `beat-${n}-${beat.id}.png`),
          note: "Drop capture/demo.mp4 for screen recording of visualize.html",
        };
      } else if (session.hasDiagram) {
        visual = {
          type: "slide",
          file: path.join("slides", `beat-${n}-${beat.id}.png`),
          note: "Diagram-only session; no visualize.html",
        };
      }
    }

    if (beat.id === "cta") {
      visual = {
        type: "slide",
        file: path.join("slides", `beat-${n}-${beat.id}.png`),
        url: beat.url,
      };
    }

    return {
      id: beat.id,
      label: beat.label,
      text: beat.text,
      durationSec: durationFromWords(wc, beat.id === "cta" ? 6 : 4, beat.id === "demo" ? 28 : 18),
      visual,
      title: beat.title || null,
    };
  });

  return {
    version: 1,
    sessionId: session.id,
    title: session.title,
    url: session.url,
    aspect: "9:16",
    size: { w: 1080, h: 1920 },
    fps: 30,
    outFile: path.join("out", "short-9x16.mp4"),
    audioFile: path.join("audio", "narration.mp3"),
    beats,
    meta: {
      wordCount: script.wordCount,
      wpm: WPM,
      generatedAt: new Date().toISOString(),
    },
    paths: outDir ? { root: outDir } : undefined,
  };
}

module.exports = { buildStoryboard, durationFromWords, words };
