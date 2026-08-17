"""Offline doubles for the Gmail path, shared by the two `test_gmail_*` files.

Not named `test_*`, so pytest collects nothing from it -- the
`artifact_config_fixtures.py` / `late_peer_harness.py` precedent.

`FakeGmailTransport` is the injected seam `GmailSink` takes in place of a
`googleapiclient` service: it records every attempt and replays a scripted list
of HTTP statuses, raising a REAL `googleapiclient.errors.HttpError` for the
failures so the sink's 429 branch is exercised against the exception class it
will actually meet, not against a stand-in of our own design.
"""

import base64
import threading
from email import message_from_bytes
from email.policy import default as default_policy
from pathlib import Path

import httplib2
from googleapiclient.errors import HttpError

from pursuit.services.llm import Gatekeeper
from pursuit.services.reporting.chain import ReportingChain
from pursuit.services.reporting.dos import DosDetector
from pursuit.services.reporting.quota import QuotaManager
from pursuit.shared.reporting_config import load_reporting_config

CONFIG_ROOT = Path(__file__).resolve().parents[2] / "config"
SHIPPED_REPORTING = CONFIG_ROOT / "police" / "reporting.json"
SHIPPED_LANGUAGE = CONFIG_ROOT / "police" / "language.json"

OK_STATUS = 200
TOO_MANY_REQUESTS = 429
SERVER_ERROR = 500
DEFAULT_MESSAGE_ID = "gmail-message-id-1"


def sample_report(game_id: str = "live42") -> dict:
    return {
        "game_uid": "uid-live-distinctive",
        "game_id": game_id,
        "outcome": "capture",
        "turns": 7,
    }


class _FakeApiRequest:
    def __init__(self, status: int, message_id: str) -> None:
        self._status = status
        self._message_id = message_id

    def execute(self) -> dict:
        if self._status == OK_STATUS:
            return {"id": self._message_id}
        raise HttpError(
            httplib2.Response({"status": self._status}), b"{}", uri="https://gmail.test/send"
        )


class FakeGmailTransport:
    """`users().messages().send(...).execute()`, scripted and recorded.

    `statuses` is replayed one entry per attempt; once exhausted the LAST entry
    repeats, so `[429]` is an always-429 server and `[429, 429, 200]` recovers
    on the third attempt. Reassigning `statuses` re-scripts it mid-test, which
    is how the queue-recovery test makes a permanently-failing server start
    working again.
    """

    def __init__(self, *, statuses, message_id: str = DEFAULT_MESSAGE_ID) -> None:
        self.statuses = list(statuses)
        self.message_id = message_id
        self.raws: list[str] = []
        self.user_ids: list[str] = []
        self.thread_ids: list[int] = []

    def users(self) -> "FakeGmailTransport":
        return self

    def messages(self) -> "FakeGmailTransport":
        return self

    def send(self, *, userId: str, body: dict) -> _FakeApiRequest:  # noqa: N803 - Gmail API name
        self.user_ids.append(userId)
        self.thread_ids.append(threading.get_ident())
        self.raws.append(body["raw"])
        index = min(len(self.raws) - 1, len(self.statuses) - 1)
        return _FakeApiRequest(self.statuses[index], self.message_id)

    @property
    def attempts(self) -> int:
        return len(self.raws)

    def parsed_attempt(self, index: int):
        """The RFC 5322 message a given attempt actually put on the wire."""
        return message_from_bytes(
            base64.urlsafe_b64decode(self.raws[index]), policy=default_policy
        )


class FakeCredentials:
    """Stands in for `google.oauth2.credentials.Credentials`.

    `granted` is what the token actually authorises, which is deliberately
    separate from what was requested: rule 30's real hazard is a `token.json`
    left over from a broader consent.
    """

    def __init__(self, *, granted, valid=True, expired=False, refresh_token=None) -> None:
        self.scopes = list(granted)
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.refreshed_with = None
        self.loaded_from = None

    @classmethod
    def prepared(cls, instance: "FakeCredentials") -> type:
        """A `Credentials` REPLACEMENT class whose `from_authorized_user_file`
        hands back `instance` and records the path it was asked for."""

        class _Loader:
            @staticmethod
            def from_authorized_user_file(token_path, scopes):
                instance.loaded_from = (str(token_path), tuple(scopes))
                return instance

        return _Loader

    def refresh(self, request) -> None:
        self.refreshed_with = request
        self.valid = True
        self.expired = False

    def to_json(self) -> str:
        return f'{{"scopes": {list(self.scopes)!r}}}'


class FakeInstalledAppFlow:
    """Stands in for the consent flow. Running it for real is 07-10's human
    step, so every automated path that reaches it records instead."""

    def __init__(self, credentials: FakeCredentials) -> None:
        self._credentials = credentials

    @classmethod
    def prepared(cls, credentials: FakeCredentials) -> type:
        """A fresh flow class per call, each with its own `consented` log."""

        class _Flow:
            consented: list = []

            @staticmethod
            def from_client_secrets_file(client_secrets_path, scopes):
                _Flow.consented.append((str(client_secrets_path), tuple(scopes)))
                return cls(credentials)

        return _Flow

    def run_local_server(self, **_kwargs) -> FakeCredentials:
        return self._credentials


def build_mail_chain(*, sink, tmp_path, sleeps):
    """The real 07-01 Figure-13 chain, every limit from the SHIPPED
    reporting.json, with the gatekeeper's `sleep` seam recording instead of
    waiting. Returns the chain and the loaded params."""
    params = load_reporting_config(SHIPPED_REPORTING)

    async def _record_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    chain = ReportingChain(
        gatekeeper=Gatekeeper(params=params, sleep=_record_sleep),
        quota=QuotaManager(
            ceiling_per_hour=params.requests_per_hour, path=tmp_path / "quota.json"
        ),
        dos=DosDetector(retries_before_failure=params.retries_before_failure),
        sink=sink.send,
        queue_depth=params.queue_depth,
    )
    return chain, params
