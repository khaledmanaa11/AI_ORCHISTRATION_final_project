"""StrategyParams + the field/key/validator schema table for strategy.json.

Run-2 architecture (docs/PRD_matrix_mover.md): the live decision path reads
exactly three tunables -- `weights_path` (the trained 15-weight artefact,
falls back to the hand-set prior when unset), `epsilon_eval` (off-policy
exploration; must be 0.0 in a league game) and `max_decision_ms` (the
per-turn budget). Every Q-learner-only key that lived here for run 1
(`alpha`, `gamma`, `qtable_path`, `sparring_mix`, `search_depth_cap`, ...)
is gone -- the matrix-game mover has no training-time hyperparameter that
the LIVE loader still needs to validate. training/ owns its own tunables
directly as module constants (see training/run_selfplay.py,
training/run_evolve.py), never through this config surface.

Every field here is an engineering default unless the field's own PRD entry
says otherwise (project rule 1) -- none is claimed as a docs/PARAMETERS.md
value.
"""

from dataclasses import dataclass

from pursuit.config_keys import StrategyKey
from pursuit.shared.loader_helpers import require_float, require_int, require_str

STRATEGY_GROUP = "strategy"


@dataclass(frozen=True)
class StrategyParams:
    """Immutable container for every field the live decision path reads."""

    brain_class: str
    weights_path: str
    epsilon_eval: float
    max_decision_ms: int
    leaf_mode: str
    relax_turn: int


# (field_name, key, requirer, is_unit_interval [0, 1] range check)
SCHEMA = [
    ("weights_path", StrategyKey.WEIGHTS_PATH, require_str, False),
    ("epsilon_eval", StrategyKey.EPSILON_EVAL, require_float, True),
    ("max_decision_ms", StrategyKey.MAX_DECISION_MS, require_int, False),
    ("leaf_mode", StrategyKey.LEAF_MODE, require_str, False),
    ("relax_turn", StrategyKey.RELAX_TURN, require_int, False),
]

#: The only leaf modes ValueSearchBrain implements; the loader rejects the rest.
LEAF_MODES = frozenset({"stock", "adaptive", "cautious"})
