"""THE stated-absence marker: `{"present": false, "detail": "<why>"}`.

WHY IT IS A MODULE AND NOT A CONVENTION. 07-07 invented this shape twice in
one file (`result_artifact_fields.TOKENS_ABSENT` and `GAMES_PLAYED_UNSET`) and
08-04 needs it a third time, for rule 49's repo links that do not exist until a
human creates the repositories. CLAUDE.md Table 5 says extract at 2+ copies, so
the shape lives here and those two are rebuilt from it -- their dict values are
byte-identical to what 07-07 wrote, which is what
`tests/unit/test_absent_marker.py` asserts.

WHY A MARKER AND NOT `null`, AND NOT A PLACEHOLDER STRING. A grader-facing
artifact has to distinguish three different facts that a bare `null` collapses
into one: the value exists, the value does not exist YET and here is why, and
the value was never asked for. A placeholder string is worse than either --
`"https://github.com/TODO"` in `declaration_<game_id>.json` reads as a claim,
and CLAUDE.md's first prohibition is against inventing values. The marker
carries the reason with the absence, so the absence is evidence rather than a
hole.

This module imports nothing. It is the bottom of the layer stack.
"""

from __future__ import annotations

__all__ = (
    "ABSENT_DETAIL_KEY",
    "ABSENT_PRESENT_KEY",
    "is_stated_absent",
    "stated_absent",
)

#: The two key names. Spelled once, so a reader written against one artifact
#: cannot miss the marker in another because of a synonym.
ABSENT_PRESENT_KEY = "present"
ABSENT_DETAIL_KEY = "detail"


def stated_absent(detail: str) -> dict:
    """One stated absence. `detail` says WHY, and is required.

    A blank reason is refused rather than accepted: "absent" with no reason is
    the hole this marker exists to close, and a caller with nothing to say has
    not finished thinking about the field.
    """
    if not isinstance(detail, str) or not detail.strip():
        raise ValueError("a stated absence must carry a non-empty reason")
    return {ABSENT_PRESENT_KEY: False, ABSENT_DETAIL_KEY: detail}


def is_stated_absent(value: object) -> bool:
    """True for a marker this module produced, False for everything else.

    Deliberately strict about the `present` key's VALUE: a dict carrying
    `present: true` is a presence record, not an absence, and a reader that
    treated any dict as absent would silently drop a real value.
    """
    return (
        isinstance(value, dict)
        and value.get(ABSENT_PRESENT_KEY) is False
        and isinstance(value.get(ABSENT_DETAIL_KEY), str)
    )
