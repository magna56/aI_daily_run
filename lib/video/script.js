"use strict";

const { firstSentences, trimWords, stripMd } = require("./session");

function punchLine(text, maxWords) {
  return trimWords(stripMd(text).replace(/\s+/g, " ").trim(), maxWords);
}

/**
 * Build a short-video narration from session fields.
 * Copy is deliberately tight — these clips target ~30–40s at 1.18x TTS.
 */
function buildScript(session) {
  const hook = punchLine(
    session.meta.Hook || session.journal["Key insight"] || session.title,
    22,
  );

  const eli5 = session.sections.get("Explain Like I'm 5") || "";
  const problem = session.sections.get("The Problem") || "";
  const setupSource = problem || eli5;
  let setup = firstSentences(setupSource, 1);
  if (!setup) setup = punchLine(session.journal["Key insight"] || hook, 14);
  else setup = punchLine(setup, 16);

  const insight = punchLine(session.journal["Key insight"] || hook, 20);

  const demoCue = session.hasVisualize
    ? "Three tools, four requests — watch the billing multiplier jump."
    : "Runnable migration code is in the article.";

  const cta = "Full walkthrough on theaicommit.com.";

  const beats = [
    { id: "hook", label: "Hook", text: hook },
    { id: "setup", label: "Setup", text: setup },
    { id: "insight", label: "Key insight", text: insight },
    { id: "demo", label: "Demo", text: demoCue },
    { id: "cta", label: "CTA", text: cta, title: session.title, url: session.url },
  ].filter((b) => b.text && b.text.trim());

  // Single line breaks only — double newlines make TTS drag between beats.
  const narration = beats.map((b) => b.text.trim()).join(" ");
  const wordCount = narration.split(/\s+/).filter(Boolean).length;

  return { beats, narration, wordCount };
}

module.exports = { buildScript };
