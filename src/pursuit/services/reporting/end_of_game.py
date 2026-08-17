"""THE game-end hook: build `log_`, build `result_`, send it through the
Figure-13 chain -- and change nothing about the game because it ran.

THE FULL RATIONALE IS `docs/PRD_end_of_game.md` -- the per-mechanism PRD
CLAUDE.md Sec2.3 requires, and where this module's reasoning moved when the
docstring took the file past 150 (the `PRD_log_artifact.md` precedent). It
carries the containment argument, the watchdog arithmetic, the rule-35 defect
a real game exposed, and the rule-21 asymmetry. What follows is the contract.

A SEPARATE MODULE RATHER THAN GROWTH IN `agent_entrypoint.py`, following the
`agent_audit_wiring -> agent_audit_exchange -> agent_audit_verdict` precedent.

A REPORTING FAILURE MUST NOT FORGE A TECHNICAL LOSS. The hook runs inside the
try whose `finally` tears the runtime down, one line before `return outcome`;
an exception there reaches `main.py:58`'s `asyncio.run` and exits non-zero,
which since 06-05 MEANS an audit mismatch. So it is contained at its own
boundary and never touches `outcome`, `ctx.state` or the exit code.
`except Exception`, NEVER `BaseException`: `CancelledError` must still
propagate, which is the reason `run_agent`'s own `try/finally` exists.

THE ARTIFACT DIRECTORY IS PER ROLE -- `<artifact_dir>/<role>/`, the split
`agent_lifecycle` already uses for `logs/<role>/`. One real `dev_launch.py`
game proved why: two processes sharing one repository shared one
`artifact_dir`, and the second seat's rewrite ATE the first seat's report
(PRD Sec4). `reporting.json` is not edited; its value is the artifact ROOT.

WIRE TRUTH ONLY, and the `audit_verdict` is lifted out of the `log_` artifact
this hook has just written, so the two artifacts cannot disagree about it.
Both artifacts are written BEFORE the chain is built, so a transport that
refuses to construct still leaves rule 50's committable files on disk.

08-04: the THIRD artifact, `declaration_<game_id>.json`, is written here too,
through `end_of_game_declaration.declare_game` and contained SEPARATELY --
PRD Sec7 carries the reasoning.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from pursuit.constants import Outcome
from pursuit.services.reporting.artifact_log import LogArtifactField, write_log_artifact
from pursuit.services.reporting.artifact_result import record_sub_game
from pursuit.services.reporting.artifacts import next_sub_game_index
from pursuit.services.reporting.chain import ReportingChain, SendOutcome
from pursuit.services.reporting.end_of_game_chain import (
    QUOTA_FILENAME,
    build_reporting_chain,
    watchdog_touching,
)
from pursuit.services.reporting.end_of_game_declaration import commit_hash_of, declare_game
from pursuit.services.reporting.result_agreement import build_agreement
from pursuit.services.reporting.sink import MailSink
from pursuit.shared.reporting_config import REPORTING_CONFIG_SOURCE, load_reporting_config

__all__ = (
    "QUOTA_FILENAME",
    "EndOfGameReport",
    "build_reporting_chain",
    "report_game_end",
    "watchdog_touching",
)

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class EndOfGameReport:
    """What one game-end hook produced. Returned for observation only -- no
    caller on the production path reads it, and none may act on it.

    `declaration_artifact` is `None` when the declaration could not be built;
    the field exists so that failure is observable rather than merely logged,
    since a silently-absent mandatory artifact is the defect this plan closed.
    """

    log_artifact: Path
    result_artifact: Path
    send: SendOutcome
    pending: int
    declaration_artifact: Path | None = None


async def report_game_end(
    ctx: object,
    cfg: object,
    *,
    outcome: Outcome | None,
    declaration_envelope: dict,
    peer_declaration_envelope: dict | None = None,
    artifact_dir: Path | str | None = None,
    sink: MailSink | None = None,
    chain: ReportingChain | None = None,
) -> EndOfGameReport | None:
    """Report this game. Returns; never raises; never changes the game.

    `artifact_dir` names the artifact ROOT; this side's files land in
    `<root>/<ctx.role>/` (see the module docstring for the real game that
    proved why). It defaults to `reporting.json`'s `artifact_dir`.

    `None` for a game that produced no outcome -- the same definition of
    "completed" `record_completed_game` states beside this call site, and for
    the same reason: a handshake that never became a game is not a game to
    report. `None` again when reporting failed, which is logged and contained.
    """
    if outcome is None:
        return None
    try:
        return await _report(
            ctx, cfg, outcome=outcome, declaration_envelope=declaration_envelope,
            peer_declaration_envelope=peer_declaration_envelope,
            artifact_dir=artifact_dir, sink=sink, chain=chain,
        )
    except Exception:
        _log.exception(
            "end-of-game reporting failed; the game's outcome, its last game_over "
            "record and this process's exit code are unchanged",
        )
        return None


async def _report(
    ctx: object,
    cfg: object,
    *,
    outcome: Outcome,
    declaration_envelope: dict,
    peer_declaration_envelope: dict | None,
    artifact_dir: Path | str | None,
    sink: MailSink | None,
    chain: ReportingChain | None,
) -> EndOfGameReport:
    """The uncontained sequence. Every failure here is caught by the caller."""
    params = load_reporting_config(Path(cfg.config_dir) / REPORTING_CONFIG_SOURCE)
    root = Path(artifact_dir) if artifact_dir is not None else Path(params.artifact_dir)
    directory = root / ctx.role
    game_id = ctx.game_uid
    index = next_sub_game_index(directory, game_id)

    log_path = write_log_artifact(
        directory, ctx.log_path, game_uid=game_id, game_id=game_id, sub_game_index=index,
    )
    written = json.loads(log_path.read_text(encoding="utf-8"))
    agreement = build_agreement(
        ctx.log_path,
        own_outcome=outcome,
        audit_verdict=written[LogArtifactField.AUDIT_VERDICT],
    )
    budget = ctx.language.gatekeeper.budget if ctx.language is not None else None
    artifact, result_path = record_sub_game(
        directory, game_uid=game_id, game_id=game_id, role=ctx.role, sub_game_index=index,
        agreement=agreement.to_dict(), budget=budget,
        commit_hash=commit_hash_of(declaration_envelope), log_artifact=log_path.name,
    )
    # The third mandatory artifact, after the two sealed ones are on disk and
    # before the chain is built. `declare_game` contains its own failures, so
    # this line cannot stop the send below (rules 32, 35).
    declaration_path = declare_game(
        ctx, cfg, directory, own_envelope=declaration_envelope,
        peer_envelope=peer_declaration_envelope, mode=params.mode,
    )

    sender = chain or build_reporting_chain(
        params, watchdog=ctx.watchdog, artifact_dir=directory,
        quota_dir=ctx.log_path.parent, sink=sink,
    )
    send = await sender.send(artifact)
    return EndOfGameReport(
        log_artifact=log_path, result_artifact=result_path,
        send=send, pending=sender.pending, declaration_artifact=declaration_path,
    )
