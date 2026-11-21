import pytest

from temporal_anchor.resolve import STRATEGIES, choose_anchor, resolve
from temporal_anchor.parse import parse_expression

ANCHORS = {
    "admission": "2025-01-01",  # Wednesday
    "procedure": "2025-01-04",  # Saturday
    "discharge": "2025-01-11",  # Saturday
    "note": "2025-01-13",  # Monday
}


def test_note_date_baseline_ignores_cue():
    predicted, assumed = resolve("post-op day 2", "operative", ANCHORS, "note_date")
    assert assumed == "note"
    assert predicted == "2025-01-15"


def test_procedure_strategy():
    predicted, assumed = resolve("post-op day 2", "operative", ANCHORS, "procedure")
    assert assumed == "procedure"
    assert predicted == "2025-01-06"


def test_section_aware_trusts_cue():
    predicted, assumed = resolve("3 days after admission", "history", ANCHORS, "section_aware")
    assert assumed == "admission"
    assert predicted == "2025-01-04"


def test_section_aware_falls_back_to_section_default():
    predicted, assumed = resolve("on day 3", "operative", ANCHORS, "section_aware")
    assert assumed == "procedure"
    assert predicted == "2025-01-07"  # procedure + 3 (post-op convention)


def test_day_count_admission_convention():
    predicted, assumed = resolve("on day 3", "hospital_course", ANCHORS, "section_aware")
    assert assumed == "admission"
    assert predicted == "2025-01-03"  # admission + (3 - 1): day 1 is admission day


def test_oracle_uses_true_anchor():
    predicted, assumed = resolve(
        "12 days after discharge", "discharge_plan", ANCHORS, "oracle", oracle_anchor="discharge"
    )
    assert assumed == "discharge"
    assert predicted == "2025-01-23"


def test_oracle_requires_anchor():
    with pytest.raises(ValueError):
        resolve("3 days ago", "history", ANCHORS, "oracle")


def test_weekday_resolution_against_note():
    # Note date is Monday 2025-01-13; "since last Tuesday" is 2025-01-07.
    predicted, _assumed = resolve("since last Tuesday", "history", ANCHORS, "note_date")
    assert predicted == "2025-01-07"


def test_weekday_resolution_against_procedure():
    # Procedure is Saturday 2025-01-04; most recent Tuesday is 2024-12-31.
    predicted, _assumed = resolve("since last Tuesday", "history", ANCHORS, "procedure")
    assert predicted == "2024-12-31"


def test_rebased_expression_uses_previous_date():
    predicted, assumed = resolve(
        "4 days later", "hospital_course", ANCHORS, "oracle",
        oracle_anchor="previous", prev_date="2025-01-05",
    )
    assert assumed == "previous"
    assert predicted == "2025-01-09"


def test_rebased_expression_needs_previous_date():
    with pytest.raises(ValueError):
        resolve("4 days later", "hospital_course", ANCHORS, "oracle", oracle_anchor="previous")


def test_fixed_strategy_ignores_rebase_frame():
    predicted, assumed = resolve(
        "4 days later", "hospital_course", ANCHORS, "note_date", prev_date="2025-01-05"
    )
    assert assumed == "note"
    assert predicted == "2025-01-17"


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_choose_anchor_known_strategies(strategy):
    parsed = parse_expression("3 days ago")
    anchor = choose_anchor(strategy, parsed, "history", oracle_anchor="note")
    assert anchor in ("admission", "procedure", "discharge", "note")


def test_unknown_strategy_raises():
    with pytest.raises(ValueError):
        resolve("3 days ago", "history", ANCHORS, "magic")


def test_generated_case_oracle_is_exact():
    from temporal_anchor.generate import generate_cases

    for case in generate_cases(10, 7):
        for expr in case.expressions:
            predicted, _ = resolve(
                expr.text, expr.section, case.anchors, "oracle",
                oracle_anchor=expr.true_anchor,
            )
            assert predicted == expr.true_date
