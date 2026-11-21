"""Demo run: audit one seeded case under every strategy.

Run: python notebooks/01_demo_run.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from temporal_anchor.audit import audit_expression
from temporal_anchor.evaluate import DEFAULT_CONFIG
from temporal_anchor.generate import generate_cases
from temporal_anchor.report import render_case_report
from temporal_anchor.resolve import STRATEGIES


def main():
    case = generate_cases(1, DEFAULT_CONFIG["seed"])[0]
    print("Note text:")
    print(case.note_text())
    print("")
    for strategy in STRATEGIES:
        rows = []
        for expr in case.expressions:
            rows.extend(audit_expression(case, expr, strategies=[strategy]))
        print("Strategy: %s" % strategy)
        print(render_case_report(case, rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
