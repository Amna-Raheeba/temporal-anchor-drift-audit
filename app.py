"""Streamlit dashboard for temporal-anchor-drift-audit.

Three tabs:
1. Note audit -- one seeded case, resolved under a chosen strategy,
   with true vs predicted dates side by side.
2. Anchor confusion -- per-strategy MAE and the anchor-confusion
   matrix for the section-aware strategy.
3. Evaluation -- the stored headline results (results/evaluation.json),
   including the summarisation-drift stage.

Run: streamlit run app.py
"""

import json
import os

import pandas as pd
import streamlit as st

from temporal_anchor.audit import audit_cases, audit_summaries, confusion_matrix, summarize_rows
from temporal_anchor.evaluate import DEFAULT_CONFIG
from temporal_anchor.generate import generate_cases
from temporal_anchor.models import ANCHORS
from temporal_anchor.resolve import STRATEGIES
from temporal_anchor.summarize import summarize_cases

st.set_page_config(page_title="Temporal Anchor Drift Audit", layout="wide")

SEED = DEFAULT_CONFIG["seed"]


@st.cache_data
def load_cases(n):
    return generate_cases(n, SEED)


@st.cache_data
def load_results():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "evaluation.json")
    if not os.path.exists(path):
        return None
    with open(path) as handle:
        return json.load(handle)


def tab_note_audit():
    st.header("Note audit")
    st.write(
        "Every relative expression in a note was written against one "
        "specific anchor. Pick a strategy and see what timeline it "
        "reconstructs -- and how many days it is wrong by."
    )
    cases = load_cases(12)
    col1, col2 = st.columns(2)
    case_id = col1.selectbox("Case", [c.case_id for c in cases])
    strategy = col2.selectbox("Resolver strategy", STRATEGIES, index=4)
    case = [c for c in cases if c.case_id == case_id][0]
    st.text(case.note_text())
    st.write(
        "Anchors: %s"
        % ", ".join("%s = %s" % (name, case.anchors[name]) for name in ANCHORS)
    )
    from temporal_anchor.audit import audit_expression

    rows = []
    for expr in case.expressions:
        rows.extend(audit_expression(case, expr, strategies=[strategy]))
    frame = pd.DataFrame(
        [
            {
                "expression": r["text"],
                "event": r["event"],
                "true_anchor": r["true_anchor"],
                "true_date": r["true_date"],
                "assumed_anchor": r["assumed_anchor"],
                "predicted_date": r["predicted_date"],
                "error_days": r["error_days"],
            }
            for r in rows
        ]
    )
    st.dataframe(frame, use_container_width=True)
    mae = frame["error_days"].abs().mean()
    st.metric("Mean absolute error (days)", "%.2f" % mae)


def tab_confusion():
    st.header("Anchor confusion")
    st.write(
        "Mean absolute timeline error per strategy on 40 seeded cases, "
        "and the anchor-confusion matrix of the section-aware strategy: "
        "rows are the anchor an expression was written against, columns "
        "the anchor the strategy assumed."
    )
    cases = load_cases(40)
    rows = audit_cases(cases)
    summary = summarize_rows(rows)
    chart = pd.DataFrame(
        {
            "strategy": list(summary.keys()),
            "mae_days": [summary[s]["mae_days"] for s in summary],
        }
    )
    st.bar_chart(chart, x="strategy", y="mae_days")
    matrix = confusion_matrix(rows, "section_aware")
    columns = ANCHORS + ["previous"]
    frame = pd.DataFrame(
        [
            dict({"true_anchor": true}, **dict((c, matrix[true][c]) for c in columns))
            for true in columns
        ]
    )
    st.dataframe(frame, use_container_width=True)
    st.write(
        "The one systematic confusion: cue-less 'on day N' expressions "
        "written against the procedure are read as hospital days "
        "(admission frame) -- they are genuinely ambiguous in the text."
    )


def tab_evaluation():
    st.header("Evaluation")
    results = load_results()
    if results is None:
        st.warning("No stored results yet. Run: python -m temporal_anchor evaluate")
        return
    st.write(
        "Stored headline results: %d cases, %d expressions (seed %d)."
        % (results["n_cases"], results["n_expressions"], results["config"]["seed"])
    )
    for stage, title in (("part1", "Before summarisation"), ("part2", "After summarisation")):
        st.subheader(title)
        frame = pd.DataFrame(
            [
                dict({"strategy": s}, **results[stage][s])
                for s in STRATEGIES
            ]
        )
        st.dataframe(frame, use_container_width=True)
    st.subheader("Summariser drift")
    drift = pd.DataFrame(
        [
            {"drift_type": name, "rate": rate}
            for name, rate in sorted(results["drift_rates"].items())
        ]
    )
    st.bar_chart(drift, x="drift_type", y="rate")
    b = results["baselines"]
    st.write(
        "String-match check vs harmful drift: precision %.3f, recall %.3f, "
        "F1 %.3f. Date-presence check passes %.1f%% of drifted summaries."
        % (b["precision"], b["recall"], b["f1"], 100 * b["date_presence_pass_rate"])
    )
    triples = summarize_cases(load_cases(5), results["config"]["summary_seed"])
    st.write(
        "Expressions surviving summarisation in a 5-case sample: %d of %d."
        % (
            sum(len(summary) for _c, summary, _d in triples),
            sum(len(c.expressions) for c, _s, _d in triples),
        )
    )
    _ = audit_summaries(triples)  # exercised for the demo path


tab1, tab2, tab3 = st.tabs(["Note audit", "Anchor confusion", "Evaluation"])
with tab1:
    tab_note_audit()
with tab2:
    tab_confusion()
with tab3:
    tab_evaluation()
