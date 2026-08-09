"""Tests for belief.json's `hint_likelihood` group (04-09, D-40) -- the
fixed mixing weight `w` `strategy/belief_hint.py` reads.

Split out of test_belief_config.py at the 150-code-line ceiling, mirroring
how the group's own dataclass and validation live in
shared/hint_likelihood_config.py rather than shared/belief_config.py.
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


def test_missing_hint_likelihood_group_raises(tmp_path):
    bad = _write_variant(tmp_path, lambda d: d.pop(BeliefKey.GROUP_HINT_LIKELIHOOD))
    with pytest.raises(KeyError):
        load_belief_config(bad)


def test_missing_hint_weight_key_raises(tmp_path):
    bad = _write_variant(
        tmp_path, lambda d: d[BeliefKey.GROUP_HINT_LIKELIHOOD].pop(BeliefKey.WEIGHT)
    )
    with pytest.raises(KeyError):
        load_belief_config(bad)


@pytest.mark.parametrize("value", [0.0, -0.1])
def test_hint_weight_out_of_lower_range_raises(tmp_path, value):
    bad = _write_variant(
        tmp_path,
        lambda d: d[BeliefKey.GROUP_HINT_LIKELIHOOD].__setitem__(BeliefKey.WEIGHT, value),
    )
    with pytest.raises(ValueError):
        load_belief_config(bad)


def test_hint_weight_at_or_above_scent_weight_raises_naming_both_keys(tmp_path):
    """D-40's asymmetry, enforced by the loader: a config that lets a hint
    outweigh scent (equal counts as "at or above") never loads. Both
    weights are set inside the hint weight's own (0, 1) validity range so
    this isolates the D-40 comparison from the separate range check above
    -- with the shipped scent_weight (4.0), any (0, 1) hint_weight already
    satisfies the comparison, so this test lowers scent_weight too."""

    def mutate(d):
        d[BeliefKey.GROUP_SCENT_LIKELIHOOD][BeliefKey.WEIGHT] = 0.2
        d[BeliefKey.GROUP_HINT_LIKELIHOOD][BeliefKey.WEIGHT] = 0.2

    bad = _write_variant(tmp_path, mutate)
    with pytest.raises(ValueError, match="hint_likelihood.weight") as excinfo:
        load_belief_config(bad)
    assert "scent_likelihood.weight" in str(excinfo.value)
