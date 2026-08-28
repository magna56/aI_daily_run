"use strict";

const { firstSentences, trimWords } = require("./session");

/**
 * Build a short-video narration from session fields.
 * Returns { beats, narration, wordCount }.
 */
function buildScript(session) {
  const hook = session.meta.Hook
    || session.journal["Key insight"]
    || session.title;

  const eli5 = session.sections.get("Explain Like I'm 5") || "";
  const problem = session.sections.get("The Problem") || "";
  const setupSource = eli5 || problem;
  const setup = firstSentences(setupSource, 2)
    || firstSentences(session.journal["Key insight"] || "", 1);

  const insight = trimWords(
    session.journal["Key insight"] || hook,
    35,
  );

  const demoCue = session.hasVisualize
    ? "Watch what happens when one question needs several tool calls — the whole conversation gets sent again, every time."
    : "The full walkthrough includes runnable code and a step-by-step migration checklist.";

  const cta = `Read the full article at theaicommit.com — link in the description.`;

  const beats = [
    { id: "hook", label: "Hook", text: hook },
    { id: "setup", label: "Setup", text: setup },
    { id: "insight", label: "Key insight", text: insight },
    { id: "demo", label: "Demo", text: demoCue },
    { id: "cta", label: "CTA", text: cta, title: session.title, url: session.url },
  ].filter((b) => b.text && b.text.trim());

  const narration = beats.map((b) => b.text.trim()).join("\n\n");
  const wordCount = narration.split(/\s+/).filter(Boolean).length;

  return { beats, narration, wordCount };
}

module.exports = { buildScript };
