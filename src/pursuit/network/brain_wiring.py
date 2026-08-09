"""Build the mover (D-43) and its scent field, once per process (Task 2).

Deviation (Rule 3 - blocking): not in 04-12-PLAN.md's `files_modified`, same
150-code-line-gate reasoning as `language_wiring.py`'s own docstring.

`registry.build_brain` and `ScentField` are strategy-layer objects (STRAT-07:
no LLM import reachable from either); this module is the one place the
network layer constructs them, so nothing is built per turn -- a per-turn
brain/field construction would both waste cycles and reset state that must
persist for the whole game (rule 52).
"""

from __future__ import annotations

from pursuit.network.language_wiring import LanguageRuntime, build_language_runtime
from pursuit.shared.belief_config import BeliefParams
from pursuit.shared.config import GameParams
from pursuit.shared.scent_config import ScentModel
from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy import registry
from pursuit.strategy.base import BrainBase
from pursuit.strategy.beliefadapter import BeliefAdapter
from pursuit.strategy.scentfield import ScentField


def build_brain_and_scent(
    *,
    engine_role: str,
    strategy: StrategyParams,
    game_params: GameParams,
    belief: BeliefParams,
    scent: ScentModel,
) -> tuple[BrainBase | BeliefAdapter, ScentField]:
    """The registry-built brain (raw, or `BeliefAdapter`-wrapped when
    `belief.belief.enabled`) plus one `ScentField` held for the game's
    duration (RESUME.md carry-over S: one per role, never per turn)."""
    brain = registry.build_brain(
        engine_role, strategy, game_params, belief_config=belief, scent_model=scent,
    )
    field = ScentField(model=scent, board_size=game_params.board_size)
    return brain, field


def inner_brain(brain: BrainBase | BeliefAdapter) -> BrainBase:
    """The wrapped `BrainBase` regardless of whether `brain` is
    `BeliefAdapter`-wrapped -- used to read `.weights` (D-38's herding
    lever) without the caller needing to know which shape it has."""
    return brain.brain if isinstance(brain, BeliefAdapter) else brain


def build_turn_collaborators(
    cfg,
) -> tuple[BrainBase | BeliefAdapter, ScentField, LanguageRuntime]:
    """`(brain, scent_field, language)` from one `AgentConfig` (04-12) --
    the one call `agent_lifecycle.default_context` makes for every real
    game, keeping that module under the 150-code-line gate. `cfg` is typed
    loosely (not `agent_wiring.AgentConfig`) only to avoid a needless
    import-order constraint; every attribute read below is one of that
    dataclass's own fields."""
    brain, scent_field = build_brain_and_scent(
        engine_role="cop" if cfg.role == "police" else "thief", strategy=cfg.strategy,
        game_params=cfg.params, belief=cfg.belief, scent=cfg.scent,
    )
    language = build_language_runtime(
        language=cfg.language, deception=cfg.deception, board_size=cfg.params.board_size,
        seed=cfg.belief.belief.seed,
    )
    return brain, scent_field, language
