# Changelog

## 0.1.0 — 2026-11-21

- Initial release.
- Seeded generator of synthetic multi-anchor clinical notes (admission,
  procedure, discharge and note anchors; nine relative-expression kinds).
- Surface parser for relative temporal expressions (offsets, weekday
  references, anchor cues, bare day-count forms).
- Six anchor-resolution strategies: four fixed single-anchor baselines,
  a section-aware heuristic, and an oracle reference.
- Audit engine: mean absolute timeline error in days, exact-match and
  catastrophic-error (>7 days) rates, per-anchor error splits, and the
  anchor-confusion matrix.
- Summarisation stage: a seeded summariser that drops, cue-strips,
  rebases and value-perturbs expressions at declared rates; surviving
  expressions are re-audited against the original ground truth.
- Naive baselines scored as drift detectors: string-match check and
  date-presence check.
- Headline evaluation on 120 seeded cases (778 expressions), CLI,
  Streamlit dashboard, and a reproduce script with a headline-drift
  guard.
