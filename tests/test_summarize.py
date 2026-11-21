import random

import pytest

from temporal_anchor.generate import generate_cases
from temporal_anchor.models import DRIFT_TYPES
from temporal_anchor.summarize import (
    DEFAULT_SUMMARY_RATES,
    drift_counts,
    summarize_case,
    summarize_cases,
)

NO_DRIFT = {"drop": 0.0, "cue_strip": 0.0, "rebase": 0.0, "value_change": 0.0}


@pytest.fixture(scope="module")
def cases():
    return generate_cases(20, 3)


def test_no_drift_preserves_everything(cases):
    case = cases[0]
    summary, drift = summarize_case(case, random.Random(1), rates=NO_DRIFT)
    assert len(summary) == len(case.expressions)
    assert all(kind == "preserved" for kind in drift.values())
    assert [e.text for e in summary] == [e.text for e in case.expressions]


def test_all_drop_empties_summary(cases):
    rates = {"drop": 1.0, "cue_strip": 0.0, "rebase": 0.0, "value_change": 0.0}
    summary, drift = summarize_case(cases[0], random.Random(1), rates=rates)
    assert summary == []
    assert all(kind == "dropped" for kind in drift.values())


def test_drift_labels_cover_all_expressions(cases):
    triples = summarize_cases(cases, 11)
    for case, _summary, drift in triples:
        assert sorted(drift.keys()) == sorted(e.expr_id for e in case.expressions)
        assert all(kind in DRIFT_TYPES for kind in drift.values())


def test_summary_expressions_keep_true_date(cases):
    triples = summarize_cases(cases, 11)
    for case, summary, _drift in triples:
        originals = dict((e.expr_id, e) for e in case.expressions)
        for expr in summary:
            assert expr.true_date == originals[expr.expr_id].true_date


def test_rebased_expressions_point_at_previous(cases):
    triples = summarize_cases(cases, 11)
    found = 0
    for _case, summary, drift in triples:
        for expr in summary:
            if drift[expr.expr_id] == "rebased":
                found += 1
                assert expr.true_anchor == "previous"
                assert expr.text.endswith("later")
    assert found > 0


def test_cue_stripped_expressions_lose_their_cue(cases):
    from temporal_anchor.parse import parse_expression

    triples = summarize_cases(cases, 11)
    found = 0
    for _case, summary, drift in triples:
        for expr in summary:
            if drift[expr.expr_id] == "cue_stripped":
                found += 1
                assert parse_expression(expr.text)["cue"] is None
    assert found > 0


def test_first_expression_never_rebased(cases):
    triples = summarize_cases(cases, 23)
    for case, _summary, drift in triples:
        first_id = case.expressions[0].expr_id
        assert drift[first_id] != "rebased"


def test_deterministic(cases):
    first = summarize_cases(cases, 11)
    second = summarize_cases(cases, 11)
    for (c1, s1, d1), (_c2, s2, d2) in zip(first, second):
        assert d1 == d2
        assert [e.text for e in s1] == [e.text for e in s2]


def test_drift_counts_aggregate(cases):
    triples = summarize_cases(cases, 11)
    counts = drift_counts([drift for _c, _s, drift in triples])
    total = sum(len(c.expressions) for c in cases)
    assert sum(counts.values()) == total
    assert sorted(counts.keys()) == sorted(DRIFT_TYPES)


def test_default_rates_are_probabilities():
    assert all(0.0 <= v <= 1.0 for v in DEFAULT_SUMMARY_RATES.values())
    assert sum(DEFAULT_SUMMARY_RATES.values()) < 1.0
