"""Finding the gap is the hard half. This measures both halves separately.

Runs two detectors over the same tasks: "does anything look missing?" -- a
stand-in for asking a model to introspect, the 9.6% path in the paper -- and a
structural check against the fields the task type requires, which needs no
model at all. Then it prices the difference the way the paper's oracle does.

Run: python3 code_example.py

Add a field to REQUIRED and watch the false-alarm rate move with it.
"""

import random

SEED = 3
TRIALS = 400

# What a task of each kind cannot be done without.
REQUIRED = {
    "bugfix":  ["repro", "expected", "scope"],
    "feature": ["motivation", "acceptance", "out_of_scope"],
}
# How each field shows up in prose. Crude on purpose: the point is that a
# structural check beats introspection even when the check is this blunt.
CUES = {
    "repro":        ("steps to reproduce", "repro:", "to reproduce"),
    "expected":     ("expected", "should ", "when this is fixed"),
    "scope":        ("only", "do not touch", "limited to"),
    "motivation":   ("because", "so that", "we need"),
    "acceptance":   ("done when", "acceptance", "success looks like"),
    "out_of_scope": ("out of scope", "not in scope", "explicitly not"),
}
SENTENCE = {
    "repro":        "Steps to reproduce: open the importer and upload a partial file.",
    "expected":     "When this is fixed, the row should be kept and flagged.",
    "scope":        "Limited to the importer; do not touch the exporter.",
    "motivation":   "We need it because a supplier sends partial files on purpose.",
    "acceptance":   "Done when a partial file imports with the bad rows flagged.",
    "out_of_scope": "Out of scope: changing the file format.",
}
# The same field, written by someone who did not use the house phrasing. A
# cue-based detector cannot see these, which is where its false alarms come
# from -- and pretending otherwise would make this demo circular.
PARAPHRASE = {
    "repro":        "Upload a partial file to the importer and it falls over.",
    "expected":     "The right behavior is to keep the row and flag it.",
    "scope":        "Touch the importer, nothing else.",
    "motivation":   "Suppliers send partial files deliberately, hence the ask.",
    "acceptance":   "Call it finished once a partial file lands with flags.",
    "out_of_scope": "The file format itself stays as it is.",
}
FILLERS = (
    "The importer has been flaky since the vendor changed their export. ",
    "Several customers have mentioned it this week. It should be quick. ",
)
OFF_HOUSE = 0.22          # how often an author phrases a field their own way


def make_task(kind, rng):
    """A task with every required field, minus a random subset."""
    fields = REQUIRED[kind]
    n_missing = rng.choice([0, 1, 1, 2])
    missing = set(rng.sample(fields, n_missing))
    parts = []
    for f in fields:
        if f in missing:
            continue
        parts.append(PARAPHRASE[f] if rng.random() < OFF_HOUSE else SENTENCE[f])
    body = rng.choice(FILLERS) + " ".join(parts)
    return body, missing


def structural_gaps(body, kind):
    """The detector from the article: compare against what should be there."""
    low = body.lower()
    return {f for f in REQUIRED[kind]
            if not any(cue in low for cue in CUES[f])}


def introspective_gaps(body, kind, rng, notice=0.10):
    """A stand-in for 'does anything look missing?'.

    An absence leaves no mark in the text, so a reader skimming for problems
    finds one only occasionally -- and sometimes objects to a field that is
    present. Rates are set to the paper's order of magnitude, not fitted.
    """
    found = set()
    for f in REQUIRED[kind]:
        present = any(cue in body.lower() for cue in CUES[f])
        if not present and rng.random() < notice:
            found.add(f)
        if present and rng.random() < 0.03:      # the occasional false alarm
            found.add(f)
    return found


def main():
    rng = random.Random(SEED)
    stats = {"structural": [0, 0, 0], "introspective": [0, 0, 0]}   # hit, miss, false
    ready_before = ready_after_intro = ready_after_struct = 0

    for _ in range(TRIALS):
        kind = rng.choice(list(REQUIRED))
        body, missing = make_task(kind, rng)

        for name, found in (("structural", structural_gaps(body, kind)),
                            ("introspective", introspective_gaps(body, kind, rng))):
            stats[name][0] += len(found & missing)
            stats[name][1] += len(missing - found)
            stats[name][2] += len(found - missing)

        if not missing:
            ready_before += 1
        # A gap you located gets resolved 80.6% of the time (the paper's rate).
        for name, found, box in (
                ("i", introspective_gaps(body, kind, rng), "intro"),
                ("s", structural_gaps(body, kind), "struct")):
            closed = {f for f in (found & missing) if rng.random() < 0.806}
            if not (missing - closed):
                if box == "intro":
                    ready_after_intro += 1
                else:
                    ready_after_struct += 1

    print("%d tasks, gaps injected at random\n" % TRIALS)
    print("  %-16s %8s %8s %12s %10s"
          % ("who finds gaps", "found", "missed", "false alarms", "recall"))
    for name in ("introspective", "structural"):
        hit, miss, false = stats[name]
        rec = hit / max(hit + miss, 1)
        print("  %-16s %8d %8d %12d %9.1f%%" % (name, hit, miss, false, rec * 100))

    print("\n  Tasks implementable without guessing\n")
    for label, n in (("as written", ready_before),
                     ("after asking the model to introspect", ready_after_intro),
                     ("after the structural check", ready_after_struct)):
        print("    %-38s %5.1f%%" % (label, 100 * n / TRIALS))

    print("\n  Both rows use the same 80.6% fix rate — the model is equally good")
    print("  at resolving a gap either way. The only thing that changed is how")
    print("  many gaps reached it, which is the paper's whole point.")
    print("\n  Note the false-alarm column. The structural check has them too, and")
    print("  they are the reason to keep REQUIRED short: a detector that fires on")
    print("  tasks that were fine is one somebody switches off.")


if __name__ == "__main__":
    main()
