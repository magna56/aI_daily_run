"use strict";

const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "..");
const JOURNAL = path.join(ROOT, "journal.md");
const SESSION_RE = /^\d{4}-\d{2}-\d{2}(-s\d+)?$/;
const SITE_ORIGIN = process.env.PUBLIC_URL || "https://theaicommit.com";

function readIfExists(p) {
  try { return fs.readFileSync(p, "utf8"); } catch { return ""; }
}

function metaLine(line) {
  const m = line.match(/^\*\*([^*]+)\*\*:\s*(.*)$/);
  return m ? [m[1].trim(), m[2].trim()] : null;
}

function parseTopic(raw, rel) {
  const lines = raw.replace(/^\uFEFF/, "").split("\n");
  let i = 0;
  while (i < lines.length && !lines[i].trim()) i++;

  const h1 = (lines[i] || "").match(/^#\s+(.*)$/);
  if (!h1) throw new Error(`${rel}: no "# Title" on first non-blank line`);
  const title = h1[1].trim();
  i++;

  const meta = {};
  for (; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    if (line.startsWith("#")) break;
    const kv = metaLine(line);
    if (!kv) break;
    meta[kv[0]] = kv[1];
  }

  return { title, meta, body: lines.slice(i).join("\n").trim() };
}

function splitSections(body) {
  const out = new Map();
  let name = null;
  let buf = [];
  let fenced = false;
  for (const line of String(body).split("\n")) {
    if (/^```/.test(line)) fenced = !fenced;
    const h = !fenced && line.match(/^##\s+(.+?)\s*$/);
    if (h) {
      if (name !== null) out.set(name, buf.join("\n"));
      name = h[1];
      buf = [];
    } else if (name !== null) buf.push(line);
  }
  if (name !== null) out.set(name, buf.join("\n"));
  return out;
}

function parseJournal(raw) {
  const out = new Map();
  if (!raw) return out;
  for (const block of raw.split(/^##\s+/m).slice(1)) {
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
        fields[key] += " " + line.trim();
      } else if (!line.trim()) {
        key = null;
      }
    }
    out.set(id, fields);
  }
  return out;
}

function stripMd(s) {
  return String(s || "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
}

function slugify(title, maxLen = 60) {
  let s = stripMd(title)
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

function firstSentences(text, count = 2) {
  const plain = stripMd(text)
    .replace(/\s+/g, " ")
    .trim();
  if (!plain) return "";
  const parts = plain.match(/[^.!?]+[.!?]+/g) || [plain];
  return parts.slice(0, count).join(" ").trim();
}

function trimWords(text, maxWords) {
  const words = stripMd(text).replace(/\s+/g, " ").trim().split(/\s+/);
  if (words.length <= maxWords) return words.join(" ");
  return words.slice(0, maxWords).join(" ") + "…";
}

function loadSession(id) {
  if (!SESSION_RE.test(id)) throw new Error(`Invalid session id: ${id}`);
  const dir = path.join(ROOT, id);
  if (!fs.existsSync(dir)) throw new Error(`No session folder: ${id}/`);

  const topicRaw = readIfExists(path.join(dir, "topic.md"));
  if (!topicRaw) throw new Error(`${id}/topic.md missing`);

  const topic = parseTopic(topicRaw, `${id}/topic.md`);
  const journal = parseJournal(readIfExists(JOURNAL)).get(id) || {};
  const sections = splitSections(topic.body);
  const slug = `${id}-${slugify(topic.title)}`;

  return {
    id,
    dir,
    slug,
    url: `${SITE_ORIGIN}/${slug}/`,
    title: topic.title,
    meta: topic.meta,
    sections,
    journal,
    hasVisualize: fs.existsSync(path.join(dir, "visualize.html")),
    hasDiagram: fs.existsSync(path.join(dir, "diagram.excalidraw")),
    diagramSvg: fs.existsSync(path.join(ROOT, "site", "assets", id, "diagram.svg"))
      ? path.join(ROOT, "site", "assets", id, "diagram.svg")
      : null,
  };
}

module.exports = {
  ROOT,
  SESSION_RE,
  loadSession,
  firstSentences,
  trimWords,
  stripMd,
  slugify,
};
