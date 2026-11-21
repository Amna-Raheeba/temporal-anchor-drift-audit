"""Naive drift detectors, included as the baselines to beat.

These are the checks a pipeline plausibly already has:

- a *date-presence check*: does the summary still contain something
  that looks like a temporal expression at all? It can only fail when
  every temporal token vanishes, so it certifies summaries that have
  quietly re-anchored half their events.
- a *string-match check*: does each original expression's text survive
  verbatim in the summary? It catches drops and rewrites alike but
  cannot tell a harmless paraphrase (cue stripped, date intact in
  meaning) from a harmful one (rebased or value-changed), and it flags
  nothing at all about which date the summary now asserts.
"""

import re

from .models import HARMFUL_DRIFT

_TEMPORAL_TOKEN = re.compile(
    r"(\d+\s*(day|week|month)s?)|(post-op|since|ago|before|after|later|prior)"
)


def date_presence_check(summary_texts):
    """True if any temporal-looking token survives in the summary."""
    joined = " ".join(summary_texts).lower()
    return _TEMPORAL_TOKEN.search(joined) is not None


def string_match_flags(original_texts, summary_texts):
    """Flag each original expression whose text changed or vanished."""
    summary_set = set(summary_texts)
    return [text not in summary_set for text in original_texts]


def score_string_match(cases_with_summaries):
    """Score the string-match check as a harmful-drift detector.

    ``cases_with_summaries`` is a list of (case, summary, drift) triples
    as produced by summarize.summarize_cases. Returns precision, recall
    and F1 for detecting harmful drift (rebased / value_changed /
    dropped), plus the date-presence check's pass rate over the same
    summaries.
    """
    flagged = 0
    harmful = 0
    true_positive = 0
    presence_passes = 0
    total_cases = 0
    for case, summary, drift in cases_with_summaries:
        total_cases += 1
        if date_presence_check([e.text for e in summary]):
            presence_passes += 1
        summary_texts = [e.text for e in summary]
        flags = string_match_flags([e.text for e in case.expressions], summary_texts)
        for expr, was_flagged in zip(case.expressions, flags):
            is_harmful = drift[expr.expr_id] in HARMFUL_DRIFT
            if is_harmful:
                harmful += 1
            if was_flagged:
                flagged += 1
                if is_harmful:
                    true_positive += 1
    precision = true_positive / float(flagged) if flagged else 0.0
    recall = true_positive / float(harmful) if harmful else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "flagged": flagged,
        "harmful": harmful,
        "true_positive": true_positive,
        "date_presence_pass_rate": presence_passes / float(total_cases)
        if total_cases
        else 0.0,
    }
