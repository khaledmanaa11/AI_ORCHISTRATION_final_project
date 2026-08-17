"""The SHIPPED config/{police,thief}/reporting.json files, asserted against
their sources -- the half of 07-01 Task 3 that guards what actually ships.

The fail-loud rejection suite lives in test_reporting_config_errors.py (split
at the 150-code-line gate), and shares `write_config` from here.
"""

import json
from pathlib import Path

import pytest

from pursuit.services.llm import Gatekeeper
from pursuit.shared.gatekeeper_params import BudgetParams, GatekeeperParams
from pursuit.shared.language_config import GATEKEEPER_MINIMA, load_language_config
from pursuit.shared.reporting_config import (
    MANDATORY_REPORTING_ADDRESS,
    ReportingMode,
    load_reporting_config,
)

ROLES = ("police", "thief")
SHIPPED_CONFIG = Path(__file__).resolve().parents[2] / "config"

#: OQ-3, the one difference between the two gatekeeper instances, pinned on
#: BOTH sides so neither can be "harmonised" into the other. 30 s is the mail
#: instance (docs/PARAMETERS.md:95's 5 s minimum negotiated upward to
#: docs/SEGAL_GUIDELINES.md:174's retry_after_seconds, per :182's stricter
#: rule); 5 s is Phase 4's shipped LLM value, which this plan must not touch.
_MAIL_BACKOFF_SECONDS = 30
_LLM_BACKOFF_SECONDS = 5

#: docs/SEGAL_GUIDELINES.md:173, the Quota Manager's ceiling (OQ-1).
_SEGAL_REQUESTS_PER_HOUR = 500


def shipped(role: str) -> dict:
    return json.loads((SHIPPED_CONFIG / role / "reporting.json").read_text(encoding="utf-8"))


def write_config(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "reporting.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.mark.parametrize("role", ROLES)
def test_shipped_file_loads(role: str) -> None:
    params = load_reporting_config(SHIPPED_CONFIG / role / "reporting.json")
    assert params.recipient == MANDATORY_REPORTING_ADDRESS
    assert params.requests_per_hour == _SEGAL_REQUESTS_PER_HOUR


@pytest.mark.parametrize("role", ROLES)
def test_shipped_file_ships_dry_run(role: str) -> None:
    """Nothing this repository ships may transmit. Only 07-10 flips a config
    to live, for one supervised send, and flips it back (rules 31, 39-40)."""
    assert load_reporting_config(SHIPPED_CONFIG / role / "reporting.json").mode is (
        ReportingMode.DRY_RUN
    )


@pytest.mark.parametrize("role", ROLES)
def test_oq3_backoff_is_scoped_to_the_mail_instance(role: str) -> None:
    """The Phase-4 regression this plan is most likely to cause, asserted as
    ONE fact: the two instances hold DIFFERENT backoffs, on purpose."""
    mail = load_reporting_config(SHIPPED_CONFIG / role / "reporting.json")
    llm = load_language_config(SHIPPED_CONFIG / role / "language.json")
    assert mail.wait_after_error_seconds == _MAIL_BACKOFF_SECONDS
    assert llm.wait_after_error_seconds == _LLM_BACKOFF_SECONDS
    assert mail.parallel_requests == llm.parallel_requests  # OQ-3: both keep 2


def test_both_roles_ship_identical_reporting_settings() -> None:
    police, thief = (load_reporting_config(SHIPPED_CONFIG / r / "reporting.json") for r in ROLES)
    assert police == thief


@pytest.mark.parametrize("role", ROLES)
def test_shipped_file_has_no_daily_leaf(role: str) -> None:
    """OQ-1: no document gives a daily figure, so none is written. A `daily`
    key appearing later would be an invented number wearing a config hat."""
    text = json.dumps(shipped(role)["gatekeeper"]).lower()
    assert "day" not in text


@pytest.mark.parametrize("role", ROLES)
def test_every_numeric_leaf_carries_a_cited_source(role: str) -> None:
    """CLAUDE.md rule 1: no invented numeric values. Structural, not a promise
    -- a new number added without a citation fails this test."""
    data = shipped(role)
    numeric = [
        f"gatekeeper.{key}"
        for key, value in data["gatekeeper"].items()
        if isinstance(value, int)
    ]
    assert numeric, "no numeric leaves found -- the scan would pass vacuously"
    assert set(numeric) <= set(data["_sources"])


@pytest.mark.parametrize("role", ROLES)
def test_artifact_dir_is_not_inside_the_gitignored_logs_tree(role: str) -> None:
    """The 07-01 decision, pinned. `.gitignore` ignores `logs/` wholesale while
    rule 50 requires the four JSON artifacts to be committed; a future edit
    pointing the artifact dir back at `logs/` would silently un-commit them."""
    artifact_dir = load_reporting_config(SHIPPED_CONFIG / role / "reporting.json").artifact_dir
    assert not Path(artifact_dir).is_absolute()
    assert Path(artifact_dir).parts[0] != "logs"


def test_reporting_params_are_gatekeeper_params_and_not_budget_params() -> None:
    """D-68's mechanism: the ABSENCE of the three budget rows is what hands the
    mail gatekeeper `budget = None`, with no caller passing a flag."""
    params = load_reporting_config(SHIPPED_CONFIG / "police" / "reporting.json")
    assert isinstance(params, GatekeeperParams)
    assert not isinstance(params, BudgetParams)
    assert Gatekeeper(params=params).budget is None


def test_the_shared_minima_table_still_holds_its_five_rows() -> None:
    """Every below-floor test in test_reporting_config_errors.py parametrizes
    over GATEKEEPER_MINIMA. An emptied table would SKIP them all silently, so
    the table's own size is asserted here rather than assumed there."""
    assert len(GATEKEEPER_MINIMA) == 5
