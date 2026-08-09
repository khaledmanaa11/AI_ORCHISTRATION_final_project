"""Tests for the belief.json loader: the scent_likelihood group (04-05,
D-18 engineering-default discipline) and the loader's own general
mechanics. Lives beside test_language_config.py / test_scent_config.py --
config/ loaders under shared/ get their tests in tests/unit/, not
tests/unit/strategy/ (matching those two files' own precedent, and 04-05's
own SUMMARY.md).

The `reliability` group's own validation (04-09, D-51) lives in
test_reliability_config.py -- split out at the SAME 150-code-line ceiling
that split this file out of test_belief_scent.py in the first place,
mirroring exactly how its source dataclass lives in
shared/reliability_config.py rather than here. This file keeps the
byte-identical check and a smoke test that load_belief_config() wires the
new group up at all, since that is about the LOADER as a whole, not the
group individually.
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


def test_role_files_are_byte_identical():
    assert POLICE_BELIEF.read_bytes() == THIEF_BELIEF.read_bytes()


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


def test_loads_the_reliability_group():
    """A loader-level smoke test that the 04-09 group is actually wired into
    BeliefParams -- its own field-by-field validation lives in
    test_reliability_config.py."""
    raw = json.loads(POLICE_BELIEF.read_text(encoding="utf-8"))
    cfg = load_belief_config(POLICE_BELIEF)
    reliability_group = raw[BeliefKey.GROUP_RELIABILITY]
    assert (
        cfg.reliability.prior,
        cfg.reliability.r_min,
        cfg.reliability.r_max,
        cfg.reliability.contradiction_step,
        cfg.reliability.recovery_rate,
    ) == (
        reliability_group[BeliefKey.PRIOR],
        reliability_group[BeliefKey.R_MIN],
        reliability_group[BeliefKey.R_MAX],
        reliability_group[BeliefKey.CONTRADICTION_STEP],
        reliability_group[BeliefKey.RECOVERY_RATE],
    )
