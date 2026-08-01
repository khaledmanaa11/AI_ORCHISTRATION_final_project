"""Tests for training/sparring.py (Task 2) and training/sparring_reference.py
(Task 3, 03-08). One file per the plan -- both tasks share it."""

from __future__ import annotations

import random
from collections import Counter, deque
from pathlib import Path

import pytest

from pursuit.shared.config import GameParams, load_game_params
from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import load_strategy_config
from pursuit.strategy.base import Observation
from pursuit.strategy.heuristic import HeuristicBrain
from pursuit.strategy.qlearning import QLearningBrain
from pursuit.strategy.qtable import QTable
from training import sparring, sparring_reference

_CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"


def _opponent_params():
    return load_strategy_config(_CONFIG_DIR / "thief" / "strategy.json")


def _game_params() -> GameParams:
    return load_game_params(_CONFIG_DIR / "police" / "game_params.json")


def _pool(**overrides) -> sparring.SparringPool:
    fields = {
        "opponent_role": "thief",
        "opponent_params": _opponent_params(),
        "game_params": _game_params(),
        "ring": deque(maxlen=10),
    }
    fields.update(overrides)
    return sparring.SparringPool(**fields)


def _tagged_table(marker: int) -> QTable:
    table = QTable()
    table.set("marker", 0, float(marker))
    return table


def test_weights_are_honoured_over_many_seeded_draws() -> None:
    pool = _pool(reference=object())
    pool.admit(_tagged_table(1))
    rng = random.Random(7)
    counts = Counter(sparring.sample_opponent(pool, rng, _opponent_params()).kind for _ in range(4000))
    total = sum(counts.values())
    assert counts["heuristic"] / total == pytest.approx(0.30, abs=0.03)
    assert counts["past_self"] / total == pytest.approx(0.50, abs=0.03)
    assert counts["reference"] / total == pytest.approx(0.20, abs=0.03)


def test_absent_reference_renormalizes_instead_of_dropping_mass() -> None:
    pool = _pool(reference=None)
    pool.admit(_tagged_table(1))
    weights = sparring._available_weights(pool, [0.30, 0.50, 0.20])
    assert weights["heuristic"] == pytest.approx(0.375)
    assert weights["past_self"] == pytest.approx(0.625)
    assert "reference" not in weights


def test_past_self_unavailable_before_any_admission_renormalizes_to_heuristic_only() -> None:
    pool = _pool(reference=None)
    weights = sparring._available_weights(pool, [0.30, 0.50, 0.20])
    assert weights == {"heuristic": 1.0}


def test_delta_uniform_only_draws_from_the_newest_fraction() -> None:
    pool = _pool(ring=deque(maxlen=10))
    for marker in range(1, 11):  # admits 1..10, anchor pins marker=1
        pool.admit(_tagged_table(marker))
    rng = random.Random(3)
    seen = set()
    for _ in range(500):
        brain = sparring._sample_past_self(pool, rng, delta=0.2)
        seen.add(brain._table.get("marker", 0))
    # newest_n = ceil(10 * 0.2) = 2 -> markers {9, 10}, plus the pinned anchor (1).
    assert seen == {9.0, 10.0, 1.0}


def test_anchor_stays_eligible_after_ring_rotates_past_it() -> None:
    pool = _pool(ring=deque(maxlen=3))
    for marker in range(1, 6):  # anchor pins marker=1; ring keeps only 3,4,5
        pool.admit(_tagged_table(marker))
    assert pool.anchor.get("marker", 0) == 1.0
    assert {t.get("marker", 0) for t in pool.ring} == {3.0, 4.0, 5.0}
    rng = random.Random(11)
    seen = {sparring._sample_past_self(pool, rng, delta=1.0)._table.get("marker", 0) for _ in range(200)}
    assert 1.0 in seen  # the anchor is reachable even though it left `ring`


def test_ring_buffer_evicts_oldest_first() -> None:
    pool = _pool(ring=deque(maxlen=3))
    for marker in range(1, 6):
        pool.admit(_tagged_table(marker))
    assert len(pool.ring) == 3
    assert [t.get("marker", 0) for t in pool.ring] == [3.0, 4.0, 5.0]


def test_sampled_past_self_table_is_not_writable() -> None:
    pool = _pool(ring=deque(maxlen=10))
    pool.admit(_tagged_table(1))
    opponent = sparring.sample_opponent(pool, random.Random(1), _opponent_params())
    # Force the past_self branch deterministically instead of relying on odds.
    brain = sparring._sample_past_self(pool, random.Random(1), delta=1.0)
    assert isinstance(brain, QLearningBrain)
    with pytest.raises(TypeError):
        brain._table.set("marker", 0, 5.0)
    with pytest.raises(TypeError):
        brain._table.bump_visit("marker")
    assert opponent.kind in {"heuristic", "past_self", "reference"}


def test_past_self_brain_decides_through_the_read_only_view() -> None:
    """Exercises ReadOnlyQTable.visits/best_action (the pass-through path
    QLearningBrain._pick_move actually calls), not just the raise-on-write
    guards covered above."""
    pool = _pool(ring=deque(maxlen=10))
    live = QTable()
    for _ in range(pool.opponent_params.min_visits):
        live.bump_visit("1,1|4,4|0|0|0")
    live.set("1,1|4,4|0|0|0", 2, 9.0)
    pool.admit(live)
    brain = sparring._sample_past_self(pool, random.Random(5), delta=1.0)
    obs = Observation(own_cell=(1, 1), target_cell=(4, 4), blocked_mask=0, barriers_used=0, turn_index=0)
    state = GameState(cop=(1, 1), thief=(4, 4), barriers=frozenset(), barriers_placed=0, turn=0)
    decision = brain._pick_move(obs, state)
    assert decision.move is not None


def test_sample_opponent_heuristic_builds_a_real_heuristic_brain() -> None:
    pool = _pool(reference=None, ring=deque(maxlen=10))  # only heuristic available
    opponent = sparring.sample_opponent(pool, random.Random(1), _opponent_params())
    assert opponent.kind == "heuristic"
    assert isinstance(opponent.brain, HeuristicBrain)


# --- Task 3: optional reference-implementation adapter -----------------------


def test_reference_absent_path_returns_none_and_logs(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING"):
        brain = sparring_reference.build_reference_opponent(
            "cop", "", _game_params(), random.Random(1)
        )
    assert brain is None
    assert any("reference_impl_path" in r.message for r in caplog.records)


def test_reference_unimportable_path_returns_none_and_logs(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level("WARNING"):
        brain = sparring_reference.build_reference_opponent(
            "cop", str(tmp_path / "no-such-clone"), _game_params(), random.Random(1)
        )
    assert brain is None
    assert any("unavailable" in r.message for r in caplog.records)


@pytest.mark.skipif(
    not (Path(__file__).parent / "_reference_clone_marker").exists(),
    reason="reference implementation clone not available on this machine (D-21)",
)
def test_reference_opponent_when_clone_present() -> None:  # pragma: no cover
    pytest.importorskip("police_thief")
