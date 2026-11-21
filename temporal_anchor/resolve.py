"""Anchor-resolution strategies.

A strategy turns a parsed expression into an absolute date by choosing
which anchor to resolve it against. The fixed strategies are what real
normalizers silently do -- pick one document-level reference date and
use it for everything. The section-aware strategy is the heuristic
alternative: trust an explicit cue when the text offers one, otherwise
fall back to a per-section default. The oracle resolves against the
anchor the expression was actually written against, and exists only as
the reference point that prices everyone else's anchor assumptions.
"""

from .models import SECTION_DEFAULT_ANCHOR, most_recent_weekday, parse_iso, shift, to_iso
from .parse import parse_expression

STRATEGIES = [
    "note_date",
    "admission",
    "procedure",
    "discharge",
    "section_aware",
    "oracle",
]

FIXED_STRATEGIES = ["note_date", "admission", "procedure", "discharge"]


def choose_anchor(strategy, parsed, section, oracle_anchor=None):
    """Return the anchor name a strategy assumes for this expression."""
    if strategy in FIXED_STRATEGIES:
        return strategy.replace("_date", "") if strategy == "note_date" else strategy
    if strategy == "section_aware":
        cue = parsed["cue"]
        if cue in ("admission", "procedure", "discharge", "note"):
            return cue
        return SECTION_DEFAULT_ANCHOR.get(section, "note")
    if strategy == "oracle":
        if oracle_anchor is None:
            raise ValueError("oracle strategy needs the ground-truth anchor")
        return oracle_anchor
    raise ValueError("unknown strategy: %s" % strategy)


def resolve(text, section, anchors, strategy, oracle_anchor=None, prev_date=None):
    """Resolve one expression to (predicted ISO date, assumed anchor).

    ``anchors`` maps anchor names to ISO date strings. ``prev_date`` is
    the ISO date of the previous event in the note, needed when a
    summariser has rebased an expression to "N days later".
    """
    parsed = parse_expression(text)
    assumed = choose_anchor(strategy, parsed, section, oracle_anchor=oracle_anchor)
    if assumed == "previous":
        if prev_date is None:
            raise ValueError("rebased expression needs the previous event date")
        base = parse_iso(prev_date)
    else:
        base = parse_iso(anchors[assumed])
    if parsed["weekday"] is not None:
        predicted = most_recent_weekday(base, parsed["weekday"])
    elif parsed["day_count"]:
        # "Day N" counts from admission as day 1 (hospital-day style)
        # but from a procedure as day 0 + N (post-op style). A resolver
        # inherits whichever convention its assumed anchor implies.
        offset = parsed["offset_days"]
        if assumed == "admission":
            offset = offset - 1
        predicted = shift(base, offset)
    else:
        predicted = shift(base, parsed["offset_days"])
    return to_iso(predicted), assumed
