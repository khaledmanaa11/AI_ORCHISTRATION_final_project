"""BeliefAdapter (D-43, D-48 Task 1+2): the Figure-7 per-turn order, seeded
reproducibility, that the hint-update step is not a no-op, and the
Regime-A/B believed-state substitution contract (Task 2).
"""

import pathlib
import random

import pytest

import pursuit.strategy.beliefadapter as ba_mod
from pursuit.shared.belief_config import load_belief_config
from pursuit.shared.config import load_game_params
from pursuit.shared.inference import NO_EVIDENCE, Inference, Region
from pursuit.shared.resolution import PREFERRED
from pursuit.shared.scent_config import load_scent_model
from pursuit.shared.state import GameState
from pursuit.strategy.beliefadapter import BeliefAdapter
from pursuit.strategy.scentfield import ScentField
from pursuit.strategy.valuebrain import ValueSearchBrain

_CONFIG_DIR = pathlib.Path(__file__).parents[3] / "config"
POLICE_BELIEF = _CONFIG_DIR / "police" / "belief.json"
POLICE_SCENT = _CONFIG_DIR / "police" / "scent.json"
POLICE_GAME = _CONFIG_DIR / "police" / "game_params.json"

#: The thief boxed in at (0,0): both in-bounds neighbours barriered, so
#: get_legal_moves returns ONLY STAY. spread() from a delta there therefore
#: returns another delta at the SAME cell -- the Regime-A identity holds for
#: ANY RNG draw, not merely a lucky seed.
_BOXED_BARRIERS = frozenset({(1, 0), (0, 1)})


@pytest.fixture(scope="module")
def model():
    return load_scent_model(POLICE_SCENT)


@pytest.fixture
def belief_cfg():
    return load_belief_config(POLICE_BELIEF)


@pytest.fixture(scope="module")
def params():
    return load_game_params(POLICE_GAME)


def _adapter(brain, params, belief_cfg, model, seed=42):
    return BeliefAdapter(brain, "cop", params, belief_cfg, model, random.Random(seed))


def _cop_brain(params):
    return ValueSearchBrain(role="cop", game_params=params, rules=PREFERRED)


def test_invalid_role_raises(params, belief_cfg, model):
    with pytest.raises(ValueError, match="role must be"):
        BeliefAdapter(_cop_brain(params), "referee", params, belief_cfg, model, random.Random(0))


def _open_state(thief=(3, 3), turn=0):
    return GameState(cop=(0, 0), thief=thief, barriers=frozenset(), barriers_placed=0, turn=turn)


def _boxed_state(cop=(6, 6)):
    return GameState(cop=cop, thief=(0, 0), barriers=_BOXED_BARRIERS, barriers_placed=2, turn=0)


def _spy(obj, name, log):
    original = getattr(obj, name)

    def wrapper(*args, **kwargs):
        log.append(name)
        return original(*args, **kwargs)

    setattr(obj, name, wrapper)


def _logging(fn, log):
    def wrapper(*args, **kwargs):
        log.append(fn.__name__)
        return fn(*args, **kwargs)

    return wrapper


def test_figure7_order_runs_once_each_in_sequence_every_turn(params, belief_cfg, model, monkeypatch):
    adapter = _adapter(_cop_brain(params), params, belief_cfg, model)
    log: list[str] = []
    for name in ("observe_exact", "predict", "update", "sample"):
        _spy(adapter.belief, name, log)
    monkeypatch.setattr(ba_mod, "scent_likelihood", _logging(ba_mod.scent_likelihood, log))
    monkeypatch.setattr(ba_mod, "hint_likelihood", _logging(ba_mod.hint_likelihood, log))

    field = ScentField(model=model, board_size=params.board_size)
    expected_step = [
        "observe_exact", "predict", "scent_likelihood", "update", "hint_likelihood", "update", "sample",
    ]
    for turn in range(2):
        log.clear()
        state = _open_state(turn=turn)
        adapter.decide(state, NO_EVIDENCE, field, PREFERRED, known_cell=(3, 3))
        assert log == expected_step


def test_two_turns_reproduce_identically_under_a_fixed_seed(params, belief_cfg, model):
    def run():
        adapter = _adapter(_cop_brain(params), params, belief_cfg, model, seed=7)
        field = ScentField(model=model, board_size=params.board_size)
        decisions = []
        for turn, thief in enumerate(((3, 3), (3, 4))):
            state = _open_state(thief=thief, turn=turn)
            decisions.append(adapter.decide(state, NO_EVIDENCE, field, PREFERRED, known_cell=thief))
        return decisions

    first, second = run(), run()
    assert first == second


def test_removing_hint_evidence_changes_the_sampled_distribution(params, belief_cfg, model):
    """Step 4 is not a no-op: with no exact reveal this turn (Regime B, a
    genuinely non-degenerate posterior), a confident regional claim changes
    the posterior the sample is drawn from, versus the same turn with
    NO_EVIDENCE (belief_hint.py's own exact all-zero no-op)."""
    state = _open_state(thief=(3, 3))

    def run(inference):
        adapter = _adapter(_cop_brain(params), params, belief_cfg, model, seed=1)
        field = ScentField(model=model, board_size=params.board_size)
        adapter.decide(state, inference, field, PREFERRED, known_cell=None)
        return adapter.belief.posterior()

    no_hint = run(NO_EVIDENCE)
    with_hint = run(Inference(region=Region.NORTHWEST, confidence=1.0))

    assert no_hint != with_hint


def test_regime_a_substitution_is_the_identity_for_a_cornered_opponent(params, belief_cfg, model):
    """Task 2: observe_exact collapses the prior to a delta and one predict
    step from a boxed-in cell (only STAY legal) spreads it right back onto
    itself -- the believed state handed to the brain is `==` the true one,
    not merely close, for ANY RNG draw."""
    brain = _cop_brain(params)
    adapter = _adapter(brain, params, belief_cfg, model)
    captured = {}
    original = brain._decide_move

    def spy(obs, believed_state):
        captured["state"] = believed_state
        return original(obs, believed_state)

    brain._decide_move = spy
    true_state = _boxed_state()
    field = ScentField(model=model, board_size=params.board_size)

    adapter.decide(true_state, NO_EVIDENCE, field, PREFERRED, known_cell=(0, 0))

    assert captured["state"] == true_state


def test_regime_b_substitution_differs_only_in_opponent_coordinate(params, belief_cfg, model):
    """Task 2: with no exact reveal (known_cell=None), the believed state
    handed to the brain keeps the cop, barriers and turn untouched but
    swaps in a sampled -- generally different -- thief cell."""
    brain = _cop_brain(params)
    adapter = _adapter(brain, params, belief_cfg, model)
    captured = {}
    original = brain._decide_move

    def spy(obs, believed_state):
        captured["state"] = believed_state
        return original(obs, believed_state)

    brain._decide_move = spy
    true_state = _open_state(thief=(3, 3))
    field = ScentField(model=model, board_size=params.board_size)

    adapter.decide(
        true_state,
        Inference(region=Region.SOUTHEAST, confidence=0.9),
        field,
        PREFERRED,
        known_cell=None,
    )

    believed = captured["state"]
    assert believed.cop == true_state.cop
    assert believed.barriers == true_state.barriers
    assert believed.barriers_placed == true_state.barriers_placed
    assert believed.turn == true_state.turn
    assert believed.thief != true_state.thief
