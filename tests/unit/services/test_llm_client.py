"""client.py's presence-only key probe (05-07, UAT G5).

No network I/O anywhere here: every case monkeypatches the environment, and
`AsyncAnthropic(...)` construction is purely local. The sentinel below is a
deliberately fake string, never a credential -- its whole job is to be
searched for afterwards, proving the VALUE never reaches a return value or
a log record (CLAUDE.md rules 39-40).
"""

import logging

from pursuit.services.llm.client import API_KEY_ENV_VAR, build_client, has_api_key

_SENTINEL_KEY = "not-a-real-key-05-07-sentinel"


def test_has_api_key_is_false_when_the_variable_is_unset(monkeypatch):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    assert has_api_key() is False


def test_has_api_key_is_false_for_an_empty_value(monkeypatch):
    """An empty string is absent -- and `build_client` must agree, or the
    warning and the actual degradation would disagree about the same box."""
    monkeypatch.setenv(API_KEY_ENV_VAR, "")
    assert has_api_key() is False
    assert build_client(timeout_seconds=1.0) is None


def test_has_api_key_is_true_when_a_value_is_present(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, _SENTINEL_KEY)
    assert has_api_key() is True


def test_has_api_key_returns_a_bool_and_never_the_key_itself(monkeypatch):
    """Presence only: the probe's whole return surface is one bool, so
    there is nothing for a caller to accidentally interpolate."""
    monkeypatch.setenv(API_KEY_ENV_VAR, _SENTINEL_KEY)
    probed = has_api_key()
    assert type(probed) is bool
    assert _SENTINEL_KEY not in repr(probed)


def test_probing_the_key_never_writes_it_to_any_log_record(monkeypatch, caplog):
    """The control CLAUDE.md rule 4 asks for: with a real-shaped value in
    the environment, capture EVERY record at DEBUG and prove the value is
    in none of them."""
    monkeypatch.setenv(API_KEY_ENV_VAR, _SENTINEL_KEY)
    with caplog.at_level(logging.DEBUG):
        has_api_key()
        build_client(timeout_seconds=1.0)
    assert all(_SENTINEL_KEY not in record.getMessage() for record in caplog.records)


def test_this_module_owns_the_one_definition_of_the_variable_name():
    """Renaming the variable is a one-line change here; nothing else in
    `src/` restates the literal."""
    assert API_KEY_ENV_VAR == "ANTHROPIC_API_KEY"
