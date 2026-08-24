#!/usr/bin/env python3
"""Generate docs/system-architecture.excalidraw — not part of the reader."""

import json
import random
import time

STROKE = "#1e1e1e"
YELLOW = "#ffec99"
GREEN = "#b2f2bb"
GRAY = "#e9ecef"
BEIGE = "#eaddd7"
BLUE = "#a5d8ff"
PURPLE = "#d0bfff"
RED = "#ffc9c9"
TEAL = "#c3fae8"

elements = []
n = 0


def nid():
    global n
    n += 1
    return f"arch_{n:04d}"


def seed():
    return random.randint(100000000, 999999999)


def add(el):
    elements.append(el)
    return el["id"]


def rect(x, y, w, h, bg=YELLOW, label=None, size=16, stroke=STROKE):
    rid = nid()
    el = {
        "id": rid, "type": "rectangle", "x": x, "y": y,
        "width": w, "height": h, "angle": 0,
        "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": 2, "roughness": 0,
        "opacity": 100, "groupIds": [], "frameId": None,
        "index": f"a{n}", "roundness": {"type": 3},
        "seed": seed(), "version": 1, "versionNonce": seed(),
        "isDeleted": False, "boundElements": [],
        "updated": int(time.time() * 1000),
        "link": None, "locked": False,
    }
    add(el)
    if label:
        tid = text(x + w / 2, y + h / 2, label, size=size, align="center",
                   v="middle", container=rid, width=w - 16)
        el["boundElements"] = [{"id": tid, "type": "text"}]
    return rid


def text(x, y, content, size=20, align="left", v="top", color=STROKE,
         container=None, width=None):
    tid = nid()
    if width is None:
        ml = max(len(line) for line in content.split("\n"))
        width = max(ml * size * 0.55, 20)
    lc = content.count("\n") + 1
    height = max(lc * size * 1.25 + 4, size * 1.25 + 4)
    add({
        "id": tid, "type": "text",
        "x": x - width / 2 if (align == "center" or container) else x,
        "y": y - height / 2 if (v == "middle" or container) else y,
        "width": width, "height": height, "angle": 0,
        "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2, "roughness": 0,
        "opacity": 100, "groupIds": [], "frameId": None,
        "index": f"a{n}", "roundness": None,
        "seed": seed(), "version": 1, "versionNonce": seed(),
        "isDeleted": False, "boundElements": None,
        "updated": int(time.time() * 1000),
        "link": None, "locked": False,
        "text": content, "fontSize": size, "fontFamily": 5,
        "textAlign": align, "verticalAlign": v if container else "top",
        "containerId": container, "originalText": content,
        "autoResize": True, "lineHeight": 1.25,
    })
    return tid


def arrow(x1, y1, x2, y2, start=None, end=None):
    aid = nid()
    dx, dy = x2 - x1, y2 - y1
    add({
        "id": aid, "type": "arrow", "x": x1, "y": y1,
        "width": abs(dx), "height": abs(dy), "angle": 0,
        "strokeColor": STROKE, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2, "roughness": 0,
        "opacity": 100, "groupIds": [], "frameId": None,
        "index": f"a{n}", "roundness": {"type": 2},
        "seed": seed(), "version": 1, "versionNonce": seed(),
        "isDeleted": False, "boundElements": None,
        "updated": int(time.time() * 1000),
        "link": None, "locked": False,
        "points": [[0, 0], [dx, dy]],
        "startBinding": ({"elementId": start, "focus": 0, "gap": 4,
                          "fixedPoint": None} if start else None),
        "endBinding": ({"elementId": end, "focus": 0, "gap": 4,
                        "fixedPoint": None} if end else None),
        "startArrowhead": None, "endArrowhead": "arrow", "elbowed": False,
    })
    return aid


def lane(x, y, w, h, title, bg):
    rid = rect(x, y, w, h, bg=bg, label=None)
    text(x + 16, y + 10, title, size=15, color="#555555", width=w - 32)
    return rid


W = 1560
text(W / 2, 16, "The AI Commit — system architecture", size=32, align="center", width=1400)
text(W / 2, 56,
     "Git repo is the source of truth. site/ is local build output, never committed. "
     "deploy.sh uploads that same folder twice.",
     size=16, align="center", color="#555555", width=1400)

# ── 1. Source ────────────────────────────────────────────────────────────
lane(20, 110, 1520, 210, "1  THIS MACHINE  —  git main  (magna56/aI_daily_run)", BEIGE)

s1 = rect(40, 150, 280, 150, YELLOW,
          "YYYY-MM-DD/\ntopic.md  visualize.html\ndiagram.excalidraw\ncode_example.py\narticles.md", 15)
s2 = rect(340, 150, 250, 150, YELLOW,
          "learn/\n11 AI basics +\n6 intermediate primers\nKind: Learn", 15)
s3 = rect(610, 150, 200, 150, YELLOW,
          "journal.md\ncard blurbs\nKey insight", 15)
s4 = rect(830, 150, 250, 150, BLUE,
          "Reader + API source\nindex.html  (SPA)\nfunctions/  (Pages)\ndb/schema.sql", 15)
s5 = rect(1100, 150, 220, 150, PURPLE,
          "build.js\nlib/runner.js\nlib/excalidraw-svg.js\nMakefile", 15)
s6 = rect(1340, 150, 180, 150, RED,
          "macOS Keychain\nCF API token\nnewsletter secret", 14)

# ── 2. Build ─────────────────────────────────────────────────────────────
lane(20, 350, 1520, 200, "2  LOCAL BUILD  —  make site   (python3 required here, not on CF)", GRAY)

b1 = rect(40, 390, 340, 140, PURPLE,
          "build.js\nparse markdown\nrun each code_example.py\nrender .excalidraw → SVG\ncache by source hash", 15)
b2 = rect(460, 390, 520, 140, BLUE,
          "site/   (gitignored)\n"
          "data/index.js  +  data/<id>.json\n"
          "assets/<id>/visualize.html + diagram\n"
          "copied functions/  _redirects  404.html", 15)
b3 = rect(1060, 390, 460, 140, YELLOW,
          "Reader contract\n"
          "grid reads index.js\n"
          "article fetches data/<id>.json\n"
          "Visualize iframe: sandbox=allow-scripts\n"
          "no same-origin / popups / forms", 15)

arrow(180, 300, 180, 390, s1, b1)
arrow(465, 300, 400, 390, s2, b1)
arrow(710, 300, 500, 390, s3, b1)
arrow(955, 300, 700, 390, s4, b2)
arrow(1210, 300, 1230, 390, s5, b1)
arrow(380, 460, 460, 460, b1, b2)
arrow(980, 460, 1060, 460, b2, b3)

# ── 3. Deploy ────────────────────────────────────────────────────────────
lane(20, 580, 1520, 150, "3  deploy.sh  —  one site/ folder, two publishes, no rebuild per host", GRAY)

d0 = rect(40, 620, 280, 90, PURPLE, "deploy.sh\nbuild once, then fork", 16)
d1 = rect(400, 620, 500, 90, BLUE,
          "GitHub Pages mirror\nthrowaway git repo → force-push gh-pages\nno Functions, no D1", 15)
d2 = rect(980, 620, 540, 90, GREEN,
          "Cloudflare Pages  (primary)\nwrangler pages deploy site --project-name=theaicommit\nthen POST /api/newsletter (idempotent)", 15)

arrow(720, 530, 180, 620, b2, d0)
arrow(320, 665, 400, 665, d0, d1)
arrow(900, 665, 980, 665, d0, d2)
arrow(1430, 300, 1430, 620, s6, d2)

# ── 4. Hosts ─────────────────────────────────────────────────────────────
lane(20, 760, 740, 280, "4a  MIRROR  —  magna56.github.io/aI_daily_run", GRAY)
lane(800, 760, 740, 280, "4b  PRIMARY  —  theaicommit.com  (Cloudflare Pages)", TEAL)

m1 = rect(40, 800, 340, 100, GRAY,
          "Static SPA only\n404.html hash-preserve redirect\nsignup form posts to theaicommit.com", 14)
m2 = rect(400, 800, 340, 100, GRAY,
          "No D1  ·  no Resend\nNo /api/* Functions\nSame HTML/JSON/assets", 14)

c1 = rect(820, 800, 220, 100, GREEN,
          "SPA + _redirects\n/api/* stay on Functions\n/* → /index.html 200", 14)
c2 = rect(1060, 800, 220, 100, GREEN,
          "Pages Functions\n/api/subscribe\n/api/confirm  /unsubscribe\n/api/newsletter  /stats", 13)
c3 = rect(1300, 800, 220, 100, YELLOW,
          "D1  theaicommit\nsubscribers\nissues  (send lock)", 14)
c4 = rect(820, 920, 340, 100, BLUE,
          "Resend\nconfirm + daily issue email\nNEWSLETTER_FROM / PUBLIC_URL", 14)
c5 = rect(1180, 920, 340, 100, RED,
          "Secrets on CF\nRESEND_API_KEY\nNEWSLETTER_SECRET\nNEWSLETTER_NOTIFY", 14)

arrow(650, 710, 210, 800, d1, m1)
arrow(1250, 710, 930, 800, d2, c1)
arrow(1040, 850, 1060, 850, c1, c2)
arrow(1280, 850, 1300, 850, c2, c3)
arrow(930, 900, 930, 920, c1, c4)
arrow(1410, 900, 1410, 920, c3, c5)

# ── 5. Browser ───────────────────────────────────────────────────────────
lane(20, 1070, 1520, 200, "5  BROWSER  —  the reader", BEIGE)

r1 = rect(40, 1110, 280, 140, YELLOW,
          "Daily lab\nhomepage grid\nlatest sessions first\nnot the learn track", 15)
r2 = rect(340, 1110, 280, 140, BLUE,
          "AI basics  #learn\nDay 1 foundations\nDay 2 agents + machine\n11 lessons", 15)
r3 = rect(640, 1110, 280, 140, PURPLE,
          "Intermediate  #learn/…\nLoRA  attention\ncalibration  embeddings\nbuild-an-LLM  agents", 15)
r4 = rect(940, 1110, 280, 140, GREEN,
          "Article panes\nOverview  Visualize\nDiagram  Code  Articles\nlive Pyodide REPL", 15)
r5 = rect(1240, 1110, 280, 140, TEAL,
          "Quiet signup\nDaily email one-liner\nconfirm link → D1 active\none issue per new daily", 15)

arrow(210, 1060, 180, 1110, m1, r1)
arrow(930, 1060, 1080, 1110, c1, r4)
arrow(1410, 1020, 1380, 1110, c3, r5)

text(40, 1290,
     "site/ is gitignored. Skills write session folders only. Publish = commit+push main, then ./deploy.sh. "
     "This diagram is docs/ — it is not a reader session and is not copied into site/.",
     size=14, color="#555555", width=1480)

out = {
    "type": "excalidraw",
    "version": 2,
    "source": "https://excalidraw.com",
    "elements": elements,
    "appState": {
        "gridSize": 20,
        "gridStep": 5,
        "gridModeEnabled": False,
        "viewBackgroundColor": "#ffffff",
    },
    "files": {},
}

path = __file__.replace(".py", ".excalidraw")
with open(path, "w") as f:
    json.dump(out, f, indent=2)
print(f"Wrote {len(elements)} elements → {path}")
