import json
import os

from temporal_anchor.evaluate import check_drift, run_evaluation


def test_stored_results_reproduce():
    path = os.path.join(
        os.path.dirname(__file__), "..", "results", "evaluation.json"
    )
    with open(path) as handle:
        stored = json.load(handle)
    fresh = run_evaluation()
    ok, problems = check_drift(stored, fresh)
    assert ok, problems
