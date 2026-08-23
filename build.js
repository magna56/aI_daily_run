#!/usr/bin/env node
/* =============================================================================
   build.js — compiles the daily session folders into the data the reader loads.
   -----------------------------------------------------------------------------
   Dependency-free. Run with:  node build.js            (write site/data/)
                               node build.js --check    (lint only, write nothing)
                               node build.js --no-run   (skip executing examples)

   Session folders are the source of truth and are never modified: /ai-daily-learn
   writes YYYY-MM-DD/{topic.md,visualize.html,diagram.excalidraw,code_example.py,articles.md} and
   this script adapts to whatever is there. Older sessions are missing a diagram
   or an articles file, and that is a warning, not an error.

   Output:
     site/data/index.js      window.SESSIONS + window.CATEGORIES — the card grid
     site/data/<id>.json     one session's full payload, fetched when opened
     site/assets/<id>/       visualize.html + diagram.excalidraw + any images
     site/<id>/index.html    real, independently-crawlable per-session page — root
                              index.html with the META/OG blocks swapped for that
                              session's own title/description/canonical/JSON-LD;
                              otherwise byte-identical (see writePerSessionShell)
     site/sitemap.xml        generated here, not hand-written — lists every session

   The split matters: the grid must stay fast as sessions accumulate, so the
   heavy parts (rendered SVG, source, captured output) load only on demand.
   ============================================================================= */

"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

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

// Reader-facing one-liners for the generated /topics/<slug>/ pages. These are
// the pages' meta description and on-page blurb, so they address the reader
// ("you") rather than describing the category to the generator — the skill's
// own Category Tiers section is where the generator-facing definitions live.
const CATEGORY_BLURBS = {
  "Coding Agents & Productivity":
    "Getting more out of the coding agents you already drive every day — Claude Code, Cursor, Codex, Gemini CLI: hooks, skills, subagents, context and cost control, and what this week's changelogs actually change about your workflow.",
  "Building Agents & MCP":
    "Authoring agent systems rather than operating them: tool schema design, MCP servers, orchestration libraries, SDKs, and the architecture decisions that decide whether an agent is debuggable.",
  "AI Engineering Practices":
    "Reviewing, testing and trusting agent-written code — migrations at scale, architecture patterns, and team workflows for codebases where most commits now start with a prompt.",
  "Evals & Reliability":
    "Does your AI feature actually work? App-level eval harnesses, catching regressions before users do, guardrails you ship, and output validation you can put in CI.",
  "New Models & APIs":
    "New model releases and what they change in practice — API differences, migration guides, pricing, context limits, and when routing to a cheaper model is the right call.",
  "AI in Production":
    "Running AI systems for real: deployment patterns, serving infrastructure, cost optimization, monitoring, and RAG at a scale where the naive version stops working.",
  "Hands-on Techniques":
    "The craft layer — fine-tuning, RAG pipelines, prompt and context engineering — explained with runnable code rather than diagrams of boxes.",
  "Applied Research":
    "Papers with working code and reproducible results, read for what they change about your engineering decisions rather than for the leaderboard number.",
  "AI Hardware for Engineers":
    "How to actually use the hardware you have or rent: picking an instance type, quantization you can run today, inference-speed wins, memory ceilings, and local-vs-hosted tradeoffs.",
  "Multimodal Engineering":
    "Vision, audio and video pipeline internals — how an image becomes tokens, what that costs, and what the model can actually see by the time it arrives.",
  "AI Safety & Alignment":
    "Alignment research, red-teaming findings and model behaviour studies, read by an engineer asking what it means for systems they ship.",
};

// Orientation, not a second taxonomy. Level is how much runway the reader
// needs; For is which job they are doing. Both are required on new sessions.
const LEVELS = ["Start here", "Building", "Deeper"];
const JOBS = ["Using tools", "Building agents", "Shipping AI", "How models work"];

// Evergreen two-day track. Folders live under learn/<id>/; ids are the slugs
// used in #learn/<id> and site/data/<id>.json. Order is the reading order.
const LEARN_TRACK = [
  "what-an-llm-does",
  "tokens-and-sampling",
  "prompting-that-holds-up",
  "coding-agents-101",
  "skills",
  "retrieval",
  "context-and-harness",
  "the-agent-loop",
  "reasoning-models",
  "how-the-forward-pass-runs",
  "the-coding-agent-harness",
];

// Cross-cutting facets, deliberately NOT a restatement of CATEGORIES: a session
// has exactly one category (what it is about) and several tags (what it touches).
// A controlled list is the whole point — free-form tags drift into
// fine-tuning / finetuning / Fine Tuning within a month and the facet stops
// working. Adding a tag means editing this list first; build.js --check warns
// on anything not here, and the skill is told to pick from it.
const TAGS = [
  // technique
  "rag", "fine-tuning", "quantization", "caching", "context-engineering",
  "prompt-engineering", "reranking", "distillation",
  // concern
  "cost", "latency", "reliability", "security", "benchmarks", "observability",
  // surface
  "agents", "mcp", "coding-agents", "multimodal", "embeddings",
  "inference-serving", "training", "transformers",
  // use-case / provenance
  "from-scratch", "paper", "production", "interview",
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
  const dir = opts.dir || path.join(ROOT, id);
  const kind = opts.kind || "daily";
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

  // Tags are optional — sessions published before the facet existed have none,
  // and an empty array is a valid state rather than a defect.
  const tags = String(topic.meta.Tags || "")
    .split(",")
    .map((t) => t.trim().toLowerCase())
    .filter(Boolean);
  for (const t of tags) {
    if (!TAGS.includes(t)) warn(`${id}: tag "${t}" is not in the TAGS vocabulary in build.js.`);
  }

  const date = topic.meta.Date || (SESSION_RE.test(id) ? id.slice(0, 10) : "");
  const level = topic.meta.Level || "";
  const job = topic.meta.For || "";
  const hook = topic.meta.Hook || "";
  if (!level) warn(`${id}: no Level in topic.md (Start here / Building / Deeper).`);
  else if (!LEVELS.includes(level)) warn(`${id}: level "${level}" is not one of ${LEVELS.join(", ")}.`);
  if (!job) warn(`${id}: no For in topic.md (${JOBS.join(" / ")}).`);
  else if (!JOBS.includes(job)) warn(`${id}: For "${job}" is not one of ${JOBS.join(", ")}.`);
  if (!hook) warn(`${id}: no Hook in topic.md — the card will fall back to the journal insight.`);
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

  /* interactive visualizer -> isolated standalone HTML, loaded only when its
     pane opens. It stays out of the JSON payload so the grid/session read path
     pays zero bytes for an interaction the reader may never use. */
  let visualize = null;
  const visualizePath = path.join(dir, "visualize.html");
  if (fs.existsSync(visualizePath)) {
    const html = fs.readFileSync(visualizePath, "utf8");
    if (!/<html[\s>]/i.test(html) || !/<title>[^<]+<\/title>/i.test(html)) {
      warn(`${id}: visualize.html must be a complete document with a <title>.`);
    } else {
      let valid = true;
      if (!/name=["']viewport["']/i.test(html)) {
        warn(`${id}: visualize.html has no viewport meta tag.`);
      }
      if (!/data-visualizer/i.test(html)) {
        warn(`${id}: visualize.html has no data-visualizer root marker.`);
      }
      if (!/adl-visualize-height/.test(html)) {
        warn(`${id}: visualize.html does not report its height to the reader.`);
      }
      if (/<script[^>]+\bsrc\s*=|<link[^>]+\bhref\s*=|\b(fetch|XMLHttpRequest|WebSocket)\s*\(/i.test(html)) {
        warn(`${id}: visualize.html references external resources or network APIs.`);
      }
      const scripts = [...html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/gi)]
        .filter((m) => !/\bjson\b/i.test(m[1]) && m[2].trim());
      for (let i = 0; i < scripts.length; i++) {
        try {
          new vm.Script(scripts[i][2], { filename: `${id}/visualize.html#script-${i + 1}` });
        } catch (e) {
          warn(`${id}: visualize.html has invalid JavaScript — ${e.message}`);
          valid = false;
          break;
        }
      }
      if (valid) {
        visualize = { file: `assets/${id}/visualize.html` };
        if (writing) {
          fs.mkdirSync(assetDir, { recursive: true });
          fs.copyFileSync(visualizePath, path.join(assetDir, "visualize.html"));
        }
      }
    }
  } else {
    warn(`${id}: no visualize.html.`);
  }

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
    tags,
    date,
    meta: topic.meta,
    source,
    insight: j["Key insight"] || (kind === "learn" ? hook : ""),
    hook,
    level,
    job,
    topic: topic.body,
    diagram,
    visualize,
    code,
    articles,
    images: images.sort(),
    kind,
    repo: kind === "learn" ? `${REPO_BLOB}/learn/${id}` : `${REPO_BLOB}/${id}`,
  };

  const card = {
    id,
    kind,
    // The canonical per-post path, so the grid can render a REAL href instead
    // of a hash-only click handler. Computed here (not inside the shell
    // renderer) precisely so it reaches data/index.js and the cards.
    slug: `${id}-${slugify(stripMd(topic.title))}`,
    title: topic.title,
    category,
    tags,
    date,
    insight: payload.insight,
    hook,
    level,
    job,
    minutes: readMinutes(topic.meta, topic.body),
    diagram: !!diagram,
    visualize: !!visualize,
    code: !!code,
    articles: articleCount,
    codeLines: code ? code.lines : 0,
    hasOutput: !!(code && code.run && code.run.ok && code.run.stdout.trim()),
  };

  return { payload, card };
}

/* ---- per-session real pages (search-indexable URLs) ------------------------ */
// See the "Real per-post URLs" plan: index.html is one static file for every
// hash-routed URL, so a crawler or a shared link only ever sees the generic
// site-wide title/description — it never learns which session it's looking
// at. This block gives each session its OWN file at site/<id>/index.html:
// same page, same app, but with real per-session metadata baked into the raw
// HTML a crawler reads without executing any JS.

const SITE_ORIGIN = "https://theaicommit.com";

function stripMd(s) {
  // Mirrors index.html's client-side plain() exactly, so a description reads
  // the same whether it was rendered by JS or baked in at build time.
  return String(s == null ? "" : s)
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/(^|\W)\*([^*]+)\*(?=\W|$)/g, "$1$2")
    .replace(/\[([^\]]+)\]\([^)\s]*\)/g, "$1");
}

// Converts a topic.md body (## headings, prose paragraphs, "- " bullets — see
// parseTopic) into plain semantic HTML for the ARTICLE_NOSCRIPT crawler
// fallback. Not a general Markdown renderer: just enough structure (headings,
// paragraphs, lists) for a non-JS crawler to read real content instead of an
// empty shell. Wrapped continuation lines (both prose and multi-line bullets)
// join onto the block they continue, matching how topic.md is actually wrapped.
function mdToHtml(body) {
  const lines = String(body || "").split("\n");
  let html = "";
  let para = [];
  let list = [];
  const flushPara = () => {
    if (para.length) html += `<p>${escAttr(stripMd(para.join(" ")))}</p>\n`;
    para = [];
  };
  const flushList = () => {
    if (list.length) html += `<ul>${list.map((li) => `<li>${escAttr(stripMd(li))}</li>`).join("")}</ul>\n`;
    list = [];
  };
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) { flushPara(); flushList(); continue; }
    const h = line.match(/^(#{2,3})\s+(.*)$/);
    if (h) {
      flushPara(); flushList();
      const tag = h[1].length === 2 ? "h2" : "h3";
      html += `<${tag}>${escAttr(stripMd(h[2]))}</${tag}>\n`;
      continue;
    }
    const li = line.match(/^[-*]\s+(.*)$/);
    if (li) {
      flushPara();
      list.push(li[1]);
      continue;
    }
    if (list.length) {
      list[list.length - 1] += " " + line;   // wrapped continuation of a bullet
      continue;
    }
    para.push(line);
  }
  flushPara();
  flushList();
  return html;
}

// Turns a title into a URL-safe slug for the canonical per-post path
// (site/<id>-<slug>/index.html). Truncated at a hyphen boundary, never mid-word.
function slugify(title, maxLen = 60) {
  let s = stripMd(String(title))
    .toLowerCase()
    .replace(/['’‘`]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  if (s.length > maxLen) {
    s = s.slice(0, maxLen);
    const lastHyphen = s.lastIndexOf("-");
    if (lastHyphen > maxLen * 0.5) s = s.slice(0, lastHyphen);
    s = s.replace(/-+$/g, "");
  }
  return s;
}

function truncateWords(s, max) {
  s = s.trim();
  if (s.length <= max) return s;
  const cut = s.slice(0, max);
  const lastSpace = cut.lastIndexOf(" ");
  return (lastSpace > max * 0.6 ? cut.slice(0, lastSpace) : cut).trim() + "…";
}

function escAttr(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/"/g, "&quot;")
    .replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Safe to drop straight into a <script type="application/ld+json"> block: a
// title/description containing a literal "</script>" would otherwise close
// the tag early and dump the rest of the page as visible text.
function jsonLdSafe(obj) {
  return JSON.stringify(obj, null, 2).replace(/</g, "\\u003c");
}

// Reads root index.html once and returns a function that stamps in one
// session's metadata — called once per session, not once per byte, so this
// stays cheap even as the archive grows.
function makeShellTemplate() {
  const raw = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
  const cut = (text, startMarker, endMarker) => {
    const s = text.indexOf(startMarker);
    const e = text.indexOf(endMarker);
    if (s === -1 || e === -1 || e < s) {
      throw new Error(`index.html is missing ${startMarker} / ${endMarker} — per-session page generation depends on both markers being present and in order.`);
    }
    return { before: text.slice(0, s), after: text.slice(e + endMarker.length) };
  };
  const metaMark = cut(raw, "<!-- META:START -->", "<!-- META:END -->");
  const ogMark = cut(metaMark.after, "<!-- OG:START -->", "<!-- OG:END -->");
  // Three pieces once the two blocks are cut out: everything before META,
  // everything between META and OG (icons/manifest — untouched per session),
  // everything after OG (the rest of <head> plus the entire <body>).
  const head = metaMark.before;
  const middle = ogMark.before;
  const NOSCRIPT_MARK = "<!-- ARTICLE_NOSCRIPT -->";
  const noscriptIdx = ogMark.after.indexOf(NOSCRIPT_MARK);
  if (noscriptIdx === -1) {
    throw new Error(`index.html is missing ${NOSCRIPT_MARK} — per-session page generation depends on it.`);
  }
  const tailBefore = ogMark.after.slice(0, noscriptIdx);
  const tailAfter = ogMark.after.slice(noscriptIdx + NOSCRIPT_MARK.length);

  /**
   * One renderer for all three page kinds, because they differ only in their
   * metadata block and their <noscript> body — every byte of CSS and JS is
   * shared, which is what keeps the SPA identical whichever URL you enter by.
   *
   * spec: { pageTitle, description, url, ogType, jsonLd, noscriptBody }
   */
  return function render(spec) {
    const meta =
      `<!-- META:START -->\n` +
      `<title>${escAttr(spec.pageTitle)}</title>\n` +
      `<meta name="description" content="${escAttr(spec.description)}" />\n` +
      `<link rel="canonical" href="${escAttr(spec.url)}" />\n` +
      `<!-- META:END -->`;

    const og =
      `<!-- OG:START -->\n` +
      `<meta property="og:type" content="${escAttr(spec.ogType)}" />\n` +
      `<meta property="og:site_name" content="The AI Commit" />\n` +
      `<meta property="og:title" content="${escAttr(spec.pageTitle)}" />\n` +
      `<meta property="og:description" content="${escAttr(spec.description)}" />\n` +
      `<meta property="og:image" content="${SITE_ORIGIN}/og-image.png" />\n` +
      `<meta property="og:image:width" content="1200" />\n` +
      `<meta property="og:image:height" content="630" />\n` +
      `<meta property="og:url" content="${escAttr(spec.url)}" />\n` +
      `<meta name="twitter:card" content="summary_large_image" />\n` +
      `<meta name="twitter:title" content="${escAttr(spec.pageTitle)}" />\n` +
      `<meta name="twitter:description" content="${escAttr(spec.description)}" />\n` +
      `<meta name="twitter:image" content="${SITE_ORIGIN}/og-image.png" />\n\n` +
      `<script type="application/ld+json">\n${jsonLdSafe(spec.jsonLd)}\n</script>\n` +
      `<!-- OG:END -->`;

    const noscript = `<noscript>\n${spec.noscriptBody}</noscript>`;

    let body = tailBefore + noscript + tailAfter;
    // Exactly one <h1> per page, in BOTH the JS-rendered and raw-HTML views.
    // The shared header ships a <p class="tagline">; only the homepage promotes
    // it to the page's h1. Session and topic pages get their h1 from the
    // article/topic title instead (noscript for crawlers, renderReader /
    // renderTopicHead once JS runs), so the tagline must stay a <p> there.
    if (spec.isHome) {
      if (!body.includes(HOME_H1.from)) {
        throw new Error(`index.html no longer contains ${HOME_H1.from} — the homepage h1 swap depends on that exact line.`);
      }
      body = body.replace(HOME_H1.from, HOME_H1.to);
    }
    return head + meta + middle + og + body;
  };
}

const HOME_H1 = {
  from: '<p class="tagline">A daily AI engineering lab for software engineers</p>',
  to: '<h1 class="tagline">A daily AI engineering lab for software engineers</h1>',
};

const PUBLISHER = {
  "@type": "Organization",
  name: "The AI Commit",
  url: SITE_ORIGIN + "/",
  logo: `${SITE_ORIGIN}/icon-512.png`,
};

// One <li> linking to a session's canonical URL. The link graph these build is
// the point: before this, a crawler could reach a session only via sitemap.xml,
// because every on-page "link" was a JS click handler on a non-anchor element.
function sessionLinkItem(card) {
  return `<li><a href="/${escAttr(card.slug)}/">${escAttr(stripMd(card.title))}</a>` +
    ` <span>${escAttr(card.date)}${card.category ? " · " + escAttr(card.category) : ""}</span></li>\n`;
}

// A session page: the article itself, plus a link back up to its topic page.
function sessionPageSpec(payload, card) {
  const title = stripMd(payload.title);
  // The canonical URL is <id>-<slug>/ — readable and keyword-bearing. The bare
  // <id>/ page (see main()) is also written and kept working for already-shared
  // links, but its canonical tag points here too, so search engines consolidate
  // on one URL instead of treating them as duplicate content.
  const url = `${SITE_ORIGIN}/${card.slug}/`;
  const description = truncateWords(stripMd(payload.insight) || title, 155);
  const topicHref = payload.category ? `/topics/${slugify(payload.category)}/` : "";

  return {
    pageTitle: `${title} — The AI Commit`,
    description,
    url,
    ogType: "article",
    jsonLd: {
      "@context": "https://schema.org",
      "@type": "TechArticle",
      headline: title,
      description,
      datePublished: payload.date,
      keywords: (payload.tags || []).join(", ") || undefined,
      url,
      mainEntityOfPage: url,
      image: `${SITE_ORIGIN}/og-image.png`,
      publisher: PUBLISHER,
    },
    noscriptBody:
      `<article>\n` +
      `<h1>${escAttr(title)}</h1>\n` +
      mdToHtml(payload.topic) +
      (topicHref
        ? `<p>More in this category: <a href="${escAttr(topicHref)}">${escAttr(payload.category)}</a></p>\n`
        : "") +
      `</article>\n`,
  };
}

// A topic page: every session in one category, as real links.
function topicPageSpec(category, cardsInCategory) {
  const slug = slugify(category);
  const url = `${SITE_ORIGIN}/topics/${slug}/`;
  const description = truncateWords(
    CATEGORY_BLURBS[category] || `Every ${category} session on The AI Commit.`, 155);

  return {
    pageTitle: `${category} — The AI Commit`,
    description,
    url,
    ogType: "website",
    jsonLd: {
      "@context": "https://schema.org",
      "@type": "CollectionPage",
      name: category,
      description,
      url,
      isPartOf: { "@type": "WebSite", name: "The AI Commit", url: SITE_ORIGIN + "/" },
      publisher: PUBLISHER,
      mainEntity: {
        "@type": "ItemList",
        numberOfItems: cardsInCategory.length,
        itemListElement: cardsInCategory.map((c, i) => ({
          "@type": "ListItem",
          position: i + 1,
          url: `${SITE_ORIGIN}/${c.slug}/`,
          name: stripMd(c.title),
        })),
      },
    },
    noscriptBody:
      `<main>\n` +
      `<h1>${escAttr(category)}</h1>\n` +
      `<p>${escAttr(CATEGORY_BLURBS[category] || "")}</p>\n` +
      `<ul>\n${cardsInCategory.map(sessionLinkItem).join("")}</ul>\n` +
      `<p><a href="/">All sessions</a></p>\n` +
      `</main>\n`,
  };
}

// The homepage: the site's own metadata, plus a crawlable index of every topic
// page and every session — the entry point for the whole link graph.
function homePageSpec(cards, categories) {
  const description =
    "Understand one real AI development in 30 minutes — a plain-English explanation, " +
    "a diagram of the actual mechanism, and code that runs live in your browser.";

  return {
    isHome: true,
    pageTitle: "The AI Commit — Daily AI Engineering Lab for Software Engineers",
    description,
    url: SITE_ORIGIN + "/",
    ogType: "website",
    jsonLd: {
      "@context": "https://schema.org",
      "@type": "WebSite",
      name: "The AI Commit",
      alternateName: "AI Commit",
      description,
      url: SITE_ORIGIN + "/",
      publisher: PUBLISHER,
    },
    // No <h1> here: the visible tagline is promoted to the homepage's h1 (see
    // HOME_H1), and a second one in the noscript index would compete with it
    // for non-JS crawlers, which render noscript content.
    noscriptBody:
      `<main>\n` +
      `<h2>Topics</h2>\n<ul>\n` +
      categories.map((c) =>
        `<li><a href="/topics/${escAttr(slugify(c))}/">${escAttr(c)}</a></li>\n`).join("") +
      `</ul>\n` +
      `<h2>All sessions</h2>\n<ul>\n${cards.filter((c) => c.kind !== "learn").map(sessionLinkItem).join("")}</ul>\n` +
      `<h2>Learn</h2>\n<ul>\n${cards.filter((c) => c.kind === "learn").map(sessionLinkItem).join("")}</ul>\n` +
      `</main>\n`,
  };
}

function writeSitemap(cards, categories) {
  // Only the canonical <id>-<slug> path is listed — the bare <id>/ page also
  // exists (for already-shared links) but its own canonical tag points here,
  // so it deliberately isn't a separate sitemap entry. Tags have no static
  // pages (they're hash filters), so nothing to list for them either.
  const newestIn = (cat) => cards
    .filter((c) => c.category === cat)
    .map((c) => c.date)
    .sort()
    .pop();

  const urls = [
    { loc: `${SITE_ORIGIN}/`, changefreq: "daily", priority: "1.0" },
    ...categories.map((cat) => ({
      loc: `${SITE_ORIGIN}/topics/${slugify(cat)}/`,
      lastmod: newestIn(cat),
      changefreq: "weekly",
      priority: "0.8",
    })),
    { loc: `${SITE_ORIGIN}/privacy.html`, changefreq: "monthly", priority: "0.3" },
    { loc: `${SITE_ORIGIN}/terms.html`, changefreq: "monthly", priority: "0.3" },
    ...cards.map((c) => ({
      loc: `${SITE_ORIGIN}/${c.slug}/`,
      lastmod: c.date,
      changefreq: "monthly",
      priority: "0.7",
    })),
  ];
  const body = urls.map((u) =>
    `  <url>\n` +
    `    <loc>${escAttr(u.loc)}</loc>\n` +
    (u.lastmod ? `    <lastmod>${u.lastmod}</lastmod>\n` : "") +
    `    <changefreq>${u.changefreq}</changefreq>\n` +
    `    <priority>${u.priority}</priority>\n` +
    `  </url>`
  ).join("\n");
  fs.writeFileSync(
    path.join(SITE, "sitemap.xml"),
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`
  );
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

  const learnRoot = path.join(ROOT, "learn");
  for (const slug of LEARN_TRACK) {
    const topicPath = path.join(learnRoot, slug, "topic.md");
    if (!fs.existsSync(topicPath)) warn(`learn/${slug}: missing topic.md — slot will be absent from the track.`);
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
  // Loaded once (not once per session) — see makeShellTemplate's own comment
  // for why. Only needed when actually writing output, same as everything
  // else gated on !check.
  const renderShell = check ? null : makeShellTemplate();

  function writeSession(out) {
    cards.push(out.card);
    if (!check) {
      fs.writeFileSync(path.join(DATA_DIR, out.card.id + ".json"), JSON.stringify(out.payload));
      const html = renderShell(sessionPageSpec(out.payload, out.card));
      // The bare <id>/ page keeps already-shared/indexed links working; its
      // canonical tag (baked into `html` above) points at the slug page, so
      // both resolve but only the slug page is treated as the "real" one.
      for (const dirName of [out.card.id, out.card.slug]) {
        const dir = path.join(SITE, dirName);
        fs.mkdirSync(dir, { recursive: true });
        fs.writeFileSync(path.join(dir, "index.html"), html);
      }
    }
  }

  for (const id of ids) {
    const out = compile(id, journal, runner, { check });
    if (out) writeSession(out);
  }

  for (const slug of LEARN_TRACK) {
    const dir = path.join(learnRoot, slug);
    if (!fs.existsSync(path.join(dir, "topic.md"))) continue;
    const out = compile(slug, journal, runner, { check, dir, kind: "learn" });
    if (out) writeSession(out);
  }

  const runStats = runner.finish();

  if (!check) {
    const banner = "/* AUTO-GENERATED by build.js from the session folders — do not edit by hand. */\n";
    fs.writeFileSync(
      path.join(DATA_DIR, "index.js"),
      banner +
      "window.CATEGORIES = " + JSON.stringify(CATEGORIES) + ";\n" +
      "window.CATEGORY_BLURBS = " + JSON.stringify(CATEGORY_BLURBS) + ";\n" +
      "window.LEVELS = " + JSON.stringify(LEVELS) + ";\n" +
      "window.JOBS = " + JSON.stringify(JOBS) + ";\n" +
      "window.LEARN_TRACK = " + JSON.stringify({
        title: "Learn",
        blurb: "A two-day course for software engineers. Eleven lessons, in order. Separate from the daily lab.",
        ids: LEARN_TRACK,
        sessions: LEARN_TRACK.map((id) => {
          const c = cards.find((x) => x.id === id);
          return c
            ? { id: c.id, title: c.title, hook: c.hook, slug: c.slug, minutes: c.minutes, level: c.level, job: c.job }
            : { id };
        }),
      }) + ";\n" +
      "window.SESSIONS = " + JSON.stringify(cards, null, 2) + ";\n"
    );
    // Categories that actually have sessions, in CATEGORIES (tier) order so
    // the topic index reads the same way the skill's rotation does.
    const covered = CATEGORIES.filter((cat) => cards.some((c) => c.category === cat));

    for (const cat of covered) {
      const inCat = cards.filter((c) => c.category === cat && c.kind !== "learn");
      const dir = path.join(SITE, "topics", slugify(cat));
      fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(path.join(dir, "index.html"), renderShell(topicPageSpec(cat, inCat)));
    }

    // The homepage is generated here rather than copied by the Makefile, so it
    // can carry the crawlable <noscript> index — same move already made for
    // sitemap.xml. site/ exists by now: mkdirSync(DATA_DIR, {recursive:true}).
    fs.writeFileSync(path.join(SITE, "index.html"), renderShell(homePageSpec(cards, covered)));

    writeSitemap(cards, covered);
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
    `${cards.filter((c) => c.visualize).length} visualizer(s), ` +
    `${cards.filter((c) => c.diagram).length} diagram(s), ` +
    `${withOutput} with captured output ` +
    `(${runStats.executed} run, ${runStats.reused} cached)` +
    (warnings.length ? `, ${warnings.length} warning(s)` : "") + "."
  );
}

main();
