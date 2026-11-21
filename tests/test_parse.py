import pytest

from temporal_anchor.parse import parse_expression


@pytest.mark.parametrize(
    "text,offset,cue",
    [
        ("post-op day 2", 2, "procedure"),
        ("post-op day 0", 0, "procedure"),
        ("hospital day 4", 3, "admission"),
        ("3 days after admission", 3, "admission"),
        ("1 day after admission", 1, "admission"),
        ("5 days after discharge", 5, "discharge"),
        ("the day before surgery", -1, "procedure"),
        ("2 days before surgery", -2, "procedure"),
        ("3 days ago", -3, "note"),
        ("1 day ago", -1, "note"),
        ("in 10 days", 10, "note"),
        ("in 2 weeks", 14, "note"),
        ("4 days later", 4, "previous"),
        ("3 days into the course", 3, None),
        ("2 days after leaving", 2, None),
        ("3 days prior", -3, None),
        ("the day before", -1, None),
        ("2 days before", -2, None),
    ],
)
def test_offsets_and_cues(text, offset, cue):
    parsed = parse_expression(text)
    assert parsed["offset_days"] == offset
    assert parsed["cue"] == cue
    assert parsed["weekday"] is None
    assert parsed["day_count"] is False


@pytest.mark.parametrize(
    "text,weekday,cue",
    [
        ("since last Tuesday", 1, "note"),
        ("since last Monday", 0, "note"),
        ("since Friday", 4, None),
    ],
)
def test_weekday_forms(text, weekday, cue):
    parsed = parse_expression(text)
    assert parsed["weekday"] == weekday
    assert parsed["cue"] == cue


@pytest.mark.parametrize("text", ["on day 3", "day 5 of the course"])
def test_day_count_forms(text):
    parsed = parse_expression(text)
    assert parsed["day_count"] is True
    assert parsed["cue"] is None


def test_day_count_value():
    assert parse_expression("on day 3")["offset_days"] == 3
    assert parse_expression("day 5 of the course")["offset_days"] == 5


def test_unparseable_raises():
    with pytest.raises(ValueError):
        parse_expression("at some point in the past")
