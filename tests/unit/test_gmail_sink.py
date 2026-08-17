"""REPORT-04 against `GmailSink`, never against `DryRunSink`.

`DryRunSink` writes a file and returns success, so it would make every
assertion in this file green whether or not the live path works. Everything
here therefore drives the real `GmailSink` through the real 07-01
`ReportingChain`, with a fake transport that raises real `HttpError`s.

NOTHING IN THIS FILE TOUCHES THE NETWORK, and that is enforced rather than
promised: an autouse fixture fails any test that attempts a non-loopback
connect or a DNS lookup, and the two `test_control_the_*_guard_fires_*` tests
prove both halves are armed.
"""

import asyncio
import json
import socket
import threading

import pytest
from googleapiclient.errors import HttpError

from pursuit.services.reporting.chain import Refusal
from pursuit.services.reporting.gmail_sink import (
    AUTHENTICATED_USER,
    GmailRetryableError,
    GmailSink,
)
from pursuit.services.reporting.sink import MailSink
from pursuit.shared.language_config import load_language_config
from pursuit.shared.reporting_config import ReportingMode, load_reporting_config
from tests.unit.gmail_fixtures import (
    OK_STATUS,
    SERVER_ERROR,
    SHIPPED_LANGUAGE,
    SHIPPED_REPORTING,
    TOO_MANY_REQUESTS,
    FakeGmailTransport,
    build_mail_chain,
    sample_report,
)

RECIPIENT = "rmisegal+uoh26finalgame@gmail.com"

#: OQ-3, transcribed as a LITERAL rather than read back from the params under
#: test: `sleeps == [params.wait_after_error_seconds] * 2` would still pass if
#: the configured backoff were quietly lowered to Table 19's bare 5 s minimum.
MAIL_BACKOFF_SECONDS = 30
#: Phase 4's LLM instance keeps its shipped value; OQ-3 is scoped to the mail
#: gatekeeper alone, and this plan must not retune the LLM path.
LLM_BACKOFF_SECONDS = 5


#: asyncio's Windows proactor loop builds its own self-pipe over a loopback
#: socketpair, so the guard below refuses everything EXCEPT loopback rather
#: than everything: a blanket refusal fails at event-loop construction and
#: would have to be removed, which is how this kind of guard usually dies.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", ""})
UNROUTED_HOST = "93.184.216.34"


@pytest.fixture(autouse=True)
def no_external_network(monkeypatch):
    """Any attempt to leave this machine -- a connect or a DNS lookup -- fails
    the test that made it. Armed for every test in this file; the two control
    tests below prove both halves fire."""
    real_connect = socket.socket.connect
    real_getaddrinfo = socket.getaddrinfo

    def _guarded_connect(self, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if str(host) not in LOOPBACK_HOSTS:
            raise AssertionError(f"attempted a network connection to {host}")
        return real_connect(self, address, *args, **kwargs)

    def _guarded_getaddrinfo(host, *args, **kwargs):
        if host is not None and str(host) not in LOOPBACK_HOSTS:
            raise AssertionError(f"attempted a DNS lookup of {host}")
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)
    monkeypatch.setattr(socket, "getaddrinfo", _guarded_getaddrinfo)


def _sink(statuses):
    transport = FakeGmailTransport(statuses=statuses)
    return GmailSink(transport=transport, recipient=RECIPIENT), transport


def test_control_the_connection_guard_fires_on_a_non_loopback_address():
    with socket.socket() as probe, pytest.raises(AssertionError, match="network connection"):
        probe.connect((UNROUTED_HOST, 80))


def test_control_the_dns_guard_fires_on_the_gmail_api_host():
    with pytest.raises(AssertionError, match="DNS lookup"):
        socket.getaddrinfo("gmail.googleapis.com", 443)


async def test_two_429s_then_success_delivers_after_two_thirty_second_backoffs(tmp_path):
    sink, transport = _sink([TOO_MANY_REQUESTS, TOO_MANY_REQUESTS, OK_STATUS])
    sleeps: list[float] = []
    chain, _params = build_mail_chain(sink=sink, tmp_path=tmp_path, sleeps=sleeps)

    outcome = await chain.send(sample_report())

    assert outcome.sent is True
    assert transport.attempts == 3
    assert sleeps == [MAIL_BACKOFF_SECONDS, MAIL_BACKOFF_SECONDS]


def test_the_mail_instance_backoff_is_thirty_and_the_llm_instance_is_still_five():
    assert load_reporting_config(SHIPPED_REPORTING).wait_after_error_seconds == (
        MAIL_BACKOFF_SECONDS
    )
    assert load_language_config(SHIPPED_LANGUAGE).wait_after_error_seconds == (
        LLM_BACKOFF_SECONDS
    )


async def test_the_sink_raises_a_named_retryable_error_on_429_and_never_sleeps(monkeypatch):
    sink, _transport = _sink([TOO_MANY_REQUESTS])
    slept: list[float] = []
    monkeypatch.setattr(asyncio, "sleep", lambda seconds: slept.append(seconds))

    with pytest.raises(GmailRetryableError, match=str(TOO_MANY_REQUESTS)):
        await sink.send(sample_report())

    assert slept == []


async def test_a_non_429_http_error_propagates_unconverted():
    sink, _transport = _sink([SERVER_ERROR])
    with pytest.raises(HttpError) as caught:
        await sink.send(sample_report())
    assert not isinstance(caught.value, GmailRetryableError)


async def test_the_bytes_on_the_wire_carry_the_json_as_an_attachment():
    sink, transport = _sink([OK_STATUS])
    await sink.send(sample_report())

    parsed = transport.parsed_attempt(0)
    attachments = [
        part for part in parsed.iter_attachments()
        if part.get_content_disposition() == "attachment"
    ]
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "result_live42.json"
    assert json.loads(attachments[0].get_payload(decode=True)) == sample_report()
    body = parsed.get_body(preferencelist=("plain",)).get_content()
    assert sample_report()["game_uid"] not in body


async def test_the_send_addresses_the_authenticated_user_alias():
    sink, transport = _sink([OK_STATUS])
    await sink.send(sample_report())
    assert transport.user_ids == [AUTHENTICATED_USER]


async def test_the_receipt_reports_live_mode_and_the_api_message_id():
    sink, transport = _sink([OK_STATUS])
    receipt = await sink.send(sample_report())
    assert receipt.mode is ReportingMode.LIVE
    assert receipt.message_id == transport.message_id
    assert receipt.paths == ()


async def test_a_permanently_failing_send_queues_and_stays_recoverable(tmp_path):
    sink, transport = _sink([TOO_MANY_REQUESTS])
    sleeps: list[float] = []
    chain, params = build_mail_chain(sink=sink, tmp_path=tmp_path, sleeps=sleeps)
    report = sample_report()

    outcome = await chain.send(report)

    assert outcome.sent is False
    assert outcome.refusal is Refusal.SEND_FAILED
    assert outcome.queued is True
    assert chain.pending == 1
    assert transport.attempts == params.retries_before_failure + 1
    assert sleeps == [MAIL_BACKOFF_SECONDS] * params.retries_before_failure

    transport.statuses = [OK_STATUS]
    drained = await chain.drain()

    assert [result.sent for result in drained] == [True]
    assert chain.pending == 0
    recovered = next(transport.parsed_attempt(-1).iter_attachments())
    assert json.loads(recovered.get_payload(decode=True)) == report


async def test_the_gmail_sink_satisfies_the_mail_sink_protocol():
    sink, _transport = _sink([OK_STATUS])
    assert isinstance(sink, MailSink)


async def test_the_blocking_api_call_runs_off_the_event_loop_thread():
    """`asyncio.to_thread`: a slow send must not stall the turn loop that the
    freeze watchdog (`network/watchdog.py`, `os._exit(1)`) is watching."""
    sink, transport = _sink([OK_STATUS])
    await sink.send(sample_report())
    assert transport.thread_ids == [transport.thread_ids[0]]
    assert transport.thread_ids[0] != threading.get_ident()
