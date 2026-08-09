"""Offline unit tests for gate5_smoke_checks.py's pure functions (05-03
must_haves: "a unit-testable core: URL-pattern check and evidence-file
writer are importable and covered offline"). Zero network, zero pyngrok,
zero env vars set -- imports scripts/ via the same sys.path-bootstrap idiom
scripts/measure_gate4.py itself uses for direct execution.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from gate5_smoke_checks import (  # noqa: E402
    build_evidence,
    check_public_url,
    missing_env_vars,
    write_evidence,
)


def test_missing_env_vars_reports_every_absent_name_in_order():
    env = {"A": "set", "C": ""}
    assert missing_env_vars(["A", "B", "C", "D"], env=env) == ["B", "C", "D"]


def test_missing_env_vars_empty_when_all_present():
    env = {"A": "x", "B": "y"}
    assert missing_env_vars(["A", "B"], env=env) == []


def test_check_public_url_accepts_https_matching_domain():
    assert check_public_url(
        "https://myteam-cop.ngrok-free.app", "myteam-cop.ngrok-free.app"
    )


def test_check_public_url_rejects_http():
    assert not check_public_url(
        "http://myteam-cop.ngrok-free.app", "myteam-cop.ngrok-free.app"
    )


def test_check_public_url_rejects_mismatched_domain():
    assert not check_public_url(
        "https://random-subdomain.ngrok-free.app", "myteam-cop.ngrok-free.app"
    )


def test_build_evidence_pass_when_all_three_checks_succeed():
    evidence = build_evidence(
        public_url="https://myteam-cop.ngrok-free.app",
        expected_domain="myteam-cop.ngrok-free.app",
        url_check_passed=True,
        round_trip_seconds=0.123,
        authorized_request_ok=True,
        unauthorized_request_rejected=True,
        generated_at="2026-08-09T00:00:00+00:00",
    )
    assert evidence["verdict"] == "PASS"
    assert evidence["round_trip_seconds"] == 0.123
    assert evidence["generated_at"] == "2026-08-09T00:00:00+00:00"


def test_build_evidence_fail_when_any_check_fails():
    evidence = build_evidence(
        public_url="https://x",
        expected_domain="x",
        url_check_passed=True,
        round_trip_seconds=0.1,
        authorized_request_ok=True,
        unauthorized_request_rejected=False,
    )
    assert evidence["verdict"] == "FAIL"


def test_write_evidence_creates_parent_dirs_and_writes_valid_json(tmp_path):
    target = tmp_path / "nested" / "evidence.json"
    evidence = {"verdict": "PASS"}

    returned = write_evidence(target, evidence)

    assert returned == target
    assert json.loads(target.read_text(encoding="utf-8")) == evidence
