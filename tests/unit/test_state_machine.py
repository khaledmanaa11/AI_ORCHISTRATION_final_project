"""Tests for the per-agent turn state machine (NET-04/NET-05, D-09/D-10/D-12).

House style: plain functions, no classes, no mocks of the module under test.
FakeReporter is a test double standing in for 02-04's event log — the exact
injection point this plan exists to create (see state_machine.TransitionReporter).
"""

import pathlib

from pursuit.network.state_machine import (
    ALLOWED_TRANSITIONS,
    State,
    TransitionSeverity,
    TurnStateMachine,
    transition,
)


class FakeReporter:
    """Records every illegal-transition report. Substitutes for 02-04's event_log."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, *, current, target, severity, reason) -> None:
        self.calls.append(
            {"current": current, "target": target, "severity": severity, "reason": reason}
        )


def test_state_set_matches_d09():
    """State has exactly the six D-09 members — no Phase-6 sub-states yet."""
    names = {s.name for s in State}
    assert names == {
        "INIT",
        "HANDSHAKE",
        "MY_TURN",
        "WAIT_OPPONENT",
        "GAME_OVER",
        "ERROR",
    }


def test_transition_table_covers_every_state():
    """Every State member is a key in ALLOWED_TRANSITIONS (D-12, no KeyError reachable)."""
    assert set(ALLOWED_TRANSITIONS) == set(State)


def test_every_legal_transition_is_applied():
    """Sweep the table itself so the test cannot drift from it."""
    for current, targets in ALLOWED_TRANSITIONS.items():
        for target in targets:
            reporter = FakeReporter()
            result = transition(current, target, reporter=reporter)
            assert result.accepted is True
            assert result.state is target
            assert result.severity is None
            assert reporter.calls == []


def test_illegal_transition_is_rejected_and_reported():
    """THE NET-05 GATE: an illegal attempt is rejected and reported exactly once."""
    reporter = FakeReporter()
    result = transition(State.INIT, State.GAME_OVER, reporter=reporter)
    assert result.accepted is False
    assert len(reporter.calls) == 1
    assert reporter.calls[0]["current"] is State.INIT
    assert reporter.calls[0]["target"] is State.GAME_OVER
    assert isinstance(reporter.calls[0]["severity"], TransitionSeverity)
    assert reporter.calls[0]["reason"]


def test_recoverable_attempt_keeps_machine_usable():
    """A duplicate re-delivery is RECOVERABLE — state unchanged, game continues (D-10)."""
    reporter = FakeReporter()
    result = transition(State.WAIT_OPPONENT, State.WAIT_OPPONENT, reporter=reporter)
    assert result.accepted is False
    assert result.severity is TransitionSeverity.RECOVERABLE
    assert result.state is State.WAIT_OPPONENT
    assert result.continues is True
    assert len(reporter.calls) == 1

    follow_up = transition(result.state, State.MY_TURN, reporter=reporter)
    assert follow_up.accepted is True
    assert follow_up.state is State.MY_TURN


def test_protocol_violation_escalates_to_error():
    """Jumping backwards to INIT is never benign — escalates to ERROR (D-10)."""
    reporter = FakeReporter()
    result = transition(State.MY_TURN, State.INIT, reporter=reporter)
    assert result.accepted is False
    assert result.severity is TransitionSeverity.PROTOCOL_VIOLATION
    assert result.state is State.ERROR
    assert result.continues is False
    assert len(reporter.calls) == 1


def test_my_turn_wait_opponent_round_trips():
    """The MY_TURN <-> WAIT_OPPONENT cycle is legal and repeatable, not one-shot (D-09)."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)

    assert machine.attempt(State.HANDSHAKE).accepted is True
    assert machine.attempt(State.MY_TURN).accepted is True

    for _ in range(2):
        result = machine.attempt(State.WAIT_OPPONENT)
        assert result.accepted is True
        assert machine.state is State.WAIT_OPPONENT

        result = machine.attempt(State.MY_TURN)
        assert result.accepted is True
        assert machine.state is State.MY_TURN

    assert reporter.calls == []


def test_terminal_states_have_no_exits():
    """GAME_OVER and ERROR are terminal; any attempt out of them is rejected + reported."""
    assert ALLOWED_TRANSITIONS[State.GAME_OVER] == frozenset()
    assert ALLOWED_TRANSITIONS[State.ERROR] == frozenset()

    reporter = FakeReporter()
    result = transition(State.ERROR, State.MY_TURN, reporter=reporter)
    assert result.accepted is False
    assert len(reporter.calls) == 1


def test_machines_do_not_share_state():
    """NET-02: two machines in one interpreter never observe each other's state."""
    a = TurnStateMachine(FakeReporter())
    b = TurnStateMachine(FakeReporter())

    a.attempt(State.HANDSHAKE)

    assert a.state is State.HANDSHAKE
    assert b.state is State.INIT
    assert TurnStateMachine(FakeReporter()).state is State.INIT


def test_state_machine_module_does_not_import_event_log():
    """Structural guard: keeps 02-03 and 02-04 parallel-safe (no import coupling)."""
    module_path = (
        pathlib.Path(__file__).parents[2]
        / "src"
        / "pursuit"
        / "network"
        / "state_machine.py"
    )
    source = module_path.read_text(encoding="utf-8")
    assert "event_log" not in source
