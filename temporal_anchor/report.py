"""Render evaluation results as CSV and Markdown."""

from .models import ANCHORS
from .resolve import STRATEGIES


def render_csv(results):
    lines = ["stage,strategy,n,mae_days,median_abs_error_days,exact_rate,catastrophic_rate,max_abs_error_days"]
    for stage in ("part1", "part2"):
        for strategy in STRATEGIES:
            m = results[stage][strategy]
            lines.append(
                "%s,%s,%d,%.4f,%.4f,%.4f,%.4f,%d"
                % (
                    stage,
                    strategy,
                    m["n"],
                    m["mae_days"],
                    m["median_abs_error_days"],
                    m["exact_rate"],
                    m["catastrophic_rate"],
                    m["max_abs_error_days"],
                )
            )
    return "\n".join(lines) + "\n"


def _strategy_table(results, stage):
    lines = [
        "| Strategy | n | MAE (days) | Exact | Catastrophic (>7d) | Max error |",
        "|---|---|---|---|---|---|",
    ]
    for strategy in STRATEGIES:
        m = results[stage][strategy]
        lines.append(
            "| %s | %d | %.2f | %.3f | %.3f | %d |"
            % (
                strategy,
                m["n"],
                m["mae_days"],
                m["exact_rate"],
                m["catastrophic_rate"],
                m["max_abs_error_days"],
            )
        )
    return lines


def _confusion_table(matrix):
    columns = ANCHORS + ["previous"]
    lines = [
        "| True anchor \\ assumed | %s |" % " | ".join(columns),
        "|---|%s|" % "|".join(["---"] * len(columns)),
    ]
    for true in columns:
        row = matrix.get(true, {})
        lines.append(
            "| %s | %s |"
            % (true, " | ".join(str(row.get(assumed, 0)) for assumed in columns))
        )
    return lines


def render_summary(results):
    lines = []
    lines.append("# Evaluation summary")
    lines.append("")
    lines.append(
        "Seeded synthetic notes: %d cases, %d expressions. All clinical "
        "content is synthetic; no real patient data." % (results["n_cases"], results["n_expressions"])
    )
    lines.append("")
    lines.append("## Part 1 -- anchor choice on the original notes")
    lines.append("")
    lines.extend(_strategy_table(results, "part1"))
    lines.append("")
    lines.append("Mean absolute error of the note-date baseline, by true anchor:")
    lines.append("")
    for anchor, value in results["part1_per_anchor_mae_note_date"].items():
        lines.append("- %s: %.2f days" % (anchor, value))
    lines.append("")
    lines.append("Anchor confusion -- section-aware strategy:")
    lines.append("")
    lines.extend(_confusion_table(results["confusion_section_aware"]))
    lines.append("")
    lines.append("## Part 2 -- after one summarisation pass")
    lines.append("")
    lines.extend(_strategy_table(results, "part2"))
    lines.append("")
    lines.append("Drift inflicted by the summariser (share of expressions):")
    lines.append("")
    for name, rate in sorted(results["drift_rates"].items()):
        lines.append("- %s: %.3f (%d)" % (name, rate, results["drift_counts"][name]))
    lines.append("")
    lines.append("Naive drift detectors, scored against the known drift labels:")
    lines.append("")
    b = results["baselines"]
    lines.append(
        "- string-match check: precision %.3f, recall %.3f, F1 %.3f for "
        "harmful drift (rebased / value-changed / dropped)"
        % (b["precision"], b["recall"], b["f1"])
    )
    lines.append(
        "- date-presence check: passes %.3f of summaries despite the "
        "drift above" % b["date_presence_pass_rate"]
    )
    lines.append("")
    return "\n".join(lines)


def render_headline(results):
    p1 = results["part1"]
    p2 = results["part2"]
    rates = results["drift_rates"]
    b = results["baselines"]
    lines = []
    lines.append("# Headline results")
    lines.append("")
    lines.append(
        "Anchor choice audited as an error source on %d seeded synthetic "
        "multi-anchor clinical notes (%d relative temporal expressions), "
        "plus one seeded summarisation pass over the same notes."
        % (results["n_cases"], results["n_expressions"])
    )
    lines.append("")
    lines.append(
        "- The standard single-anchor (note-date) normalizer reconstructs "
        "the timeline with mean absolute error **%.2f days** and a "
        "catastrophic-error rate (>7 days) of **%.1f%%** -- its error is "
        "concentrated exactly on the expressions written against other "
        "anchors (procedure-anchored: %.2f days MAE)."
        % (
            p1["note_date"]["mae_days"],
            100 * p1["note_date"]["catastrophic_rate"],
            results["part1_per_anchor_mae_note_date"].get("procedure", 0.0),
        )
    )
    lines.append(
        "- A section-aware heuristic (trust explicit cues, else a "
        "per-section default) cuts MAE to **%.2f days** and catastrophic "
        "errors to **%.1f%%**; the oracle that knows each expression's "
        "true anchor sits at %.2f days, so most of the remaining gap is "
        "genuinely ambiguous cue-less expressions, not heuristic sloppiness."
        % (
            p1["section_aware"]["mae_days"],
            100 * p1["section_aware"]["catastrophic_rate"],
            p1["oracle"]["mae_days"],
        )
    )
    lines.append(
        "- One summarisation pass drops **%.1f%%** of expressions off the "
        "timeline entirely, strips the anchor cue from %.1f%%, rebases "
        "%.1f%% onto the previous event, and perturbs the stated offset "
        "of %.1f%%."
        % (
            100 * rates["dropped"],
            100 * rates["cue_stripped"],
            100 * rates["rebased"],
            100 * rates["value_changed"],
        )
    )
    lines.append(
        "- After summarisation, section-aware MAE rises to **%.2f days** "
        "and even the oracle -- now reading only what the summary "
        "literally asserts -- is stuck at %.2f days: rebased and "
        "value-changed expressions assert wrong dates that no resolver "
        "can repair from the text."
        % (p2["section_aware"]["mae_days"], p2["oracle"]["mae_days"])
    )
    lines.append(
        "- The naive checks pipelines actually run do not catch this: a "
        "string-match check detects harmful drift at F1 **%.3f**, and a "
        "date-presence check passes **%.1f%%** of the drifted summaries."
        % (b["f1"], 100 * b["date_presence_pass_rate"])
    )
    lines.append("")
    lines.append(
        "Caveat: all notes are synthetic and seeded, generated from known "
        "timelines; the summariser's drift rates are declared parameters, "
        "not measurements of any real summariser. The audit measures what "
        "anchor assumptions and each drift type cost, in days, under "
        "those declared conditions."
    )
    lines.append("")
    return "\n".join(lines)


def render_case_report(case, rows):
    """A per-case Markdown audit table for one strategy's rows."""
    lines = []
    lines.append("## Case %s" % case.case_id)
    lines.append("")
    lines.append(
        "Anchors: %s"
        % ", ".join(
            "%s = %s" % (name, case.anchors[name]) for name in ANCHORS
        )
    )
    lines.append("")
    lines.append("| Expression | Event | True anchor | True date | Assumed | Predicted | Error (d) |")
    lines.append("|---|---|---|---|---|---|---|")
    for row in rows:
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %+d |"
            % (
                row["text"],
                row["event"],
                row["true_anchor"],
                row["true_date"],
                row["assumed_anchor"],
                row["predicted_date"],
                row["error_days"],
            )
        )
    lines.append("")
    return "\n".join(lines)
