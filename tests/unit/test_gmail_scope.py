"""Rule 30 -- send-only, twice: what is REQUESTED and what is GRANTED.

`docs/RULES.md:66`: "Use send-only permission scope for the mail interface ->
Security breach that disqualifies the code." A test that only asserted
`gmail.send` is present would pass against a client that also holds
`gmail.readonly`, so every case below is a REJECTION case with the happy path
as its counterweight.

No credential and no network: `build_gmail_transport` takes its loader as a
seam, and `load_send_only_credentials` is driven with the `google-*` names in
`gmail_sink` monkeypatched to the fakes in `gmail_fixtures.py`.
"""

import pytest

from pursuit.services.reporting import gmail_sink
from pursuit.services.reporting.gmail_sink import (
    GMAIL_SEND_SCOPE,
    SEND_ONLY_SCOPES,
    GmailCredentialsError,
    GmailScopeError,
    build_gmail_transport,
    load_send_only_credentials,
    require_send_only_scope,
)
from pursuit.shared.reporting_config import load_reporting_config
from tests.unit.gmail_fixtures import (
    SHIPPED_REPORTING,
    FakeCredentials,
    FakeInstalledAppFlow,
)

#: Every one of these must be REFUSED. The first is the exact hazard rule 30
#: names: send-only plus one extra.
FORBIDDEN_SCOPE_SETS = (
    (GMAIL_SEND_SCOPE, "https://www.googleapis.com/auth/gmail.readonly"),
    (GMAIL_SEND_SCOPE, "https://mail.google.com/"),
    ("https://www.googleapis.com/auth/gmail.modify",),
    ("https://www.googleapis.com/auth/gmail.compose",),
    ("https://mail.google.com/",),
    (),
)

PARAMS = load_reporting_config(SHIPPED_REPORTING)


def _refusing_loader(**_kwargs):
    raise AssertionError("a credential was read after a scope that should have been refused")


def test_the_forbidden_scope_table_is_not_empty():
    """Guards the parametrize below: an emptied table would SKIP silently."""
    assert len(FORBIDDEN_SCOPE_SETS) == 6


@pytest.mark.parametrize("scopes", FORBIDDEN_SCOPE_SETS)
def test_a_scope_beyond_send_only_is_refused_before_any_credential_is_read(scopes):
    with pytest.raises(GmailScopeError, match="send-only"):
        build_gmail_transport(PARAMS, scopes=scopes, credentials_loader=_refusing_loader)


def test_the_send_only_scope_passes_the_gate(monkeypatch):
    monkeypatch.delenv(PARAMS.credentials_env_var, raising=False)
    assert require_send_only_scope(SEND_ONLY_SCOPES, source="test") == SEND_ONLY_SCOPES


def test_a_duplicated_send_scope_is_still_send_only():
    assert require_send_only_scope(
        (GMAIL_SEND_SCOPE, GMAIL_SEND_SCOPE), source="test"
    ) == (GMAIL_SEND_SCOPE, GMAIL_SEND_SCOPE)


def test_the_scope_gate_runs_before_the_credential_gate(monkeypatch):
    """Same unset environment, two scopes, two DIFFERENT errors -- which is
    what proves the ordering rather than merely asserting it."""
    monkeypatch.delenv(PARAMS.credentials_env_var, raising=False)
    monkeypatch.delenv(PARAMS.token_env_var, raising=False)
    with pytest.raises(GmailScopeError):
        build_gmail_transport(PARAMS, scopes=(GMAIL_SEND_SCOPE, "https://mail.google.com/"))
    with pytest.raises(GmailCredentialsError, match=PARAMS.credentials_env_var):
        build_gmail_transport(PARAMS)


def test_a_token_granting_more_than_send_only_is_refused(tmp_path, monkeypatch):
    """The second gate: a `token.json` left over from a broader consent is what
    actually authorises the call, and it never appears in the requested list."""
    token = tmp_path / "token.json"
    token.write_text("{}", encoding="utf-8")
    over_granted = FakeCredentials(
        granted=(GMAIL_SEND_SCOPE, "https://www.googleapis.com/auth/gmail.readonly")
    )
    monkeypatch.setattr(gmail_sink, "Credentials", FakeCredentials.prepared(over_granted))
    with pytest.raises(GmailScopeError, match="granted"):
        load_send_only_credentials(
            credentials_path=str(tmp_path / "client_secret.json"), token_path=str(token)
        )


def test_a_valid_send_only_token_is_used_without_a_consent_flow(tmp_path, monkeypatch):
    token = tmp_path / "token.json"
    token.write_text("{}", encoding="utf-8")
    granted = FakeCredentials(granted=SEND_ONLY_SCOPES)
    flow = FakeInstalledAppFlow.prepared(granted)
    monkeypatch.setattr(gmail_sink, "Credentials", FakeCredentials.prepared(granted))
    monkeypatch.setattr(gmail_sink, "InstalledAppFlow", flow)

    creds = load_send_only_credentials(
        credentials_path=str(tmp_path / "client_secret.json"), token_path=str(token)
    )

    assert creds is granted
    assert flow.consented == []
    assert granted.loaded_from == (str(token), tuple(SEND_ONLY_SCOPES))
    assert "gmail.send" in token.read_text(encoding="utf-8")


def test_an_expired_token_with_a_refresh_token_is_refreshed(tmp_path, monkeypatch):
    token = tmp_path / "token.json"
    token.write_text("{}", encoding="utf-8")
    stale = FakeCredentials(
        granted=SEND_ONLY_SCOPES, valid=False, expired=True, refresh_token="refresh-me"
    )
    flow = FakeInstalledAppFlow.prepared(stale)
    monkeypatch.setattr(gmail_sink, "Credentials", FakeCredentials.prepared(stale))
    monkeypatch.setattr(gmail_sink, "InstalledAppFlow", flow)
    monkeypatch.setattr(gmail_sink, "Request", lambda: "refresh-request")

    creds = load_send_only_credentials(
        credentials_path=str(tmp_path / "client_secret.json"), token_path=str(token)
    )

    assert creds.refreshed_with == "refresh-request"
    assert flow.consented == []


def test_with_no_token_file_the_consent_flow_requests_only_the_send_scope(tmp_path, monkeypatch):
    granted = FakeCredentials(granted=SEND_ONLY_SCOPES)
    flow = FakeInstalledAppFlow.prepared(granted)
    monkeypatch.setattr(gmail_sink, "InstalledAppFlow", flow)
    secrets_path = tmp_path / "client_secret.json"

    creds = load_send_only_credentials(
        credentials_path=str(secrets_path), token_path=str(tmp_path / "token.json")
    )

    assert creds is granted
    assert flow.consented == [(str(secrets_path), tuple(SEND_ONLY_SCOPES))]


def test_the_transport_is_built_against_gmail_v1_with_discovery_caching_off(
    tmp_path, monkeypatch
):
    granted = FakeCredentials(granted=SEND_ONLY_SCOPES)
    calls = []
    monkeypatch.setenv(PARAMS.credentials_env_var, str(tmp_path / "client_secret.json"))
    monkeypatch.setenv(PARAMS.token_env_var, str(tmp_path / "token.json"))
    monkeypatch.setattr(
        gmail_sink, "build", lambda *args, **kwargs: calls.append((args, kwargs)) or "service"
    )

    transport = build_gmail_transport(PARAMS, credentials_loader=lambda **_: granted)

    assert transport == "service"
    assert calls == [(("gmail", "v1"), {"credentials": granted, "cache_discovery": False})]
