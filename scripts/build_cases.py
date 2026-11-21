"""Build the sample case files under data/.

Writes data/cases.json (40 seeded cases) and data/demo_case.json (the
first case on its own), using the canonical evaluation seed.

Run: python scripts/build_cases.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from temporal_anchor.evaluate import DEFAULT_CONFIG
from temporal_anchor.generate import generate_cases


def main():
    root = os.path.join(os.path.dirname(__file__), "..")
    data_dir = os.path.normpath(os.path.join(root, "data"))
    os.makedirs(data_dir, exist_ok=True)
    cases = generate_cases(40, DEFAULT_CONFIG["seed"])
    with open(os.path.join(data_dir, "cases.json"), "w") as handle:
        json.dump([c.to_dict() for c in cases], handle, indent=2)
    with open(os.path.join(data_dir, "demo_case.json"), "w") as handle:
        json.dump(cases[0].to_dict(), handle, indent=2)
    print("Wrote %d cases to data/cases.json" % len(cases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
