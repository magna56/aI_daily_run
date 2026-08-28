"use strict";

const { trimWords, stripMd } = require("./session");

function punchLine(text, maxWords) {
  return trimWords(stripMd(text).replace(/\s+/g, " ").trim(), maxWords);
}

function splitHook(hook) {
  const h = stripMd(hook);
  const dash = h.split(/\s+[—–-]\s+/);
  if (dash.length >= 2) return { pain: dash[0].trim(), twist: dash.slice(1).join(" — ").trim() };
  return { pain: h, twist: "" };
}

/**
 * Main explainer first. Optional "## For a Software Engineer" as one extra beat.
 */
function buildScript(session) {
  const hookMeta = session.meta.Hook || "";
  const insightRaw = session.journal["Key insight"] || hookMeta || session.title;
  const problem = session.sections.get("The Problem") || "";
  const engineer = session.sections.get("For a Software Engineer") || "";
  const { pain, twist } = splitHook(hookMeta);

  const coldOpen = punchLine(
    pain.split(/,/)[0] || pain || "The Assistants API stopped answering.",
    14,
  );

  const frame = punchLine(
    twist && twist.split(/\s+/).length >= 6
      ? twist
      : "The Responses API will not run your tool-calling loop. Your process does.",
    20,
  );

  const mechanism = punchLine(
    "Cost did not go down. One question that needs three tools is four requests, and the whole conversation is re-billed every time.",
    28,
  );

  const engineerBeat = engineer
    ? punchLine(
      "For an engineer: this is sticky sessions to a stateless service. Threads were sticky. Conversations are the store. Poll-a-run is now a while in your process.",
      32,
    )
    : "";

  const demoCue = session.hasVisualize
    ? "On screen: three tools, four requests — same context, sent again."
    : "The migration loop is in the article.";

  const cta = "Full walkthrough on theaicommit.com.";

  const beats = [
    { id: "cold_open", label: "Cold open", text: coldOpen, onScreen: coldOpen },
    { id: "frame", label: "Topic frame", text: frame, onScreen: "You own the tool loop" },
    { id: "mechanism", label: "Mechanism", text: mechanism, onScreen: "3 tools = 4 requests" },
  ];
  if (engineerBeat) {
    beats.push({
      id: "engineer",
      label: "For a software engineer",
      text: engineerBeat,
      onScreen: "Sticky sessions → Conversations store",
    });
  }
  beats.push(
    { id: "demo", label: "Demo", text: demoCue, onScreen: "3 tools · 4 requests" },
    { id: "cta", label: "CTA", text: cta, title: session.title, url: session.url, onScreen: "theaicommit.com" },
  );

  const narration = beats.map((b) => b.text.trim()).join(" ");
  const wordCount = narration.split(/\s+/).filter(Boolean).length;

  return { beats, narration, wordCount };
}

module.exports = { buildScript };
