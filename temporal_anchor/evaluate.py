"""The headline experiment.

Part 1 -- anchor choice as an error source. Seeded multi-anchor notes
are resolved by every strategy; the audit reports mean absolute
timeline error in days, catastrophic-error rate, and the anchor-
confusion matrix, against the single-anchor (note-date) baseline that
standard normalizers effectively use.

Part 2 -- summarisation drift. The same notes are passed through the
seeded summariser; surviving expressions are re-audited, dropped ones
counted as timeline loss, and the naive string-match / date-presence
checks are scored as drift detectors against the known drift labels.
"""

import json
import os

from .audit import (
    audit_cases,
    audit_summaries,
    confusion_matrix,
    per_anchor_mae,
    summarize_rows,
)
from .baselines import score_string_match
from .generate import generate_cases
from .resolve import STRATEGIES
from .summarize import DEFAULT_SUMMARY_RATES, drift_counts, summarize_cases

DEFAULT_CONFIG = {
    "seed": 20261121,
    "n_cases": 120,
    "summary_seed": 777,
}

# Aggregate keys the reproduce script guards against drift.
DRIFT_KEYS = [
    "part1.note_date.mae_days",
    "part1.section_aware.mae_days",
    "part1.oracle.mae_days",
    "part1.note_date.catastrophic_rate",
    "part1.section_aware.catastrophic_rate",
    "part2.section_aware.mae_days",
    "part2.note_date.mae_days",
    "drift_rates.dropped",
    "baselines.f1",
]

DRIFT_TOLERANCE = 1e-9


def _round_block(block):
    return dict(
        (key, round(value, 4) if isinstance(value, float) else value)
        for key, value in block.items()
    )


def run_evaluation(config=None):
    """Run the full evaluation; returns a JSON-serialisable dict."""
    config = dict(DEFAULT_CONFIG, **(config or {}))
    cases = generate_cases(config["n_cases"], config["seed"])

    # Part 1: anchor choice on the original notes.
    rows_before = audit_cases(cases)
    part1 = dict(
        (name, _round_block(metrics))
        for name, metrics in summarize_rows(rows_before).items()
    )
    confusion = dict(
        (name, confusion_matrix(rows_before, name)) for name in STRATEGIES
    )

    # Part 2: after a summarisation pass.
    triples = summarize_cases(cases, config["summary_seed"])
    rows_after = audit_summaries(triples)
    part2 = dict(
        (name, _round_block(metrics))
        for name, metrics in summarize_rows(rows_after).items()
    )
    counts = drift_counts([drift for _c, _s, drift in triples])
    total_expr = sum(counts.values())
    baselines = score_string_match(triples)

    return {
        "config": config,
        "n_cases": len(cases),
        "n_expressions": total_expr,
        "part1": part1,
        "part2": part2,
        "part1_per_anchor_mae_note_date": dict(
            (k, round(v, 4))
            for k, v in per_anchor_mae(rows_before, "note_date").items()
        ),
        "part1_per_anchor_mae_section_aware": dict(
            (k, round(v, 4))
            for k, v in per_anchor_mae(rows_before, "section_aware").items()
        ),
        "confusion_section_aware": confusion["section_aware"],
        "confusion_note_date": confusion["note_date"],
        "drift_counts": counts,
        "drift_rates": dict(
            (name, round(count / float(total_expr), 4))
            for name, count in counts.items()
        ),
        "summary_rates": DEFAULT_SUMMARY_RATES,
        "baselines": dict(
            (k, round(v, 4) if isinstance(v, float) else v)
            for k, v in baselines.items()
        ),
    }


def _flatten(results):
    flat = {}

    def walk(prefix, node):
        if isinstance(node, dict):
            for key, value in node.items():
                walk("%s.%s" % (prefix, key) if prefix else key, value)
        else:
            flat[prefix] = node

    walk("", results)
    return flat


def check_drift(stored, fresh):
    """Compare stored vs fresh headline aggregates.

    Returns (ok, problems) where problems are (key, stored, fresh, diff)
    tuples for every guarded key outside tolerance.
    """
    flat_stored = _flatten(stored)
    flat_fresh = _flatten(fresh)
    problems = []
    for key in DRIFT_KEYS:
        before = flat_stored.get(key)
        after = flat_fresh.get(key)
        if before is None or after is None:
            problems.append((key, before, after, None))
            continue
        diff = abs(float(before) - float(after))
        if diff > DRIFT_TOLERANCE:
            problems.append((key, before, after, diff))
    return (not problems), problems


def save_results(results, out_dir):
    """Write evaluation.json / .csv / evaluation_summary.md / HEADLINE.md."""
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "evaluation.json"), "w") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
    from .report import render_csv, render_headline, render_summary

    with open(os.path.join(out_dir, "evaluation.csv"), "w") as handle:
        handle.write(render_csv(results))
    with open(os.path.join(out_dir, "evaluation_summary.md"), "w") as handle:
        handle.write(render_summary(results))
    with open(os.path.join(out_dir, "HEADLINE.md"), "w") as handle:
        handle.write(render_headline(results))
