"""A small surface parser for relative temporal expressions.

Resolvers never see the structured ground truth; like a real temporal
normalizer, they see only the expression text (and the note section).
The parser extracts what the text itself offers:

- ``offset_days``: the signed day offset the text states, if any;
- ``weekday``: a weekday index for "since last Tuesday" forms;
- ``cue``: the anchor the text explicitly names ("post-op" -> procedure,
  "after admission" -> admission, "ago" -> note, ...), or ``None`` when
  the text is silent about its reference frame, or ``"previous"`` for
  the summariser's rebased "N days later" form;
- ``day_count``: True for bare "day N" forms, whose day-counting
  convention depends on which anchor is assumed.
"""

import re

from .models import WEEKDAYS

_WEEKDAY_INDEX = dict((name.lower(), i) for i, name in enumerate(WEEKDAYS))

_PATTERNS = [
    # (regex, builder) -- most specific forms first.
    (re.compile(r"post-op day (\d+)"), lambda m: _result(offset=int(m.group(1)), cue="procedure")),
    (re.compile(r"hospital day (\d+)"), lambda m: _result(offset=int(m.group(1)) - 1, cue="admission")),
    (re.compile(r"(\d+) days? after admission"), lambda m: _result(offset=int(m.group(1)), cue="admission")),
    (re.compile(r"(\d+) days? after discharge"), lambda m: _result(offset=int(m.group(1)), cue="discharge")),
    (re.compile(r"the day before surgery"), lambda m: _result(offset=-1, cue="procedure")),
    (re.compile(r"(\d+) days? before surgery"), lambda m: _result(offset=-int(m.group(1)), cue="procedure")),
    (re.compile(r"since last (\w+)"), lambda m: _result(weekday=_WEEKDAY_INDEX[m.group(1).lower()], cue="note")),
    (re.compile(r"(\d+) days? ago"), lambda m: _result(offset=-int(m.group(1)), cue="note")),
    (re.compile(r"in (\d+) weeks?"), lambda m: _result(offset=7 * int(m.group(1)), cue="note")),
    (re.compile(r"in (\d+) days?"), lambda m: _result(offset=int(m.group(1)), cue="note")),
    # Summariser output forms.
    (re.compile(r"(\d+) days? later"), lambda m: _result(offset=int(m.group(1)), cue="previous")),
    (re.compile(r"(\d+) days? into the course"), lambda m: _result(offset=int(m.group(1)), cue=None)),
    (re.compile(r"(\d+) days? after leaving"), lambda m: _result(offset=int(m.group(1)), cue=None)),
    (re.compile(r"(\d+) days? prior"), lambda m: _result(offset=-int(m.group(1)), cue=None)),
    (re.compile(r"the day before\b"), lambda m: _result(offset=-1, cue=None)),
    (re.compile(r"(\d+) days? before\b"), lambda m: _result(offset=-int(m.group(1)), cue=None)),
    (re.compile(r"since (\w+)"), lambda m: _result(weekday=_WEEKDAY_INDEX[m.group(1).lower()], cue=None)),
    (re.compile(r"on day (\d+)"), lambda m: _result(offset=int(m.group(1)), cue=None, day_count=True)),
    (re.compile(r"day (\d+) of the course"), lambda m: _result(offset=int(m.group(1)), cue=None, day_count=True)),
]


def _result(offset=None, weekday=None, cue=None, day_count=False):
    return {
        "offset_days": offset,
        "weekday": weekday,
        "cue": cue,
        "day_count": day_count,
    }


def parse_expression(text):
    """Parse one expression's surface text. Raises ValueError if unknown."""
    lowered = text.strip().lower()
    for pattern, builder in _PATTERNS:
        match = pattern.search(lowered)
        if match:
            return builder(match)
    raise ValueError("unparseable temporal expression: %s" % text)
