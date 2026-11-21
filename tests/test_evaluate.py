import pytest

from temporal_anchor.evaluate import DRIFT_KEYS, check_drift, run_evaluation


@pytest.fixture(scope="module")
def results():
    return run_evaluation({"n_cases": 40})


def test_evaluation_shape(results):
    assert results["n_cases"] == 40
    assert results["n_expressions"] > 0
    for stage in ("part1", "part2"):
        for strategy in ("note_date", "section_aware", "oracle"):
            assert strategy in results[stage]


def test_part1_headline_relationships(results):
    p1 = results["part1"]
    assert p1["oracle"]["mae_days"] == 0.0
    assert p1["note_date"]["mae_days"] > 3.0
    assert p1["section_aware"]["mae_days"] < p1["note_date"]["mae_days"]
    assert p1["note_date"]["catastrophic_rate"] > 0.2


def test_part2_drift_registered(results):
    total = sum(results["drift_counts"].values())
    assert total == results["n_expressions"]
    assert results["drift_counts"]["dropped"] > 0
    assert results["drift_counts"]["rebased"] > 0
    # Fewer expressions survive to be scored in part 2.
    assert results["part2"]["oracle"]["n"] < results["part1"]["oracle"]["n"]
    # The summary-reading oracle is no longer perfect.
    assert results["part2"]["oracle"]["mae_days"] > 0.0


def test_check_drift_clean(results):
    ok, problems = check_drift(results, results)
    assert ok
    assert problems == []


def test_check_drift_detects_change(results):
    import copy

    tampered = copy.deepcopy(results)
    tampered["part1"]["note_date"]["mae_days"] += 1.0
    ok, problems = check_drift(results, tampered)
    assert not ok
    assert any(key == "part1.note_date.mae_days" for key, _s, _f, _d in problems)


def test_drift_keys_are_real_paths(results):
    from temporal_anchor.evaluate import _flatten

    flat = _flatten(results)
    for key in DRIFT_KEYS:
        assert key in flat, key
