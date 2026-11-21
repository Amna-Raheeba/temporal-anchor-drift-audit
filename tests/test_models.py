from datetime import date

from temporal_anchor.models import (
    ANCHORS,
    Case,
    Expression,
    most_recent_weekday,
    parse_iso,
    shift,
    to_iso,
)


def test_parse_and_format_iso_round_trip():
    assert parse_iso("2025-03-04") == date(2025, 3, 4)
    assert to_iso(date(2025, 3, 4)) == "2025-03-04"


def test_shift():
    assert shift(date(2025, 1, 31), 1) == date(2025, 2, 1)
    assert shift(date(2025, 3, 1), -1) == date(2025, 2, 28)


def test_most_recent_weekday_basic():
    # 2025-01-06 is a Monday; most recent Tuesday strictly before it is
    # 2024-12-31.
    assert most_recent_weekday(date(2025, 1, 6), 1) == date(2024, 12, 31)


def test_most_recent_weekday_same_day_promotes_a_week():
    # Asked on a Tuesday about "last Tuesday": a full week back.
    assert most_recent_weekday(date(2025, 1, 7), 1) == date(2024, 12, 31)


def test_case_round_trip():
    case = Case(
        case_id="case-x",
        anchors=dict((name, "2025-01-0%d" % (i + 1)) for i, name in enumerate(ANCHORS)),
        expressions=[
            Expression("e1", "fever onset", "history", "ago", "3 days ago", "note", "2025-01-01")
        ],
    )
    clone = Case.from_dict(case.to_dict())
    assert clone.case_id == case.case_id
    assert clone.anchors == case.anchors
    assert clone.expressions[0].text == "3 days ago"
    assert clone.anchor_date("admission") == date(2025, 1, 1)


def test_note_text_groups_by_section():
    case = Case(
        case_id="case-x",
        anchors=dict((name, "2025-01-01") for name in ANCHORS),
        expressions=[
            Expression("e1", "fever onset", "history", "ago", "3 days ago", "note", "2025-01-01"),
            Expression("e2", "wound check", "operative", "post_op_day", "post-op day 2", "procedure", "2025-01-03"),
        ],
    )
    text = case.note_text()
    assert "[history]" in text
    assert "[operative]" in text
    assert "post-op day 2" in text
