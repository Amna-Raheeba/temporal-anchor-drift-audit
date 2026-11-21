from temporal_anchor.baselines import (
    date_presence_check,
    score_string_match,
    string_match_flags,
)
from temporal_anchor.generate import generate_cases
from temporal_anchor.summarize import summarize_cases


def test_date_presence_check():
    assert date_presence_check(["post-op day 2", "in 3 days"]) is True
    assert date_presence_check(["the patient is doing well"]) is False


def test_string_match_flags():
    flags = string_match_flags(
        ["3 days ago", "post-op day 2"], ["3 days ago", "day 2 of the course"]
    )
    assert flags == [False, True]


def test_string_match_scores_against_known_drift():
    cases = generate_cases(20, 3)
    triples = summarize_cases(cases, 11)
    scores = score_string_match(triples)
    assert 0.0 <= scores["precision"] <= 1.0
    assert 0.0 <= scores["recall"] <= 1.0
    assert 0.0 <= scores["f1"] <= 1.0
    assert scores["harmful"] > 0
    # The string-match check flags harmless cue-strips too, so its
    # precision for harmful drift must be below 1.
    assert scores["precision"] < 1.0
    # The date-presence check waves drifted summaries through.
    assert scores["date_presence_pass_rate"] > 0.9
