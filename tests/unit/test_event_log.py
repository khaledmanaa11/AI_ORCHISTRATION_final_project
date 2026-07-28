"""Stub tests for plan 02-04 (JSONL event log). NET-05/NET-07 (D-11)."""

import pytest


def test_append_event_writes_one_jsonl_line():
    """append_event writes exactly one JSONL line per call."""
    pytest.skip("stub — implemented in plan 02-04")


def test_append_event_flushes_and_fsyncs():
    """append_event flushes and fsyncs so events survive a crash."""
    pytest.skip("stub — implemented in plan 02-04")


def test_record_uses_canonical_json():
    """Each record is serialized with canonical JSON (sort_keys, no spaces)."""
    pytest.skip("stub — implemented in plan 02-04")


def test_console_echo_emitted():
    """Each event is also echoed to the console."""
    pytest.skip("stub — implemented in plan 02-04")
