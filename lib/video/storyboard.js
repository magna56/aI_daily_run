"use strict";

const path = require("path");

const WPM = Number(process.env.VIDEO_WPM) || 185;

function words(s) {
  return String(s || "").split(/\s+/).filter(Boolean).length;
}

function durationFromWords(wc, min = 2, max = 12) {
  const sec = Math.ceil((wc / WPM) * 60);
  return Math.min(max, Math.max(min, sec));
}

const BEAT_CAPS = {
  hook: 10,
  setup: 8,
  insight: 9,
  demo: 14,
  cta: 5,
};

/**
 * Turn script beats into a timed storyboard for assembly.
 * Pass opts.beatDurations (from per-beat TTS) for frame-accurate sync.
 */
function buildStoryboard(session, script, opts = {}) {
  const outDir = opts.outDir;
  const fromAudio = opts.beatDurations || {};

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

    const cap = BEAT_CAPS[beat.id] || 10;
    const durationSec = fromAudio[beat.id]
      || durationFromWords(wc, 2, cap);

    return {
      id: beat.id,
      label: beat.label,
      text: beat.text,
      durationSec,
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
      syncedToAudio: Object.keys(fromAudio).length > 0,
      generatedAt: new Date().toISOString(),
    },
    paths: outDir ? { root: outDir } : undefined,
  };
}

module.exports = { buildStoryboard, durationFromWords, words };
