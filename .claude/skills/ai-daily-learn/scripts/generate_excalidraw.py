#!/usr/bin/env python3
"""Generate an Excalidraw diagram for an AI Daily Learn session.

Usage:
    python3 generate_excalidraw.py \
        --title "Mixture of Agents" \
        --subtitle "Multi-LLM collaboration for better outputs" \
        --concepts '["Proposer Agents|Multiple LLMs generate diverse initial responses",
                     "Aggregator|Synthesizes proposals into a refined final answer"]' \
        --flow '["Input Query", "Parallel Proposals", "Aggregation", "Output"]' \
        --visuals '[{...}]' \
        --category "Agent Frameworks & Tools" \
        --output ~/ai_learning/2026-07-04/diagram.excalidraw

--visuals is where the diagram actually EXPLAINS the article, as opposed to listing it.
--concepts is a terse at-a-glance grid and --flow is a pipeline strip; neither shows a
mechanism. A visual panel does, by making the shape of the thing carry the argument.
Never fall back to a paragraph of prose in a box: if the point cannot be drawn, it
belongs in topic.md, which already explains the article at length.

Pass a JSON array of panels. Three types, each suited to a different kind of claim:

  {"type": "stack",                     # a quantity COMPOUNDING across steps
   "title": "Every turn re-sends everything before it",
   "note":  "optional one-line caption",
   "columns": ["Turn 1", "Turn 2", "Turn 3"],
   "legend": "what the red bottom block means"}

    Column i is drawn i+1 blocks tall, so growth is the shape. The bottom block of
    every column is red: the same early item, re-paid in every later step.

  {"type": "rows",                      # WHERE a change lands changes the outcome
   "title": "Caching is a prefix match",
   "rows": [{"label": "Prefix untouched",
             "segments": [{"label": "tools", "state": "ok", "w": 2},
                          {"label": "history", "state": "ok", "w": 5}],
             "result": "0.1x read"}]}

    Rows share one segment sequence and differ only in colour, so a cascade reads
    by scanning down. states: ok (green) / bad (red) / new (blue) / neutral (grey).
    "w" weights a segment's width; it defaults to 1.

  {"type": "bars",                      # the RANKING or RATIO is the surprise
   "title": "Same session, priced four ways",
   "bars": [{"label": "Cache thrashing", "value": 31.67,
             "display": "$31.67", "state": "bad"}]}

    Lengths are proportional to "value"; "display" is the text shown beside the bar.
"""

import json
import math
import random
import time
import argparse
import sys

STROKE = "#1e1e1e"
YELLOW = "#ffec99"
GREEN = "#b2f2bb"
GRAY = "#e9ecef"
BEIGE = "#eaddd7"
BLUE = "#a5d8ff"
PURPLE = "#d0bfff"
RED_BG = "#ffc9c9"
TRANSPARENT = "transparent"

FONT = 5
TITLE_SIZE = 36
SUBTITLE_SIZE = 24
BODY_SIZE = 20
SMALL_SIZE = 16
TINY_SIZE = 13

CANVAS_W = 1200

# Semantic fills for the visual panels. These carry meaning (cached / invalidated /
# untouched), so they are deliberately NOT the per-category palette below — a reader
# should be able to read state off the colour without a legend lookup.
STATE_COLORS = {
    "ok": GREEN,
    "bad": RED_BG,
    "new": BLUE,
    "neutral": GRAY,
}

CATEGORY_COLORS = {
    "New Models & APIs": (BLUE, PURPLE),
    "AI Hardware for Engineers": (GRAY, YELLOW),
    "Agent Frameworks & Tools": (GREEN, BLUE),
    "Coding Agents & Productivity": (PURPLE, GREEN),
    "AI in Production": (YELLOW, RED_BG),
    "Applied Research": (PURPLE, BLUE),
    "AI Safety & Testing": (RED_BG, YELLOW),
    "Multimodal Engineering": (BLUE, GREEN),
    "Open Source Tools": (GREEN, YELLOW),
    "AI Engineering Practices": (BEIGE, GRAY),
    "Hands-on Techniques": (YELLOW, GREEN),
}

elements = []
id_counter = 0


def make_id():
    global id_counter
    id_counter += 1
    return f"adl_{id_counter:04d}"


def make_seed():
    return random.randint(100000000, 999999999)


def rect(x, y, w, h, bg=YELLOW, stroke=STROKE, stroke_w=2, label=None,
         label_size=BODY_SIZE, corner=3):
    rid = make_id()
    el = {
        "id": rid, "type": "rectangle", "x": x, "y": y,
        "width": w, "height": h, "angle": 0,
        "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": stroke_w,
        "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "index": f"a{id_counter}",
        "roundness": {"type": corner}, "seed": make_seed(),
        "version": 1, "versionNonce": make_seed(),
        "isDeleted": False, "boundElements": [],
        "updated": int(time.time() * 1000),
        "link": None, "locked": False,
    }
    elements.append(el)
    if label:
        tid = text(x + w / 2, y + h / 2, label, size=label_size,
                   align="center", v_align="middle", container=rid, width=w - 20)
        el["boundElements"] = [{"id": tid, "type": "text"}]
    return rid


def text(x, y, content, size=BODY_SIZE, align="left", v_align="top",
         color=STROKE, container=None, width=None):
    tid = make_id()
    if width is None:
        ml = max(len(line) for line in content.split("\n"))
        width = max(ml * size * 0.55, 20)
    lc = content.count("\n") + 1
    height = max(lc * size * 1.25 + 4, size * 1.25 + 4)
    el = {
        "id": tid, "type": "text",
        "x": x - width / 2 if (align == "center" or container) else x,
        "y": y - height / 2 if (v_align == "middle" or container) else y,
        "width": width, "height": height, "angle": 0,
        "strokeColor": color, "backgroundColor": TRANSPARENT,
        "fillStyle": "solid", "strokeWidth": 2, "roughness": 0,
        "opacity": 100, "groupIds": [], "frameId": None,
        "index": f"a{id_counter}", "roundness": None,
        "seed": make_seed(), "version": 1, "versionNonce": make_seed(),
        "isDeleted": False, "boundElements": None,
        "updated": int(time.time() * 1000),
        "link": None, "locked": False,
        "text": content, "fontSize": size, "fontFamily": FONT,
        "textAlign": align,
        "verticalAlign": v_align if container else "top",
        "containerId": container,
        "originalText": content, "autoResize": True, "lineHeight": 1.25,
    }
    elements.append(el)
    return tid


def wrap_lines(content, width_px, size):
    """Greedy word-wrap for sizing a box ahead of render time.

    The SVG renderer re-wraps every text element to its declared width using
    real per-glyph metrics (see excalidraw-svg.js's `measure`), which run
    slightly narrower than this flat size*0.55-per-char estimate — so this
    always predicts as many or more lines than the renderer actually needs.
    That means the box this sizes is never too short, only possibly a touch
    tall, which is the safe direction to be wrong in.
    """
    words = content.split()
    lines, cur, cur_w = [], [], 0.0
    for w in words:
        adv = len(w) * size * 0.55
        sep = size * 0.3 if cur else 0
        if cur and cur_w + sep + adv > width_px:
            lines.append(" ".join(cur))
            cur, cur_w = [w], adv
        else:
            cur.append(w)
            cur_w += sep + adv
    if cur:
        lines.append(" ".join(cur))
    return lines


def arrow(x1, y1, x2, y2, stroke=STROKE, stroke_w=2,
          start_id=None, end_id=None):
    aid = make_id()
    dx, dy = x2 - x1, y2 - y1
    el = {
        "id": aid, "type": "arrow", "x": x1, "y": y1,
        "width": abs(dx), "height": abs(dy), "angle": 0,
        "strokeColor": stroke, "backgroundColor": TRANSPARENT,
        "fillStyle": "solid", "strokeWidth": stroke_w,
        "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "index": f"a{id_counter}",
        "roundness": {"type": 2}, "seed": make_seed(),
        "version": 1, "versionNonce": make_seed(),
        "isDeleted": False, "boundElements": None,
        "updated": int(time.time() * 1000),
        "link": None, "locked": False,
        "points": [[0, 0], [dx, dy]],
        "startBinding": ({"elementId": start_id, "focus": 0, "gap": 5,
                          "fixedPoint": None} if start_id else None),
        "endBinding": ({"elementId": end_id, "focus": 0, "gap": 5,
                        "fixedPoint": None} if end_id else None),
        "startArrowhead": None, "endArrowhead": "arrow", "elbowed": False,
    }
    elements.append(el)
    return aid


def panel_title(y, title, note=None):
    """Section heading, and an optional one-line caption under it."""
    if title:
        text(50, y, title, size=SUBTITLE_SIZE, width=CANVAS_W - 100)
        y += 34
    if note:
        lines = wrap_lines(note, CANVAS_W - 100, SMALL_SIZE)
        text(50, y, note, size=SMALL_SIZE, color="#555555", width=CANVAS_W - 100)
        y += len(lines) * SMALL_SIZE * 1.25 + 10
    return y


def visual_stack(y, spec, secondary_bg):
    """Columns of stacked blocks — shows a quantity compounding across steps.

    Column i is i+1 blocks tall, so the growth is the shape itself. The bottom
    block of every column is drawn in the 'bad' colour: that is the SAME early
    item being re-paid in every later step, which is the point the panel exists
    to make.
    """
    cols = spec.get("columns", [])
    if not cols:
        return y
    y = panel_title(y, spec.get("title"), spec.get("note"))

    n = len(cols)
    block_h, block_gap, col_gap = 18, 4, 22
    col_w = min(140, (CANVAS_W - 100 - (n - 1) * col_gap) // n)
    total_w = n * col_w + (n - 1) * col_gap
    start_x = (CANVAS_W - total_w) // 2

    stack_h = n * (block_h + block_gap)
    baseline = y + stack_h

    for i in range(n):
        cx = start_x + i * (col_w + col_gap)
        for j in range(i + 1):
            by = baseline - (j + 1) * (block_h + block_gap)
            rect(cx, by, col_w, block_h,
                 bg=RED_BG if j == 0 else secondary_bg, stroke_w=1)
        text(cx + col_w / 2, baseline + 16, cols[i], size=TINY_SIZE,
             align="center", v_align="middle", width=col_w + 16)

    y = baseline + 42

    legend = spec.get("legend")
    if legend:
        rect(50, y, 22, 16, bg=RED_BG, stroke_w=1)
        text(80, y + 8, legend, size=SMALL_SIZE, v_align="middle",
             color="#444444", width=CANVAS_W - 140)
        y += 30
    return y + 12


def visual_rows(y, spec):
    """Labelled horizontal bars split into coloured segments.

    Built for before/after and good/bad comparisons where WHERE a change lands
    matters — each row is the same sequence of segments, and only the colours
    differ, so the cascade is visible by scanning down the columns.
    """
    rows = spec.get("rows", [])
    if not rows:
        return y
    y = panel_title(y, spec.get("title"), spec.get("note"))

    label_w, result_w, gap = 250, 165, 14
    seg_x = 50 + label_w + gap
    seg_total = CANVAS_W - 50 - result_w - gap - seg_x
    row_h, row_gap = 44, 12

    for row in rows:
        segs = row.get("segments", [])
        weights = [max(float(s.get("w", 1)), 0.1) for s in segs]
        wsum = sum(weights) or 1

        text(50, y + row_h / 2, row.get("label", ""), size=SMALL_SIZE,
             v_align="middle", width=label_w)

        x = seg_x
        for seg, weight in zip(segs, weights):
            w = int(seg_total * weight / wsum)
            rect(x, y, w, row_h,
                 bg=STATE_COLORS.get(seg.get("state", "neutral"), GRAY),
                 stroke_w=1, label=seg.get("label", ""), label_size=TINY_SIZE)
            x += w

        result = row.get("result", "")
        if result:
            text(CANVAS_W - 50 - result_w, y + row_h / 2, result,
                 size=SMALL_SIZE, v_align="middle", width=result_w)
        y += row_h + row_gap

    return y + 18


def visual_bars(y, spec):
    """Horizontal bar chart — lengths are proportional, so the ranking is visual.

    Use it when the surprising part of a result is the ORDER or the RATIO, not
    the individual figures.
    """
    bars = spec.get("bars", [])
    if not bars:
        return y
    y = panel_title(y, spec.get("title"), spec.get("note"))

    label_w, gap, value_w = 300, 16, 110
    bar_x = 50 + label_w + gap
    bar_max = CANVAS_W - 50 - value_w - gap - bar_x
    bar_h, bar_gap = 34, 14
    peak = max((abs(float(b.get("value", 0))) for b in bars), default=1) or 1

    for b in bars:
        text(50, y + bar_h / 2, b.get("label", ""), size=SMALL_SIZE,
             v_align="middle", width=label_w)
        w = max(int(bar_max * abs(float(b.get("value", 0))) / peak), 4)
        rect(bar_x, y, w, bar_h,
             bg=STATE_COLORS.get(b.get("state", "neutral"), GRAY), stroke_w=1)
        text(bar_x + w + 12, y + bar_h / 2, str(b.get("display", b.get("value", ""))),
             size=SMALL_SIZE, v_align="middle", width=value_w)
        y += bar_h + bar_gap

    return y + 18


VISUAL_BUILDERS = {
    "stack": lambda y, spec, sec: visual_stack(y, spec, sec),
    "rows": lambda y, spec, sec: visual_rows(y, spec),
    "bars": lambda y, spec, sec: visual_bars(y, spec),
}


def build_diagram(title, subtitle, concepts, flow=None, category=None, visuals=None):
    primary_bg, secondary_bg = CATEGORY_COLORS.get(
        category or "", (BLUE, PURPLE))

    Y = 0

    text(CANVAS_W / 2, Y, title, size=TITLE_SIZE, align="center",
         width=CANVAS_W - 100)
    Y += 50
    text(CANVAS_W / 2, Y, subtitle, size=SUBTITLE_SIZE, align="center",
         width=CANVAS_W - 100, color="#666666")
    Y += 50

    today = time.strftime("%Y-%m-%d")
    cat_label = category or "AI Learning"
    rect(50, Y, 200, 35, bg=GRAY, label=today, label_size=SMALL_SIZE)
    rect(270, Y, 300, 35, bg=primary_bg, label=cat_label, label_size=SMALL_SIZE)
    Y += 60

    for spec in (visuals or []):
        builder = VISUAL_BUILDERS.get(spec.get("type"))
        if builder is None:
            print(f"warning: unknown visual type {spec.get('type')!r}, skipping",
                  file=sys.stderr)
            continue
        Y = builder(Y, spec, secondary_bg)

    text(50, Y, "Key Concepts", size=SUBTITLE_SIZE, width=300)
    Y += 40

    col_w = 560
    row_h = 110
    gap = 20
    colors = [primary_bg, secondary_bg]

    for i, concept_str in enumerate(concepts):
        parts = concept_str.split("|", 1)
        name = parts[0].strip()
        desc = parts[1].strip() if len(parts) > 1 else ""

        col = i % 2
        row = i // 2
        cx = 50 + col * (col_w + gap)
        cy = Y + row * (row_h + gap)

        rect(cx, cy, col_w, row_h, bg=colors[col], stroke=STROKE, stroke_w=2)
        text(cx + 15, cy + 10, name, size=BODY_SIZE, width=col_w - 30)
        if desc:
            text(cx + 15, cy + 38, desc, size=SMALL_SIZE,
                 width=col_w - 30, color="#444444")

    num_rows = (len(concepts) + 1) // 2
    Y += num_rows * (row_h + gap) + 20

    if flow and len(flow) >= 2:
        text(50, Y, "How It Works", size=SUBTITLE_SIZE, width=300)
        Y += 40

        n = len(flow)
        # Long flows used to keep the 60px arrow gap and let the boxes collapse
        # — eight steps left 68px per box, narrower than a single word, so
        # labels broke mid-word ("Regist er Dispat ch"). Trade gap for box.
        gap = 60 if n <= 5 else (36 if n <= 7 else 24)
        label_size = SMALL_SIZE if n <= 6 else SMALL_SIZE - 2
        box_w = min(200, (CANVAS_W - 100 - (n - 1) * gap) // n)

        # Size the box to the label instead of assuming one line fits: the
        # renderer (and Excalidraw itself) grows a shape whose bound text
        # overflows, and a grown box would otherwise collide with what follows.
        inner = max(box_w - 20, 1)
        lines = 1
        for step in flow:
            word_w = max((len(w) * label_size * 0.55 for w in step.split()), default=0)
            # Greedy wrap at the same char-width estimate text() uses.
            count, cur = 1, 0.0
            for w in step.split():
                adv = len(w) * label_size * 0.55 + label_size * 0.3
                if cur and cur + adv > inner:
                    count += 1
                    cur = adv
                else:
                    cur += adv
            lines = max(lines, count, math.ceil(word_w / inner))
        box_h = max(55, int(lines * label_size * 1.25) + 12)

        total_w = n * box_w + (n - 1) * gap
        start_x = (CANVAS_W - total_w) // 2

        flow_ids = []
        for i, step in enumerate(flow):
            fx = start_x + i * (box_w + gap)
            bg = primary_bg if i % 2 == 0 else secondary_bg
            fid = rect(fx, Y, box_w, box_h, bg=bg, label=step,
                       label_size=label_size)
            flow_ids.append((fid, fx))

        for i in range(len(flow_ids) - 1):
            src_id, src_x = flow_ids[i]
            dst_id, dst_x = flow_ids[i + 1]
            arrow(src_x + box_w, Y + box_h // 2,
                  dst_x, Y + box_h // 2,
                  start_id=src_id, end_id=dst_id)

        Y += box_h + 40

    Y += 10
    rect(50, Y, CANVAS_W - 100, 40, bg=BEIGE, stroke=STROKE, stroke_w=1,
         label="AI Daily Learn — open code_example.py to try it hands-on",
         label_size=SMALL_SIZE)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Excalidraw diagram for AI Daily Learn")
    parser.add_argument("--title", required=True)
    parser.add_argument("--subtitle", required=True)
    parser.add_argument("--concepts", required=True,
                        help='JSON array of "Name|Description" strings')
    parser.add_argument("--flow", default=None,
                        help="JSON array of flow step names")
    parser.add_argument("--visuals", default=None,
                        help="JSON array of visual panels (see module docstring)")
    parser.add_argument("--category", default=None)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        concepts = json.loads(args.concepts)
    except json.JSONDecodeError as e:
        print(f"Error parsing --concepts: {e}", file=sys.stderr)
        sys.exit(1)

    flow = None
    if args.flow:
        try:
            flow = json.loads(args.flow)
        except json.JSONDecodeError as e:
            print(f"Error parsing --flow: {e}", file=sys.stderr)
            sys.exit(1)

    if len(concepts) < 2:
        print("Need at least 2 concepts", file=sys.stderr)
        sys.exit(1)

    visuals = None
    if args.visuals:
        try:
            visuals = json.loads(args.visuals)
        except json.JSONDecodeError as e:
            print(f"Error parsing --visuals: {e}", file=sys.stderr)
            sys.exit(1)

    build_diagram(args.title, args.subtitle, concepts,
                  flow=flow, category=args.category, visuals=visuals)

    excalidraw = {
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

    with open(args.output, "w") as f:
        json.dump(excalidraw, f, indent=2)

    print(f"Generated {len(elements)} elements -> {args.output}")


if __name__ == "__main__":
    main()
