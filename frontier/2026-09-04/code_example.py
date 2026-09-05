"""Compiling a spec into a local function, with no ML libraries.

Implements the shape of Compile by Training (arXiv:2609.04199): the spec is never
run directly. Teachers synthesize examples from it, a small local artifact is
fitted to those, and the teachers then leave the picture. The artifact here is
induced extraction rules rather than a LoRA adapter, so it is all standard
library, and both effects the paper reports show up: more pairs help with
diminishing returns, and a 2:1 teacher blend beats the cheap teacher alone. The
compiler never sees ground truth -- only what the teachers said.

Run: python3 code_example.py   (CHEAP_ONLY = True compiles from the weak teacher
alone, and the induced rule follows it off a cliff)
"""

import re

# --- knobs: edit these ---------------------------------------------------
CHEAP_ONLY = False
TRAIN_SIZES = (60, 240, 960)
COMPILES = 15             # independent compiles per size, then averaged
HELD_OUT = 300
CHEAP_ERROR = 0.68        # the weak teacher's systematic failure rate
STRONG_ERROR = 0.05
CHEAP_SHARE = 2 / 3       # the paper's 2:1 cheap-to-strong mix
REMOTE_COST = 0.0012      # dollars per request if the big model stays in the path
TEACHER_COST = 0.0009     # dollars per synthesized pair, paid once

FIELDS = ("number", "street", "city", "state", "zip")
STREETS = ["Oak St", "Maple Ave", "Third Blvd", "Elm Rd", "Pine Way"]
CITIES = ["Springfield", "Fairview", "Riverton", "Ashland"]
STATES = ["IL", "OR", "TX", "OH"]

def lcg(seed):
    """Seeded draws. Takes the high bits -- an LCG's low bits are badly patterned."""
    s = seed
    def nxt():
        nonlocal s
        s = (s * 1664525 + 1013904223) % (2 ** 32)
        return s >> 12
    return nxt

def make_case(rand):
    truth = {"number": str(100 + rand() % 900),
             "street": STREETS[rand() % len(STREETS)],
             "city": CITIES[rand() % len(CITIES)],
             "state": STATES[rand() % len(STATES)],
             "zip": str(10000 + rand() % 89999)}
    raw = "  %s   %s , %s ,  %s   %s " % (
        truth["number"], truth["street"].lower(), truth["city"].upper(),
        truth["state"].lower(), truth["zip"])
    return raw, truth

def seg(raw, i):
    parts = [p.strip() for p in raw.split(",")]
    return parts[i] if i < len(parts) else ""


# Each field gets a correct rule and a plausible near-miss. The near-miss is what
# a weak teacher teaches.
CANDIDATES = {
    "number": [lambda r: (re.match(r"\s*(\d+)", r) or [None, ""])[1], lambda r: seg(r, 0)],
    "street": [lambda r: " ".join(seg(r, 0).split()[1:]).title(),
               lambda r: " ".join(seg(r, 0).split()[1:])],
    "city":   [lambda r: seg(r, 1).title(), lambda r: seg(r, 1)],
    "state":  [lambda r: (seg(r, 2).split() or [""])[0].upper(),
               lambda r: (seg(r, 2).split() or [""])[0]],
    "zip":    [lambda r: (re.search(r"(\d{5})\s*$", r) or [None, ""])[1], lambda r: seg(r, 2)],
}

def teacher(truth, error_rate, rand):
    """A weak teacher fails systematically, not randomly: it skips normalizing."""
    out = dict(truth)
    if rand() % 1000 < error_rate * 1000:
        out["street"] = out["street"].lower()
        out["city"] = out["city"].upper()
    return out


def build_pairs(n, rand, cheap_only):
    pairs = []
    for _ in range(n):
        raw, truth = make_case(rand)
        cheap = cheap_only or (rand() % 1000) < CHEAP_SHARE * 1000
        pairs.append((raw, teacher(truth, CHEAP_ERROR if cheap else STRONG_ERROR, rand)))
    return pairs


def compile_spec(pairs):
    """The compiler: per field, keep whichever rule best matches the teachers."""
    chosen = {}
    for field in FIELDS:
        best, best_hits = None, -1
        for rule in CANDIDATES[field]:
            hits = sum(1 for raw, labels in pairs if rule(raw) == labels[field])
            if hits > best_hits:
                best, best_hits = rule, hits
        chosen[field] = best
    return chosen


def validates(rec):
    """The local guard at the call site. It decides when to fall back."""
    return bool(rec["number"].isdigit() and len(rec["zip"]) == 5
                and len(rec["state"]) == 2 and rec["state"].isupper())


def evaluate(artifact, rand):
    """Scored against TRUTH, never against the teachers."""
    right = fallbacks = 0
    for _ in range(HELD_OUT):
        raw, truth = make_case(rand)
        got = {f: artifact[f](raw) for f in FIELDS}
        if not validates(got):
            fallbacks += 1
            continue
        right += sum(got[f] == truth[f] for f in FIELDS) / len(FIELDS)
    return right / HELD_OUT, fallbacks / HELD_OUT


def measure(n, cheap_only):
    runs = [evaluate(compile_spec(build_pairs(n, lcg(1000 + k * 7919), cheap_only)), lcg(777))
            for k in range(COMPILES)]
    return sum(a for a, _ in runs) / COMPILES, sum(f for _, f in runs) / COMPILES


def main():
    print("Compiling one spec: messy address -> five fields")
    print("  teacher mix: %s, averaged over %d compiles\n"
          % ("cheap only" if CHEAP_ONLY else "2:1 cheap to strong", COMPILES))
    print("  %8s %11s %11s %13s" % ("pairs", "accuracy", "fallback", "compile cost"))
    for n in TRAIN_SIZES:
        acc, fb = measure(n, CHEAP_ONLY)
        print("  %8d %11.3f %10.1f%% %12s" % (n, acc, 100 * fb, "$%.2f" % (n * TEACHER_COST)))

    mixed = measure(960, False)[0]
    cheap = measure(960, True)[0]
    print("\n  teacher mix at 960 pairs")
    print("    2:1 cheap to strong   %.3f" % mixed)
    print("    cheap teacher alone   %.3f" % cheap)
    print("    the blend is worth    %+.3f" % (mixed - cheap))

    build = 960 * TEACHER_COST
    print("\n  economics once compiled")
    print("    build cost, paid once   $%.2f\n    remote per request      $%.4f"
          % (build, REMOTE_COST))
    print("    break-even at          %6d requests" % round(build / REMOTE_COST))


if __name__ == "__main__":
    main()
