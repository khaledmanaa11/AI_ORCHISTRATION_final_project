"""Registry wiring (Task 3, D-43): belief.enabled toggling reproduces Phase
3 exactly when off, target_cell's end of vestigial status, and the per-turn
timing budget with belief on.

`belief_cfg`/`scent_model` come from tests/integration/conftest.py (QUAL-02:
one shared fixture, reused by every §10.4 gate module); `default_params` and
`strategy_params()` are inherited from the same package, matching
`test_strategy_pluggable.py`'s own precedent. Reproducibility across seeded
runs and action-replay scoring are split into `test_belief_policy_replay.py`
at the 150-code-line ceiling (CLAUDE.md: split files, never compress code).
"""

from __future__ import annotations

import dataclasses
import random
import time

import pytest

from pursuit.sdk.actions import CopAction
from pursuit.sdk.resolve import make_state, resolve_turn
from pursuit.shared.config import GameParams
from pursuit.shared.inference import NO_EVIDENCE
from pursuit.shared.resolution import PREFERRED
from pursuit.strategy import registry
from pursuit.strategy.base import Observation
from pursuit.strategy.beliefadapter import BeliefAdapter
from pursuit.strategy.scentfield import ScentField
from pursuit.strategy.valuebrain import ValueSearchBrain
from tests.integration.conftest import strategy_params


def _observation(state, role, target):
    own = state.cop if role == "cop" else state.thief
    return Observation(
        own_cell=own, target_cell=target, blocked_mask=0,
        barriers_used=state.barriers_placed, turn_index=state.turn,
    )


def decide(brain, role, state, field):
    """A BeliefAdapter gets .decide() (Regime A: the true opponent cell is
    always integrable here); a raw BrainBase gets ._decide_move(observe)."""
    if isinstance(brain, BeliefAdapter):
        known = state.thief if role == "cop" else state.cop
        return brain.decide(state, NO_EVIDENCE, field, PREFERRED, known_cell=known)
    target = state.thief if role == "cop" else state.cop
    return brain._decide_move(_observation(state, role, target), state)


def play(cop_brain, thief_brain, game_params: GameParams, cop_field=None, thief_field=None):
    state = make_state(game_params)
    outcome, actions = None, []
    for _ in range(game_params.move_ceiling + 1):
        cop_decision = decide(cop_brain, "cop", state, cop_field)
        thief_decision = decide(thief_brain, "thief", state, thief_field)
        cop_action = (
            CopAction(barrier=cop_decision.barrier)
            if cop_decision.barrier is not None
            else CopAction(move=cop_decision.move)
        )
        actions.append((cop_action, thief_decision.move))
        state, outcome = resolve_turn(state, cop_action, thief_decision.move, game_params, PREFERRED)
        if outcome is not None:
            break
    return outcome, state, actions


def test_belief_disabled_reproduces_phase3_behaviour_exactly(default_params, belief_cfg, scent_model):
    disabled = dataclasses.replace(belief_cfg, belief=dataclasses.replace(belief_cfg.belief, enabled=False))
    cop_raw = registry.build_brain("cop", strategy_params("cop"), default_params)
    thief_raw = registry.build_brain("thief", strategy_params("thief"), default_params)
    cop_wired = registry.build_brain(
        "cop", strategy_params("cop"), default_params, belief_config=disabled, scent_model=scent_model
    )
    thief_wired = registry.build_brain(
        "thief", strategy_params("thief"), default_params, belief_config=disabled, scent_model=scent_model
    )
    assert type(cop_wired) is type(cop_raw) is ValueSearchBrain
    assert type(thief_wired) is type(thief_raw) is ValueSearchBrain

    raw = play(cop_raw, thief_raw, default_params)
    wired = play(cop_wired, thief_wired, default_params)
    assert raw == wired


def test_target_cell_is_no_longer_vestigial(default_params, belief_cfg, scent_model):
    """Unlike Phase 3 (ValueSearchBrain never read obs.target_cell -- the
    matrix came straight from state.thief), the SAME true state now yields
    DIFFERENT decisions when the believed opponent cell differs."""
    cop_brain = ValueSearchBrain(role="cop", game_params=default_params, rules=PREFERRED)
    true_state = make_state(default_params)

    def decide_believing(known_cell):
        adapter = BeliefAdapter(cop_brain, "cop", default_params, belief_cfg, scent_model, random.Random(9))
        field = ScentField(model=scent_model, board_size=default_params.board_size)
        return adapter.decide(true_state, NO_EVIDENCE, field, PREFERRED, known_cell=known_cell)

    near = decide_believing((true_state.cop[0], true_state.cop[1] + 1))
    far = decide_believing((default_params.board_size - 1, default_params.board_size - 1))
    assert near != far


@pytest.mark.no_cover
def test_belief_enabled_completes_within_the_per_turn_time_budget(default_params, belief_cfg, scent_model):
    cop_params, thief_params = strategy_params("cop"), strategy_params("thief")
    cop = registry.build_brain(
        "cop", cop_params, default_params, belief_config=belief_cfg, scent_model=scent_model
    )
    thief = registry.build_brain(
        "thief", thief_params, default_params, belief_config=belief_cfg, scent_model=scent_model
    )
    cop_field = ScentField(model=scent_model, board_size=default_params.board_size)
    thief_field = ScentField(model=scent_model, board_size=default_params.board_size)

    state = make_state(default_params)
    outcome = None
    cop_ms, thief_ms = [], []
    # CPU time (thread_time), not wall-clock: max_decision_ms prices the
    # algorithm's own computation, and the timed path is pure compute -- no
    # I/O, no sleeps (test_no_forbidden_import_reachable_from_decision_path
    # keeps sockets/services out of pursuit.strategy). On an idle core the
    # two clocks agree; under a loaded machine wall-clock also counts OS
    # preemption of OTHER processes, which flaked this gate in full-suite
    # runs while saying nothing about the algorithm. thread_time over
    # process_time so a sibling thread in the test process never bills us.
    # The no_cover marker above excludes the coverage tracer for the same
    # reason: tracing is test instrumentation, absent in production, and it
    # multiplies pure-Python CPU here ~6x (measured ~2ms -> ~12ms/decision).
    # Windows charges thread CPU in 15.625ms scheduler ticks, so with the
    # tracer left on, one tick of quantization noise crossed the budget.
    # The budget itself is unchanged: config/*/strategy.json max_decision_ms.
    for _ in range(default_params.move_ceiling + 1):
        start = time.thread_time()
        cop_decision = decide(cop, "cop", state, cop_field)
        cop_ms.append((time.thread_time() - start) * 1000.0)
        start = time.thread_time()
        thief_decision = decide(thief, "thief", state, thief_field)
        thief_ms.append((time.thread_time() - start) * 1000.0)
        cop_action = (
            CopAction(barrier=cop_decision.barrier)
            if cop_decision.barrier is not None
            else CopAction(move=cop_decision.move)
        )
        state, outcome = resolve_turn(state, cop_action, thief_decision.move, default_params, PREFERRED)
        if outcome is not None:
            break

    assert outcome is not None
    print(
        f"\nbelief-enabled per-turn decision CPU time over {len(cop_ms)} turns -- "
        f"cop: max={max(cop_ms):.3f}ms mean={sum(cop_ms) / len(cop_ms):.3f}ms; "
        f"thief: max={max(thief_ms):.3f}ms mean={sum(thief_ms) / len(thief_ms):.3f}ms "
        f"(budget: cop={cop_params.max_decision_ms}ms, thief={thief_params.max_decision_ms}ms)"
    )
    assert max(cop_ms) < cop_params.max_decision_ms
    assert max(thief_ms) < thief_params.max_decision_ms
