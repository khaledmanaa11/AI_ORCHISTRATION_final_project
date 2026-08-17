"""Rules 33-34, asserted by RE-PARSING the message that would be sent.

Nothing here inspects `message.py`'s builder state. Every assertion runs
against `email.message_from_bytes(render_message(...))`, because the thing the
lecturer's processing sees is the rendered bytes, and a builder can be careful
while the renderer leaks.

The leak checks come in PAIRS: a positive assertion that a distinctive report
value is absent from every non-attachment part, and a control that plants that
same value there and asserts the check FAILS. An absence assertion with no
control is a test that would pass against a message with no body at all.
"""

import json
from email import message_from_bytes
from email.policy import default as default_policy
from pathlib import Path

import pytest

from pursuit.services.reporting.artifacts import result_filename
from pursuit.services.reporting.message import (
    ATTACHMENT_MAINTYPE,
    ATTACHMENT_SUBTYPE,
    BODY_TEXT,
    SUBJECT_PREFIX,
    build_report_message,
    render_message,
    report_filename,
)
from pursuit.shared.reporting_config import load_reporting_config

# docs/PARAMETERS.md:178 -- transcribed as a LITERAL, not imported from the
# module under test, so a rename in source fails against the document.
MANDATORY_ADDRESS_LITERAL = "rmisegal+uoh26finalgame@gmail.com"
CONFIG_ROOT = Path(__file__).resolve().parents[2] / "config"
SHIPPED_ROLES = ("police", "thief")

GAME_ID = "abc123"
GAME_UID = "uid-9f3c-distinctive-value"


def _report() -> dict:
    return {
        "game_uid": GAME_UID,
        "game_id": GAME_ID,
        "outcome": "capture",
        "turns": 11,
        "tokens": {"input": 400, "output": 120},
    }


def _rendered(report: dict | None = None) -> bytes:
    message = build_report_message(
        report=report if report is not None else _report(),
        recipient=MANDATORY_ADDRESS_LITERAL,
    )
    return render_message(message)


def _attachments(rendered: bytes) -> list:
    """Parts DISPOSED as attachments. `iter_attachments()` alone yields every
    non-body part whatever its disposition, so filtering here is what stops an
    inline JSON part from counting as "attached" (rule 34)."""
    parsed = message_from_bytes(rendered, policy=default_policy)
    return [
        part for part in parsed.iter_attachments()
        if part.get_content_disposition() == "attachment"
    ]


def _non_attachment_text(rendered: bytes) -> str:
    """Every header value plus the plain-text body -- everything a reader sees
    that is NOT the attachment."""
    parsed = message_from_bytes(rendered, policy=default_policy)
    chunks = [f"{name}: {value}" for name, value in parsed.items()]
    chunks.append(parsed.get_body(preferencelist=("plain",)).get_content())
    return "\n".join(chunks)


def _leak_free(rendered: bytes, needle: str) -> bool:
    return needle not in _non_attachment_text(rendered)


def test_exactly_one_attachment_part():
    assert len(_attachments(_rendered())) == 1


def test_attachment_is_disposed_as_an_attachment_with_the_artifact_filename():
    part = _attachments(_rendered())[0]
    assert part.get_content_disposition() == "attachment"
    assert part.get_filename() == result_filename(GAME_ID)


def test_attachment_is_typed_as_json():
    part = _attachments(_rendered())[0]
    assert part.get_content_type() == f"{ATTACHMENT_MAINTYPE}/{ATTACHMENT_SUBTYPE}"


def test_attachment_round_trips_through_json_loads_to_the_original_object():
    part = _attachments(_rendered())[0]
    assert json.loads(part.get_payload(decode=True).decode("utf-8")) == _report()


def test_body_is_exactly_the_boilerplate_constant():
    """Modulo the wire line separator only: `render_message` emits CRLF (see
    its docstring), so the parsed body's newlines are the transport's, not
    content the builder added."""
    parsed = message_from_bytes(_rendered(), policy=default_policy)
    body = parsed.get_body(preferencelist=("plain",)).get_content()
    assert body.replace("\r\n", "\n") == BODY_TEXT


def test_a_distinctive_report_value_never_leaves_the_attachment():
    assert _leak_free(_rendered(), GAME_UID)


def test_control_the_leak_check_fails_when_the_body_carries_the_value():
    message = build_report_message(report=_report(), recipient=MANDATORY_ADDRESS_LITERAL)
    body = message.get_body(preferencelist=("plain",))
    body.set_content(f"{BODY_TEXT}\ngame_uid was {GAME_UID}\n")
    assert not _leak_free(render_message(message), GAME_UID)


def test_control_the_leak_check_fails_when_a_header_carries_the_value():
    message = build_report_message(report=_report(), recipient=MANDATORY_ADDRESS_LITERAL)
    del message["Subject"]
    message["Subject"] = f"{SUBJECT_PREFIX}{GAME_UID}"
    assert not _leak_free(render_message(message), GAME_UID)


def test_subject_names_the_artifact_file():
    parsed = message_from_bytes(_rendered(), policy=default_policy)
    assert parsed["Subject"] == f"{SUBJECT_PREFIX}{result_filename(GAME_ID)}"


def test_no_from_header_is_written_the_gmail_api_fills_it_in():
    assert message_from_bytes(_rendered(), policy=default_policy)["From"] is None


def test_to_header_is_the_mandatory_destination():
    parsed = message_from_bytes(_rendered(), policy=default_policy)
    assert parsed["To"] == MANDATORY_ADDRESS_LITERAL


@pytest.mark.parametrize("role", SHIPPED_ROLES)
def test_both_shipped_configs_name_the_mandatory_destination(role):
    params = load_reporting_config(CONFIG_ROOT / role / "reporting.json")
    assert params.recipient == MANDATORY_ADDRESS_LITERAL


def test_shipped_roles_table_is_not_empty():
    """Guards the parametrize above: an emptied tuple would SKIP silently."""
    assert len(SHIPPED_ROLES) == 2


def test_rendered_bytes_use_crlf_so_disk_and_wire_agree():
    assert b"\r\n" in _rendered()


def test_report_filename_rejects_a_report_with_no_game_id():
    with pytest.raises(KeyError, match="game_id"):
        report_filename({"game_uid": GAME_UID})


def test_report_filename_rejects_a_non_dict_report():
    with pytest.raises(TypeError, match="must be a dict"):
        report_filename(["not", "a", "report"])
