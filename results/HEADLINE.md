# Headline results

Anchor choice audited as an error source on 120 seeded synthetic multi-anchor clinical notes (778 relative temporal expressions), plus one seeded summarisation pass over the same notes.

- The standard single-anchor (note-date) normalizer reconstructs the timeline with mean absolute error **6.11 days** and a catastrophic-error rate (>7 days) of **37.9%** -- its error is concentrated exactly on the expressions written against other anchors (procedure-anchored: 7.41 days MAE).
- A section-aware heuristic (trust explicit cues, else a per-section default) cuts MAE to **0.32 days** and catastrophic errors to **1.8%**; the oracle that knows each expression's true anchor sits at 0.00 days, so most of the remaining gap is genuinely ambiguous cue-less expressions, not heuristic sloppiness.
- One summarisation pass drops **11.8%** of expressions off the timeline entirely, strips the anchor cue from 19.3%, rebases 16.7% onto the previous event, and perturbs the stated offset of 11.2%.
- After summarisation, section-aware MAE rises to **2.13 days** and even the oracle -- now reading only what the summary literally asserts -- is stuck at 2.45 days: rebased and value-changed expressions assert wrong dates that no resolver can repair from the text.
- The naive checks pipelines actually run do not catch this: a string-match check detects harmful drift at F1 **0.797**, and a date-presence check passes **100.0%** of the drifted summaries.

Caveat: all notes are synthetic and seeded, generated from known timelines; the summariser's drift rates are declared parameters, not measurements of any real summariser. The audit measures what anchor assumptions and each drift type cost, in days, under those declared conditions.
