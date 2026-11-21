"""The audit engine: score resolver strategies against ground truth.

For every expression in every case, each strategy's predicted date is
compared with the date the event actually happened on. The audit
reports, per strategy: mean absolute error in days, exact-match rate,
the catastrophic-error rate (errors over seven days -- the size that
moves a follow-up, a medication window, or a medico-legal fact), and
the anchor-confusion matrix: which anchor the strategy assumed, against
the anchor the expression was actually written against.
"""

from .models import ANCHORS, parse_iso
from .resolve import STRATEGIES, resolve

CATASTROPHIC_DAYS = 7


def audit_expression(case, expr, strategies=None, prev_date=None):
    """Resolve one expression under each strategy; return result rows."""
    strategies = strategies or STRATEGIES
    rows = []
    true_day = parse_iso(expr.true_date)
    for strategy in strategies:
        oracle_anchor = expr.true_anchor if strategy == "oracle" else None
        predicted, assumed = resolve(
            expr.text,
            expr.section,
            case.anchors,
            strategy,
            oracle_anchor=oracle_anchor,
            prev_date=prev_date,
        )
        error = (parse_iso(predicted) - true_day).days
        rows.append(
            {
                "case_id": case.case_id,
                "expr_id": expr.expr_id,
                "event": expr.event,
                "kind": expr.kind,
                "text": expr.text,
                "true_anchor": expr.true_anchor,
                "true_date": expr.true_date,
                "strategy": strategy,
                "assumed_anchor": assumed,
                "predicted_date": predicted,
                "error_days": error,
            }
        )
    return rows


def audit_cases(cases, strategies=None):
    """Audit every expression of every case. Returns a list of rows."""
    rows = []
    for case in cases:
        for expr in case.expressions:
            rows.extend(audit_expression(case, expr, strategies=strategies))
    return rows


def _median(values):
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def audit_summaries(cases_with_summaries, strategies=None):
    """Audit summary expressions against the original ground truth.

    ``cases_with_summaries`` is a list of (case, summary, drift) triples
    from summarize.summarize_cases. Each surviving summary expression is
    resolved and scored against the date the event actually happened
    on; dropped expressions are absent here and counted separately via
    the drift maps. The "previous event" a rebased expression refers to
    is the previous expression in the original note order.
    """
    rows = []
    for case, summary, _drift in cases_with_summaries:
        prev_by_id = {}
        previous = None
        for expr in case.expressions:
            prev_by_id[expr.expr_id] = previous
            previous = expr.true_date
        originals = dict((e.expr_id, e) for e in case.expressions)
        for expr in summary:
            stage_rows = audit_expression(
                case,
                expr,
                strategies=strategies,
                prev_date=prev_by_id[expr.expr_id],
            )
            for row in stage_rows:
                # Ground truth stays the original anchor, not the
                # literal anchor the summary text asserts.
                row["true_anchor"] = originals[expr.expr_id].true_anchor
                row["kind"] = originals[expr.expr_id].kind
            rows.extend(stage_rows)
    return rows


def summarize_rows(rows):
    """Aggregate audit rows into per-strategy metrics."""
    by_strategy = {}
    for row in rows:
        by_strategy.setdefault(row["strategy"], []).append(row)
    summary = {}
    for strategy, group in by_strategy.items():
        errors = [abs(r["error_days"]) for r in group]
        n = len(group)
        summary[strategy] = {
            "n": n,
            "mae_days": sum(errors) / float(n),
            "median_abs_error_days": _median(errors),
            "exact_rate": sum(1 for e in errors if e == 0) / float(n),
            "catastrophic_rate": sum(
                1 for e in errors if e > CATASTROPHIC_DAYS
            )
            / float(n),
            "max_abs_error_days": max(errors),
        }
    return summary


def confusion_matrix(rows, strategy):
    """Anchor-confusion matrix for one strategy.

    Rows are the anchor the expression was written against; columns are
    the anchor the strategy assumed. Returns {true: {assumed: count}}.
    """
    matrix = dict(
        (true, dict((assumed, 0) for assumed in ANCHORS + ["previous"]))
        for true in ANCHORS + ["previous"]
    )
    for row in rows:
        if row["strategy"] != strategy:
            continue
        matrix[row["true_anchor"]][row["assumed_anchor"]] += 1
    return matrix


def per_anchor_mae(rows, strategy):
    """Mean absolute error of one strategy, split by true anchor."""
    groups = {}
    for row in rows:
        if row["strategy"] != strategy:
            continue
        groups.setdefault(row["true_anchor"], []).append(abs(row["error_days"]))
    return dict(
        (anchor, sum(values) / float(len(values)))
        for anchor, values in sorted(groups.items())
    )
