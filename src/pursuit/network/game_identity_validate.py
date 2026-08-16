"""05-12 / G7: the ONE safety gate a PEER-PUBLISHED game_id passes through.

Split out of `game_identity.py` (135/150 at `0437559`) at the 150-code-line
gate, pre-authorized by 05-12-PLAN.md before the first line was written --
the same split that module's own docstring records it was itself born from
(`agent_wiring.py`, "148/150 -- no room"). CLAUDE.md: split files, never
compress code to fit.

`HandshakeResult.peer_game_id` is read verbatim off the wire
(`handshake_evaluate.py:162`) and `Envelope.from_dict` validates the payload
only as a dict, so it is whatever JSON value the opponent chose. Measured at
`0437559` it reached THREE unsafe sinks with no check at all:

  - a set constructor -- `{ctx.game_uid, result.peer_game_id}`. `game_id: {}`
    or `[]` raised `TypeError: unhashable type` inside
    `adopt_negotiated_game_id`, whose caller `run_agent` guards only
    `except ToolError`, so the process died AT THE HANDSHAKE and WE became
    the side that published no nonces (rule 36);
  - a filesystem path -- `ctx.log_path.parent / f"{resolved}{suffix}"` then
    `.replace(target)`. Measured: `game_id: "../../evil"` relocated our wire
    log two directories UP and, because `turn_commit_ledger.ledger_path`
    derives from `log_path.stem`, took the D-64 nonce ledger with it,
    overwriting whatever was at the destination unchecked. `"a\\x00b"` raised
    `ValueError: embedded null character in dst`, and a 5000-character id
    raised `FileNotFoundError [WinError 3]` -- both from that same line;
  - the audit's membership key. See `absence` below.

WHAT THIS IS NOT: a conformance check. A foreign league implementation whose
ids are UUIDs, or longer than ours, or upper-case, or not hex at all, is an
HONEST peer and MUST still be matched (rules 16/22) -- `audit_state.py`
checks the committed game_id by MEMBERSHIP rather than equality for exactly
that reason. 05-10 refused `isinstance(turn, int)` on the same ground and
measured that the type check, not the peer, was the defect. Only shapes that
cannot safely BE a filename are rejected here.

REJECTION IS NOT AN ACCUSATION, and that is what makes it safe to be strict.
An unusable id means the peer "published no id", which is the case
`adopt_negotiated_game_id` has always handled: the thief keeps its own uid,
and `candidate_game_ids` becomes None, which `audit_state.state_binding_detail`
SKIPS entirely (its stated limitation (a)). So a rejected id costs the peer
nothing -- it disables an optional anti-replay binding for that game and
accuses no one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # typing only -- an eager import here would be a real cycle
    from pursuit.network.agent_context import AgentContext

# Structural limits, NOT tunables and NOT PARAMETERS.md values (CLAUDE.md
# rule 1) -- the `_DECLARE_RETRIES` precedent at agent_audit_wiring.py:41.
# Nobody should ever want to change these, and there is no legal game whose
# outcome depends on them.
#
# _MAX_PEER_GAME_ID derivation: the id becomes a FILENAME STEM on this side.
# The longest component derived from it is `write_declaration`'s
# `declaration_{id}_peer.json` -- 22 characters of fixed affix -- and
# `ledger_path` adds 14 (`{id}.ledger.jsonl`). Every filesystem this project
# runs on caps a single path component at 255 bytes, so the hard ceiling is
# 233. 128 sits comfortably below it while still admitting every convention
# anyone would plausibly use: our own 16-hex uid, a 36-character UUID, a
# 64-hex SHA-256, a team-code-prefixed label.
_MAX_PEER_GAME_ID = 128
_PATH_SEPARATORS = ("/", "\\")
_PARENT_REF = ".."
# Illegal in a Win32 path component; harmless-looking but OSError-raising.
_RESERVED_CHARS = frozenset('<>:"|?*')
_LOWEST_PRINTABLE = " "
_DELETE_CHAR = "\x7f"


def _is_safe_filename_stem(value: str) -> bool:
    """True when *value* can serve as a single, self-contained filename stem.

    Every clause below rejects a shape that was MEASURED to relocate, silently
    rename, or raise from the one `Path.replace` in `adopt_negotiated_game_id`
    -- never a shape that is merely unfamiliar.
    """
    if any(sep in value for sep in _PATH_SEPARATORS) or _PARENT_REF in value:
        return False  # traversal: measured to move our log AND its nonce ledger
    if any(ch in _RESERVED_CHARS or ch < _LOWEST_PRINTABLE or ch == _DELETE_CHAR
           for ch in value):
        return False  # control chars raise; reserved chars raise on Windows
    # Windows silently strips a trailing dot or surrounding whitespace, so the
    # file on disk would NOT be named what we believe we adopted -- which is
    # the artifact-join defect (G2) arriving through a different door.
    return value == value.strip() and not value.endswith(".")


def usable_peer_game_id(value: object) -> str | None:
    """Return *value* when it is safe to use as this game's id, else None.

    None is the module's word for "the peer published no id". It is the ONE
    answer both `negotiated_game_id` (the thief's fallback) and
    `adopt_negotiated_game_id` (the candidate set) consume, so "absent" cannot
    mean two different things on the two lines -- measured at `0437559`, an
    empty-string id meant BOTH: `peer_game_id or own_uid` treated `''` as
    absent and kept our uid, while `result.peer_game_id is not None` treated
    it as present and built `{own_uid, ''}`, a set holding neither of the
    peer's real ids. Every honest record then failed membership at
    `audit_state.py:113-118` and we self-declared a TECHNICAL_LOSS against an
    honest opponent (rules 16/22).
    """
    if not isinstance(value, str) or not value or len(value) > _MAX_PEER_GAME_ID:
        return None
    return value if _is_safe_filename_stem(value) else None


def relocate_log(ctx: AgentContext, resolved: str) -> bool:
    """Move the wire log onto `resolved`, reporting whether the id may now be
    adopted -- the ONE place a game id becomes a `Path` in this codebase.

    BELT AND BRACES over `usable_peer_game_id`, not a substitute for it:
    `resolved` is already a validated stem by the time it arrives, but no
    rule can enumerate every OS-specific illegal name (Win32 still reserves
    `CON`, `LPT1` and friends), and 05-12's first truth is absolute --
    NOTHING a peer sends may raise out of `run_agent`.

    On failure we keep our OWN uid and log path rather than half-adopting.
    `negotiated_game_id`/`candidate_game_ids` are already set by the caller,
    so the peer's id stays on the table for the audit and NOBODY is accused;
    the four artifacts merely fail to join on one stem, which is a degraded
    report, not a lost game."""
    target = ctx.log_path.parent / f"{resolved}{ctx.log_path.suffix}"
    try:
        if ctx.log_path.exists() and ctx.log_path != target:
            ctx.log_path.replace(target)
    except (OSError, ValueError):
        # ValueError is not academic: an embedded NUL raises `ValueError:
        # replace: embedded null character in dst`, NOT OSError -- measured.
        return False
    ctx.log_path = target
    return True
