"""What your coding agent request is missing, and what that costs.

Two pieces. The first is a linter you can lift: given a request, say which of the
named parts it contains. The second prices the gap RealSWE (arXiv:2608.27831)
measured, by running the same penalties over two populations of requests -- the
curated ones benchmarks are built from, and the ones people actually type.

Only the PENALTIES are measured. BASE_RESOLUTION is a knob: set it to whatever
your own agent scores on complete requests, because the interesting number here
is the gap, not the level.

Run: python3 code_example.py

Change ADD_TO_EVERY to see what a habit is worth across a whole corpus.
"""

# --- knobs: edit these ---------------------------------------------------
ADD_TO_EVERY = "desired_behavior"    # or "repro_and_env", or None
BASE_RESOLUTION = 57.6               # your agent's rate on complete requests
FEATURE_SHARE = 0.25                 # how much of your work is features, not bugs

# Measured in the paper: points of resolution lost when the part is absent.
PENALTIES = {"desired_behavior": 8.0,   # 7.1-8.9, significant on all 7 models
             "motivation": 3.4,          # feature requests only
             "repro": 1.0,               # repro + env together were ~1.8
             "env": 0.8,
             "style": 0.0}               # formality, mood, hedging, person

# How often each part is actually present. Benchmarks are curated; people are not.
# 88% of real requests are problem-statement-only, against 7% of benchmark ones,
# and only 5% of real requests state the desired behavior at all.
CORPORA = {
    "curated benchmark issues": {"desired_behavior": 0.66, "motivation": 0.60,
                                 "repro": 0.75, "env": 0.60},
    "what people actually type": {"desired_behavior": 0.05, "motivation": 0.06,
                                  "repro": 0.08, "env": 0.06},
}

CUES = {
    "desired_behavior": ("when this is fixed", "should ", "expected", "we want",
                         "so that", "instead of"),
    "motivation": ("because", "we need", "in order to", "the reason"),
    "repro": ("steps to reproduce", "to reproduce", "run ", "$ ", "traceback"),
    "env": ("version", "python 3", "on macos", "on linux", "os:", "browser"),
}


def detect_fields(request):
    """Which named parts does this request contain? Lift this one.

    Deliberately crude. Its job is to make you notice before you hit enter,
    not to grade your writing, so a false alarm costs you one glance.
    """
    body = request.lower()
    return {field: any(cue in body for cue in cues) for field, cues in CUES.items()}


def missing_desired_behavior(request):
    return not detect_fields(request)["desired_behavior"]


def expected_resolution(presence, feature_share=FEATURE_SHARE):
    """Start from the complete-request rate, subtract what is missing."""
    lost = 0.0
    lost += (1 - presence["desired_behavior"]) * PENALTIES["desired_behavior"]
    lost += (1 - presence["repro"]) * PENALTIES["repro"]
    lost += (1 - presence["env"]) * PENALTIES["env"]
    # Motivation only bites on feature requests, which are a slice of the work.
    lost += (1 - presence["motivation"]) * PENALTIES["motivation"] * feature_share
    return BASE_RESOLUTION - lost


def with_habit(presence, habit):
    """What if you always wrote one of these, on every request?"""
    out = dict(presence)
    if habit == "desired_behavior":
        out["desired_behavior"] = 1.0
    elif habit == "repro_and_env":
        out["repro"] = 1.0
        out["env"] = 1.0
    return out


SAMPLES = [
    ("the importer crashes on rows where the date column is empty",
     "a real request, and the most common shape there is"),
    ("The importer crashes on empty dates. When this is fixed, an empty date "
     "should be treated as unknown and the row kept, because a supplier sends "
     "partial files on purpose.",
     "the same request with two sentences added"),
    ("Importer raises ValueError on empty date. Steps to reproduce: run "
     "`import.py fixtures/partial.csv`. Python 3.12 on macOS.",
     "a careful bug report, missing the one part that pays"),
]


def main():
    print("1. What the linter sees\n")
    for text, label in SAMPLES:
        found = detect_fields(text)
        have = ", ".join(f for f, ok in found.items() if ok) or "problem statement only"
        flag = "  <-- no desired behavior" if missing_desired_behavior(text) else ""
        print("  %s" % label)
        print("     %s%s\n" % (have, flag))

    print("2. What that costs across a whole corpus\n")
    print("  %-28s %10s %12s" % ("corpus", "expected", "vs curated"))
    curated = expected_resolution(CORPORA["curated benchmark issues"])
    for name, presence in CORPORA.items():
        rate = expected_resolution(presence)
        delta = "" if rate == curated else "%+.1f pp" % (rate - curated)
        print("  %-28s %9.1f%% %12s" % (name, rate, delta))
    real = expected_resolution(CORPORA["what people actually type"])
    print("\n  The paper measured this gap at 6.4 points on average, across seven")
    print("  models, on the same underlying bugs and the same correct patches.")

    print("\n3. What one habit is worth (ADD_TO_EVERY = %s)\n" % ADD_TO_EVERY)
    for habit in ("desired_behavior", "repro_and_env"):
        improved = expected_resolution(
            with_habit(CORPORA["what people actually type"], habit))
        mark = "  <-- the knob you are turning" if habit == ADD_TO_EVERY else ""
        print("  always write %-16s %5.1f%%   %+.1f pp%s"
              % (habit, improved, improved - real, mark))

    chosen = expected_resolution(
        with_habit(CORPORA["what people actually type"], ADD_TO_EVERY))
    print("\n  Writing the desired behavior on every request recovers most of the")
    print("  gap. Filling in the fields your bug template asks for recovers a")
    print("  fraction of it, and takes considerably longer to type.")
    print("\n  your corpus, with the habit: %.1f%% (from %.1f%%)" % (chosen, real))


if __name__ == "__main__":
    main()
