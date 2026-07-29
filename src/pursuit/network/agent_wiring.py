"""Small wiring closures + config-dir readers -- split out of
agent_lifecycle.py at the 150-code-line gate (Segal Table 5): role.json
reading, the NET-05/NET-07 JSONL sink closures, and the NET-09 inbound
handshake seam. `agent_lifecycle.py` imports every name here and re-exports
it, so `agent_lifecycle.load_role` / `.make_transition_reporter` /
`.make_freeze_handler` / `.make_handshake_responder` keep working for every
caller (including the tests) exactly as if they were still defined there.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from pursuit.network import turn_events
from pursuit.network.envelope import EnvelopeKey, MessageType
from pursuit.network.event_log import append_event
from pursuit.network.handshake import respond_to_handshake
from pursuit.network.state_machine import (
    State,
    TransitionReporter,
    TransitionSeverity,
    TurnStateMachine,
)
from pursuit.network.tools import HandshakeHandler


class RoleKey:
    """The one key role.json carries -- named, not a bare string literal."""

    ROLE = "role"


def load_role(config_dir: Path | str) -> str:
    """Read the per-agent role.json (NET-01: role comes from the config dir
    named on the command line, never a flag or a global)."""
    path = Path(config_dir) / "role.json"
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    role = data.get(RoleKey.ROLE)
    if not isinstance(role, str) or not role.strip():
        raise ValueError(f"{path}: missing or blank {RoleKey.ROLE!r}")
    return role


def make_transition_reporter(log_path: Path, *, game_uid: str, role: str) -> TransitionReporter:
    """NET-05 sink: every illegal transition persists to the JSONL log (D-11)
    and echoes one console line. `turn=0` here is structural, not a game
    number: 02-03's TransitionReporter Protocol carries no turn field."""

    def _reporter(
        *, current: State, target: State, severity: TransitionSeverity, reason: str
    ) -> None:
        record = turn_events.illegal_transition_record(
            game_uid=game_uid, turn=0, sender=role, current=current, target=target,
            severity=severity, reason=reason,
        )
        append_event(log_path, record, echo=print)

    return _reporter


def make_freeze_handler(
    log_path: Path, *, game_uid: str, role: str, threshold_seconds: float
) -> Callable[[], None]:
    """NET-07 sink (RESEARCH Pitfall 6): writes and fsyncs (via append_event)
    a watchdog_incident record BEFORE Watchdog's injected exit_action runs.
    `idle_seconds` is reported as the threshold itself -- the on_freeze seam
    is a zero-argument callable and carries no measured idle duration; the
    threshold is the one honest lower bound available at this call site."""

    def _on_freeze() -> None:
        record = turn_events.watchdog_incident_record(
            game_uid=game_uid, turn=0, sender=role,
            idle_seconds=threshold_seconds, threshold_seconds=threshold_seconds,
        )
        append_event(log_path, record)

    return _on_freeze


def make_handshake_responder(
    *, machine: TurnStateMachine, reporter: TransitionReporter, local_digest: str, local_role: str
) -> HandshakeHandler:
    """THE NET-09 inbound seam (D-05, D-08, design note 12): an `async def`
    adapter around 02-08's synchronous `respond_to_handshake` -- required to
    be async because 02-06's tool body awaits it directly on this process's
    event loop (RESEARCH Pitfall 2)."""

    async def _respond(turn: int, sender: str, payload: dict) -> dict:
        reply, _result = respond_to_handshake(
            machine=machine, reporter=reporter, local_digest=local_digest,
            local_role=local_role,
            incoming={
                EnvelopeKey.TYPE: MessageType.HANDSHAKE.value,
                EnvelopeKey.TURN: turn,
                EnvelopeKey.SENDER: sender,
                EnvelopeKey.PAYLOAD: payload,
            },
        )
        return reply

    return _respond
