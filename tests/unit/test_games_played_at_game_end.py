"""07-00 -- the games-played counter driven END TO END through the real
`run_agent`, at every exit that function has. Rules 37/38: a false
games-played declaration is an ABSOLUTE DISQUALIFICATION
(`docs/RULES.md:79`), so it is not enough that `record_completed_game` is
correct in isolation -- it has to be CALLED at the right moment and at no
other, and only the production entry point can say whether it is.

Sibling of `test_games_played_counter.py` (which owns the unit-level half),
split at the 150-code-line gate. `_SEED` and `_seeded` are imported from
there rather than re-derived, so the two files cannot disagree about what a
seeded throwaway config directory is.

Every case here points `cfg.config_dir` at `tmp_path` and then RESTORES the
real `record_completed_game`, because these are the cases that must
exercise the production file write. `tests/_shipped_config_guard.py` is
what makes that safe to do.

WHY THE LAST TWO CASES EXIST. The increment sits AFTER the commit-reveal
audit, and `record_completed_game`'s docstring calls that placement
load-bearing. It was not: a probe that moved the call to immediately after
`run_turn_loop` passed all fourteen cases that existed at the time,
including every case in the sibling file and all four order assertions in
`test_agent_entrypoint.py`. A game whose only result comes from the audit
would simply have gone uncounted -- an UNDER-declaration, which rule 38
punishes exactly as hard as an over-declaration. Found by running the wrong
fix, not by reading the diff.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network import agent_entrypoint, agent_step0_wiring
from pursuit.security import step0_collect
from tests.unit._agent_entrypoint_fixtures import _FakeCtx, _FakeSecurity, _patch_common
from tests.unit.test_games_played_counter import _SEED, _seeded


async def _counter_after_one_run(
    monkeypatch, tmp_path, *, agreed, outcome, commit_reveal=False, audit_outcome=None,
):
    """Drive the REAL `run_agent` -- collaborators faked, zero sockets, zero
    sleeps -- against a THROWAWAY config dir, and return what the counter
    reads afterwards together with the sequence that actually ran."""
    config_dir, _, counter = _seeded(tmp_path)
    order: list[str] = []
    _patch_common(monkeypatch, agreed=agreed, order=order, config_dir=config_dir)
    monkeypatch.setattr(
        agent_entrypoint, "record_completed_game", agent_step0_wiring.record_completed_game,
    )

    def _context(cfg_arg, **kwargs):
        order.append("default_context")
        ctx = _FakeCtx()
        ctx.security = _FakeSecurity(commit_reveal=commit_reveal)
        return ctx

    async def _turn_loop(ctx):
        order.append("run_turn_loop")
        return outcome

    async def _audit(ctx, *, board_outcome=None):
        order.append("run_final_audit")
        return audit_outcome

    monkeypatch.setattr(agent_entrypoint, "default_context", _context)
    monkeypatch.setattr(agent_entrypoint, "run_turn_loop", _turn_loop)
    monkeypatch.setattr(agent_entrypoint, "run_final_audit", _audit)
    await agent_entrypoint.run_agent(str(config_dir))
    return step0_collect.read_games_played(counter), order


async def test_run_agent_counts_a_game_that_ended(monkeypatch, tmp_path):
    """The happy path: the turn loop produced an outcome, so a `game_over`
    record stands behind it and the game is counted exactly once."""
    count, order = await _counter_after_one_run(
        monkeypatch, tmp_path, agreed=True, outcome=Outcome.CAPTURE,
    )
    assert "run_turn_loop" in order, "the turn loop never ran -- the case proves nothing"
    assert count == _SEED + 1


async def test_run_agent_counts_nothing_when_the_handshake_never_agreed(monkeypatch, tmp_path):
    """`run_agent`'s early `return None`. A handshake that never became a
    game is not a game played -- and this is the exit the old call site,
    inside `write_declaration`, could not distinguish."""
    count, order = await _counter_after_one_run(
        monkeypatch, tmp_path, agreed=False, outcome=Outcome.CAPTURE,
    )
    assert "run_turn_loop" not in order, "a disagreed handshake must not reach the turn loop"
    assert count == _SEED


async def test_run_agent_counts_nothing_when_the_game_never_resolved(monkeypatch, tmp_path):
    """The turn loop ran but no leg produced an outcome, so no `game_over`
    record was written either. Nothing to declare."""
    count, order = await _counter_after_one_run(
        monkeypatch, tmp_path, agreed=True, outcome=None,
    )
    assert "run_turn_loop" in order
    assert count == _SEED


async def test_run_agent_counts_a_game_the_audit_alone_decided(monkeypatch, tmp_path):
    """THE case that separates "count after the audit" from "count after the
    turn loop", and the one no test defended until a probe went looking.

    The turn loop never resolved, so the board outcome is None; the mutual
    audit then returns TECHNICAL_LOSS, which `run_agent` adopts as the
    game's result and which this side will report under rule 35. That is a
    game PLAYED -- lost, not skipped. Counting before the audit misses it,
    and an under-declaration is a rule-38 breach just as an
    over-declaration is."""
    count, order = await _counter_after_one_run(
        monkeypatch, tmp_path, agreed=True, outcome=None,
        commit_reveal=True, audit_outcome=Outcome.TECHNICAL_LOSS,
    )
    assert "run_final_audit" in order, "the audit never ran -- the case proves nothing"
    assert count == _SEED + 1


async def test_run_agent_counts_nothing_when_not_even_the_audit_decided(monkeypatch, tmp_path):
    """The paired control that stops the case above from degenerating into
    "count anything once the audit has run": commit-reveal ON, turn loop
    unresolved, and an audit that reaches no verdict either. Without this,
    a fix that counted every commit-reveal game regardless of outcome would
    pass the case above."""
    count, order = await _counter_after_one_run(
        monkeypatch, tmp_path, agreed=True, outcome=None,
        commit_reveal=True, audit_outcome=None,
    )
    assert "run_final_audit" in order
    assert count == _SEED
