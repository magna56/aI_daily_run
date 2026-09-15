#!/usr/bin/env python3
"""Measure how far a document has drifted from its author's own voice.

Pure Python, no dependencies, no network, no API keys. Reads plain text or
markdown. Everything here is deterministic — the rewriting is done by the
model running the skill, this script only supplies the measurements it is not
allowed to guess at.

    python3 voiceprint.py \
        --baseline original.md sample.md \
        --ai ai_version.md \
        --draft current.md \
        --assistant chatgpt

    --json   machine-readable output for the skill to read back
    --top N  how many drifted paragraphs to list (default 8)

Exit status is 0 unless the inputs are unusable (too little baseline text).
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Tell profiles.
#
# PROVISIONAL — these lists are hand-seeded, not measured. The spec
# (docs/voiceprint-spec.md §4) requires them to be replaced by a corpus run
# that reports a lift value per span. Until that happens, treat a tell hit as
# a prompt to look at the sentence, never as proof of anything.
# --------------------------------------------------------------------------

GENERIC_TELLS = [
    "delve", "tapestry", "testament to", "underscore", "underscores",
    "multifaceted", "navigate the complexities", "in today's", "landscape of",
    "robust framework", "pivotal", "realm of", "myriad", "plethora",
    "it is worth noting", "it's worth noting", "crucial role", "vital role",
    "deep dive", "unlock", "unleash", "harness the power", "seamless",
    "seamlessly", "cutting-edge", "ever-evolving", "rapidly evolving",
    "at the forefront", "shed light on", "paradigm", "holistic",
    "comprehensive understanding", "invaluable", "meticulous", "meticulously",
    "foster a", "fostering", "embark", "journey of", "resonate", "profound",
    "intricate", "nuanced understanding", "align with my", "passionate about",
    "eager to contribute", "i am excited about the opportunity",
    "significant improvements", "a wide range of", "commitment to excellence",
]

ASSISTANT_TELLS = {
    "chatgpt": [
        "delve", "tapestry", "underscore", "multifaceted", "navigate the",
        "in today's fast-paced", "it's not just", "a testament to",
        "elevate", "game-changer", "landscape", "realm", "furthermore",
        "moreover", "in conclusion", "let's dive", "boasts",
    ],
    "claude": [
        "i should note", "it's worth noting", "that said", "to be clear",
        "genuinely", "the honest answer", "worth flagging", "nuance",
        "i want to be careful", "meaningfully", "substantive", "rather than",
    ],
    "gemini": [
        "here's a breakdown", "key takeaways", "in essence", "absolutely",
        "let's break it down", "the bottom line", "crucially", "notably",
        "dive deeper", "at its core", "think of it as", "in short",
    ],
}

CONNECTIVE_OPENERS = [
    "moreover", "furthermore", "additionally", "consequently", "indeed",
    "nevertheless", "nonetheless", "in addition", "in conclusion", "ultimately",
    "importantly", "notably", "crucially", "overall", "in essence",
]

HEDGES = [
    "may", "might", "could", "perhaps", "generally", "often", "typically",
    "arguably", "somewhat", "relatively", "fairly", "largely", "usually",
    "tends to", "seems to", "appears to",
]

FIRST_PERSON = ["i", "i'm", "i've", "i'd", "i'll", "me", "my", "mine",
                "we", "we're", "we've", "our", "ours", "us"]

BE_VERBS = ["is", "are", "was", "were", "be", "been", "being", "am"]

IRREGULAR_PARTICIPLES = [
    "done", "made", "given", "taken", "seen", "known", "shown", "written",
    "built", "held", "led", "found", "kept", "brought", "sent", "put",
    "run", "drawn", "chosen", "driven", "grown", "left", "lost", "meant",
]

UNITS = r"(?:%|percent|hours?|minutes?|seconds?|days?|weeks?|months?|years?|" \
        r"ms|kb|mb|gb|tb|k|m|bn|x|people|students?|papers?|times?|\$|€|£)"

ANTITHESIS_PATTERNS = [
    (r"\bnot only\b[^.!?]{0,80}?\bbut\b", "not only ... but"),
    (r"\bnot just\b[^.!?]{0,80}?\bbut\b", "not just ... but"),
    (r"\bit(?:'s| is) not\b[^.!?]{0,60}?\bit(?:'s| is)\b", "it's not X, it's Y"),
    (r"\bisn't\b[^.!?]{0,60}?\bit(?:'s| is)\b", "isn't X, it's Y"),
    (r"\bless about\b[^.!?]{0,60}?\bmore about\b", "less about ... more about"),
    (r"\brather than\b[^.!?]{0,40}?\b,\s*(?:it|this|they)\b", "rather than X, Y"),
]

# "adjective, adjective, and adjective" / "noun, noun, and noun"
TRICOLON = re.compile(r"\b(\w{4,}), (\w{4,}),? and (\w{4,})\b", re.I)

COMMON_WORDS = set("""
the be to of and a in that have i it for not on with he as you do at this but his
by from they we say her she or an will my one all would there their what so up out
if about who get which go me when make can like time no just him know take people
into year your good some could them see other than then now look only come its over
think also back after use two how our work first well way even new want because any
these give day most us is are was were been has had did does am then very much more
than such only own same too can will should must may might shall each few many while
where why how all both between through during before after above below under again
further once here there when both each such nor own same so than too very
""".split())


# --------------------------------------------------------------------------
# Text handling
# --------------------------------------------------------------------------

def read(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    # Strip markdown scaffolding that would skew word counts, but remember it:
    # heading and bullet injection into flowing prose is itself a tell.
    return text


def paragraphs(text):
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return [p for p in parts if len(words(p)) >= 12]


def sentences(text):
    flat = re.sub(r"\s+", " ", text).strip()
    flat = re.sub(r"\b(Mr|Mrs|Ms|Dr|Prof|St|vs|etc|e\.g|i\.e|Inc|Ltd)\.",
                  r"\1<DOT>", flat)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'“])", flat)
    out = []
    for p in parts:
        p = p.replace("<DOT>", ".").strip()
        if len(words(p)) >= 2:
            out.append(p)
    return out


def words(text):
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-]*", text)


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def sd(xs):
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def per_k(count, n_words):
    return round(1000.0 * count / n_words, 2) if n_words else 0.0


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------

def count_spans(text_low, spans):
    hits = {}
    for s in spans:
        n = len(re.findall(r"\b" + re.escape(s), text_low))
        if n:
            hits[s] = n
    return hits


def specificity(text):
    """Concrete referents per 100 words, plus sentences with none at all."""
    sents = sentences(text)
    numerals = len(re.findall(r"\b\d[\d,.]*\b", text))
    units = len(re.findall(r"\b\d[\d,.]*\s*" + UNITS, text, re.I))
    years = len(re.findall(r"\b(?:19|20)\d{2}\b", text))
    # proper nouns: capitalized tokens that are not sentence-initial
    propers = 0
    for s in sents:
        toks = words(s)
        propers += sum(1 for t in toks[1:] if t[0].isupper() and t.lower() not in COMMON_WORDS)
    n = len(words(text))
    concrete_total = numerals + propers + years + units
    empty = 0
    for s in sents:
        toks = words(s)
        has = bool(re.search(r"\d", s)) or any(
            t[0].isupper() and t.lower() not in COMMON_WORDS for t in toks[1:]
        )
        if not has:
            empty += 1
    return {
        "per_100_words": round(100.0 * concrete_total / n, 2) if n else 0.0,
        "numerals": numerals,
        "proper_nouns": propers,
        "sentences_without_specifics": empty,
        "sentences_total": len(sents),
        "empty_share": round(empty / len(sents), 3) if sents else 0.0,
    }


def tells(text, assistant):
    low = text.lower()
    # A span listed both generically and under the named assistant is one tell,
    # not two — dedupe before counting or the paragraph scores double-charge it.
    profile = [s for s in ASSISTANT_TELLS.get(assistant, []) if s not in GENERIC_TELLS]
    generic = count_spans(low, GENERIC_TELLS)
    specific = count_spans(low, profile)
    anti = []
    for pat, label in ANTITHESIS_PATTERNS:
        for _ in re.finditer(pat, low):
            anti.append(label)
    tri = [" / ".join(m.groups()) for m in TRICOLON.finditer(text)]
    openers = 0
    for p in paragraphs(text):
        first = p.lstrip("#-*0123456789. ").lower()
        if any(first.startswith(c) for c in CONNECTIVE_OPENERS):
            openers += 1
    structure = len(re.findall(r"^\s*(?:#{1,6}\s|[-*•]\s|\d+\.\s)", text, re.M))
    n = len(words(text))
    total = sum(generic.values()) + sum(specific.values()) + len(anti) + len(tri)
    return {
        "generic": generic,
        "assistant_specific": specific,
        "antithesis": anti,
        "tricolons": tri,
        "connective_openers": openers,
        "structure_lines": structure,
        "total": total,
        "per_1k_words": per_k(total, n),
    }


def profile(text, assistant="generic", label=""):
    sents = sentences(text)
    lens = [len(words(s)) for s in sents]
    paras = paragraphs(text)
    plens = [len(words(p)) for p in paras]
    toks = [t.lower() for t in words(text)]
    n = len(toks)
    if not n:
        return None

    contractions = len(re.findall(r"\b\w+['’](?:s|t|re|ve|ll|d|m)\b", text))
    passive = 0
    for i, t in enumerate(toks[:-1]):
        if t in BE_VERBS:
            nxt = toks[i + 1]
            if nxt.endswith("ed") or nxt in IRREGULAR_PARTICIPLES:
                passive += 1

    return {
        "label": label,
        "words": n,
        "sentences": len(sents),
        "paragraphs": len(paras),
        "sent_len_mean": round(mean(lens), 2),
        "sent_len_sd": round(sd(lens), 2),
        "pct_sents_under_8": round(100.0 * sum(1 for x in lens if x < 8) / len(lens), 1) if lens else 0.0,
        "pct_sents_over_30": round(100.0 * sum(1 for x in lens if x > 30) / len(lens), 1) if lens else 0.0,
        "para_len_mean": round(mean(plens), 1),
        "para_len_sd": round(sd(plens), 1),
        "contractions_per_1k": per_k(contractions, n),
        "commas_per_1k": per_k(text.count(","), n),
        "semicolons_per_1k": per_k(text.count(";"), n),
        "colons_per_1k": per_k(text.count(":"), n),
        "em_dashes_per_1k": per_k(text.count("—") + len(re.findall(r"\s--\s", text)), n),
        "parens_per_1k": per_k(text.count("("), n),
        "long_words_per_1k": per_k(sum(1 for t in toks if len(t) >= 10), n),
        "uncommon_rate": round(sum(1 for t in toks if t not in COMMON_WORDS) / n, 3),
        "first_person_per_1k": per_k(sum(1 for t in toks if t in FIRST_PERSON), n),
        "hedges_per_1k": per_k(sum(1 for t in toks if t in HEDGES), n),
        "passive_per_1k": per_k(passive, n),
        "specificity": specificity(text),
        "tells": tells(text, assistant),
    }


# --------------------------------------------------------------------------
# Comparison
# --------------------------------------------------------------------------

# metric -> (weight, tolerance as a fraction of the baseline value)
VOICE_METRICS = {
    "sent_len_sd":          (3.0, 0.20),
    "sent_len_mean":        (2.0, 0.15),
    "contractions_per_1k":  (2.5, 0.35),
    "pct_sents_under_8":    (1.5, 0.40),
    "pct_sents_over_30":    (1.0, 0.50),
    "em_dashes_per_1k":     (1.0, 0.60),
    "semicolons_per_1k":    (0.8, 0.60),
    "commas_per_1k":        (1.0, 0.25),
    "first_person_per_1k":  (1.5, 0.30),
    "hedges_per_1k":        (1.0, 0.40),
    "passive_per_1k":       (1.2, 0.40),
    "long_words_per_1k":    (1.2, 0.30),
    "para_len_sd":          (1.0, 0.40),
}


def drift(base, other):
    """Per-metric signed change, and a 0-100 voice-match score."""
    rows = []
    penalty = 0.0
    weight_total = 0.0
    outside = 0
    for metric, (w, tol) in VOICE_METRICS.items():
        b, o = base[metric], other[metric]
        denom = max(abs(b), 1e-6)
        rel = (o - b) / denom
        over = max(0.0, abs(rel) - tol)
        # Saturate a single wild metric at 1.0 so one blown measure cannot
        # swamp the score, but also cannot be shrugged off.
        penalty += w * min(over, 1.0)
        weight_total += w
        outside += 1 if over > 0 else 0
        rows.append({
            "metric": metric,
            "baseline": b,
            "value": o,
            "change_pct": round(100.0 * rel, 1),
            "outside_tolerance": over > 0,
        })
    rows.sort(key=lambda r: -abs(r["change_pct"]))
    # A document does not have to blow every metric to read as someone else's.
    # Saturating ~55% of the weighted total is already a different writer, so
    # that is treated as 0 rather than requiring all thirteen to max out.
    score = max(0, round(100 * (1 - min(1.0, penalty / (0.55 * weight_total)))))
    return {
        "score": score,
        "metrics_outside_tolerance": outside,
        "metrics_total": len(VOICE_METRICS),
        "metrics": rows,
    }


def paragraph_report(draft_text, base, assistant, top):
    """Rank the draft's paragraphs by how little they sound like the author.

    Per-paragraph statistics are noisy, so this deliberately uses only the
    signals that survive small samples: tells, specificity, contraction
    absence, and sentence lengths that sit outside the author's own range.
    """
    lo = max(3.0, base["sent_len_mean"] - 1.3 * max(base["sent_len_sd"], 1.0))
    hi = base["sent_len_mean"] + 1.3 * max(base["sent_len_sd"], 1.0)
    out = []
    for i, p in enumerate(paragraphs(draft_text), 1):
        pm = profile(p, assistant, "para %d" % i)
        if not pm:
            continue
        reasons = []
        points = 0.0

        t = pm["tells"]
        for span, n in list(t["generic"].items()) + list(t["assistant_specific"].items()):
            reasons.append('phrase "%s"%s' % (span, " x%d" % n if n > 1 else ""))
            points += 1.4 * n
        for a in set(t["antithesis"]):
            reasons.append("antithesis frame: %s" % a)
            points += 1.2
        for tri in t["tricolons"][:2]:
            reasons.append("tricolon: %s" % tri)
            points += 1.0

        sp = pm["specificity"]
        if sp["sentences_total"] and sp["empty_share"] >= 0.6:
            reasons.append("%d of %d sentences carry no name, number or date"
                           % (sp["sentences_without_specifics"], sp["sentences_total"]))
            points += 2.2
        if sp["per_100_words"] < 0.5 * base["specificity"]["per_100_words"]:
            reasons.append("specifics %.1f/100w vs your usual %.1f"
                           % (sp["per_100_words"], base["specificity"]["per_100_words"]))
            points += 1.5

        if base["contractions_per_1k"] >= 4 and pm["contractions_per_1k"] == 0 and pm["words"] >= 40:
            reasons.append("no contractions; you average %.1f/1k words"
                           % base["contractions_per_1k"])
            points += 1.2

        lens = [len(words(s)) for s in sentences(p)]
        if len(lens) >= 3:
            inside = sum(1 for x in lens if lo <= x <= hi)
            if inside == len(lens) and sd(lens) < 0.5 * max(base["sent_len_sd"], 1.0):
                reasons.append("%d sentences, all %d-%d words; you normally run %d-%d"
                               % (len(lens), min(lens), max(lens),
                                  max(1, int(lo)), int(hi)))
                points += 1.8

        out.append({
            "index": i,
            "words": pm["words"],
            "drift_points": round(points, 1),
            "reasons": reasons,
            "text": p,
        })
    out.sort(key=lambda r: -r["drift_points"])
    return [r for r in out if r["drift_points"] > 0][:top]


# --------------------------------------------------------------------------

def load_many(paths, assistant, label):
    text = "\n\n".join(read(p) for p in paths)
    return text, profile(text, assistant, label)


def human(report):
    L = []
    b = report["baseline"]
    L.append("VOICEPRINT  (baseline: %d words across %d file(s))"
             % (b["words"], report["baseline_files"]))
    L.append("  sentences %.1f words avg, sd %.1f   contractions %.1f/1k   "
             "specifics %.1f/100w"
             % (b["sent_len_mean"], b["sent_len_sd"], b["contractions_per_1k"],
                b["specificity"]["per_100_words"]))
    if report.get("baseline_warning"):
        L.append("  ! %s" % report["baseline_warning"])

    if report.get("ai_drift"):
        L.append("")
        d = report["ai_drift"]
        L.append("WHAT THE %s EDIT CHANGED  (voice match %d/100, %d of %d measures "
                 "outside your range)"
                 % (report["assistant"].upper(), d["score"],
                    d["metrics_outside_tolerance"], d["metrics_total"]))
        for r in report["ai_drift"]["metrics"][:8]:
            flag = " *" if r["outside_tolerance"] else ""
            L.append("  %-22s %8s -> %-8s %+7.1f%%%s"
                     % (r["metric"], r["baseline"], r["value"], r["change_pct"], flag))

    if report.get("draft_drift"):
        L.append("")
        dd = report["draft_drift"]
        L.append("YOUR CURRENT DRAFT  (voice match %d/100, %d of %d measures "
                 "outside your range)"
                 % (dd["score"], dd["metrics_outside_tolerance"], dd["metrics_total"]))
        for r in report["draft_drift"]["metrics"][:8]:
            flag = " *" if r["outside_tolerance"] else ""
            L.append("  %-22s %8s -> %-8s %+7.1f%%%s"
                     % (r["metric"], r["baseline"], r["value"], r["change_pct"], flag))
        d = report["draft"]
        L.append("  tells: %d (%.1f/1k)   sentences with no specifics: %d of %d"
                 % (d["tells"]["total"], d["tells"]["per_1k_words"],
                    d["specificity"]["sentences_without_specifics"],
                    d["specificity"]["sentences_total"]))

    if report.get("paragraphs"):
        L.append("")
        L.append("PARAGRAPHS THAT DO NOT SOUND LIKE YOU")
        for p in report["paragraphs"]:
            L.append("")
            L.append("  [%d]  %.1f pts, %d words" % (p["index"], p["drift_points"], p["words"]))
            for r in p["reasons"]:
                L.append("        - %s" % r)
            L.append("        \"%s...\"" % " ".join(p["text"].split()[:14]))
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", nargs="+", required=True,
                    help="files the author definitely wrote (pre-AI original, other samples)")
    ap.add_argument("--ai", nargs="*", default=[], help="the AI-edited version")
    ap.add_argument("--draft", nargs="*", default=[], help="the current working draft")
    ap.add_argument("--assistant", default="generic",
                    choices=["claude", "chatgpt", "gemini", "generic"])
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    base_text, base = load_many(args.baseline, args.assistant, "baseline")
    if base is None or base["words"] < 400:
        sys.stderr.write(
            "error: need at least 400 words of the author's own writing "
            "(got %d). No baseline, no rewrite.\n" % (base["words"] if base else 0))
        return 2

    report = {
        "assistant": args.assistant,
        "baseline_files": len(args.baseline),
        "baseline": base,
        "profiles_are_provisional": True,
    }
    if base["words"] < 800:
        report["baseline_warning"] = (
            "baseline is %d words; under 800 the fingerprint is weak, "
            "treat the score as directional" % base["words"])
    if base["tells"]["per_1k_words"] > 6:
        report["baseline_warning"] = (
            "the baseline itself scores %.1f tells/1k words - if these samples "
            "were AI-assisted the fingerprint is unreliable"
            % base["tells"]["per_1k_words"])

    if args.ai:
        ai_text, ai = load_many(args.ai, args.assistant, "ai")
        report["ai"] = ai
        report["ai_drift"] = drift(base, ai)

    if args.draft:
        draft_text, dr = load_many(args.draft, args.assistant, "draft")
        report["draft"] = dr
        report["draft_drift"] = drift(base, dr)
        report["paragraphs"] = paragraph_report(draft_text, base, args.assistant, args.top)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(human(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
