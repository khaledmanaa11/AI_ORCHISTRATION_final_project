"""Stub tests for plan 02-07 (deadline/retry). NET-06 (D-13, D-17)."""

import pytest


def test_wait_for_opponent_returns_envelope():
    """wait_for_opponent returns the envelope once it arrives."""
    pytest.skip("stub — implemented in plan 02-07")


def test_wait_for_opponent_times_out():
    """wait_for_opponent raises/returns a timeout after response_timeout seconds."""
    pytest.skip("stub — implemented in plan 02-07")


def test_retry_count_from_config_respected():
    """The retry loop attempts exactly retry_count times, from config."""
    pytest.skip("stub — implemented in plan 02-07")


def test_backoff_applied_between_attempts():
    """backoff_seconds elapses between successive retry attempts."""
    pytest.skip("stub — implemented in plan 02-07")


def test_technical_win_after_retries_exhausted():
    """Exhausting all retries yields a technical win for the waiting side."""
    pytest.skip("stub — implemented in plan 02-07")


def test_tool_error_is_not_a_technical_win():
    """A tool-level error (not silence) does not trigger a technical win."""
    pytest.skip("stub — implemented in plan 02-07")
