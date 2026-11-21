"""Example: load the demo case and audit it with the note-date baseline
vs the section-aware strategy.

Run: python examples/run_audit.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from temporal_anchor.audit import audit_expression, summarize_rows
from temporal_anchor.models import Case


def main():
    path = os.path.join(os.path.dirname(__file__), "demo_note.json")
    with open(path) as handle:
        case = Case.from_dict(json.load(handle))
    print(case.note_text())
    print("")
    for strategy in ("note_date", "section_aware"):
        rows = []
        for expr in case.expressions:
            rows.extend(audit_expression(case, expr, strategies=[strategy]))
        metrics = summarize_rows(rows)[strategy]
        print(
            "%s: MAE %.2f days, exact %.2f, catastrophic %.2f"
            % (
                strategy,
                metrics["mae_days"],
                metrics["exact_rate"],
                metrics["catastrophic_rate"],
            )
        )
        for row in rows:
            if row["error_days"] != 0:
                print(
                    "  off by %+d days: '%s' (true anchor %s, assumed %s)"
                    % (
                        row["error_days"],
                        row["text"],
                        row["true_anchor"],
                        row["assumed_anchor"],
                    )
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
