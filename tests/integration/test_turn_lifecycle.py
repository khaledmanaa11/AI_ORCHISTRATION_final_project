"""§10.4 gate criterion 3, state-machine core: "The orchestrator (single
entry point) drives turn order via a state machine; illegal transitions are
reported." GATE-2 (two separate processes, no shared runtime state) lives in
test_turn_isolation.py -- split out at the 150-code-line gate (QUAL-08, split
never compress), same criterion set, one module per concern.

LIMITATION: this module runs in ONE pytest process, driving the REAL
`run_turn_loop` for one peer while the other is manipulated only through its
real tool surface over the in-memory transport (RESEARCH Pattern 5). It does
NOT prove OS-level process separation or a literal localhost hop; those are
demonstrated by the standalone two-terminal launch (D-02), run in Task 4 of
plan 02-10 and recorded in 02-10-SUMMARY.md.
"""

from __future__ import annotations

import asyncio
import dataclasses

from fastmcp import Client

from pursuit.constants import Outcome
from pursuit.network import agent_lifecycle
from pursuit.network.config_hash import config_digest
from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.handshake import make_client_caller, perform_handshake
from pursuit.network.orchestrator import run_turn_loop
from pursuit.network.state_machine import State, TransitionSeverity
from pursuit.sdk import engine
from tests.integration.conftest import read_events


async def test_full_lifecycle_init_to_game_over(agent_log_paths, network_params):
    """GATE-3, NET-04, NET-09, D-08, D-09, D-11, D-14, D-15 -- drives the REAL
    `run_turn_loop` for peer A; peer B is manipulated only through its real
    tool surface, over the in-memory transport (never a hand-rolled loop)."""
    log_a, log_b = agent_log_paths
    cfg_a = agent_lifecycle.load_agent_config("config/police")
    cfg_b = agent_lifecycle.load_agent_config("config/thief")
    ctx_a = agent_lifecycle.default_context(cfg_a, game_uid="gate3-full", log_path=log_a)
    ctx_b = agent_lifecycle.default_context(cfg_b, game_uid="gate3-full", log_path=log_b)

    # In-memory transport only (RESEARCH Pattern 5): aim A's outgoing client at
    # B's real server object -- never a socket, never a URL.
    ctx_a.runtime.client = lambda: Client(ctx_b.runtime.server)

    local_digest = config_digest(cfg_a.config_dir / "game_params.json")
    async with ctx_a.runtime.client() as client:
        handshake_result = await perform_handshake(
            machine=ctx_a.machine, reporter=ctx_a.reporter, local_digest=local_digest,
            local_role=ctx_a.role, call_peer=make_client_caller(client),
        )
    # game_params.json is byte-identical across config/{police,thief} (D-06/NET-09);
    # no JSONL record exists for a SUCCESSFUL handshake (only aborts are reported, per
    # handshake.py's design), so the digest agreement is asserted on the in-memory result.
    assert handshake_result.agreed is True

    move_count = {"n": 0}

    def _choose(state, agent, params):
        move_count["n"] += 1
        if move_count["n"] == 1:
            return engine.legal_moves(state, agent, params)[0]
        return state.thief  # the second cop move lands on the thief -- a real SDK capture

    ctx_a.choose_move = _choose

    # Positions overridden to adjacent, reachable cells: resolve_turn now
    # validates legality (RULES-RESOLUTION.md), so the old scenario -- the
    # cop's second move teleporting from wherever its own first legal move
    # left it straight onto the thief's first-move destination, several
    # cells away -- is no longer reachable (it only "worked" because the
    # superseded apply_move validated nothing). The thief STAYS both
    # rounds (always legal), and a SECOND thief move is now injected too: a
    # capture requires both sides' actions to be known before resolve_turn
    # can fire -- the single-sided-capture bug this migration fixes -- so
    # round 2 needs its own thief input, unlike the old apply_cop_action-
    # only capture check that fired from the cop's move alone.
    ctx_a.state = dataclasses.replace(ctx_a.state, cop=(0, 0), thief=(1, 1))
    thief_dest = ctx_a.state.thief

    async def _inject(turn: int) -> None:
        envelope = Envelope(
            type=MessageType.MOVE, turn=turn, sender="thief",
            payload={"x": thief_dest[0], "y": thief_dest[1]},
        )
        args = {k: v for k, v in envelope.to_dict().items() if k != EnvelopeKey.TYPE}
        async with Client(ctx_a.runtime.server) as client:
            await client.call_tool("receive_move", args)

    await _inject(1)
    await _inject(2)

    # An outer wall-clock ceiling, sourced from config (never a new literal), as a
    # safety net only -- the loop itself completes almost instantly (D-13, RESEARCH).
    outcome = await asyncio.wait_for(run_turn_loop(ctx_a), timeout=network_params.response_timeout)

    assert outcome is Outcome.CAPTURE
    assert ctx_a.machine.state is State.GAME_OVER  # criterion 3's terminal proof

    events = read_events(log_a)
    assert events, "no records were written"
    for record in events:
        assert isinstance(record, dict)  # every line parsed as valid JSON already

    # HANDSHAKE -> MY_TURN -> WAIT_OPPONENT is read from turn_record's own
    # state_from/state_to fields, in order (D-09's repeated cycle). INIT never
    # appears: 02-03's legal transitions apply silently and 02-09 logs only on
    # send/receive/illegal/technical-win/game-over, so the pre-handshake INIT
    # state is never independently durable -- documented here, not fabricated.
    path = []
    for record in events:
        if "state_from" in record and "state_to" in record:
            path.append(record["state_from"])
            path.append(record["state_to"])
    if any(r["event"] == "game_over" for r in events):
        path.append("game_over")
    assert _is_ordered_subsequence(
        path, [State.HANDSHAKE.value, State.MY_TURN.value, State.WAIT_OPPONENT.value, "game_over"]
    )
    assert State.ERROR.value not in path

    # D-14: at least one durable record per turn that actually ran -- the sends
    # `_choose` actually made plus the one injected receive, never a magic count.
    turn_records = [r for r in events if r["event"] in ("message_sent", "message_received")]
    assert len(turn_records) >= move_count["n"] + 1


async def test_illegal_transition_reported_with_severity(agent_log_paths):
    """GATE-3, NET-05, D-10, D-11 -- NET-05's real gate is 'was it reported',
    asserted on the JSONL record itself, for BOTH severities, through the
    REAL wired reporter (make_transition_reporter -> append_event)."""
    log_a, _log_b = agent_log_paths
    cfg = agent_lifecycle.load_agent_config("config/police")
    ctx = agent_lifecycle.default_context(cfg, game_uid="gate3-illegal", log_path=log_a)

    ctx.machine.attempt(State.HANDSHAKE)
    ctx.machine.attempt(State.MY_TURN)

    # RECOVERABLE: a duplicate/self re-delivery is illegal but benign -- the game keeps running.
    recoverable = ctx.machine.attempt(State.MY_TURN)
    assert recoverable.accepted is False
    assert recoverable.severity is TransitionSeverity.RECOVERABLE
    assert ctx.machine.state is State.MY_TURN
    assert ctx.machine.attempt(State.WAIT_OPPONENT).accepted is True  # still playable

    # PROTOCOL_VIOLATION: an out-of-table jump escalates to State.ERROR and ends the game.
    violation = ctx.machine.attempt(State.INIT)
    assert violation.accepted is False
    assert violation.severity is TransitionSeverity.PROTOCOL_VIOLATION
    assert ctx.machine.state is State.ERROR

    events = read_events(log_a)
    illegal_records = [r for r in events if r["event"] == "illegal_transition"]
    assert len(illegal_records) == 2
    for record in illegal_records:
        assert "state_from" in record and "state_to" in record
        assert record["details"]["severity"] in {
            TransitionSeverity.RECOVERABLE.value,
            TransitionSeverity.PROTOCOL_VIOLATION.value,
        }
    severities = {r["details"]["severity"] for r in illegal_records}
    assert severities == {
        TransitionSeverity.RECOVERABLE.value,
        TransitionSeverity.PROTOCOL_VIOLATION.value,
    }


def _is_ordered_subsequence(haystack: list, needle: list) -> bool:
    """True iff every element of `needle` appears in `haystack`, IN ORDER,
    not necessarily contiguously (MY_TURN <-> WAIT_OPPONENT legitimately
    repeats, D-09)."""
    it = iter(haystack)
    return all(target in it for target in needle)
