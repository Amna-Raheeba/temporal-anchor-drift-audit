import pytest

from temporal_anchor.generate import generate_cases
from temporal_anchor.models import ANCHORS, parse_iso
from temporal_anchor.parse import parse_expression


@pytest.fixture(scope="module")
def cases():
    return generate_cases(30, 42)


def test_deterministic(cases):
    again = generate_cases(30, 42)
    assert [c.to_dict() for c in cases] == [c.to_dict() for c in again]


def test_case_count_and_ids(cases):
    assert len(cases) == 30
    assert cases[0].case_id == "case-001"
    assert cases[-1].case_id == "case-030"


def test_anchor_ordering(cases):
    for case in cases:
        admission = case.anchor_date("admission")
        procedure = case.anchor_date("procedure")
        discharge = case.anchor_date("discharge")
        note = case.anchor_date("note")
        assert admission < procedure < discharge <= note


def test_all_anchors_present(cases):
    for case in cases:
        assert sorted(case.anchors.keys()) == sorted(ANCHORS)


def test_expression_count_bounds(cases):
    for case in cases:
        assert 5 <= len(case.expressions) <= 8


def test_every_expression_parses_and_true_date_matches(cases):
    # Ground-truth consistency: resolving the parsed offset against the
    # recorded true anchor must reproduce the recorded true date.
    from temporal_anchor.resolve import resolve

    for case in cases:
        for expr in case.expressions:
            parse_expression(expr.text)  # must not raise
            predicted, assumed = resolve(
                expr.text,
                expr.section,
                case.anchors,
                "oracle",
                oracle_anchor=expr.true_anchor,
            )
            assert assumed == expr.true_anchor
            assert predicted == expr.true_date, (case.case_id, expr.text)


def test_mixed_anchors_present(cases):
    seen = set()
    for case in cases:
        for expr in case.expressions:
            seen.add(expr.true_anchor)
    assert seen == set(ANCHORS)


def test_events_unique_within_case(cases):
    for case in cases:
        events = [e.event for e in case.expressions]
        assert len(events) == len(set(events))


def test_true_dates_are_iso(cases):
    for case in cases:
        for expr in case.expressions:
            parse_iso(expr.true_date)  # must not raise
