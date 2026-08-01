"""Optional sparring opponent: rmisegal/Game-P2P-Cop-Chase (D-21).

ADR -- never vendored, never a submodule. The reference repo's LICENSE is an
Educational Use EULA (c) Dr. Yoram Segal / GTAI; SS4c forbids redistributing,
sublicensing, publishing, or sharing the software with any third party who
is not an enrolled Segal student, and this project ships two PUBLIC repos at
Phase 8. Their `requires-python = ">=3.13"` also can never resolve against
our `>=3.10` via `uv add`. The only zero-redistribution, zero-resolver-
conflict shape is an opt-in LOCAL CLONE the operator points
`training.reference_impl_path` at (gitignored, empty default) -- reached
here by a guarded `sys.path` insert + import, never a vendored copy.

Four verified adapter translations (RESEARCH Sec1), each required or the
reference agent plays a materially different game than ours:
  1. Move set: construct with move_set=["N","S","E","W"] -- Board(size)
     otherwise falls back to 8-direction king movement our 5-action engine
     rejects.
  2. Belief seeding: BeliefGrid starts uniform (argmax = (0,0)); seed it via
     observe_smell so a *known*-target reference agent doesn't walk to the
     corner (Phase 3's known-target contract, D-11).
  3. Barrier semantics: MoveType.BARRIER REPLACES the move that turn and
     walls the neighbour cell in `direction`; translated here as move=STAY
     plus a barrier proposal, matching our engine's separate move+barrier
     call shape.
  4. Call `_decide_move`, never `decide` -- `decide` invokes the LLM/banter
     path (loads `strategy/`, `peer/`, `infra/`), and rule 25 forbids an LLM
     anywhere near a move, even in training.

Import-guarded and never raises: an empty path, a missing clone, or any
other ImportError all log a warning naming the reason and return None, so
the default (no-clone) configuration trains fine and the sparring pool
renormalizes its weights (training.sparring._available_weights).
"""

from __future__ import annotations

import logging
import random
import sys
from pathlib import Path

from pursuit.constants import MoveSource
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.base import BrainBase, Decision, Observation

logger = logging.getLogger(__name__)

_MOVE_SET = ["N", "S", "E", "W"]


def build_reference_opponent(
    role: str, reference_impl_path: str, game_params: GameParams, rng: random.Random
) -> BrainBase | None:
    """Return the reference-brain adapter for `role`, or None (D-21)."""
    if not reference_impl_path:
        logger.warning("reference_impl_path is empty -- sparring pool renormalizes without it")
        return None
    try:
        return _ReferenceBrain(role, reference_impl_path, game_params, rng)
    except ImportError as exc:
        logger.warning("reference implementation unavailable (%s) -- pool renormalizes", exc)
        return None


class _ReferenceBrain(BrainBase):
    """Adapts rmisegal/Game-P2P-Cop-Chase's PoliceBrain/ThiefBrain.

    Rebuilds their OwnGameState/BeliefGrid FRESH on every `_decide_move`
    call from OUR GameState/Observation rather than tracking a second,
    parallel mutable object across turns -- our engine stays the single
    source of truth and this adapter never accumulates its own drift.
    """

    def __init__(
        self, role: str, clone_path: str, game_params: GameParams, rng: random.Random
    ) -> None:
        sys.path.insert(0, str(Path(clone_path) / "src"))
        from police_thief.constants import DELTAS, MoveType, Role  # noqa: PLC0415
        from police_thief.domain.belief import BeliefGrid  # noqa: PLC0415
        from police_thief.domain.brains import PoliceBrain, ThiefBrain  # noqa: PLC0415
        from police_thief.domain.own_state import OwnGameState  # noqa: PLC0415

        self._role = role
        self._board_size = game_params.board_size
        self._barriers_max = game_params.barrier_quota
        self._Role, self._MoveType, self._DELTAS = Role, MoveType, DELTAS
        self._OwnGameState, self._BeliefGrid = OwnGameState, BeliefGrid
        brain_cls = PoliceBrain if role == "cop" else ThiefBrain
        self._brain = brain_cls(llm=None, rng=rng, trash=object())  # trash must be non-None

    def _decide_move(self, obs: Observation, state: GameState) -> Decision:
        ref_role = self._Role.POLICE if self._role == "cop" else self._Role.THIEF
        ref_state = self._OwnGameState(ref_role, obs.own_cell, self._board_size, move_set=_MOVE_SET)
        belief = self._BeliefGrid(self._board_size)
        row, col = obs.target_cell
        belief.observe_smell({f"{row},{col}": 1.0})  # translation 2: seed the known target
        move_type, direction = self._brain._decide_move(ref_state, belief, self._barriers_max)
        if move_type is self._MoveType.HOLD or direction is None:
            return Decision(move=obs.own_cell, source=MoveSource.HEURISTIC)
        dr, dc = self._DELTAS[direction]
        neighbor = (obs.own_cell[0] + dr, obs.own_cell[1] + dc)
        if move_type is self._MoveType.BARRIER:  # translation 3: barrier replaces the move
            barrier = neighbor if self._role == "cop" else None
            return Decision(move=obs.own_cell, source=MoveSource.HEURISTIC, barrier=barrier)
        return Decision(move=neighbor, source=MoveSource.HEURISTIC)

    def _pick_move(self, obs: Observation, state: GameState) -> Decision:
        """ABC compliance only -- the harness always calls `_decide_move`
        (never both) so the reference brain's own RNG never draws twice."""
        decision = self._decide_move(obs, state)
        return Decision(move=decision.move, source=decision.source)
