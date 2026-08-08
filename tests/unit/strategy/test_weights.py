"""weights.py: the learned artefact -- fail-loud loading, round-trip, PRIOR.

A configured-but-missing artefact must raise rather than silently falling back
to PRIOR: shipping a league game on the prior while believing it trained is the
exact failure mode this guard exists to prevent (module doc).
"""

from __future__ import annotations

import json

import pytest

from pursuit.strategy.features import FEATURE_COUNT, FEATURE_NAMES
from pursuit.strategy.weights import PRIOR, describe, load_weights, save_weights


def test_load_weights_of_none_returns_the_prior():
    assert load_weights(None) is PRIOR


def test_configured_but_missing_path_raises_file_not_found(tmp_path):
    missing = tmp_path / "no_such_weights.json"
    with pytest.raises(FileNotFoundError, match="not found"):
        load_weights(missing)


def test_wrong_length_vector_raises_value_error(tmp_path):
    path = tmp_path / "bad_weights.json"
    path.write_text(json.dumps({"weights": [1.0, 2.0]}))
    with pytest.raises(ValueError, match="expected"):
        load_weights(path)


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "trained.json"
    weights = tuple(0.1 * index for index in range(FEATURE_COUNT))
    save_weights(path, weights)
    assert load_weights(path) == weights


def test_save_weights_rejects_the_wrong_length():
    with pytest.raises(ValueError, match="expected"):
        save_weights("unused.json", (1.0, 2.0))


def test_describe_names_every_feature():
    text = describe(PRIOR)
    for name in FEATURE_NAMES:
        assert name in text
