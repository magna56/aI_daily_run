"use strict";

const { firstSentences, trimWords, stripMd } = require("./session");

function punchLine(text, maxWords) {
  return trimWords(stripMd(text).replace(/\s+/g, " ").trim(), maxWords);
}

/** Pull a concrete number or multiplier from article text if present. */
function findStat(text) {
  const hay = String(text || "");
  const mult = hay.match(/(\d+(?:\.\d+)?)\s*[×x]/i);
  if (mult) return `${mult[1]}×`;
  const tools = hay.match(/(\d+)\s+tool calls?/i);
  if (tools) return `${tools[1]} tool calls`;
  const pct = hay.match(/(\d+(?:\.\d+)?)\s*%/);
  if (pct) return `${pct[1]}%`;
  return null;
}

function splitHook(hook) {
  const h = stripMd(hook);
  const dash = h.split(/\s+[—–-]\s+/);
  if (dash.length >= 2) return { pain: dash[0].trim(), twist: dash.slice(1).join(" — ").trim() };
  return { pain: h, twist: "" };
}

/**
 * Short-video script tuned for technical B2B shorts.
 * See docs/video-pipeline.md § Content strategy.
 */
function buildScript(session) {
  const hookMeta = session.meta.Hook || "";
  const insightRaw = session.journal["Key insight"] || hookMeta || session.title;
  const problem = session.sections.get("The Problem") || "";
  const engineer = session.sections.get("For a Software Engineer") || "";

  const stat = findStat(insightRaw) || findStat(problem) || findStat(engineer);
  const { pain, twist } = splitHook(hookMeta);

  const coldClause = pain.split(/,/)[0]?.trim() || pain;
  const coldOpen = punchLine(
    coldClause.split(/\s+/).length <= 12 ? coldClause : pain,
    10,
  );

  const frame = punchLine(
    twist && twist.split(/\s+/).length >= 6
      ? twist
      : "The Responses API won't run your tool loop — your code does.",
    12,
  );

  // Beat 3 — mechanism: one number + consequence.
  let mechanism;
  if (/tool call|re-bill|re-send|four times|multipl/i.test(insightRaw)) {
    mechanism = stat
      ? `${stat} on one question — every tool call re-sends the whole conversation.`
      : "Every tool call re-bills the entire conversation. Three tools, four requests.";
  } else if (stat) {
    mechanism = `${stat} — ${punchLine(insightRaw, 10)}`;
  } else {
    mechanism = punchLine(insightRaw, 16);
  }

  const demoCue = session.hasVisualize
    ? "Watch the multiplier on one question with three tool calls."
    : "Runnable migration code is in the article.";

  const cta = "Full walkthrough on theaicommit.com.";

  const beats = [
    { id: "cold_open", label: "Cold open", text: coldOpen, onScreen: coldOpen },
    { id: "frame", label: "Topic frame", text: frame, onScreen: frame },
    { id: "mechanism", label: "Mechanism", text: mechanism, onScreen: stat || mechanism },
    { id: "demo", label: "Demo", text: demoCue },
    { id: "cta", label: "CTA", text: cta, title: session.title, url: session.url },
  ].filter((b) => b.text && b.text.trim());

  const narration = beats.map((b) => b.text.trim()).join(" ");
  const wordCount = narration.split(/\s+/).filter(Boolean).length;

  return { beats, narration, wordCount };
}

module.exports = { buildScript };
