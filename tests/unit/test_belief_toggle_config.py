"""Tests for belief.json's `belief` group (04-11, D-43) -- the adapter's own
on/off flag and RNG seed, including the `seed: null` (derive-and-log) path.

Mirrors tests/unit/test_reliability_config.py's own precedent: exercised
only through load_belief_config(), never by constructing BeliefToggleParams
directly.
"""

import json
import pathlib

import pytest

from pursuit.shared.belief_config import BeliefKey, load_belief_config

_CONFIG_DIR = pathlib.Path(__file__).parent.parent.parent / "config"
POLICE_BELIEF = _CONFIG_DIR / "police" / "belief.json"


def _write_variant(tmp_path, mutate):
    data = json.loads(POLICE_BELIEF.read_text(encoding="utf-8"))
    mutate(data)
    target = tmp_path / "belief.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    return target


def test_missing_belief_group_raises(tmp_path):
    bad = _write_variant(tmp_path, lambda d: d.pop(BeliefKey.GROUP_BELIEF))
    with pytest.raises(KeyError):
        load_belief_config(bad)


def test_missing_enabled_key_raises(tmp_path):
    bad = _write_variant(tmp_path, lambda d: d[BeliefKey.GROUP_BELIEF].pop(BeliefKey.ENABLED))
    with pytest.raises(KeyError):
        load_belief_config(bad)


def test_enabled_wrong_type_raises(tmp_path):
    bad = _write_variant(
        tmp_path, lambda d: d[BeliefKey.GROUP_BELIEF].__setitem__(BeliefKey.ENABLED, "yes")
    )
    with pytest.raises(TypeError):
        load_belief_config(bad)


def test_missing_seed_key_raises(tmp_path):
    bad = _write_variant(tmp_path, lambda d: d[BeliefKey.GROUP_BELIEF].pop(BeliefKey.SEED))
    with pytest.raises(KeyError):
        load_belief_config(bad)


def test_seed_wrong_type_raises(tmp_path):
    bad = _write_variant(
        tmp_path, lambda d: d[BeliefKey.GROUP_BELIEF].__setitem__(BeliefKey.SEED, "twenty")
    )
    with pytest.raises(TypeError):
        load_belief_config(bad)


def test_seed_null_is_accepted_as_none(tmp_path):
    """A missing/null seed is NOT an error (module docstring): the caller
    derives one and logs it (strategy/registry.py::_resolve_belief_seed)."""
    ok = _write_variant(tmp_path, lambda d: d[BeliefKey.GROUP_BELIEF].__setitem__(BeliefKey.SEED, None))
    params = load_belief_config(ok)
    assert params.belief.seed is None
    assert params.belief.enabled is True
