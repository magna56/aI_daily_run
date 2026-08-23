#!/usr/bin/env node
/* =============================================================================
   build.js — compiles the daily session folders into the data the reader loads.
   -----------------------------------------------------------------------------
   Dependency-free. Run with:  node build.js            (write site/data/)
                               node build.js --check    (lint only, write nothing)
                               node build.js --no-run   (skip executing examples)

   Session folders are the source of truth and are never modified: /ai-daily-learn
   writes YYYY-MM-DD/{topic.md,diagram.excalidraw,code_example.py,articles.md} and
   this script adapts to whatever is there. Older sessions are missing a diagram
   or an articles file, and that is a warning, not an error.

   Output:
     site/data/index.js      window.SESSIONS + window.CATEGORIES — the card grid
     site/data/<id>.json     one session's full payload, fetched when opened
     site/assets/<id>/       diagram.excalidraw + any images, for download/display

   The split matters: the grid must stay fast as sessions accumulate, so the
   heavy parts (rendered SVG, source, captured output) load only on demand.
   ============================================================================= */

"use strict";

const fs = require("fs");
const path = require("path");

const { renderExcalidrawSVG } = require("./lib/excalidraw-svg");
const { createRunner } = require("./lib/runner");

const ROOT = __dirname;
const SITE = path.join(ROOT, "site");
const DATA_DIR = path.join(SITE, "data");
const ASSET_DIR = path.join(SITE, "assets");
const JOURNAL = path.join(ROOT, "journal.md");

// Where the "Files: on GitHub" link in each session points. Override with
// ADL_REPO_BLOB when this repo lives somewhere else (a fork, another host, a
// copy on a personal machine) so the links do not dangle.
const REPO_BLOB = process.env.ADL_REPO_BLOB
  || "https://github.com/magna56/aI_daily_run/blob/main";

// The categories /ai-daily-learn draws from, in tier order: Tier A (ship it this
// week) first, then B (understand the machine), then C (frontier). Kept here so
// the reader can validate a session's Category and show coverage.
//
// NOTE: selection is *tier-weighted* (A~50% / B~30% / C~20%), not a flat cycle —
// so the reader's "next category" hint is only that, a hint. See the skill's
// Category Tiers section for the real rule and why flat rotation was dropped.
const CATEGORIES = [
  // Tier A — ship it this week
  "Coding Agents & Productivity",
  "Building Agents & MCP",
  "AI Engineering Practices",
  "Evals & Reliability",
  // Tier B — understand the machine
  "New Models & APIs",
  "AI in Production",
  "Hands-on Techniques",
  // Tier C — frontier
  "Applied Research",
  "AI Hardware for Engineers",
  "Multimodal Engineering",
  "AI Safety & Alignment",
];

// A session folder: a date, optionally suffixed for a second session that day.
const SESSION_RE = /^\d{4}-\d{2}-\d{2}(-s\d+)?$/;
const IMAGE_RE = /\.(png|jpe?g|gif|svg|webp)$/i;

const warnings = [];
const errors = [];
const warn = (m) => warnings.push(m);
const fail = (m) => errors.push(m);

/* ---- small parsers -------------------------------------------------------- */

// "**Category**: AI in Production" -> ["Category", "AI in Production"]
function metaLine(line) {
  const m = line.match(/^\*\*([^*]+)\*\*:\s*(.*)$/);
  return m ? [m[1].trim(), m[2].trim()] : null;
}

// "[label](url)" anywhere in a string -> {label, url}
function firstLink(s) {
  const m = String(s || "").match(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/);
  return m ? { label: m[1], url: m[2] } : null;
}

/**
 * topic.md: `# Title`, a block of `**Key**: value` lines, then `## Section`s.
 * Returns the title, the metadata block, and the remaining markdown body.
 */
function parseTopic(raw, rel) {
  const lines = raw.replace(/^﻿/, "").split("\n");
  let i = 0;
  while (i < lines.length && !lines[i].trim()) i++;

  const h1 = (lines[i] || "").match(/^#\s+(.*)$/);
  if (!h1) {
    fail(`${rel}: no "# Title" heading on the first non-blank line.`);
    return null;
  }
  const title = h1[1].trim();
  i++;

  const meta = {};
  for (; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    if (line.startsWith("#")) break;   // reached the first section
    const kv = metaLine(line);
    if (!kv) break;                    // reached prose
    meta[kv[0]] = kv[1];
  }

  return { title, meta, body: lines.slice(i).join("\n").trim() };
}

/**
 * journal.md: `## <id> — <Title>` blocks of `- **Key**: value` bullets.
 * The hand-written "Key insight" is the best one-line blurb we have, so the
 * cards reuse it rather than inventing a new summary.
 */
function parseJournal(raw) {
  const out = new Map();
  if (!raw) return out;
  const blocks = raw.split(/^##\s+/m).slice(1);
  for (const block of blocks) {
    const nl = block.indexOf("\n");
    const heading = (nl === -1 ? block : block.slice(0, nl)).trim();
    const id = heading.split(/\s+[—-]\s+/)[0].trim();
    if (!SESSION_RE.test(id)) continue;

    const fields = {};
    let key = null;
    for (const line of block.slice(nl + 1).split("\n")) {
      const bullet = line.match(/^-\s+\*\*([^*]+)\*\*:\s*(.*)$/);
      if (bullet) {
        key = bullet[1].trim();
        fields[key] = bullet[2].trim();
      } else if (key && line.trim() && !line.startsWith("#")) {
        fields[key] += " " + line.trim();   // wrapped continuation line
      } else if (!line.trim()) {
        key = null;
      }
    }
    out.set(id, fields);
  }
  return out;
}

/**
 * articles.md: `## Group` headings holding `### [Title](url)` entries, each
 * with an optional `**Key**: v | **Key**: v` meta line and a `>` summary.
 * Headings vary a lot across sessions ("Papers", "Primary Source", "The
 * one-line takeaway"), so groups without entries are kept as prose notes.
 */
function parseArticles(raw) {
  const groups = [];
  let group = null;
  let item = null;
  let metaBuf = "";          // the entry's byline, which often wraps mid-value
  let inMeta = false;

  const pushGroup = () => { if (group && (group.items.length || group.note.trim())) groups.push(group); };

  // The byline is one logical line ("**Authors**: … | **Published**: … "), but
  // it is hard-wrapped in the source. Rejoin, then split on the pipes — parsing
  // line by line would drop everything after the first wrap into the summary.
  const flushMeta = () => {
    inMeta = false;
    const buf = metaBuf.trim();
    metaBuf = "";
    if (!item || !buf) return;
    if (!buf.startsWith("**")) { item.summary += (item.summary ? " " : "") + buf; return; }
    // Split on the pipes, and also wherever a new **Key**: starts — some
    // bylines put each field on its own line with no separator at all.
    for (const part of buf.split(/\s*\|\s*|(?=\*\*[^*|]+\*\*:)/)) {
      const kv = metaLine((part || "").trim());
      if (kv) item.meta[kv[0]] = kv[1];
    }
  };

  for (const line of raw.split("\n")) {
    const h2 = line.match(/^##\s+(.*)$/);
    const h3 = line.match(/^###\s+(.*)$/);

    if (h2 || h3 || !line.trim()) flushMeta();

    if (h2) {
      pushGroup();
      group = { heading: h2[1].trim(), items: [], note: "" };
      item = null;
      continue;
    }
    if (line.match(/^#\s+/)) continue;   // the file's own title

    if (h3) {
      if (!group) group = { heading: "", items: [], note: "" };
      const link = firstLink(h3[1]);
      item = {
        title: link ? link.label : h3[1].replace(/^\d+\.\s*/, "").trim(),
        url: link ? link.url : "",
        meta: {},
        summary: "",
      };
      group.items.push(item);
      inMeta = true;
      continue;
    }

    if (!line.trim()) continue;

    if (item) {
      const quote = line.match(/^>\s?(.*)$/);
      if (quote) {
        flushMeta();
        item.summary += (item.summary ? " " : "") + quote[1].trim();
        continue;
      }
      if (inMeta) { metaBuf += (metaBuf ? " " : "") + line.trim(); continue; }
      item.summary += (item.summary ? " " : "") + line.trim();
    } else if (group) {
      group.note += line + "\n";
    }
  }
  flushMeta();
  pushGroup();
  return groups;
}

/* ---- helpers -------------------------------------------------------------- */

function readIfExists(p) {
  return fs.existsSync(p) ? fs.readFileSync(p, "utf8") : null;
}

function readMinutes(meta, body) {
  const raw = meta["Time to read"] || meta["Read time"] || "";
  const m = raw.match(/(\d+)/);
  if (m) return Number(m[1]);
  const words = String(body || "").split(/\s+/).length;
  return Math.max(1, Math.round(words / 220));
}

function rmrf(p) { fs.rmSync(p, { recursive: true, force: true }); }

/* ---- per-session compile --------------------------------------------------- */

function compile(id, journal, runner, opts) {
  const dir = path.join(ROOT, id);
  const topicRaw = readIfExists(path.join(dir, "topic.md"));
  if (!topicRaw) {
    warn(`${id}: no topic.md — skipping this folder.`);
    return null;
  }

  const topic = parseTopic(topicRaw, `${id}/topic.md`);
  if (!topic) return null;

  const j = journal.get(id) || {};
  const category = topic.meta.Category || j.Category || "";
  if (!category) warn(`${id}: no Category in topic.md or journal.md.`);
  else if (!CATEGORIES.includes(category)) {
    warn(`${id}: category "${category}" is not one of the 10 rotation categories.`);
  }

  const date = topic.meta.Date || id.slice(0, 10);
  const assetDir = path.join(ASSET_DIR, id);
  const writing = !opts.check;

  /* diagram -> SVG, plus the original file so the download button works from
     the published site (gh-pages has no copy of the source tree). */
  let diagram = null;
  const diagramPath = path.join(dir, "diagram.excalidraw");
  if (fs.existsSync(diagramPath)) {
    try {
      const scene = JSON.parse(fs.readFileSync(diagramPath, "utf8"));
      const r = renderExcalidrawSVG(scene, { uid: id.replace(/[^0-9a-z]/gi, "") });
      if (r.skipped.length) {
        warn(`${id}: diagram has unsupported element type(s): ${r.skipped.join(", ")}.`);
      }
      diagram = { svg: r.svg, width: r.width, height: r.height, file: `assets/${id}/diagram.excalidraw` };
      if (writing) {
        fs.mkdirSync(assetDir, { recursive: true });
        fs.copyFileSync(diagramPath, path.join(assetDir, "diagram.excalidraw"));
      }
    } catch (e) {
      warn(`${id}: could not render diagram.excalidraw — ${e.message}`);
    }
  } else {
    warn(`${id}: no diagram.excalidraw.`);
  }

  /* code + captured output */
  let code = null;
  const codePath = path.join(dir, "code_example.py");
  if (fs.existsSync(codePath)) {
    const source = fs.readFileSync(codePath, "utf8");
    const run = writing ? runner.run(id, codePath, assetDir) : { skipped: true, reason: "check mode" };
    if (run && run.ran && !run.ok) {
      warn(`${id}: code_example.py exited ${run.exitCode}${run.timedOut ? " (timeout)" : ""}.`);
    }
    if (run && run.durationMs != null) delete run.durationMs; // keep payloads stable
    code = { source, lines: source.split("\n").length, run };
  } else {
    warn(`${id}: no code_example.py.`);
  }

  /* articles */
  let articles = null;
  const articlesRaw = readIfExists(path.join(dir, "articles.md"));
  if (articlesRaw) articles = parseArticles(articlesRaw);
  else warn(`${id}: no articles.md.`);
  const articleCount = (articles || []).reduce((n, g) => n + g.items.length, 0);

  /* images that already sit in the session folder (a script's saved chart) */
  const images = [];
  for (const name of fs.readdirSync(dir)) {
    if (!IMAGE_RE.test(name)) continue;
    images.push(name);
    if (writing) {
      fs.mkdirSync(assetDir, { recursive: true });
      fs.copyFileSync(path.join(dir, name), path.join(assetDir, name));
    }
  }
  // Images the run produced were copied straight into assetDir by the runner.
  const produced = (code && code.run && code.run.images) || [];
  for (const name of produced) if (!images.includes(name)) images.push(name);

  const source = firstLink(topic.meta.Source) ||
    (topic.meta.Source ? { label: topic.meta.Source, url: "" } : null);

  const payload = {
    id,
    title: topic.title,
    category,
    date,
    meta: topic.meta,
    source,
    insight: j["Key insight"] || "",
    topic: topic.body,
    diagram,
    code,
    articles,
    images: images.sort(),
    repo: `${REPO_BLOB}/${id}`,
  };

  const card = {
    id,
    title: topic.title,
    category,
    date,
    insight: payload.insight,
    minutes: readMinutes(topic.meta, topic.body),
    diagram: !!diagram,
    code: !!code,
    articles: articleCount,
    codeLines: code ? code.lines : 0,
    hasOutput: !!(code && code.run && code.run.ok && code.run.stdout.trim()),
  };

  return { payload, card };
}

/* ---- main ------------------------------------------------------------------ */

function main() {
  const check = process.argv.includes("--check");
  const noRun = process.argv.includes("--no-run") || process.env.NORUN === "1";

  const ids = fs.readdirSync(ROOT)
    .filter((name) => SESSION_RE.test(name) && fs.statSync(path.join(ROOT, name)).isDirectory())
    .sort()
    .reverse();   // newest first, which is also the order the grid wants

  if (!ids.length) {
    console.error("No session folders (YYYY-MM-DD) found in " + ROOT);
    process.exit(1);
  }

  const journal = parseJournal(readIfExists(JOURNAL));
  for (const id of ids) if (!journal.has(id)) warn(`${id}: no journal.md entry — the card will fall back to the topic body.`);

  if (!check) {
    rmrf(DATA_DIR);
    rmrf(ASSET_DIR);
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  const runner = createRunner({ root: ROOT, run: !check && !noRun });
  const cards = [];

  for (const id of ids) {
    const out = compile(id, journal, runner, { check });
    if (!out) continue;
    cards.push(out.card);
    if (!check) {
      fs.writeFileSync(path.join(DATA_DIR, id + ".json"), JSON.stringify(out.payload));
    }
  }

  const runStats = runner.finish();

  if (!check) {
    const banner = "/* AUTO-GENERATED by build.js from the session folders — do not edit by hand. */\n";
    fs.writeFileSync(
      path.join(DATA_DIR, "index.js"),
      banner +
      "window.CATEGORIES = " + JSON.stringify(CATEGORIES) + ";\n" +
      "window.SESSIONS = " + JSON.stringify(cards, null, 2) + ";\n"
    );
  }

  warnings.forEach((w) => console.warn("  warn: " + w));
  if (errors.length) {
    errors.forEach((e) => console.error("  ERROR: " + e));
    console.error(`\nBuild failed with ${errors.length} error(s).`);
    process.exit(1);
  }

  const withOutput = cards.filter((c) => c.hasOutput).length;
  if (check) {
    console.log(`Lint passed: ${cards.length} session(s), ${warnings.length} warning(s).`);
    return;
  }
  console.log(
    `Wrote site/data for ${cards.length} session(s) — ` +
    `${cards.filter((c) => c.diagram).length} diagram(s), ` +
    `${withOutput} with captured output ` +
    `(${runStats.executed} run, ${runStats.reused} cached)` +
    (warnings.length ? `, ${warnings.length} warning(s)` : "") + "."
  );
}

main();
