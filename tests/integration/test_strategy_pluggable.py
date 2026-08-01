"""GATE-3 / E10 + E2 -- pluggable, separate, algorithm-decided (STRAT-03/07,
PRD §10.4 criterion c).

Three proofs, each mapped to one test:

1. Both brain classes named in real config alone (`[strategy].police_class`/
   `thief_class`) build via `registry.build_brain` and play a full game to a
   terminal outcome -- "the swap needs no code edit" (E10).
2. Playing both classes leaves `src/pursuit/network/` byte-for-byte
   unchanged (`git diff` snapshot taken before and after) -- the strategy
   package never reaches into the network layer to make the swap work.
3. `scripts/check_no_llm_in_strategy.py` -- the SAME script CI runs -- is
   loaded by file path and its `find_violations()` is called directly, both
   against the real tree (must be clean) and against a synthetic poisoned
   tree (must fail), proving the CI gate and this test share one
   implementation (QUAL-02), not two.
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess

from pursuit.sdk import engine
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy import registry
from pursuit.strategy.base import BrainBase, Observation
from pursuit.strategy.encoding import blocked_mask
from pursuit.strategy.heuristic import HEURISTIC_BRAIN_NAME
from pursuit.strategy.qlearning import QLEARNING_BRAIN_NAME
from pursuit.strategy.qtable import QTable
from tests.integration.conftest import strategy_params

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
_CHECK_SCRIPT = _REPO_ROOT / "scripts" / "check_no_llm_in_strategy.py"
_BRAIN_CLASSES = (HEURISTIC_BRAIN_NAME, QLEARNING_BRAIN_NAME)


def _params_for_class(role: str, brain_class: str, qtable_path: pathlib.Path) -> StrategyParams:
    params = strategy_params(role, brain_class=brain_class, qtable_path=qtable_path)
    if brain_class == QLEARNING_BRAIN_NAME:
        QTable().save(params.qtable_path)  # empty: every decision routes to the fallback
    return params


def _observation(state: GameState, role: str, target, params: GameParams) -> Observation:
    own = state.cop if role == "cop" else state.thief
    return Observation(
        own_cell=own,
        target_cell=target,
        blocked_mask=blocked_mask(state, own, role, params),
        barriers_used=state.barriers_placed,
        turn_index=state.turn,
    )


def _play_full_game(cop_brain: BrainBase, thief_brain: BrainBase, params: GameParams):
    state = engine.make_state(params)
    outcome = None
    for _ in range(params.move_ceiling):
        cop_decision = cop_brain._decide_move(_observation(state, "cop", state.thief, params), state)
        state, outcome = engine.apply_cop_action(state, cop_decision.move, cop_decision.barrier, params)
        if outcome is not None:
            break
        thief_decision = thief_brain._decide_move(_observation(state, "thief", state.cop, params), state)
        state, outcome = engine.apply_thief_move(state, thief_decision.move, params)
        if outcome is not None:
            break
    return outcome


def test_both_brain_classes_build_from_config_alone_and_play_to_terminal(
    tmp_path: pathlib.Path, default_params: GameParams
) -> None:
    for index, brain_class in enumerate(_BRAIN_CLASSES):
        cop_params = _params_for_class("cop", brain_class, tmp_path / f"cop_{index}.json")
        thief_params = _params_for_class("thief", brain_class, tmp_path / f"thief_{index}.json")
        cop_brain = registry.build_brain("cop", cop_params, default_params)
        thief_brain = registry.build_brain("thief", thief_params, default_params)

        outcome = _play_full_game(cop_brain, thief_brain, default_params)

        assert outcome is not None, f"{brain_class} never reached a terminal outcome"


def _network_diff_snapshot() -> str:
    result = subprocess.run(
        ["git", "diff", "--", "src/pursuit/network"],
        capture_output=True, text=True, check=True, cwd=_REPO_ROOT,
    )
    return result.stdout


def test_brain_swap_leaves_network_layer_byte_for_byte_unchanged(
    tmp_path: pathlib.Path, default_params: GameParams
) -> None:
    before = _network_diff_snapshot()
    for brain_class in _BRAIN_CLASSES:
        cop_params = _params_for_class("cop", brain_class, tmp_path / "net_cop.json")
        thief_params = _params_for_class("thief", brain_class, tmp_path / "net_thief.json")
        registry.build_brain("cop", cop_params, default_params)
        registry.build_brain("thief", thief_params, default_params)
    after = _network_diff_snapshot()
    assert before == after, "swapping brain classes touched src/pursuit/network"


def _load_check_module():
    spec = importlib.util.spec_from_file_location("check_no_llm_in_strategy", _CHECK_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_no_forbidden_import_reachable_from_decision_path() -> None:
    """The CI-facing script and this GATE-3 test call the identical function
    (QUAL-02) -- a clean real tree finds zero violations."""
    check = _load_check_module()
    assert check.find_violations() == []


def test_check_script_flags_a_synthetic_forbidden_import(tmp_path: pathlib.Path) -> None:
    """Proves the check can actually fail (per 03-02's own precedent) --
    against a synthetic tree, never by poisoning real source."""
    check = _load_check_module()
    (tmp_path / "poisoned.py").write_text("import socket\n", encoding="utf-8")
    violations = check.find_violations(root=tmp_path)
    assert len(violations) == 1
    assert "socket" in violations[0]
