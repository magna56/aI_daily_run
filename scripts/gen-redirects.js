const { execSync } = require("child_process");
const fs = require("fs");

// Reimplemented to match build.js:1496 and :1561 exactly.
const stripMd = (s) => String(s == null ? "" : s)
  .replace(/`([^`]+)`/g, "$1").replace(/\*\*([^*]+)\*\*/g, "$1")
  .replace(/(^|\W)\*([^*]+)\*(?=\W|$)/g, "$1$2");
function slugify(title, maxLen = 60) {
  let s = stripMd(String(title)).toLowerCase()
    .replace(/['’‘`]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  if (s.length > maxLen) {
    s = s.slice(0, maxLen);
    const h = s.lastIndexOf("-");
    if (h > maxLen * 0.5) s = s.slice(0, h);
    s = s.replace(/-+$/g, "");
  }
  return s;
}
const sh = (c) => execSync(c, { encoding: "utf8", maxBuffer: 64 << 20 });

// every topic.md the repo has ever tracked
const files = sh(`git log --pretty=format: --name-only --diff-filter=A -- '*/topic.md' | sort -u`)
  .split("\n").map(s => s.trim()).filter(Boolean);

const rules = [];
for (const f of files) {
  if (!fs.existsSync(f)) continue;                       // deleted session
  const dir = f.replace(/\/topic\.md$/, "");
  const isFrontier = dir.startsWith("frontier/");
  const isLearn = dir.startsWith("learn/");
  const base = isFrontier ? "frontier-" + dir.split("/")[1]
             : isLearn ? dir.split("/")[1]
             : dir;
  const titleAt = (rev) => {
    try {
      const t = sh(`git show ${rev}:${JSON.stringify(f).slice(1, -1)} 2>/dev/null | head -1`);
      const m = t.match(/^#\s+(.+)$/m);
      return m ? m[1].trim() : null;
    } catch { return null; }
  };
  const revs = sh(`git log --format=%H -- ${JSON.stringify(f).slice(1, -1)}`).split("\n").filter(Boolean);
  const current = titleAt("HEAD");
  if (!current) continue;
  const curSlug = `${base}-${slugify(stripMd(current))}`;
  const seen = new Set([curSlug]);
  for (const r of revs) {
    const t = titleAt(r);
    if (!t) continue;
    const s = `${base}-${slugify(stripMd(t))}`;
    if (!seen.has(s)) { seen.add(s); rules.push([s, curSlug, t, current]); }
  }
}
console.log(JSON.stringify(rules, null, 1));
