"use strict";

const fs = require("fs");
const path = require("path");

const DEPS = path.join(__dirname, "..", "..", ".video-deps", "node_modules", "playwright");

function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function nl(s) {
  return esc(s).replace(/\n/g, "<br>");
}

function storyHtml(beat) {
  const kicker = beat.kicker || "";
  const headline = beat.onScreen || beat.text;
  const sub = beat.sub || "";
  const deep = beat.deep || "";
  return `<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;width:1080px;height:1920px;background:#090b10;color:#f4f6fb;
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}
.bar{position:fixed;left:0;top:0;width:14px;height:100%;background:#818cf8}
.safe{padding:200px 64px 340px 80px}
.kicker{margin:0 0 28px;font:800 26px/1.2 system-ui;letter-spacing:.14em;color:#facc15;text-transform:uppercase}
h1{margin:0 0 28px;font:800 58px/1.18 system-ui;letter-spacing:-.03em;max-width:940px}
.sub{margin:0 0 22px;font:650 32px/1.38 system-ui;color:#c5cde0;max-width:920px}
.deep{margin:0;font:650 26px/1.4 system-ui;color:#a5b4fc;max-width:920px}
.brand{position:fixed;left:80px;bottom:292px;font:700 20px/1 system-ui;letter-spacing:.14em;color:#929db1}
</style></head><body>
<div class="bar"></div>
<div class="safe">
${kicker ? `<p class="kicker">${esc(kicker)}</p>` : ""}
<h1>${nl(headline)}</h1>
${sub ? `<p class="sub">${nl(sub)}</p>` : ""}
${deep ? `<p class="deep">${nl(deep)}</p>` : ""}
</div>
<div class="brand">THE AI COMMIT</div>
</body></html>`;
}

function codeHtml(beat) {
  const c2 = beat.code2
    ? `<div class="card" style="margin-top:16px">
<p class="label">${esc(beat.code2Label || "eval")}</p>
<pre>${esc(beat.code2)}</pre>
</div>`
    : "";
  return `<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;width:1080px;height:1920px;background:#090b10;color:#f4f6fb;
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}
.bar{position:fixed;left:0;top:0;width:14px;height:100%;background:#818cf8}
.safe{padding:176px 48px 320px 64px}
.kicker{margin:0 0 18px;font:800 24px/1.2 system-ui;letter-spacing:.14em;color:#facc15;text-transform:uppercase}
h1{margin:0 0 18px;font:800 40px/1.18 system-ui;letter-spacing:-.02em}
.card{background:#141821;border:1px solid #303747;border-radius:16px;padding:18px 20px}
.label{font:700 16px/1 ui-monospace,Menlo,monospace;color:#818cf8;letter-spacing:.08em;
text-transform:uppercase;margin:0 0 10px}
pre{margin:0;white-space:pre-wrap;word-break:break-word;font:600 22px/1.4 ui-monospace,Menlo,monospace;
color:#e2e8f4}
.note{margin:16px 0 0;font:650 26px/1.35 system-ui;color:#facc15}
.brand{position:fixed;left:80px;bottom:292px;font:700 20px/1 system-ui;letter-spacing:.14em;color:#929db1}
</style></head><body>
<div class="bar"></div>
<div class="safe">
${beat.kicker ? `<p class="kicker">${esc(beat.kicker)}</p>` : ""}
<h1>${nl(beat.onScreen || beat.text)}</h1>
<div class="card">
<p class="label">code_example.py — the reduction</p>
<pre>${esc(beat.code)}</pre>
</div>
${c2}
${beat.codeNote ? `<p class="note">${esc(beat.codeNote)}</p>` : ""}
</div>
<div class="brand">THE AI COMMIT</div>
</body></html>`;
}

async function writeHtmlSlides(scriptBeats, slidesDir) {
  if (!fs.existsSync(DEPS)) return { ok: false, reason: "no playwright" };
  const { chromium } = require(DEPS);
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  for (let i = 0; i < scriptBeats.length; i++) {
    const beat = scriptBeats[i];
    const n = String(i + 1).padStart(2, "0");
    const html = beat.kind === "code" ? codeHtml(beat) : storyHtml(beat);
    await page.setContent(html, { waitUntil: "load" });
    await page.screenshot({
      path: path.join(slidesDir, `beat-${n}-${beat.id}.png`),
      type: "png",
      clip: { x: 0, y: 0, width: 1080, height: 1920 },
    });
  }
  await browser.close();
  return { ok: true };
}

module.exports = { writeHtmlSlides };
