"""Tests for belief.json's `reliability` group (04-09, D-51) -- the bounds
`strategy/reliability.py`'s `Reliability` is constructed from.

Split out of test_belief_config.py at the 150-code-line ceiling, mirroring
how the group's own dataclass and validation live in
shared/reliability_config.py rather than shared/belief_config.py.
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


def test_missing_reliability_group_raises(tmp_path):
    bad = _write_variant(tmp_path, lambda d: d.pop(BeliefKey.GROUP_RELIABILITY))
    with pytest.raises(KeyError):
        load_belief_config(bad)


def test_missing_reliability_key_raises(tmp_path):
    bad = _write_variant(
        tmp_path, lambda d: d[BeliefKey.GROUP_RELIABILITY].pop(BeliefKey.PRIOR)
    )
    with pytest.raises(KeyError):
        load_belief_config(bad)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        (BeliefKey.R_MIN, 0.0),
        (BeliefKey.R_MIN, 0.95),  # not < r_max
        (BeliefKey.R_MAX, 1.0),
        (BeliefKey.PRIOR, 0.02),  # below r_min
        (BeliefKey.PRIOR, 0.99),  # above r_max
        (BeliefKey.CONTRADICTION_STEP, 0.0),
        (BeliefKey.CONTRADICTION_STEP, 1.5),
        (BeliefKey.RECOVERY_RATE, 0.0),
        (BeliefKey.RECOVERY_RATE, 1.5),
    ],
)
def test_reliability_out_of_range_fields_raise(tmp_path, key, value):
    bad = _write_variant(
        tmp_path, lambda d: d[BeliefKey.GROUP_RELIABILITY].__setitem__(key, value)
    )
    with pytest.raises(ValueError):
        load_belief_config(bad)
