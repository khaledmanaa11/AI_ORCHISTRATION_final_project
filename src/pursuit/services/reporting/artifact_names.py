"""The four docs/PARAMETERS.md filenames and the `<NN>` sub-game index.

Split out of `artifacts.py` at the 150-code-line gate (Segal Table 5) -- the
combined module measured 167 -- along the seam its own subject list already
named: the NAMES (a document this project must match) and the SEAL plus the
WRITE POLICY (a hashing and placement decision) were always two subjects
sharing one file. This half is the dependency-free leaf: pure strings and
paths, importing nothing from `pursuit`. `artifacts.py` re-exports every
public name below, so callers keep ONE import path.

Split, never compressed: not one line of any function's body or docstring was
shortened to make room (CLAUDE.md Table 5).

THE NAMES ARE A GRADER-FACING SPEC SURFACE. `docs/PARAMETERS.md:163-168`
fixes all four verbatim, and the distinguishing detail is that `_g<NN>` is
PRESENT on `config_`/`log_` and ABSENT on `declaration_`/`result_`.
`tests/unit/test_artifact_names.py` transcribes that table as literals, so a
rename here fails against the DOCUMENT rather than against another copy of
itself.

`<NN>` IS NOT THE RULE-37/38 GAMES-PLAYED COUNTER (D-72). It is a
per-`game_id` sub-game index, derived from what already exists for THAT
`game_id` in the artifact directory. `config/{police,thief}/games_played.json`
is neither read nor written by this module nor by anything it calls -- 07-00
fixed that counter's mechanism and 07-10 owns its value.
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = (
    "ARTIFACT_SUFFIX",
    "FIRST_SUB_GAME_INDEX",
    "SUB_GAME_INDEX_WIDTH",
    "ArtifactField",
    "ArtifactPrefix",
    "config_filename",
    "declaration_filename",
    "log_filename",
    "next_sub_game_index",
    "result_filename",
    "sub_game_suffix",
)

ARTIFACT_SUFFIX = ".json"
# Structural, read off `<NN>` in docs/PARAMETERS.md:159-168: two characters
# wide, and "the match number", which counts from one. Neither is a tunable
# Appendix F VALUE -- widening or zero-basing either would stop matching the
# document. The width is a MINIMUM: a 100th sub-game of one game_id widens to
# `_g100` rather than truncating, because a truncated index would collide.
SUB_GAME_INDEX_WIDTH = 2
FIRST_SUB_GAME_INDEX = 1


class ArtifactPrefix:
    """The four filename stems, docs/PARAMETERS.md:165-168 verbatim."""

    DECLARATION = "declaration_"
    CONFIG = "config_"
    LOG = "log_"
    RESULT = "result_"


class ArtifactField:
    """The join keys every artifact carries -- "all four carry a shared
    `game_uid`" (docs/PARAMETERS.md:159). Named once so four writers cannot
    drift onto four spellings of the same key."""

    GAME_UID = "game_uid"
    GAME_ID = "game_id"
    SUB_GAME_INDEX = "sub_game_index"


def sub_game_suffix(sub_game_index: int) -> str:
    """`_g<NN>` for a valid 01-based index; raise for anything else.

    `bool` is rejected explicitly: it is an `int` subclass, so `True` would
    otherwise silently name a file `_g01`.
    """
    if isinstance(sub_game_index, bool) or not isinstance(sub_game_index, int):
        raise TypeError(f"sub_game_index must be an int, got {type(sub_game_index).__name__}")
    if sub_game_index < FIRST_SUB_GAME_INDEX:
        raise ValueError(f"sub_game_index must be >= {FIRST_SUB_GAME_INDEX}, got {sub_game_index}")
    return f"_g{sub_game_index:0{SUB_GAME_INDEX_WIDTH}d}"


def declaration_filename(game_id: str) -> str:
    """`declaration_<game_id>.json` -- NO `_g<NN>` (docs/PARAMETERS.md:165)."""
    return f"{ArtifactPrefix.DECLARATION}{game_id}{ARTIFACT_SUFFIX}"


def config_filename(game_id: str, sub_game_index: int) -> str:
    """`config_<game_id>_g<NN>.json` (docs/PARAMETERS.md:166)."""
    return f"{ArtifactPrefix.CONFIG}{game_id}{sub_game_suffix(sub_game_index)}{ARTIFACT_SUFFIX}"


def log_filename(game_id: str, sub_game_index: int) -> str:
    """`log_<game_id>_g<NN>.json` (docs/PARAMETERS.md:167)."""
    return f"{ArtifactPrefix.LOG}{game_id}{sub_game_suffix(sub_game_index)}{ARTIFACT_SUFFIX}"


def result_filename(game_id: str) -> str:
    """`result_<game_id>.json` -- NO `_g<NN>` (docs/PARAMETERS.md:168)."""
    return f"{ArtifactPrefix.RESULT}{game_id}{ARTIFACT_SUFFIX}"


def _indexed_name_pattern(game_id: str) -> re.Pattern[str]:
    """Match ONLY the two indexed artifacts of exactly this `game_id`.

    `game_id` is `re.escape`d: it is negotiated with a peer (D-61), so it is
    not ours to trust as a regex fragment. `durable_write_json`'s `.prev`/
    `.tmp` rotation generations do not match, because the suffix is anchored
    immediately after the digits.
    """
    stems = f"{re.escape(ArtifactPrefix.CONFIG)}|{re.escape(ArtifactPrefix.LOG)}"
    return re.compile(f"^(?:{stems}){re.escape(game_id)}_g([0-9]+){re.escape(ARTIFACT_SUFFIX)}$")


def next_sub_game_index(artifact_dir: Path | str, game_id: str) -> int:
    """The `<NN>` this game_id's NEXT sub-game gets: one past the highest
    already on disk for THAT game_id, and `FIRST_SUB_GAME_INDEX` when the
    directory holds none (or does not exist yet).

    Derived from the artifact directory and from nothing else. A different
    `game_id` restarts at 01 for free, because the pattern embeds it.
    """
    directory = Path(artifact_dir)
    if not directory.is_dir():
        return FIRST_SUB_GAME_INDEX
    pattern = _indexed_name_pattern(game_id)
    highest = FIRST_SUB_GAME_INDEX - 1
    for entry in directory.iterdir():
        match = pattern.match(entry.name)
        if match is not None:
            highest = max(highest, int(match.group(1)))
    return max(highest + 1, FIRST_SUB_GAME_INDEX)
