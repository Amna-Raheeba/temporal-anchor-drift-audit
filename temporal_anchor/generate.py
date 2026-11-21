"""Seeded generation of synthetic multi-anchor clinical notes.

Every case starts from a ground-truth timeline: an admission date, a
procedure date inside the stay, a discharge date, and a note date at or
just after discharge. Expressions are then planted against *different*
anchors, as real notes are -- the history is written against the note
date ("three days ago", "since last Tuesday"), the course against
admission and the operation, the plan against discharge. The anchor each
expression was written against is recorded as ground truth.

All patient content is synthetic. No real patient data is used anywhere.
"""

import random
from datetime import date, timedelta

from .models import (
    WEEKDAYS,
    Case,
    Expression,
    most_recent_weekday,
    shift,
    to_iso,
)

EVENTS = [
    "symptom onset",
    "fever onset",
    "antibiotic start",
    "wound check",
    "drain removal",
    "first ambulation",
    "blood transfusion",
    "imaging study",
    "consult placed",
    "medication change",
    "pain review",
    "suture removal",
]

BASE_DATE = date(2025, 1, 6)  # a Monday; fixed so seeds are stable


def _day_word(n):
    return "day" if n == 1 else "days"


def _plant(rng, case, anchors, kind, event):
    """Create one expression of the given kind against its true anchor."""
    admission = anchors["admission"]
    procedure = anchors["procedure"]
    discharge = anchors["discharge"]
    note = anchors["note"]

    if kind == "ago":
        offset = -rng.randint(1, 14)
        text = "%d %s ago" % (-offset, _day_word(-offset))
        return text, "note", shift(note, offset), "history"
    if kind == "weekday":
        target = rng.randrange(7)
        true_day = most_recent_weekday(note, target)
        return "since last %s" % WEEKDAYS[target], "note", true_day, "history"
    if kind == "post_op_day":
        offset = rng.randint(0, 10)
        text = "post-op day %d" % offset
        section = rng.choice(["hospital_course", "operative"])
        return text, "procedure", shift(procedure, offset), section
    if kind == "hospital_day":
        n = rng.randint(1, 14)
        text = "hospital day %d" % n
        return text, "admission", shift(admission, n - 1), "hospital_course"
    if kind == "after_admission":
        offset = rng.randint(1, 14)
        text = "%d %s after admission" % (offset, _day_word(offset))
        section = rng.choice(["hospital_course", "history"])
        return text, "admission", shift(admission, offset), section
    if kind == "before_surgery":
        offset = rng.randint(1, 3)
        if offset == 1:
            text = "the day before surgery"
        else:
            text = "%d days before surgery" % offset
        section = rng.choice(["history", "operative"])
        return text, "procedure", shift(procedure, -offset), section
    if kind == "after_discharge":
        offset = rng.randint(1, 21)
        text = "%d %s after discharge" % (offset, _day_word(offset))
        return text, "discharge", shift(discharge, offset), "discharge_plan"
    if kind == "follow_up":
        if rng.random() < 0.5:
            offset = rng.randint(3, 30)
            text = "in %d %s" % (offset, _day_word(offset))
        else:
            weeks = rng.randint(1, 6)
            offset = 7 * weeks
            text = "in %d %s" % (weeks, "week" if weeks == 1 else "weeks")
        return text, "note", shift(note, offset), "discharge_plan"
    if kind == "bare_day":
        # A cue-less "on day N": genuinely ambiguous between hospital
        # day N (admission + N - 1) and post-op day N (procedure + N).
        n = rng.randint(1, 10)
        text = "on day %d" % n
        if rng.random() < 0.5:
            return text, "admission", shift(admission, n - 1), "hospital_course"
        return text, "procedure", shift(procedure, n), "hospital_course"
    raise ValueError("unknown expression kind: %s" % kind)


# Kinds sampled for each note, weighted so anchor frames are mixed.
KIND_POOL = [
    "ago",
    "weekday",
    "post_op_day",
    "hospital_day",
    "after_admission",
    "before_surgery",
    "after_discharge",
    "follow_up",
    "bare_day",
    "post_op_day",
    "ago",
    "hospital_day",
]


def generate_case(case_index, rng):
    """Generate one case. rng is a random.Random instance."""
    admission = BASE_DATE + timedelta(days=rng.randint(0, 300))
    stay = rng.randint(4, 21)
    procedure = admission + timedelta(days=rng.randint(1, stay - 1))
    discharge = admission + timedelta(days=stay)
    note = discharge + timedelta(days=rng.randint(0, 2))
    anchors = {
        "admission": admission,
        "procedure": procedure,
        "discharge": discharge,
        "note": note,
    }
    case = Case(
        case_id="case-%03d" % case_index,
        anchors=dict((name, to_iso(day)) for name, day in anchors.items()),
    )
    n_expr = rng.randint(5, 8)
    events = rng.sample(EVENTS, n_expr)
    for i in range(n_expr):
        kind = rng.choice(KIND_POOL)
        text, true_anchor, true_day, section = _plant(
            rng, case, anchors, kind, events[i]
        )
        case.expressions.append(
            Expression(
                expr_id="e%d" % (i + 1),
                event=events[i],
                section=section,
                kind=kind,
                text=text,
                true_anchor=true_anchor,
                true_date=to_iso(true_day),
            )
        )
    return case


def generate_cases(n_cases, seed):
    """Generate n_cases cases deterministically from a seed."""
    rng = random.Random(seed)
    return [generate_case(i + 1, rng) for i in range(n_cases)]
