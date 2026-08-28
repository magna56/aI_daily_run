"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const DEPS = path.join(__dirname, "..", "..", ".video-deps", "node_modules", "playwright");

function playwright() {
  if (!fs.existsSync(DEPS)) {
    throw new Error(
      "Playwright not installed. Run: npm install --prefix .video-deps playwright && npx playwright install chromium",
    );
  }
  return require(DEPS);
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * Record visualize.html interactions to capture/demo.mp4 (9:16).
 */
async function captureVisualize(session, outDir, opts = {}) {
  const htmlPath = path.join(session.dir, "visualize.html");
  if (!fs.existsSync(htmlPath)) {
    return { ok: false, reason: "no visualize.html" };
  }

  const captureDir = path.join(outDir, "capture");
  fs.mkdirSync(captureDir, { recursive: true });
  const webmPath = path.join(captureDir, "demo.webm");
  const mp4Path = path.join(captureDir, "demo.mp4");

  const { chromium } = playwright();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1080, height: 1920 },
    deviceScaleFactor: 1,
    recordVideo: {
      dir: captureDir,
      size: { width: 1080, height: 1920 },
    },
  });

  const page = await context.newPage();
  await page.goto(`file://${htmlPath}`, { waitUntil: "networkidle" });
  await page.waitForSelector("#tools");

  const pause = opts.pauseMs || 700;
  const videoSpeed = opts.videoSpeed || 1.45;

  // Show default: 3 tools, pairing OK.
  await sleep(pause);

  // Fewer tools → lower multiplier.
  await page.locator("#tools").fill("1");
  await page.locator("#tools").dispatchEvent("input");
  await sleep(pause);

  // More tools → billing spike.
  await page.locator("#tools").fill("6");
  await page.locator("#tools").dispatchEvent("input");
  await sleep(pause + 200);

  // Migration bug: drop function_call item.
  await page.locator("#dropCall").check();
  await sleep(pause + 300);

  await page.locator("#dropCall").uncheck();
  await page.locator("#dropCall").dispatchEvent("input");
  await sleep(400);

  // Conversations API retention difference.
  await page.locator('#stateGroup button[data-id="conv"]').click();
  await sleep(pause);

  await page.locator("#reset").click();
  await sleep(pause);

  const savedWebm = await page.video().path();
  await page.close();
  await context.close();
  await browser.close();

  if (savedWebm && savedWebm !== webmPath && fs.existsSync(savedWebm)) {
    fs.renameSync(savedWebm, webmPath);
  } else if (!fs.existsSync(webmPath)) {
    const candidates = fs.readdirSync(captureDir).filter((f) => f.endsWith(".webm"));
    if (!candidates.length) throw new Error("Playwright did not write a video file");
    fs.renameSync(path.join(captureDir, candidates[0]), webmPath);
  }

  execFileSync("ffmpeg", [
    "-y", "-i", webmPath,
    "-vf", `setpts=PTS/${videoSpeed},scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2`,
    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
    "-an",
    mp4Path,
  ], { stdio: "pipe" });

  if (!opts.keepWebm) fs.unlinkSync(webmPath);

  return { ok: true, path: mp4Path };
}

module.exports = { captureVisualize };
