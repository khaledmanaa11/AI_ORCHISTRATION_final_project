"""GATE-3 / E10 + E2 -- pluggable, separate, algorithm-decided (STRAT-03/07,
PRD §10.4 criterion c).

Three proofs, each mapped to one test:

1. Both a cop-capable and a thief-capable brain class named in real config
   alone (`[strategy].police_class`/`thief_class`) build via
   `registry.build_brain` and play a full game to a terminal outcome -- "the
   swap needs no code edit" (E10). `value_search` (docs/PRD_matrix_mover.md)
   plays either seat; `chaser_cop`/`greedy_evader` (strategy/naive.py) are
   the fixed, role-specific sparring anchors.
2. Playing every combination leaves `src/pursuit/network/` byte-for-byte
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

import pytest

from pursuit.sdk import engine
from pursuit.sdk.actions import CopAction
from pursuit.shared.config import GameParams
from pursuit.shared.resolution import PREFERRED
from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy import registry
from pursuit.strategy.base import BrainBase, Observation
from pursuit.strategy.naive import CHASER_COP_NAME, GREEDY_EVADER_NAME
from pursuit.strategy.valuebrain import VALUE_SEARCH_BRAIN_NAME
from tests.integration.conftest import strategy_params

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
_CHECK_SCRIPT = _REPO_ROOT / "scripts" / "check_no_llm_in_strategy.py"
_COP_BRAIN_CLASSES = (VALUE_SEARCH_BRAIN_NAME, CHASER_COP_NAME)
_THIEF_BRAIN_CLASSES = (VALUE_SEARCH_BRAIN_NAME, GREEDY_EVADER_NAME)


def _observation(state: GameState, role: str, target, params: GameParams) -> Observation:
    own = state.cop if role == "cop" else state.thief
    return Observation(
        own_cell=own, target_cell=target, blocked_mask=0, barriers_used=0, turn_index=state.turn
    )


def _play_full_game(cop_brain: BrainBase, thief_brain: BrainBase, params: GameParams):
    """Both brains decide from the SAME pre-turn state, then resolve once
    (RULES-RESOLUTION.md): the cop-then-thief loop this replaces let the
    thief see the cop's already-applied move before choosing its own, which
    is exactly the sequential defect the joint turn closes. PREFERRED per
    plan 03-14 -- this test is not about book-only semantics."""
    state = engine.make_state(params)
    outcome = None
    for _ in range(params.move_ceiling):
        cop_decision = cop_brain._decide_move(_observation(state, "cop", state.thief, params), state)
        thief_decision = thief_brain._decide_move(_observation(state, "thief", state.cop, params), state)
        cop_action = (
            CopAction(barrier=cop_decision.barrier)
            if cop_decision.barrier is not None
            else CopAction(move=cop_decision.move)
        )
        state, outcome = engine.resolve_turn(state, cop_action, thief_decision.move, params, PREFERRED)
        if outcome is not None:
            break
    return outcome


def _params_for(role: str, brain_class: str) -> StrategyParams:
    return strategy_params(role, brain_class=brain_class)


def test_both_brain_classes_build_from_config_alone_and_play_to_terminal(
    default_params: GameParams,
) -> None:
    for cop_class, thief_class in zip(_COP_BRAIN_CLASSES, _THIEF_BRAIN_CLASSES, strict=True):
        cop_params = _params_for("cop", cop_class)
        thief_params = _params_for("thief", thief_class)
        cop_brain = registry.build_brain("cop", cop_params, default_params)
        thief_brain = registry.build_brain("thief", thief_params, default_params)

        outcome = _play_full_game(cop_brain, thief_brain, default_params)

        assert outcome is not None, f"{cop_class}/{thief_class} never reached a terminal outcome"


def _inside_git_work_tree() -> bool:
    """True when the suite is running from a git checkout.

    This test compares `git diff` before and after, so it needs a repository.
    A source archive, an sdist, or an unpacked release has no .git, and git
    exits 129 there -- which surfaced as a bare CalledProcessError that said
    nothing about the real cause. CI (actions/checkout) and any clone do have
    one, so the coverage is not lost; it is only declared honestly.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True, check=False, cwd=_REPO_ROOT,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def _network_diff_snapshot() -> str:
    result = subprocess.run(
        ["git", "diff", "--", "src/pursuit/network"],
        capture_output=True, text=True, check=True, cwd=_REPO_ROOT,
    )
    return result.stdout


@pytest.mark.skipif(
    not _inside_git_work_tree(),
    reason="needs a git work tree: the assertion is a git-diff comparison",
)
def test_brain_swap_leaves_network_layer_byte_for_byte_unchanged(
    default_params: GameParams,
) -> None:
    before = _network_diff_snapshot()
    for cop_class, thief_class in zip(_COP_BRAIN_CLASSES, _THIEF_BRAIN_CLASSES, strict=True):
        cop_params = _params_for("cop", cop_class)
        thief_params = _params_for("thief", thief_class)
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
