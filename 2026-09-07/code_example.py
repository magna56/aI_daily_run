"""What a compact tool result saves, and who pays for it.

Serializes the same SQL result four ways, prices each in tokens, and then
simulates the part that actually decides: whether the model reading it can
still answer. Position-only formats put the header at the top and nothing
else, so recovering a field means counting across the row from memory --
a task a frontier model does reliably and a small one does not.

No network, no SDK. The accuracy model is a stand-in, fitted to the per-model
spreads published in the TOON benchmark, not a measurement of your stack.

Run: python3 code_example.py

Change READER to a small model and watch which tools stop being safe.
"""

COLS = ["id", "region", "units", "revenue"]
ROWS = [[17, "EU", 412, 288000], [18, "NA", 377, 301500],
        [19, "APAC", 590, 204000], [20, "LATAM", 233, 96750]]
SCALE = 20                      # pretend it is 80 rows, not 4
READER = "small"                # "frontier" | "mid" | "small"

# Best-format-minus-worst-format spread, in accuracy points, from the TOON
# benchmark's per-model table (244 questions, six formats).
SPREAD = {"frontier": 1.6, "mid": 3.7, "small": 4.9}
# What fraction of that spread a question type exposes. 1.0 means the question
# is hard enough to show the model's full best-vs-worst format gap; field
# retrieval scored 97.8-100% in every format, so it shows almost none of it.
EXPOSURE = {"lookup": 0.05, "filter": 0.35, "aggregate": 0.7, "validate": 1.0}


def labeled(cols, rows):
    """A name on every field. Nothing depends on the reader counting."""
    return "[" + ",".join(
        "{" + ",".join('"%s":%s' % (c, _v(v)) for c, v in zip(cols, r)) + "}"
        for r in rows) + "]"


def compact(cols, rows):
    """Header once, then values. Position carries the meaning."""
    return ("cols: " + ",".join(cols) + "\n"
            + "\n".join("  " + ",".join(str(v) for v in r) for r in rows))


def csv(cols, rows):
    return ",".join(cols) + "\n" + "\n".join(",".join(str(v) for v in r) for r in rows)


def json_pretty(cols, rows):
    out = ["["]
    for r in rows:
        out.append("  {")
        out += ['    "%s": %s,' % (c, _v(v)) for c, v in zip(cols, r)]
        out.append("  },")
    out.append("]")
    return "\n".join(out)


def _v(v):
    return '"%s"' % v if isinstance(v, str) else str(v)


def tokens(text):
    """Rough, and only used to compare formats against each other."""
    return max(1, round(len(text) / 3.6))


def carries_names(fmt):
    """Does every value arrive next to its field name?"""
    return fmt in ("labeled", "json_pretty")


def accuracy(fmt, reader, intent, base=72.2):
    """Stand-in: a position-only format costs the reader's spread, scaled by
    how much the question leans on structure. Labeled formats pay nothing."""
    if carries_names(fmt):
        return base
    return base - SPREAD[reader] * EXPOSURE[intent]


FORMATS = {"labeled": labeled, "compact": compact, "csv": csv, "json_pretty": json_pretty}


def main():
    rows = ROWS * SCALE
    print("one result set: %d rows x %d columns, read by the %s model\n"
          % (len(rows), len(COLS), READER))

    print("  %-13s %9s %10s %s" % ("format", "tokens", "vs labeled", "names on every value"))
    base_tok = tokens(labeled(COLS, rows))
    sizes = {}
    for name, fn in FORMATS.items():
        t = tokens(fn(COLS, rows))
        sizes[name] = t
        print("  %-13s %9s %9s%% %s"
              % (name, "{:,}".format(t), round(100 * (t - base_tok) / base_tok),
                 "yes" if carries_names(name) else "no"))

    print("\n  Accuracy by what the agent does with the rows (percentage points)\n")
    print("  %-13s%9s%9s%10s%9s"
          % ("format", "lookup", "filter", "aggregate", "validate"))
    for name in FORMATS:
        cells = ["%9.1f" % accuracy(name, READER, i)
                 for i in ("lookup", "filter", "aggregate", "validate")]
        print("  %-13s%s" % (name, "".join(cells)))

    print("\n  Same table, read by each model, on the question type that hurts most\n")
    print("  %-12s %14s %14s %10s" % ("reader", "labeled", "compact", "cost"))
    for reader in ("frontier", "mid", "small"):
        lab = accuracy("labeled", reader, "validate")
        com = accuracy("compact", reader, "validate")
        print("  %-12s %13.1f%% %13.1f%% %9.1f pts" % (reader, lab, com, lab - com))

    saved = 100 * (base_tok - sizes["compact"]) / base_tok
    print("\n  Going compact saves %.0f%% of the tokens, for every reader equally."
          % saved)
    print("  The accuracy it costs is charged to exactly one of them.")


if __name__ == "__main__":
    main()
