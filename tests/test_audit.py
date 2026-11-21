import pytest

from temporal_anchor.audit import (
    audit_cases,
    audit_expression,
    audit_summaries,
    confusion_matrix,
    per_anchor_mae,
    summarize_rows,
)
from temporal_anchor.generate import generate_cases
from temporal_anchor.models import ANCHORS
from temporal_anchor.resolve import STRATEGIES
from temporal_anchor.summarize import summarize_cases


@pytest.fixture(scope="module")
def cases():
    return generate_cases(25, 99)


@pytest.fixture(scope="module")
def rows(cases):
    return audit_cases(cases)


def test_row_per_expression_per_strategy(rows, cases):
    total = sum(len(c.expressions) for c in cases)
    assert len(rows) == total * len(STRATEGIES)


def test_oracle_has_zero_error(rows):
    oracle = [r for r in rows if r["strategy"] == "oracle"]
    assert oracle
    assert all(r["error_days"] == 0 for r in oracle)


def test_fixed_strategies_assume_their_anchor(rows):
    for row in rows:
        if row["strategy"] == "note_date":
            assert row["assumed_anchor"] == "note"
        if row["strategy"] == "admission":
            assert row["assumed_anchor"] == "admission"


def test_summarize_rows_shape(rows):
    summary = summarize_rows(rows)
    assert sorted(summary.keys()) == sorted(STRATEGIES)
    for metrics in summary.values():
        assert 0.0 <= metrics["exact_rate"] <= 1.0
        assert 0.0 <= metrics["catastrophic_rate"] <= 1.0
        assert metrics["mae_days"] >= 0.0


def test_note_date_worse_than_section_aware(rows):
    summary = summarize_rows(rows)
    assert summary["note_date"]["mae_days"] > summary["section_aware"]["mae_days"]
    assert (
        summary["note_date"]["catastrophic_rate"]
        > summary["section_aware"]["catastrophic_rate"]
    )


def test_confusion_matrix_counts(rows):
    matrix = confusion_matrix(rows, "section_aware")
    total = sum(sum(cols.values()) for cols in matrix.values())
    n_expr = sum(1 for r in rows if r["strategy"] == "section_aware")
    assert total == n_expr


def test_confusion_oracle_is_diagonal(rows):
    matrix = confusion_matrix(rows, "oracle")
    for true in ANCHORS:
        for assumed in ANCHORS:
            if assumed != true:
                assert matrix[true][assumed] == 0


def test_confusion_note_date_single_column(rows):
    matrix = confusion_matrix(rows, "note_date")
    for true in ANCHORS:
        for assumed in ANCHORS:
            if assumed != "note":
                assert matrix[true][assumed] == 0


def test_per_anchor_mae_note_date(rows):
    split = per_anchor_mae(rows, "note_date")
    # Expressions actually written against the note date resolve exactly
    # under the note-date baseline; the others carry the anchor gaps.
    assert split["note"] == 0.0
    assert split["admission"] > 0.0
    assert split["procedure"] > 0.0


def test_audit_expression_single_strategy(cases):
    case = cases[0]
    expr = case.expressions[0]
    out = audit_expression(case, expr, strategies=["oracle"])
    assert len(out) == 1
    assert out[0]["error_days"] == 0


def test_audit_summaries_scores_against_original_truth(cases):
    triples = summarize_cases(cases, 5)
    summary_rows = audit_summaries(triples)
    assert summary_rows
    # After summarisation even the oracle (reading the summary
    # literally) can no longer be perfect: rebased and value-changed
    # expressions assert wrong dates.
    oracle = [r for r in summary_rows if r["strategy"] == "oracle"]
    assert any(r["error_days"] != 0 for r in oracle)
    # ...but ground truth recorded on rows is the ORIGINAL anchor.
    originals = dict(
        ((c.case_id, e.expr_id), e.true_anchor)
        for c in cases
        for e in c.expressions
    )
    for row in summary_rows:
        assert row["true_anchor"] == originals[(row["case_id"], row["expr_id"])]
