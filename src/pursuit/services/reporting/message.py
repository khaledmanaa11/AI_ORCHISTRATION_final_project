"""The one MIME shape the mandatory game report is ever sent in (rules 33-34,
REPORT-05).

RULE 34 IS A ZERO-SCORE RULE, AND IT IS ABOUT THE *SHAPE* OF THE MESSAGE.
`docs/RULES.md:75`: "Send a final report as free text -- only as an attached
JSON file -> A non-JSON report is rejected in processing -> zero score." So the
report is a `Content-Disposition: attachment` part of type `application/json`,
and the text body is a FIXED boilerplate constant that carries no report
content at all. `tests/unit/test_mail_message.py` asserts both by re-parsing
the rendered bytes with the stdlib parser -- i.e. against the message that
would actually be sent, not against this module's intentions.

ONE SERIALIZER, NOT TWO. The attachment bytes come from
`config_hash.canonical_json`, the same entry point `artifacts.artifact_digest`
and `security/commit_pack.py` use. A second `json.dumps(sort_keys=True, ...)`
here would be a second canonicalisation of a payload this project also hashes
(QUAL-02, D-46), and the two would drift the first time one of them changed.

THE FILENAME IS 07-02's, NOT A NEW ONE. `docs/PARAMETERS.md:168` names
`result_<game_id>.json` and calls it "the mandatory report emailed to the
lecturer" -- so the attachment's filename is `result_filename(game_id)` from
the artifact namer, and a rename there renames the attachment for free.

THERE IS NO `From` HEADER, DELIBERATELY. The Gmail API fills it in from the
authenticated account (`userId="me"`), so writing one here would either be
wrong or would hardcode a personal address into git. `To` is passed in by the
caller from `reporting.json`; this module has no default recipient and no
address literal, because a fixed destination that a module could default to is
a fixed destination a typo can quietly change (docs/PARAMETERS.md:176-179).
"""

from __future__ import annotations

from email.message import EmailMessage
from email.policy import SMTP

from pursuit.network.config_hash import canonical_json
from pursuit.services.reporting.artifact_names import ArtifactField, result_filename

__all__ = (
    "ATTACHMENT_MAINTYPE",
    "ATTACHMENT_SUBTYPE",
    "BODY_TEXT",
    "SUBJECT_PREFIX",
    "build_report_message",
    "render_message",
    "report_filename",
)

#: rule 33 (`docs/RULES.md:74`) -- the report is structured JSON, so the part
#: that carries it is typed as JSON rather than as an opaque octet-stream.
ATTACHMENT_MAINTYPE = "application"
ATTACHMENT_SUBTYPE = "json"

#: The whole body. No interpolation, no f-string, no caller-supplied text: this
#: constant is what makes "the body carries no report content" a property of
#: the module rather than a habit of its callers.
BODY_TEXT = (
    "Automated end-of-game report from the UOH26 pursuit agents.\n"
    "\n"
    "The report is the attached JSON file. This body deliberately carries no\n"
    "report content: a report sent as free text is rejected in processing\n"
    "(rules 33-34).\n"
)

#: The subject names the ARTIFACT, which is a filename a grader can sort on and
#: which 07-02 already derives from `game_id`. It is not report content.
SUBJECT_PREFIX = "UOH26 pursuit game report: "


def report_filename(report: dict) -> str:
    """The attachment's filename: `result_<game_id>.json`.

    Raises `KeyError` naming `game_id` when the report has no header -- a
    report that cannot be named is a report that cannot be filed against a
    game, and mailing it anonymously is worse than failing loudly.
    """
    if not isinstance(report, dict):
        raise TypeError(f"report must be a dict, got {type(report).__name__}")
    if ArtifactField.GAME_ID not in report:
        raise KeyError(
            f"report has no '{ArtifactField.GAME_ID}'; the mandatory report is named "
            f"result_<game_id>.json (docs/PARAMETERS.md:168)"
        )
    return result_filename(report[ArtifactField.GAME_ID])


def build_report_message(*, report: dict, recipient: str) -> EmailMessage:
    """Assemble the report as an ATTACHED JSON file with a boilerplate body.

    `recipient` comes from `reporting.json`'s validated `recipient` leaf and
    has no default here (see the module docstring).
    """
    filename = report_filename(report)
    message = EmailMessage()
    message["To"] = recipient
    message["Subject"] = f"{SUBJECT_PREFIX}{filename}"
    message.set_content(BODY_TEXT)
    message.add_attachment(
        canonical_json(report).encode("utf-8"),
        maintype=ATTACHMENT_MAINTYPE,
        subtype=ATTACHMENT_SUBTYPE,
        filename=filename,
    )
    return message


def render_message(message: EmailMessage) -> bytes:
    """The RFC 5322 bytes that go on the wire or to the `.eml` on disk.

    `email.policy.SMTP` rather than the message's own default policy, so the
    line separator is CRLF: this is the form the Gmail API's `raw` field and a
    mail client both expect, and rendering one form for disk and another for
    the wire would mean the `.eml` a dry run leaves behind is not the message
    a live run sends.
    """
    return message.as_bytes(policy=SMTP)
