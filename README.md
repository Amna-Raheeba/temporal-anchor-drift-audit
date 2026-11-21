# Temporal Anchor Drift Audit

An audit of **which date a clinical note's relative time expressions
are silently resolved against** — and what summarisation does to them —
measured in days of timeline error.

## 1. What it is

Clinical notes are full of relative time expressions: "three days
ago", "post-op day 2", "since last Tuesday", "hospital day 4". Every
one of them is meaningless until a reader picks an **anchor** — the
date the expression counts from. Real notes mix anchors freely: the
history counts from the day the note was dictated, the course from
admission and from the operation, the plan from discharge. Temporal
normalizers, however, typically resolve everything against a single
document date. Nobody measures what that silent choice costs.

This tool measures it. It:

1. generates seeded synthetic notes from ground-truth timelines with
   four competing anchors in play (admission, procedure, discharge,
   note date), each expression written against a recorded anchor;
2. runs anchor-resolution strategies over the notes — the four fixed
   single-anchor baselines, a section-aware heuristic, and an oracle —
   and reports timeline error in days, plus the **anchor-confusion
   matrix**: which anchor each strategy assumed vs the anchor each
   expression was actually written against;
3. passes the notes through a seeded summariser that drops,
   cue-strips, rebases and value-perturbs expressions at declared
   rates, then re-audits — including scoring the naive string-match
   and date-presence checks as drift detectors.

Everything is offline, deterministic and seeded. Pure Python standard
library; no API keys, no model downloads, no network. All clinical
content is synthetic — no real patient data anywhere.

## 2. The novel mechanism

Prior temporal-extraction work (HeidelTime, MedTime, MedTimeline, the
THYME/i2b2 challenges) extracts and normalizes temporal expressions
and is evaluated on extraction F1 against one document creation time.
Anchor *choice* is never treated as an error source in its own right.

Here it is the object of study. Because the notes are generated from a
known timeline, the anchor each expression was written against is
ground truth, so a resolver's silent assumption becomes a measurable
quantity: an anchor-confusion matrix and a per-anchor error bill, in
days. The summarisation stage extends the same framing: drift is
classified by what it does to the anchor (cue stripped, frame rebased
onto the previous event, value perturbed, expression dropped), and
each type is priced separately — including the errors that are
irreducible, where the summary itself now asserts the wrong date and
no resolver reading it can recover the truth.

## 3. Headline results (measured)

120 seeded cases, 778 expressions (seed 20261121; reproduce with
`python scripts/reproduce_results.py`).

**Part 1 — anchor choice on the original notes:**

| Strategy | MAE (days) | Exact | Catastrophic (>7d) |
|---|---|---|---|
| note-date (standard baseline) | 6.11 | 0.355 | 0.379 |
| admission | 7.23 | 0.293 | 0.445 |
| procedure | 4.53 | 0.316 | 0.248 |
| discharge | 5.81 | 0.247 | 0.355 |
| section-aware heuristic | 0.32 | 0.959 | 0.018 |
| oracle (true anchor) | 0.00 | 1.000 | 0.000 |

The note-date baseline's error is not spread evenly — it lands exactly
on the expressions written against other anchors: admission-anchored
expressions are off by 13.10 days on average, procedure-anchored by
7.41 days, discharge-anchored by 0.92, note-anchored by 0.00. The
section-aware strategy's one systematic confusion (32 of 778) is the
genuinely ambiguous cue-less "on day N", written against the procedure
but read in the admission frame.

**Part 2 — after one summarisation pass** (drift rates: 41.0%
preserved, 19.3% cue-stripped, 16.7% rebased, 11.2% value-changed,
11.8% dropped off the timeline entirely):

| Strategy | MAE (days) | Exact | Catastrophic (>7d) |
|---|---|---|---|
| note-date | 7.24 | 0.260 | 0.434 |
| section-aware | 2.13 | 0.639 | 0.101 |
| oracle (reads summary literally) | 2.45 | 0.695 | 0.093 |

Note the oracle row: after summarisation, even resolving every
expression against the anchor the summary *literally* asserts leaves
2.45 days of MAE, because rebased and value-changed expressions assert
wrong dates. The section-aware heuristic lands slightly closer on MAE
(2.13) precisely because it sometimes ignores the summary's literal
frame in favour of a section default — luck, not understanding, and
the README of the results says so.

**The naive checks do not catch the drift.** A string-match check
(expression text must survive verbatim) detects harmful drift
(rebased / value-changed / dropped) at precision 0.675, recall 0.974,
F1 0.797 — it cannot separate a harmless cue-strip from a rebase. A
date-presence check passes 100% of the drifted summaries.

## 4. How it works

1. **Generate** (`generate.py`) — a case draws admission, procedure,
   discharge and note dates, then plants 5–8 expressions of nine
   kinds ("…days ago", weekday references, post-op days, hospital
   days, after-admission / before-surgery / after-discharge offsets,
   follow-ups, and cue-less "on day N"), each against its natural
   anchor, recorded as ground truth.
2. **Parse** (`parse.py`) — resolvers see only surface text: a small
   parser extracts the stated offset (or weekday), any explicit anchor
   cue, and bare day-count forms.
3. **Resolve** (`resolve.py`) — fixed strategies always use their one
   anchor; section-aware trusts an explicit cue, else a per-section
   default; the oracle uses the recorded true anchor. Bare "day N"
   inherits the day-counting convention of whichever anchor is
   assumed (hospital day N = admission + N − 1; post-op day N =
   procedure + N) — one more quiet assumption the audit prices.
4. **Audit** (`audit.py`) — per strategy: MAE, median and max error,
   exact-match rate, catastrophic rate (>7 days), per-anchor MAE, and
   the anchor-confusion matrix.
5. **Summarise** (`summarize.py`) — a seeded summariser applies the
   four drift types at declared rates; `audit.audit_summaries`
   re-scores survivors against the *original* ground truth, and
   `baselines.py` scores the naive checks against the known labels.

## 5. Repository layout

```
temporal_anchor/   package: models, generate, parse, resolve, audit,
                   summarize, baselines, evaluate, report, cli
data/              seeded sample cases (cases.json, demo_case.json)
examples/          demo_note.json, run_audit.py, sample_report.md
notebooks/         01_demo_run.py, 02_evaluation_experiment.py
scripts/           build_cases.py, reproduce_results.py (drift guard)
results/           evaluation.json/.csv, evaluation_summary.md, HEADLINE.md
tests/             pytest suite (99 tests)
app.py             Streamlit dashboard (3 tabs)
```

## 6. Quickstart

```bash
pip install -r requirements.txt
python -m temporal_anchor demo       # one case, every strategy
python -m temporal_anchor audit      # per-strategy table, 20 cases
python -m temporal_anchor evaluate   # full run, writes results/
python scripts/reproduce_results.py  # verify results/ has not drifted
pytest                               # full test suite
streamlit run app.py                 # dashboard
```

## 7. Honest limits

- All notes are synthetic and seeded, generated from known timelines
  with templated surface forms. The parser and the section-aware
  heuristic are evaluated on the expression forms the generator
  produces; real notes are messier, and real normalizers face
  extraction errors this audit deliberately excludes so that anchor
  error is isolated.
- The summariser is a declared probabilistic policy (drop 0.12,
  cue-strip 0.25, rebase 0.15, value-change 0.10), not a measured
  sample of any real LLM summariser. The experiment prices each drift
  type under those rates; it does not claim real summarisers drift at
  these rates.
- Every case is a surgical admission with all four anchors present.
  Non-surgical cases (no procedure anchor), and notes dictated
  mid-stay, are out of scope.
- The oracle's part-1 perfection is by construction — it exists to
  price the other strategies' assumptions, not as a proposed system.

## 8. Author and license

Amna Raheeba. MIT License (see `LICENSE`).
