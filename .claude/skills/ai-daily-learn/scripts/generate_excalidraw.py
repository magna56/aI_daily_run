#!/usr/bin/env python3
"""Generate an Excalidraw diagram for an AI Daily Learn session.

Usage:
    python3 generate_excalidraw.py \
        --title "Mixture of Agents" \
        --subtitle "Multi-LLM collaboration for better outputs" \
        --concepts '["Proposer Agents|Multiple LLMs generate diverse initial responses",
                     "Aggregator|Synthesizes proposals into a refined final answer"]' \
        --flow '["Input Query", "Parallel Proposals", "Aggregation", "Output"]' \
        --category "Agent Frameworks & Tools" \
        --output ~/ai_learning/2026-07-04/diagram.excalidraw
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


def build_diagram(title, subtitle, concepts, flow=None, category=None):
    primary_bg, secondary_bg = CATEGORY_COLORS.get(
        category or "", (BLUE, PURPLE))

    Y = 0
    CANVAS_W = 1200

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

    build_diagram(args.title, args.subtitle, concepts,
                  flow=flow, category=args.category)

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
