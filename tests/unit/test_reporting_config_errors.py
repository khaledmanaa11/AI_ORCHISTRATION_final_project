"""load_reporting_config's fail-loud half: every rejection, and every message
naming the offending key.

Split from test_reporting_config.py at the 150-code-line gate (Segal Table 5);
the shipped-file fixtures and `write_config` are defined once there (QUAL-02),
matching the test_gatekeeper.py / test_gatekeeper_retry.py precedent.
"""

from pathlib import Path

import pytest

from pursuit.shared.language_config import GATEKEEPER_MINIMA
from pursuit.shared.reporting_config import ReportingKey, load_reporting_config
from tests.unit.test_reporting_config import shipped, write_config

#: Realistic rule-39/40 leaks: what someone reaches for when "just make it
#: work" beats "read the contract". Each must be REFUSED by the loader.
_CREDENTIAL_LEAKS = (
    "C:/Users/Hp/secrets/client_secret.json",
    "/home/me/.config/gmail/token.json",
    "ya29.a0AfB_byC-not-a-real-token",
    '{"installed": {"client_id": "x"}}',
    "gmail_credentials_path",
)

_REQUIRED_GROUPS = (ReportingKey.GROUP_GATEKEEPER, ReportingKey.GROUP_REPORTING)

_REPORTING_LEAVES = (
    ReportingKey.MODE,
    ReportingKey.RECIPIENT,
    ReportingKey.ARTIFACT_DIR,
    ReportingKey.CREDENTIALS_ENV_VAR,
    ReportingKey.TOKEN_ENV_VAR,
)


def _police() -> dict:
    return shipped("police")


def test_the_leak_and_leaf_tables_are_not_empty() -> None:
    """A parametrize over an empty list SKIPS silently -- assert the three
    tables below carry cases before trusting any test that iterates them."""
    assert len(_CREDENTIAL_LEAKS) == 5
    assert len(_REPORTING_LEAVES) == 5
    assert len(GATEKEEPER_MINIMA) == 5


@pytest.mark.parametrize("group", _REQUIRED_GROUPS)
def test_a_missing_group_raises_keyerror_naming_it(tmp_path: Path, group: ReportingKey) -> None:
    data = _police()
    del data[group.value]
    with pytest.raises(KeyError, match=group.value):
        load_reporting_config(write_config(tmp_path, data))


def test_a_missing_version_raises_keyerror_naming_it(tmp_path: Path) -> None:
    data = _police()
    del data[ReportingKey.VERSION.value]
    with pytest.raises(KeyError, match=ReportingKey.VERSION.value):
        load_reporting_config(write_config(tmp_path, data))


@pytest.mark.parametrize("group", _REQUIRED_GROUPS)
def test_a_non_object_group_raises_typeerror_naming_it(
    tmp_path: Path, group: ReportingKey
) -> None:
    data = _police()
    data[group.value] = "not an object"
    with pytest.raises(TypeError, match=group.value):
        load_reporting_config(write_config(tmp_path, data))


@pytest.mark.parametrize(("name", "key", "row", "minimum"), GATEKEEPER_MINIMA)
def test_a_row_below_its_table_19_floor_raises_naming_the_key(
    tmp_path: Path, name: str, key: object, row: int, minimum: int
) -> None:
    """The five MINIMUM rows may be raised, never lowered (docs/PARAMETERS.md
    Table 19). The same floors the LLM loader enforces, from the same table."""
    data = _police()
    data[ReportingKey.GROUP_GATEKEEPER.value][key.value] = minimum - 1
    with pytest.raises(ValueError, match=key.value) as raised:
        load_reporting_config(write_config(tmp_path, data))
    assert str(minimum) in str(raised.value)
    assert f"row {row}" in str(raised.value)


@pytest.mark.parametrize(("name", "key", "row", "minimum"), GATEKEEPER_MINIMA)
def test_a_row_at_its_floor_is_accepted(
    tmp_path: Path, name: str, key: object, row: int, minimum: int
) -> None:
    """The control for the test above: exactly the floor must PASS, or the
    rejection test would pass against a loader that rejected everything."""
    data = _police()
    data[ReportingKey.GROUP_GATEKEEPER.value][key.value] = minimum
    assert getattr(load_reporting_config(write_config(tmp_path, data)), name) == minimum


def test_a_non_int_row_raises_typeerror_naming_the_key(tmp_path: Path) -> None:
    data = _police()
    data[ReportingKey.GROUP_GATEKEEPER.value][ReportingKey.REQUESTS_PER_HOUR.value] = "500"
    with pytest.raises(TypeError, match=ReportingKey.REQUESTS_PER_HOUR.value):
        load_reporting_config(write_config(tmp_path, data))


@pytest.mark.parametrize("hourly", [0, -1])
def test_a_non_positive_hourly_ceiling_is_refused(tmp_path: Path, hourly: int) -> None:
    data = _police()
    data[ReportingKey.GROUP_GATEKEEPER.value][ReportingKey.REQUESTS_PER_HOUR.value] = hourly
    with pytest.raises(ValueError, match=ReportingKey.REQUESTS_PER_HOUR.value):
        load_reporting_config(write_config(tmp_path, data))


@pytest.mark.parametrize("leaf", _REPORTING_LEAVES)
def test_a_missing_reporting_leaf_raises_keyerror_naming_it(
    tmp_path: Path, leaf: ReportingKey
) -> None:
    data = _police()
    del data[ReportingKey.GROUP_REPORTING.value][leaf.value]
    with pytest.raises(KeyError, match=leaf.value):
        load_reporting_config(write_config(tmp_path, data))


@pytest.mark.parametrize("mode", ["DRY_RUN", "test", "", "live "])
def test_an_unknown_mode_is_refused(tmp_path: Path, mode: str) -> None:
    data = _police()
    data[ReportingKey.GROUP_REPORTING.value][ReportingKey.MODE.value] = mode
    with pytest.raises(ValueError, match=ReportingKey.MODE.value):
        load_reporting_config(write_config(tmp_path, data))


def test_live_is_a_permitted_mode(tmp_path: Path) -> None:
    """Control: `live` must load, or the rejection test above would be passing
    against a loader that had simply stopped accepting anything."""
    data = _police()
    data[ReportingKey.GROUP_REPORTING.value][ReportingKey.MODE.value] = "live"
    assert load_reporting_config(write_config(tmp_path, data)).mode.value == "live"


def test_any_recipient_but_the_mandatory_address_is_refused(tmp_path: Path) -> None:
    data = _police()
    data[ReportingKey.GROUP_REPORTING.value][ReportingKey.RECIPIENT.value] = "rmisegal@gmail.com"
    with pytest.raises(ValueError, match=ReportingKey.RECIPIENT.value):
        load_reporting_config(write_config(tmp_path, data))


@pytest.mark.parametrize("blank", ["", "   "])
def test_a_blank_artifact_dir_is_refused(tmp_path: Path, blank: str) -> None:
    data = _police()
    data[ReportingKey.GROUP_REPORTING.value][ReportingKey.ARTIFACT_DIR.value] = blank
    with pytest.raises(ValueError, match=ReportingKey.ARTIFACT_DIR.value):
        load_reporting_config(write_config(tmp_path, data))


@pytest.mark.parametrize("leaked", _CREDENTIAL_LEAKS)
@pytest.mark.parametrize("key", [ReportingKey.CREDENTIALS_ENV_VAR, ReportingKey.TOKEN_ENV_VAR])
def test_a_credential_value_in_place_of_an_env_var_name_is_refused(
    tmp_path: Path, key: ReportingKey, leaked: str
) -> None:
    """Rules 39-40: config names the VARIABLE; the environment holds the value.
    This is the field a secret would reach git through."""
    data = _police()
    data[ReportingKey.GROUP_REPORTING.value][key.value] = leaked
    with pytest.raises(ValueError, match=key.value):
        load_reporting_config(write_config(tmp_path, data))
