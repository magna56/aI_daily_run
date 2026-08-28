"use strict";

const { firstSentences, trimWords, stripMd } = require("./session");

function punchLine(text, maxWords) {
  return trimWords(stripMd(text).replace(/\s+/g, " ").trim(), maxWords);
}

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
 * ~75–90 word explainer (docs/video-market-research.md): educational pace, not a 15s tip.
 */
function buildScript(session) {
  const hookMeta = session.meta.Hook || "";
  const insightRaw = session.journal["Key insight"] || hookMeta || session.title;
  const problem = session.sections.get("The Problem") || "";
  const engineer = session.sections.get("For a Software Engineer") || "";
  const job = session.meta.For || "Building agents";

  const stat = findStat(insightRaw) || findStat(problem) || findStat(engineer);
  const { pain, twist } = splitHook(hookMeta);

  const identity = /agent/i.test(job + hookMeta + session.title)
    ? "If you ship agents: "
    : "";

  const coldOpen = punchLine(
    identity + (pain.split(/,/)[0] || pain || firstSentences(problem, 1)),
    16,
  );

  const frame = punchLine(
    twist && twist.split(/\s+/).length >= 8
      ? twist
      : "The replacement is the Responses API. It will not run your tool-calling loop — your own process does.",
    22,
  );

  let mechanism;
  if (/tool call|re-bill|re-send|four times|multipl|loop/i.test(insightRaw + problem)) {
    mechanism = stat
      ? `Nothing got cheaper. ${stat} still applies: one question that needs three tools is four requests, and the whole conversation is re-billed every time. A URL swap leaves an agent that answers once and forgets.`
      : "Nothing got cheaper. One question that needs three tools is four requests, and the whole conversation is re-billed every time. A URL swap leaves an agent that answers once and forgets.";
  } else if (stat) {
    mechanism = `${stat}. ${punchLine(insightRaw, 28)}`;
  } else {
    mechanism = punchLine(insightRaw, 36);
  }

  const demoCue = session.hasVisualize
    ? "On screen: slide the tool count. Three tools, four requests — the same context sent again."
    : "The article has the migration loop and a pairing assert you can drop into your client.";

  const cta = "Full walkthrough, with code, on theaicommit.com.";

  const beats = [
    { id: "cold_open", label: "Cold open", text: coldOpen, onScreen: punchLine(coldOpen, 8) },
    { id: "frame", label: "Topic frame", text: frame, onScreen: punchLine(frame, 10) },
    { id: "mechanism", label: "Mechanism", text: mechanism, onScreen: stat || "3 tools = 4 requests" },
    { id: "demo", label: "Demo", text: demoCue, onScreen: "3 tools · 4 requests" },
    { id: "cta", label: "CTA", text: cta, title: session.title, url: session.url, onScreen: "theaicommit.com" },
  ].filter((b) => b.text && b.text.trim());

  const narration = beats.map((b) => b.text.trim()).join(" ");
  const wordCount = narration.split(/\s+/).filter(Boolean).length;

  return { beats, narration, wordCount };
}

module.exports = { buildScript };
