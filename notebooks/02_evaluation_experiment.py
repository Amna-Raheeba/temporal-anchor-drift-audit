"""Evaluation experiment: the headline run, in notebook form.

Runs the full evaluation (anchor choice + summarisation drift) and
prints the headline numbers. Uses the canonical configuration, so the
output matches results/evaluation.json.

Run: python notebooks/02_evaluation_experiment.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from temporal_anchor.evaluate import run_evaluation


def main():
    results = run_evaluation()
    print(
        "Cases: %d | expressions: %d"
        % (results["n_cases"], results["n_expressions"])
    )
    for stage, title in (("part1", "Original notes"), ("part2", "After summarisation")):
        print("")
        print(title)
        for strategy, m in sorted(results[stage].items()):
            print(
                "  %-16s MAE %6.2f days | exact %.3f | catastrophic %.3f"
                % (strategy, m["mae_days"], m["exact_rate"], m["catastrophic_rate"])
            )
    print("")
    print("Drift rates:", results["drift_rates"])
    print("String-match baseline F1: %.3f" % results["baselines"]["f1"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
