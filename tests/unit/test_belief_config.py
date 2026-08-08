"""Tests for the belief.json loader (Task 3, D-18 engineering-default
discipline). Lives beside test_language_config.py / test_scent_config.py --
config/ loaders under shared/ get their tests in tests/unit/, not
tests/unit/strategy/ (matching those two files' own precedent).

Split out of tests/unit/strategy/test_belief_scent.py at the 150-code-line
ceiling (CLAUDE.md: split files, never compress code to fit) -- see that
plan's SUMMARY.md for the Rule-3 deviation note.
"""

import json
import pathlib
from dataclasses import FrozenInstanceError

import pytest

from pursuit.shared.belief_config import BeliefKey, load_belief_config

_CONFIG_DIR = pathlib.Path(__file__).parent.parent.parent / "config"
POLICE_BELIEF = _CONFIG_DIR / "police" / "belief.json"
THIEF_BELIEF = _CONFIG_DIR / "thief" / "belief.json"


def _write_variant(tmp_path, mutate):
    data = json.loads(POLICE_BELIEF.read_text(encoding="utf-8"))
    mutate(data)
    target = tmp_path / "belief.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    return target


def test_loads_all_fields():
    raw = json.loads(POLICE_BELIEF.read_text(encoding="utf-8"))
    cfg = load_belief_config(POLICE_BELIEF)
    group = raw[BeliefKey.GROUP_SCENT_LIKELIHOOD]
    assert (cfg.scent_weight, cfg.epsilon, cfg.age_cap, cfg.freshness_decay) == (
        group[BeliefKey.WEIGHT],
        group[BeliefKey.EPSILON],
        group[BeliefKey.AGE_CAP],
        group[BeliefKey.FRESHNESS_DECAY],
    )


def test_params_are_frozen():
    cfg = load_belief_config(POLICE_BELIEF)
    with pytest.raises(FrozenInstanceError):
        cfg.epsilon = 0.9  # type: ignore[misc]


def test_role_configs_yield_independent_objects():
    police = load_belief_config(POLICE_BELIEF)
    thief = load_belief_config(THIEF_BELIEF)
    assert police is not thief
    assert load_belief_config(POLICE_BELIEF) is not police


def test_missing_key_raises(tmp_path):
    bad = _write_variant(
        tmp_path, lambda d: d[BeliefKey.GROUP_SCENT_LIKELIHOOD].pop(BeliefKey.EPSILON)
    )
    with pytest.raises(KeyError):
        load_belief_config(bad)


def test_missing_group_raises(tmp_path):
    bad = _write_variant(tmp_path, lambda d: d.pop(BeliefKey.GROUP_SCENT_LIKELIHOOD))
    with pytest.raises(KeyError):
        load_belief_config(bad)


def test_wrong_typed_field_raises(tmp_path):
    bad = _write_variant(
        tmp_path,
        lambda d: d[BeliefKey.GROUP_SCENT_LIKELIHOOD].__setitem__(BeliefKey.AGE_CAP, "five"),
    )
    with pytest.raises(TypeError):
        load_belief_config(bad)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        (BeliefKey.WEIGHT, 0.0),
        (BeliefKey.WEIGHT, -1.0),
        (BeliefKey.EPSILON, 1.0),
        (BeliefKey.EPSILON, -0.1),
        (BeliefKey.AGE_CAP, 0),
        (BeliefKey.FRESHNESS_DECAY, 1.0),
        (BeliefKey.FRESHNESS_DECAY, 0.0),
    ],
)
def test_out_of_range_fields_raise(tmp_path, key, value):
    bad = _write_variant(
        tmp_path, lambda d: d[BeliefKey.GROUP_SCENT_LIKELIHOOD].__setitem__(key, value)
    )
    with pytest.raises(ValueError):
        load_belief_config(bad)
