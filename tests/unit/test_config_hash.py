"""Stub tests for plan 02-02 (config digest). NET-09 (D-08, D-15)."""

import pytest


def test_digest_is_stable_for_same_content():
    """Hashing the same content twice yields the same digest."""
    pytest.skip("stub — implemented in plan 02-02")


def test_digest_ignores_formatting_drift():
    """Canonical JSON hashing ignores whitespace/key-order drift."""
    pytest.skip("stub — implemented in plan 02-02")


def test_digest_differs_on_semantic_change():
    """A semantic content change produces a different digest."""
    pytest.skip("stub — implemented in plan 02-02")


def test_police_and_thief_game_params_digests_match():
    """Police and thief game_params.json digests match (NET-09 precondition)."""
    pytest.skip("stub — implemented in plan 02-02")
