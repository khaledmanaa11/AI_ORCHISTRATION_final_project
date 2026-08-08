"""shared/deception_config.py: fail-loud loading of the one engineering-
defaults block, plus the byte-identity both role files must keep."""

import json
import pathlib

import pytest

from pursuit.shared.deception_config import (
    DECEPTION_CONFIG_SOURCE,
    DeceptionKey,
    load_deception_config,
)

_CONFIG = pathlib.Path(__file__).parents[2] / "config"
POLICE = _CONFIG / "police" / "deception.json"
THIEF = _CONFIG / "thief" / "deception.json"


def write_variant(tmp_path, **overrides) -> pathlib.Path:
    """The shipped police config with `thief`/`cop` leaves overridden."""
    data = json.loads(POLICE.read_text(encoding="utf-8"))
    for key, value in overrides.items():
        group = "cop" if key == DeceptionKey.MIN_HERDING_GAIN.value else "thief"
        data[group][key] = value
    path = tmp_path / "deception.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_the_shipped_config_loads():
    params = load_deception_config(POLICE)
    assert params.version
    assert 0.0 < params.truth_floor < 1.0
    assert params.lie_candidate_pool >= 1


def test_both_role_files_are_byte_identical():
    """Separate processes, one negotiated block -- a drift between them is a
    silent asymmetry no test downstream would attribute to config."""
    assert POLICE.read_bytes() == THIEF.read_bytes()


def test_the_ceiling_is_derived_from_the_floor():
    params = load_deception_config(POLICE)
    assert params.max_lie_probability == 1.0 - params.truth_floor


def test_the_shipped_defaults_leave_room_to_lie_and_to_tell_the_truth():
    params = load_deception_config(POLICE)
    assert params.min_lie_probability > 0.0, "long-range honesty must not be total"
    assert params.max_lie_probability < 1.0, "D-37's truth floor"


@pytest.mark.parametrize("bad", [0.0, 1.0, -0.1, 1.5])
def test_a_truth_floor_outside_the_open_unit_interval_is_rejected(tmp_path, bad):
    with pytest.raises(ValueError, match="truth_floor"):
        load_deception_config(write_variant(tmp_path, truth_floor=bad))


def test_a_min_lie_probability_above_the_implied_ceiling_is_rejected(tmp_path):
    """min > max would make the curve non-monotonic and the floor a fiction."""
    with pytest.raises(ValueError, match="min_lie_probability"):
        load_deception_config(write_variant(tmp_path, truth_floor=0.5, min_lie_probability=0.9))


def test_a_negative_min_lie_probability_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="min_lie_probability"):
        load_deception_config(write_variant(tmp_path, min_lie_probability=-0.1))


@pytest.mark.parametrize(("danger", "safe"), [(8.0, 2.0), (5.0, 5.0), (-1.0, 4.0)])
def test_unordered_distance_thresholds_are_rejected(tmp_path, danger, safe):
    with pytest.raises(ValueError, match="danger_distance"):
        load_deception_config(write_variant(tmp_path, danger_distance=danger, safe_distance=safe))


@pytest.mark.parametrize("bad", [0, -1])
def test_an_empty_candidate_pool_is_rejected(tmp_path, bad):
    with pytest.raises(ValueError, match="lie_candidate_pool"):
        load_deception_config(write_variant(tmp_path, lie_candidate_pool=bad))


def test_a_negative_herding_gain_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="min_herding_gain"):
        load_deception_config(write_variant(tmp_path, min_herding_gain=-0.5))


def test_a_missing_group_names_the_file(tmp_path):
    path = tmp_path / "deception.json"
    path.write_text(json.dumps({"version": "1.00", "thief": {}}), encoding="utf-8")
    with pytest.raises(KeyError, match=DECEPTION_CONFIG_SOURCE):
        load_deception_config(path)


def test_a_missing_leaf_names_the_file(tmp_path):
    data = json.loads(POLICE.read_text(encoding="utf-8"))
    del data["thief"][DeceptionKey.TRUTH_FLOOR.value]
    path = tmp_path / "deception.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(KeyError, match=DECEPTION_CONFIG_SOURCE):
        load_deception_config(path)


def test_a_wrongly_typed_leaf_is_rejected(tmp_path):
    with pytest.raises(TypeError, match="truth_floor"):
        load_deception_config(write_variant(tmp_path, truth_floor="low"))


def test_no_numeric_literal_lives_on_the_key_enum():
    """D-05 discipline: the enum is structural, the numbers are in JSON."""
    for key in DeceptionKey:
        assert isinstance(key.value, str)
        assert not key.value.replace("_", "").isdigit()


def test_each_call_returns_a_fresh_instance():
    """CLAUDE.md rule 2: never a shared live object between the two seats."""
    assert load_deception_config(POLICE) is not load_deception_config(POLICE)
