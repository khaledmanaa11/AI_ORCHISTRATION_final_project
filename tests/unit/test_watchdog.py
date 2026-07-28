"""Stub tests for plan 02-04 (watchdog). NET-07 (D-14, D-18)."""

import pytest


def test_touch_resets_last_activity():
    """Calling touch() resets the last-activity timestamp."""
    pytest.skip("stub — implemented in plan 02-04")


def test_freeze_triggers_incident_record():
    """Exceeding the watchdog threshold without a touch triggers an incident record."""
    pytest.skip("stub — implemented in plan 02-04")


def test_incident_record_written_before_exit():
    """The incident record is written to disk before the process exits."""
    pytest.skip("stub — implemented in plan 02-04")


def test_no_freeze_while_touched():
    """Repeated touches within the threshold prevent a freeze declaration."""
    pytest.skip("stub — implemented in plan 02-04")


def test_poll_interval_comes_from_config():
    """The watchdog's poll interval is read from network.json, not hardcoded."""
    pytest.skip("stub — implemented in plan 02-04")
