"use strict";

const fs = require("fs");
const path = require("path");
const { stripMd } = require("./session");

function tokenPct(text) {
  const m = String(text).match(/(\d+)\s*%\s+of tokens/i)
    || String(text).match(/discarded roughly\s+\*\*(\d+)\s*%\*\*/i);
  return m ? m[1] : "";
}

function sneakCode(session) {
  const p = path.join(session.dir, "code_example.py");
  if (!fs.existsSync(p)) return "";
  const raw = fs.readFileSync(p, "utf8");
  const fn = raw.match(/def sum_split\([\s\S]*?return sum_sequential\(partials\)\n/);
  if (fn) {
    return fn[0]
      .replace(/"""[\s\S]*?"""\n\s*/, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }
  return "";
}

function sneakShip(session) {
  const p = path.join(session.dir, "topic.md");
  if (!fs.existsSync(p)) return "";
  const raw = fs.readFileSync(p, "utf8");
  const fn = raw.match(/def assert_logprobs_close\([\s\S]*?return worst/);
  if (!fn) return "";
  return fn[0]
    .replace(/"""[\s\S]*?"""\n\s*/, "")
    .replace(/\n\s*assert worst[\s\S]*?not numerics"\)/, "\n    assert worst <= tol")
    .trim();
}

/**
 * Advertisement cut: hook people who have not read the article.
 * Do not teach the walkthrough. Leave the floor, the assert, and the
 * engineer analogy as reasons to open the URL.
 */
function buildScript(session) {
  const problem = session.sections.get("The Problem") || "";
  const view = session.meta["Engineer's view"] || "";
  const pct = tokenPct(problem) || "45";
  const code = sneakCode(session);
  const ship = sneakShip(session);
  const named = stripMd(view).split(/[.—]/)[0].trim()
    || "This is a flaky test under load";

  const beats = [
    {
      id: "cold_open",
      label: "Hook",
      kind: "story",
      kicker: "Your eval just failed",
      text: "CI went red. You did not change the model.",
      onScreen: "CI went red.\nYou didn't touch\nthe weights.",
      sub: "Same prompt. Temperature 0. The GPU box and your laptop still picked different next tokens.",
    },
    {
      id: "frame",
      label: "Stakes",
      kind: "story",
      kicker: "Not a random flake",
      text: `One training run discarded ${pct}% of tokens after a 0.013 train-infer gap.`,
      onScreen: `${pct}% of tokens\nthrown away.`,
      sub: "A 0.013 disagreement hit a threshold. The run collapsed. Your exact-string assert can die the same way.",
    },
  ];

  if (code) {
    beats.push({
      id: "code",
      label: "Code flash",
      kind: "code",
      kicker: "Runnable in the article",
      text: "The reduction that flips the argmax, and the assert you actually ship.",
      onScreen: "Don't assert strings.\nAssert a number you measured.",
      code,
      code2: ship,
      code2Label: "what you copy into CI",
      codeNote: named.replace(/\.$/, "") + ".",
    });
  }

  beats.push({
    id: "cta",
    label: "CTA",
    kind: "story",
    kicker: "Why — and what to do Monday",
    text: "The flaky-test version of this, the noise floor, the batch-size catch. Link in comments.",
    onScreen: "Why it fails on traffic,\nnot on your code.",
    sub: "The walkthrough, the visualize tab, and Python you can run are in the article. Not here.",
    deep: "theaicommit.com — link in comments",
    url: session.url,
    title: "theaicommit.com",
  });

  const narration = beats.map((b) => b.text.trim()).join(" ");
  const wordCount = narration.split(/\s+/).filter(Boolean).length;
  return { beats, narration, wordCount };
}

module.exports = { buildScript };
