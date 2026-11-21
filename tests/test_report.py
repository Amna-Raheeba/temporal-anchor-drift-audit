import pytest

from temporal_anchor.audit import audit_expression
from temporal_anchor.evaluate import run_evaluation
from temporal_anchor.generate import generate_cases
from temporal_anchor.report import (
    render_case_report,
    render_csv,
    render_headline,
    render_summary,
)


@pytest.fixture(scope="module")
def results():
    return run_evaluation({"n_cases": 30})


def test_csv_shape(results):
    csv_text = render_csv(results)
    lines = csv_text.strip().split("\n")
    assert lines[0].startswith("stage,strategy,n,")
    assert len(lines) == 1 + 2 * 6  # header + 2 stages x 6 strategies


def test_summary_mentions_key_sections(results):
    text = render_summary(results)
    assert "Part 1" in text
    assert "Part 2" in text
    assert "string-match" in text


def test_headline_uses_measured_numbers(results):
    text = render_headline(results)
    assert "%.2f" % results["part1"]["note_date"]["mae_days"] in text
    assert "Caveat" in text


def test_case_report_rows():
    case = generate_cases(1, 5)[0]
    rows = []
    for expr in case.expressions:
        rows.extend(audit_expression(case, expr, strategies=["note_date"]))
    text = render_case_report(case, rows)
    assert case.case_id in text
    assert "note" in text
    assert text.count("\n") > len(rows)
