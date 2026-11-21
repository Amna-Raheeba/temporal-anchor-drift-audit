"""Command line interface: python -m temporal_anchor <command>.

Commands:
- demo: audit one seeded case under every strategy and print it.
- evaluate: run the full evaluation, print the headline, and write the
  result files into results/.
- audit: print the per-strategy table for a seeded batch of cases.
"""

import argparse
import os
import sys

from .audit import audit_cases, summarize_rows
from .evaluate import DEFAULT_CONFIG, run_evaluation, save_results
from .generate import generate_cases
from .report import render_case_report
from .resolve import STRATEGIES


def _demo(_args):
    case = generate_cases(1, DEFAULT_CONFIG["seed"])[0]
    print("Note text:")
    print(case.note_text())
    print("")
    from .audit import audit_expression

    for strategy in STRATEGIES:
        rows = []
        for expr in case.expressions:
            rows.extend(
                r
                for r in audit_expression(case, expr, strategies=[strategy])
            )
        print("Strategy: %s" % strategy)
        print(render_case_report(case, rows))
    return 0


def _evaluate(_args):
    results = run_evaluation()
    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"
    )
    save_results(results, os.path.normpath(out_dir))
    p1 = results["part1"]
    print(
        "Evaluated %d cases, %d expressions."
        % (results["n_cases"], results["n_expressions"])
    )
    print(
        "Part 1 MAE (days): note_date %.2f | section_aware %.2f | oracle %.2f"
        % (
            p1["note_date"]["mae_days"],
            p1["section_aware"]["mae_days"],
            p1["oracle"]["mae_days"],
        )
    )
    print(
        "Part 2 MAE (days): note_date %.2f | section_aware %.2f | oracle %.2f"
        % (
            results["part2"]["note_date"]["mae_days"],
            results["part2"]["section_aware"]["mae_days"],
            results["part2"]["oracle"]["mae_days"],
        )
    )
    print("Results written to results/.")
    return 0


def _audit(args):
    cases = generate_cases(args.cases, DEFAULT_CONFIG["seed"])
    summary = summarize_rows(audit_cases(cases))
    print("%-16s %5s %10s %8s %12s" % ("strategy", "n", "MAE days", "exact", "catastrophic"))
    for strategy in STRATEGIES:
        m = summary[strategy]
        print(
            "%-16s %5d %10.2f %8.3f %12.3f"
            % (strategy, m["n"], m["mae_days"], m["exact_rate"], m["catastrophic_rate"])
        )
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="temporal_anchor",
        description="Audit temporal anchor assumptions and summarisation drift in clinical notes.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="Audit one seeded case under every strategy.")
    sub.add_parser("evaluate", help="Run the full evaluation and write results/.")
    audit_parser = sub.add_parser("audit", help="Per-strategy table for a seeded batch.")
    audit_parser.add_argument("--cases", type=int, default=20)
    args = parser.parse_args(argv)
    if args.command == "demo":
        return _demo(args)
    if args.command == "evaluate":
        return _evaluate(args)
    if args.command == "audit":
        return _audit(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
