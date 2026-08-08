"""Config-driven brain construction: the only place a BrainBase is built (STRAT-03, D-07).

Resolution goes through the explicit dict below -- never eval, exec, or an
unguarded importlib call on a config string. A config file that could name
an arbitrary importable would be an arbitrary-code-execution path, and this
project ships config alongside the agent.

Run-2 architecture (docs/PRD_matrix_mover.md): exactly three brains are
registered. `ValueSearchBrain` is the shipped matrix-game mover and plays
either seat; `ChaserCop`/`GreedyEvader` are the fixed sparring anchors
(strategy/naive.py) also playable through config for scouting and league
warm-ups. The old run-1 tabular Q-learner (`QLearningBrain`) and its
`HeuristicBrain` fallback partner are gone -- superseded, not merely
replaced (see the PRD's Sec1 for why simultaneous play made Q-learning
unsound here).

`build_brain` also threads a `GameParams` through to every brain's
constructor (03-04 deviation, Rule 2/3): `BrainBase._pick_move(obs, state)`
(03-02) deliberately carries no board-config parameter, but a real brain's
internal search/BFS machinery needs `board_size` to compute legal moves
(`pursuit.shared.board.get_legal_moves`). 03-02's own `ChooseMove` seam in
`orchestrator.py` already receives `GameParams` per call
(`Callable[[GameState, str, GameParams], tuple[int, int]]`); this mirrors
that by injecting it once, at construction, rather than changing the frozen
`_pick_move`/`_decide_move` ABC signature.
"""

from pursuit.shared.config import GameParams
from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy.base import BrainBase
from pursuit.strategy.naive import CHASER_COP_NAME, GREEDY_EVADER_NAME, ChaserCop, GreedyEvader
from pursuit.strategy.valuebrain import VALUE_SEARCH_BRAIN_NAME, ValueSearchBrain

# Explicit name -> class registry.
_BRAIN_REGISTRY: dict[str, type[BrainBase]] = {
    VALUE_SEARCH_BRAIN_NAME: ValueSearchBrain,
    CHASER_COP_NAME: ChaserCop,
    GREEDY_EVADER_NAME: GreedyEvader,
}


def build_brain(role: str, params: StrategyParams, game_params: GameParams) -> BrainBase:
    """Construct the BrainBase named by params.brain_class for role.

    Parameters
    ----------
    role:
        "cop" or "thief" -- passed through to the brain's constructor so a
        two-stage brain (movement then barrier) knows which role it plays.
    params:
        The per-role StrategyParams already resolved by
        load_strategy_config(); params.brain_class names the class to build.
    game_params:
        The board/rules GameParams (game_params.json) every brain needs for
        legal-move generation and BFS distance -- never resolved internally
        from a role-guessed path (see module docstring).

    Raises
    ------
    ValueError
        If params.brain_class is not a registered name -- names the
        offending value and every known name. Never falls back to a
        default brain: a silent fallback means a training run or a league
        game played by the wrong policy with no signal anything is wrong.
    """
    name = params.brain_class
    if name not in _BRAIN_REGISTRY:
        known = sorted(_BRAIN_REGISTRY)
        raise ValueError(f"Unknown brain class {name!r}; known classes: {known}")
    brain_cls = _BRAIN_REGISTRY[name]
    return brain_cls(role=role, params=params, game_params=game_params)
