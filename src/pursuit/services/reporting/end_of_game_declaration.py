"""THE production caller for `declaration_<game_id>.json` -- the one thing
07-02 built and nothing wired.

WHY THIS MODULE EXISTS. 08-01 re-derived at HEAD that
`build_declaration_artifact`, `write_declaration_artifact` and
`DeclarationContext` had ZERO production callers: their own module, a docstring
mention, the package re-export, and tests. `declaration_<game_id>.json` is one
of rule 50's FOUR MANDATORY artifacts and rule 49 wants four repo links inside
it, so a wrapper no game calls means `docs/PARAMETERS.md:165`'s declaration
content had never reached the wire. That is the D7-3 standard -- "test-only
reachability is dead code" -- applied to a deliverable instead of a helper.
`tests/unit/test_declaration_reachability.py` is the gate that keeps it wired.

A SEPARATE MODULE RATHER THAN GROWTH IN `end_of_game.py`, which measured
142/150 code lines: the `end_of_game_chain.py` precedent, split at the same
gate for the same reason. `commit_hash_of` moved here from that module in the
same step -- it reads the Step-0 envelope, which is this module's subject.

CONTAINED SEPARATELY FROM THE MAIL SEND, AND THE ORDER IS LOAD-BEARING. Rule 32
disqualifies the points of an unreported game and rule 35 scores ZERO FOR BOTH
TEAMS when one side fails to report, so nothing on the declaration path may be
able to prevent `result_` from being sent. `declare_game` therefore returns
`None` and logs on ANY failure, and `end_of_game._report` calls it after both
sealed artifacts are on disk and before the chain is built.

WIRE TRUTH ONLY. The start and end times are the earliest and latest timestamps
in THIS side's own JSONL wire log -- events that were actually written, not a
clock read at report time and not anything derived from `ctx.state`. 07-11
closed a rules 8-9 disqualifying leak through exactly that door and this
artifact does not reopen it: `ctx.state` is never touched here, which
`test_declaration_reachability.py` asserts by AST.

THE GAMES-PLAYED FIGURE IS NOT SET HERE, ANYWHERE, BY ANY ROUTE. The embedded
Step-0 envelope carries `games_played_so_far` because rule 37 puts it there,
and its value is today's raw per-role counter, which 07-00 measured moving +14
for zero games. So the artifact's TOP LEVEL carries
`DECLARED_GAMES_PLAYED_UNSET`, saying exactly that and naming the document a
human decides the real figure from. Choosing a number here would be the rule-38
absolute disqualification.
"""

from __future__ import annotations

import logging
from pathlib import Path

from pursuit.network.event_log import EventField
from pursuit.network.secret_wiring import resolve_shared_secret
from pursuit.security.step0_collect import DeclarationField
from pursuit.services.reporting.artifact_declaration import (
    ENVELOPE_DECLARATION_KEY,
    DeclarationContext,
    build_declaration_artifact,
    write_declaration_artifact,
)
from pursuit.services.reporting.log_read import read_tolerating_partial_tail
from pursuit.shared.league_config import LEAGUE_CONFIG_SOURCE, load_league_config

__all__ = ("commit_hash_of", "declare_game", "game_window")

_log = logging.getLogger(__name__)


def commit_hash_of(declaration_envelope: dict) -> str:
    """THIS game's commit hash, out of the Step-0 declaration it ran under.

    Moved verbatim from `end_of_game._commit_hash` at the 150-line split.
    Never a second `git rev-parse`: `step0_collect._git_commit_hash` already
    collected it, "raises loudly on failure -- never a blank hash", and the
    handshake verified the envelope. Re-deriving it could name a different
    commit from the one declared (rule 53, PARAMETERS mandatory rule 5).
    """
    return declaration_envelope[ENVELOPE_DECLARATION_KEY][DeclarationField.COMMIT_HASH]


def game_window(log_path: Path | str) -> tuple[str, str]:
    """`(start_time, end_time)` -- the earliest and latest wire-log timestamps.

    Measured, not stamped: `event_log.append_event` writes an ISO-8601 UTC
    timestamp on every record, so these two are events that really happened.
    A clock read at report time would put the END time minutes late on a run
    whose reporting queued, and would invent a START time entirely.

    Raises `ValueError` on a log with no usable timestamp. It refuses rather
    than substituting `now`: `DeclarationContext` requires a non-empty
    `start_time`, and a fabricated one is worse than a missing artifact.
    """
    records, _truncated = read_tolerating_partial_tail(log_path)
    stamps = sorted(
        record[EventField.TIMESTAMP]
        for record in records
        if isinstance(record, dict) and isinstance(record.get(EventField.TIMESTAMP), str)
    )
    if not stamps:
        raise ValueError(f"no timestamped wire-log record to date this game from: {log_path}")
    return stamps[0], stamps[-1]


def build_game_declaration(
    ctx: object, cfg: object, *, own_envelope: dict, peer_envelope: dict | None, mode: object
) -> dict:
    """The artifact, uncontained. Every failure here is caught by `declare_game`."""
    league = load_league_config(Path(cfg.config_dir) / LEAGUE_CONFIG_SOURCE, mode=mode)
    start_time, end_time = game_window(ctx.log_path)
    return build_declaration_artifact(
        game_uid=ctx.game_uid,
        game_id=ctx.game_uid,
        own_envelope=own_envelope,
        peer_envelope=peer_envelope,
        context=DeclarationContext(
            repo_urls=league.declaration_repo_urls(),
            mcp_server_addresses=league.declaration_mcp_addresses(),
            token_ceiling=league.token_ceiling,
            start_time=start_time,
            end_time=end_time,
        ),
    )


def declare_game(
    ctx: object,
    cfg: object,
    directory: Path | str,
    *,
    own_envelope: dict,
    peer_envelope: dict | None,
    mode: object,
) -> Path | None:
    """Write this game's `declaration_<game_id>.json`. Never raises.

    `peer_envelope` is `HandshakeResult.peer_step0_declaration` -- `None` when
    the peer sent a digest and no content, which the artifact records as an
    honest absence rather than an empty declaration.
    """
    try:
        artifact = build_game_declaration(
            ctx, cfg, own_envelope=own_envelope, peer_envelope=peer_envelope, mode=mode
        )
        secret = resolve_shared_secret(Path(cfg.config_dir))
        return write_declaration_artifact(
            directory, artifact, secret=secret[1] if secret is not None else None
        )
    except Exception:
        _log.exception(
            "the declaration artifact could not be written; the log_ and result_ "
            "artifacts and the mail report are unaffected (rules 32, 35)",
        )
        return None
