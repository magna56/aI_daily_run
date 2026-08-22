/* =============================================================================
   runner.js — executes a session's code_example.py and captures what it printed.
   -----------------------------------------------------------------------------
   The captured stdout is the whole point: it turns an inert .py file into a
   lesson you can finish in the browser, on a phone, without a checkout.

   Safety/robustness rules, in priority order:
     1. Never dirty the repo. Scripts run in a throwaway temp cwd, because at
        least one example (2026-07-08) writes a PNG next to itself.
     2. Never fail the build. A crash, a timeout or a missing interpreter is
        recorded as a result and rendered as "run it locally", not thrown.
     3. Never rerun needlessly. Results are cached by source hash, so a rebuild
        after an index.html tweak re-executes nothing.

   macOS has no `timeout(1)`, so the limit comes from spawnSync's own option
   rather than from wrapping the command.
   ============================================================================= */

"use strict";

const { spawnSync } = require("child_process");
const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");

const TIMEOUT_MS = 60_000;
const MAX_BUFFER = 8 * 1024 * 1024;
const MAX_STDOUT = 40_000;   // keep payloads small; the tail is rarely the point
const MAX_STDERR = 2_000;    // enough for a traceback's last frames
const CACHE_VERSION = 1;     // bump to invalidate every cached run
const IMAGE_RE = /\.(png|jpe?g|gif|svg|webp)$/i;

/** Prefer the repo's venv (it has numpy + matplotlib) over the system python. */
function findPython(root) {
  const venv = path.join(root, ".venv", "bin", "python3");
  if (fs.existsSync(venv)) return venv;
  const probe = spawnSync("python3", ["--version"], { encoding: "utf8" });
  return probe.status === 0 ? "python3" : null;
}

function truncate(s, max, label) {
  const str = String(s == null ? "" : s);
  if (str.length <= max) return str;
  const dropped = str.length - max;
  return str.slice(0, max) + `\n... [${dropped.toLocaleString()} more characters — ${label}]\n`;
}

function tail(s, max) {
  const str = String(s == null ? "" : s).trimEnd();
  return str.length <= max ? str : "... " + str.slice(-max);
}

/* ---- cache ---------------------------------------------------------------- */

function loadCache(file) {
  try {
    const c = JSON.parse(fs.readFileSync(file, "utf8"));
    if (c && c.version === CACHE_VERSION && c.runs) return c;
  } catch (_) { /* missing or corrupt cache is simply a cold cache */ }
  return { version: CACHE_VERSION, runs: {} };
}

function saveCache(file, cache) {
  try {
    fs.writeFileSync(file, JSON.stringify(cache, null, 2) + "\n");
  } catch (e) {
    console.warn("  warn: could not write run cache: " + e.message);
  }
}

/* ---- execution ------------------------------------------------------------ */

function execute(python, script, imagesOutDir) {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "adl-run-"));
  const started = Date.now();
  try {
    const res = spawnSync(python, [path.resolve(script)], {
      cwd,
      timeout: TIMEOUT_MS,
      maxBuffer: MAX_BUFFER,
      encoding: "utf8",
      env: Object.assign({}, process.env, {
        MPLBACKEND: "Agg",          // never try to open a window
        PYTHONUNBUFFERED: "1",
        PYTHONDONTWRITEBYTECODE: "1",
      }),
    });

    const durationMs = Date.now() - started;
    const timedOut = res.error && res.error.code === "ETIMEDOUT";
    const images = [];

    // Anything the script drew is worth showing next to its output.
    if (imagesOutDir) {
      for (const name of fs.readdirSync(cwd)) {
        if (!IMAGE_RE.test(name)) continue;
        fs.mkdirSync(imagesOutDir, { recursive: true });
        fs.copyFileSync(path.join(cwd, name), path.join(imagesOutDir, name));
        images.push(name);
      }
    }

    return {
      ran: true,
      ok: !timedOut && res.status === 0,
      timedOut: !!timedOut,
      exitCode: res.status == null ? null : res.status,
      durationMs,
      stdout: truncate(res.stdout, MAX_STDOUT, "run it locally for the full output"),
      stderr: tail(res.stderr, MAX_STDERR),
      images: images.sort(),
      note: timedOut
        ? `Timed out after ${TIMEOUT_MS / 1000}s.`
        : res.error ? res.error.message : "",
    };
  } catch (e) {
    return {
      ran: false, ok: false, timedOut: false, exitCode: null,
      durationMs: Date.now() - started, stdout: "", stderr: "",
      images: [], note: e.message,
    };
  } finally {
    fs.rmSync(cwd, { recursive: true, force: true });
  }
}

/* ---- entry point ---------------------------------------------------------- */

/**
 * Build a runner bound to one repo root.
 * @param {object} opts { root, cacheFile, run (false => skip execution) }
 */
function createRunner(opts) {
  const o = opts || {};
  const root = o.root || process.cwd();
  const cacheFile = o.cacheFile || path.join(root, ".build-cache.json");
  const enabled = o.run !== false;
  const cache = loadCache(cacheFile);
  const python = enabled ? findPython(root) : null;
  const fresh = {};
  let executed = 0, reused = 0;

  if (enabled && !python) {
    console.warn("  warn: no python3 found — code output will be omitted.");
  }

  return {
    python,

    /**
     * @param {string} id       session id, used to namespace copied images
     * @param {string} script   path to code_example.py
     * @param {string} imgDir   where to copy any images the script produced
     */
    run(id, script, imgDir) {
      const source = fs.readFileSync(script, "utf8");
      const hash = crypto.createHash("sha1")
        .update(String(CACHE_VERSION)).update("\0").update(source)
        .digest("hex").slice(0, 16);

      if (!enabled || !python) {
        return { skipped: true, reason: enabled ? "no python3 available" : "run disabled (NORUN)" };
      }

      const hit = cache.runs[id];
      // Images live outside the cache, so a hit is only usable while the copies
      // it refers to are still on disk.
      const imagesPresent = !hit || !hit.result.images.length
        || hit.result.images.every((f) => fs.existsSync(path.join(imgDir, f)));

      if (hit && hit.hash === hash && imagesPresent) {
        fresh[id] = hit;
        reused++;
        return hit.result;
      }

      const result = execute(python, script, imgDir);
      fresh[id] = { hash, result };
      executed++;
      return result;
    },

    /** Persist only the sessions seen this build, so deleted ones fall out. */
    finish() {
      if (enabled && python) saveCache(cacheFile, { version: CACHE_VERSION, runs: fresh });
      return { executed, reused };
    },
  };
}

module.exports = { createRunner, TIMEOUT_MS };
