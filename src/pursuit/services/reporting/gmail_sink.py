"""The ONLY module in `src/` that imports `google-*` (D-70), and the live half
of REPORT-04/REPORT-05.

Vendor isolation, exactly as `services/llm/anthropic_provider.py` owns the
Anthropic SDK: everything else in the project talks to `sink.MailSink`, so the
Gmail dependency can be swapped, faked or removed at one address. Proven by a
grep over `src/`, not by an assertion.

IT DOES NOT SLEEP, AND THAT IS THE POINT. On HTTP 429 this sink raises
`GmailRetryableError`; the WAIT belongs to `Gatekeeper._call_with_retry`, which
already runs `retries_before_failure + 1` attempts and awaits
`wait_after_error_seconds` between them (30 s for the mail instance, OQ-3). A
second backoff here would be a second gatekeeper (SEGAL §4 forbids it) and
would make the backoff test pass for the wrong reason.

RULE 30 IS ENFORCED TWICE, ON PURPOSE. `docs/RULES.md:66`: a scope wider than
send-only is "a security breach that disqualifies the code". So the REQUESTED
scopes are checked before any credential is read, and the GRANTED scopes on the
loaded token are checked before any send -- a `token.json` left over from a
broader consent is what actually authorises the call, and it would sail past a
check that only looked at the list we asked for.

NO SECRET LIVES HERE (rules 39-40). `reporting.json` holds the NAMES of two
environment variables; this module reads their values with `os.environ.get()`
and never defaults them. Both target files are already in `.gitignore`.
"""

from __future__ import annotations

import asyncio
import base64
import os
from collections.abc import Callable, Iterable
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pursuit.services.reporting.message import build_report_message, render_message
from pursuit.services.reporting.sink import SendReceipt
from pursuit.shared.reporting_config import ReportingMode, ReportingParams

__all__ = (
    "GMAIL_SEND_SCOPE",
    "SEND_ONLY_SCOPES",
    "GmailCredentialsError",
    "GmailRetryableError",
    "GmailScopeError",
    "GmailSink",
    "build_gmail_transport",
    "require_send_only_scope",
)

#: rule 30 -- send-only, and nothing else. Google's own identifier string.
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
SEND_ONLY_SCOPES = (GMAIL_SEND_SCOPE,)

GMAIL_API_NAME = "gmail"
GMAIL_API_VERSION = "v1"
#: The Gmail API's own alias for the authenticated account, which is also why
#: `message.py` writes no `From` header.
AUTHENTICATED_USER = "me"
#: RFC 6585's status code. Structural, not a tunable: rule 28 names 429 as the
#: block the token bucket exists to prevent.
TOO_MANY_REQUESTS = 429


class GmailScopeError(ValueError):
    """A requested or granted scope other than exactly `gmail.send` (rule 30)."""


class GmailCredentialsError(RuntimeError):
    """A credential/token environment variable that is unset or empty."""


class GmailRetryableError(RuntimeError):
    """HTTP 429. Raised, never slept on -- the gatekeeper owns the wait."""


def require_send_only_scope(scopes: Iterable[str], *, source: str) -> tuple[str, ...]:
    """Return `scopes` iff they are exactly `{gmail.send}`, else raise.

    A set comparison, so a duplicate is tolerated but an EXTRA scope and an
    EMPTY list are both rejected: "contains gmail.send" would pass a client
    that also holds `gmail.readonly`, which is the breach rule 30 names.
    """
    requested = tuple(scopes)
    if set(requested) != {GMAIL_SEND_SCOPE}:
        raise GmailScopeError(
            f"{source} must be exactly [{GMAIL_SEND_SCOPE}] -- send-only permission "
            f"scope (rule 30, docs/RULES.md:66). Got {list(requested)}"
        )
    return requested


def _require_env_value(params: ReportingParams, env_var: str) -> str:
    value = os.environ.get(env_var)
    if not value:
        raise GmailCredentialsError(
            f"environment variable {env_var} (named by reporting.json for "
            f"{params.mode.value} mode) is unset; place the file it names outside git "
            f"and export the path (rules 39-40)"
        )
    return value


def load_send_only_credentials(*, credentials_path: str, token_path: str) -> Credentials:
    """The cached token, refreshed or newly consented, verified send-only.

    The consent branch opens a browser and is 07-10's human step; every
    automated path either finds a valid token or fails loudly.
    """
    token_file = Path(token_path)
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(token_path, list(SEND_ONLY_SCOPES))
    if creds is not None and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif creds is None or not creds.valid:
        creds = InstalledAppFlow.from_client_secrets_file(
            credentials_path, list(SEND_ONLY_SCOPES)
        ).run_local_server()
    require_send_only_scope(creds.scopes or (), source="the granted OAuth token")
    token_file.write_text(creds.to_json(), encoding="utf-8")
    return creds


def build_gmail_transport(
    params: ReportingParams,
    *,
    scopes: Iterable[str] = SEND_ONLY_SCOPES,
    credentials_loader: Callable[..., Credentials] = load_send_only_credentials,
) -> object:
    """The Gmail service `GmailSink` sends through (07-10 supplies the files).

    Ordered so that the rule-30 check runs FIRST: a broader scope is refused
    before any credential is read, any file is touched or any network call is
    possible.
    """
    require_send_only_scope(scopes, source="the requested OAuth scopes")
    credentials = credentials_loader(
        credentials_path=_require_env_value(params, params.credentials_env_var),
        token_path=_require_env_value(params, params.token_env_var),
    )
    return build(
        GMAIL_API_NAME, GMAIL_API_VERSION, credentials=credentials, cache_discovery=False
    )


class GmailSink:
    """`reporting.mode = live`: one report, one `users().messages().send()`.

    `transport` is injected and has no default, so every test drives this class
    with a fake and none needs a credential or a network.
    """

    def __init__(self, *, transport: object, recipient: str) -> None:
        self._transport = transport
        self._recipient = recipient

    async def send(self, report: dict) -> SendReceipt:
        """Send the report as an attached JSON file. Raises on failure."""
        message = build_report_message(report=report, recipient=self._recipient)
        raw = base64.urlsafe_b64encode(render_message(message)).decode("ascii")
        sent = await asyncio.to_thread(self._execute, raw)
        return SendReceipt(mode=ReportingMode.LIVE, message_id=sent.get("id"))

    def _execute(self, raw: str) -> dict:
        """The blocking API call, off the event loop (`asyncio.to_thread`) so a
        slow send cannot stall the turn loop the freeze watchdog guards."""
        try:
            return (
                self._transport.users()
                .messages()
                .send(userId=AUTHENTICATED_USER, body={"raw": raw})
                .execute()
            )
        except HttpError as exc:
            if exc.status_code == TOO_MANY_REQUESTS:
                raise GmailRetryableError(
                    f"Gmail returned {TOO_MANY_REQUESTS}; the gatekeeper's ladder owns "
                    f"the wait (rule 28)"
                ) from exc
            raise
