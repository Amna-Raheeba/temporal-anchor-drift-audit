"""Core data model for the temporal anchor drift audit.

A *case* is one synthetic discharge-style note built from a ground-truth
timeline. The note's events are dated relative to one of four competing
anchors -- admission, procedure, discharge, and the note (dictation)
date -- exactly as real clinical notes mix reference frames. Every
relative temporal expression in the note records which anchor it was
written against; that record is the ground truth the resolvers are
audited against, and it is never shown to them.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

ANCHORS = ["admission", "procedure", "discharge", "note"]

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

SECTIONS = ["history", "hospital_course", "operative", "discharge_plan"]

# Where a section-aware resolver looks when an expression carries no
# explicit anchor cue of its own.
SECTION_DEFAULT_ANCHOR = {
    "history": "note",
    "hospital_course": "admission",
    "operative": "procedure",
    "discharge_plan": "note",
}

# Expression kinds the generator can plant.
EXPRESSION_KINDS = [
    "ago",
    "weekday",
    "post_op_day",
    "hospital_day",
    "after_admission",
    "before_surgery",
    "after_discharge",
    "follow_up",
    "bare_day",
]

# Drift types a summarisation pass can inflict on an expression.
DRIFT_TYPES = ["preserved", "cue_stripped", "rebased", "value_changed", "dropped"]

# Drift types that change what date the summary actually asserts.
HARMFUL_DRIFT = ["rebased", "value_changed", "dropped"]


def parse_iso(text):
    """Parse an ISO date string (YYYY-MM-DD) into a datetime.date."""
    year, month, day = text.split("-")
    return date(int(year), int(month), int(day))


def to_iso(day):
    return day.isoformat()


def shift(day, offset_days):
    return day + timedelta(days=int(offset_days))


def most_recent_weekday(anchor_day, weekday_index):
    """Most recent date with the given weekday strictly before anchor_day.

    "Since last Tuesday" said on a Tuesday means the Tuesday of the
    previous week, so a zero delta is promoted to seven days.
    """
    delta = (anchor_day.weekday() - weekday_index) % 7
    if delta == 0:
        delta = 7
    return anchor_day - timedelta(days=delta)


@dataclass
class Expression:
    """One relative temporal expression planted in a note."""

    expr_id: str
    event: str
    section: str
    kind: str
    text: str
    true_anchor: str
    true_date: str  # ISO date the event actually happened on

    def to_dict(self):
        return {
            "expr_id": self.expr_id,
            "event": self.event,
            "section": self.section,
            "kind": self.kind,
            "text": self.text,
            "true_anchor": self.true_anchor,
            "true_date": self.true_date,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            expr_id=data["expr_id"],
            event=data["event"],
            section=data["section"],
            kind=data["kind"],
            text=data["text"],
            true_anchor=data["true_anchor"],
            true_date=data["true_date"],
        )


@dataclass
class Case:
    """One synthetic note: four anchor dates plus its expressions."""

    case_id: str
    anchors: dict  # anchor name -> ISO date string
    expressions: list = field(default_factory=list)

    def anchor_date(self, name):
        return parse_iso(self.anchors[name])

    def note_text(self):
        """Render the note as sectioned plain text."""
        lines = []
        for section in SECTIONS:
            here = [e for e in self.expressions if e.section == section]
            if not here:
                continue
            lines.append("[%s]" % section)
            for expr in here:
                lines.append("- %s: %s." % (expr.event, expr.text))
        return "\n".join(lines)

    def to_dict(self):
        return {
            "case_id": self.case_id,
            "anchors": dict(self.anchors),
            "expressions": [e.to_dict() for e in self.expressions],
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            case_id=data["case_id"],
            anchors=dict(data["anchors"]),
            expressions=[Expression.from_dict(e) for e in data["expressions"]],
        )
