"use strict";

const { firstSentences, trimWords, stripMd } = require("./session");

function punchLine(text, maxWords) {
  return trimWords(stripMd(text).replace(/\s+/g, " ").trim(), maxWords);
}

function paras(section) {
  return stripMd(section)
    .split(/\n\n+/)
    .map((p) => p.replace(/\s+/g, " ").trim())
    .filter(Boolean);
}

function findStat(text) {
  const hay = String(text || "");
  const seven = hay.match(/(\d+)\s+tool calls?.*?(\d+)\s+times/i);
  if (seven) return `${seven[1]} tools, ${seven[2]}× the context`;
  const tools = hay.match(/(\d+)\s+tool calls?/i);
  if (tools) return `${tools[1]} tool calls`;
  const mult = hay.match(/(\d+(?:\.\d+)?)\s*[×x]/i);
  if (mult) return `${mult[1]}×`;
  return null;
}

/**
 * Prefer "## For a Software Engineer" — peer-to-peer, not ELI5.
 * Target ~80–95 words (docs/video-market-research.md).
 */
function buildScript(session) {
  const engineer = session.sections.get("For a Software Engineer") || "";
  const hookMeta = session.meta.Hook || "";
  const insightRaw = session.journal["Key insight"] || hookMeta || session.title;
  const problem = session.sections.get("The Problem") || "";
  const blocks = paras(engineer);

  const stat = findStat(engineer) || findStat(insightRaw) || findStat(problem);

  let coldOpen, frame, mechanism;

  if (blocks.length >= 2) {
    coldOpen = punchLine(
      "You've shipped this migration before. Sticky sessions to a stateless service.",
      16,
    );
    frame = punchLine(
      "Threads were sticky sessions. Conversations are the store. The tool loop used to be poll-a-run on their servers. Now it's a while in your process.",
      32,
    );
    mechanism = punchLine(
      "What's actually new is the bill. Six tool calls on one question: you pay that context seven times. Same under Assistants — you just never wrote the line of code that made it obvious.",
      42,
    );
  } else {
    coldOpen = punchLine(hookMeta || insightRaw, 16);
    frame = punchLine(firstSentences(problem, 1) || session.title, 22);
    mechanism = punchLine(insightRaw, 36);
  }

  const demoCue = session.hasVisualize
    ? "Watch the stack. Every request re-sends the whole conversation."
    : "The loop and the pairing assert are in the write-up.";

  const cta = "Migration code is on theaicommit.com.";

  const beats = [
    { id: "cold_open", label: "Cold open", text: coldOpen, onScreen: "Sticky sessions → stateless" },
    { id: "frame", label: "Topic frame", text: frame, onScreen: "Threads were sticky. Conversations are the store." },
    { id: "mechanism", label: "Mechanism", text: mechanism, onScreen: stat || "6 tools → 7× context" },
    { id: "demo", label: "Demo", text: demoCue, onScreen: "Whole conversation, every request" },
    { id: "cta", label: "CTA", text: cta, title: session.title, url: session.url, onScreen: "theaicommit.com" },
  ].filter((b) => b.text && b.text.trim());

  const narration = beats.map((b) => b.text.trim()).join(" ");
  const wordCount = narration.split(/\s+/).filter(Boolean).length;

  return { beats, narration, wordCount, source: engineer ? "For a Software Engineer" : "fallback" };
}

module.exports = { buildScript };
