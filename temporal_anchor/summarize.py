"""A seeded summariser that inflicts realistic temporal drift.

Real summarisation passes do not usually delete dates outright; they do
quieter damage. This module models the four failure modes, drawn per
expression from declared probabilities:

- ``cue_stripped``: the anchor cue is paraphrased away ("post-op day 2"
  becomes "day 2 of the course"). The stated offset survives, but the
  reference frame is gone and any resolver must guess it.
- ``rebased``: the number is copied but the frame is changed -- the
  summary writes "N days later", silently re-anchoring the expression
  to the previous event in the note. Read literally it asserts a
  different date; no resolver can recover the original from the text.
- ``value_changed``: the offset itself is perturbed ("three days ago"
  becomes "five days ago"), as rounding and paraphrase do.
- ``dropped``: the expression disappears from the summary entirely;
  the event falls off the reconstructed timeline.

Everything is seeded and deterministic, and the drift applied to each
expression is recorded, so the audit measures the summariser's damage
against known ground truth instead of guessing at it.
"""

import random
import re

from .models import DRIFT_TYPES, Expression

DEFAULT_SUMMARY_RATES = {
    "drop": 0.12,
    "cue_strip": 0.25,
    "rebase": 0.15,
    "value_change": 0.10,
}

# Cue-stripped surface forms per kind. Kinds without a natural stripped
# form (follow_up, weekday handled below) fall back as noted.
_STRIP_FORMS = {
    "post_op_day": lambda n: "day %d of the course" % n,
    "hospital_day": lambda n: "on day %d" % n,
    "after_admission": lambda n: "%d %s into the course" % (n, "day" if n == 1 else "days"),
    "after_discharge": lambda n: "%d %s after leaving" % (n, "day" if n == 1 else "days"),
    "before_surgery": lambda n: "the day before" if n == 1 else "%d days before" % n,
    "ago": lambda n: "%d %s prior" % (n, "day" if n == 1 else "days"),
}


def _stated_number(expr):
    """The day count an expression's text states (None for weekday forms)."""
    if expr.kind == "hospital_day":
        match = re.search(r"hospital day (\d+)", expr.text)
        return int(match.group(1))
    match = re.search(r"(\d+)", expr.text)
    if match:
        return int(match.group(1))
    if expr.text == "the day before surgery":
        return 1
    return None


def _rerender_with_number(expr, number):
    """Re-render an expression's text with a different stated number."""
    if expr.kind == "before_surgery" and number == 1:
        return "the day before surgery"
    if re.search(r"\d+", expr.text):
        return re.sub(r"\d+", str(number), expr.text, count=1)
    return expr.text


def _strip_cue(expr):
    """Return the cue-stripped surface form, or None if not strippable."""
    number = _stated_number(expr)
    if expr.kind == "weekday":
        return expr.text.replace("since last ", "since ")
    if expr.kind == "bare_day":
        return None  # already cue-less; nothing left to strip
    if expr.kind == "follow_up":
        return None  # "in N days" carries no removable anchor cue
    builder = _STRIP_FORMS.get(expr.kind)
    if builder is None or number is None:
        return None
    return builder(number)


def summarize_case(case, rng, rates=None):
    """Summarise one case.

    Returns (summary_expressions, drift) where summary_expressions are
    Expression records whose text is the summary's version (dropped
    expressions are absent) and drift maps expr_id -> drift type for
    every original expression. A summary expression's ``true_anchor``
    field records the anchor its text *literally* asserts (the original
    anchor, or "previous" after a rebase) -- which is what an oracle
    reading only the summary would use.
    """
    rates = rates or DEFAULT_SUMMARY_RATES
    summary = []
    drift = {}
    for position, expr in enumerate(case.expressions):
        roll = rng.random()
        if roll < rates["drop"]:
            drift[expr.expr_id] = "dropped"
            continue
        roll -= rates["drop"]
        if roll < rates["cue_strip"]:
            stripped = _strip_cue(expr)
            if stripped is not None:
                drift[expr.expr_id] = "cue_stripped"
                summary.append(_variant(expr, stripped, expr.true_anchor))
                continue
        roll -= rates["cue_strip"]
        if roll < rates["rebase"] and position > 0:
            # A rebase needs a previous event to be "later" than; the
            # first expression in a note has none and is never rebased.
            number = _stated_number(expr)
            if number is not None:
                drift[expr.expr_id] = "rebased"
                text = "%d %s later" % (number, "day" if number == 1 else "days")
                summary.append(_variant(expr, text, "previous"))
                continue
        roll -= rates["rebase"]
        if roll < rates["value_change"]:
            number = _stated_number(expr)
            if number is not None:
                delta = rng.choice([-2, -1, 1, 2])
                new_number = max(1, number + delta)
                if new_number != number:
                    drift[expr.expr_id] = "value_changed"
                    summary.append(
                        _variant(
                            expr,
                            _rerender_with_number(expr, new_number),
                            expr.true_anchor,
                        )
                    )
                    continue
        drift[expr.expr_id] = "preserved"
        summary.append(_variant(expr, expr.text, expr.true_anchor))
    return summary, drift


def _variant(expr, text, literal_anchor):
    return Expression(
        expr_id=expr.expr_id,
        event=expr.event,
        section=expr.section,
        kind=expr.kind,
        text=text,
        true_anchor=literal_anchor,
        true_date=expr.true_date,
    )


def summarize_cases(cases, seed, rates=None):
    """Summarise a list of cases with one seeded RNG stream."""
    rng = random.Random(seed)
    out = []
    for case in cases:
        summary, drift = summarize_case(case, rng, rates=rates)
        out.append((case, summary, drift))
    return out


def drift_counts(drift_maps):
    """Aggregate drift-type counts over many cases' drift maps."""
    counts = dict((name, 0) for name in DRIFT_TYPES)
    for drift in drift_maps:
        for kind in drift.values():
            counts[kind] += 1
    return counts
