# Evaluation summary

Seeded synthetic notes: 120 cases, 778 expressions. All clinical content is synthetic; no real patient data.

## Part 1 -- anchor choice on the original notes

| Strategy | n | MAE (days) | Exact | Catastrophic (>7d) | Max error |
|---|---|---|---|---|---|
| note_date | 778 | 6.11 | 0.355 | 0.379 | 23 |
| admission | 778 | 7.23 | 0.293 | 0.445 | 28 |
| procedure | 778 | 4.53 | 0.316 | 0.248 | 21 |
| discharge | 778 | 5.81 | 0.247 | 0.355 | 22 |
| section_aware | 778 | 0.32 | 0.959 | 0.018 | 18 |
| oracle | 778 | 0.00 | 1.000 | 0.000 | 0 |

Mean absolute error of the note-date baseline, by true anchor:

- admission: 13.10 days
- discharge: 0.92 days
- note: 0.00 days
- procedure: 7.41 days

Anchor confusion -- section-aware strategy:

| True anchor \ assumed | admission | procedure | discharge | note | previous |
|---|---|---|---|---|---|
| admission | 226 | 0 | 0 | 0 | 0 |
| procedure | 32 | 202 | 0 | 0 | 0 |
| discharge | 0 | 0 | 66 | 0 | 0 |
| note | 0 | 0 | 0 | 252 | 0 |
| previous | 0 | 0 | 0 | 0 | 0 |

## Part 2 -- after one summarisation pass

| Strategy | n | MAE (days) | Exact | Catastrophic (>7d) | Max error |
|---|---|---|---|---|---|
| note_date | 686 | 7.24 | 0.260 | 0.434 | 36 |
| admission | 686 | 7.54 | 0.222 | 0.427 | 53 |
| procedure | 686 | 5.17 | 0.277 | 0.267 | 45 |
| discharge | 686 | 6.86 | 0.197 | 0.405 | 37 |
| section_aware | 686 | 2.13 | 0.638 | 0.101 | 36 |
| oracle | 686 | 2.45 | 0.695 | 0.093 | 53 |

Drift inflicted by the summariser (share of expressions):

- cue_stripped: 0.193 (150)
- dropped: 0.118 (92)
- preserved: 0.410 (319)
- rebased: 0.167 (130)
- value_changed: 0.112 (87)

Naive drift detectors, scored against the known drift labels:

- string-match check: precision 0.675, recall 0.974, F1 0.797 for harmful drift (rebased / value-changed / dropped)
- date-presence check: passes 1.000 of summaries despite the drift above
