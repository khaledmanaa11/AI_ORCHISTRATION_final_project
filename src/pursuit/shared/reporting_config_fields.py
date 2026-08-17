"""reporting.json's key names, its two fixed strings, and the per-group
validation `shared/reporting_config.py` delegates to.

Split from that loader at the 150-code-line gate (Segal Table 5 -- CLAUDE.md:
"split files, never compress"), on exactly the precedent 04-06 set when
`shared/language_config.py` grew past the gate and `ModelKey` +
`validate_model_group` moved into `shared/language_model_config.py`. The
dependency runs ONE way: this module never imports its loader.

The five Table-19 MINIMUM rows are floor-checked against
`language_config.GATEKEEPER_MINIMA` -- the same table the LLM loader has
always used, imported rather than re-declared, so a floor can never drift
between the two gatekeeper instances (CLAUDE.md Table 5: extract at 2+ copies).
"""

from enum import Enum
from re import compile as re_compile

from pursuit.shared.language_config import GATEKEEPER_MINIMA, GATEKEEPER_NEGOTIABLE
from pursuit.shared.loader_helpers import require_int, require_key, require_str

REPORTING_CONFIG_SOURCE = "reporting.json"

#: docs/PARAMETERS.md:176 -- "the single mandatory destination" for game
#: reports, which "must be configured as the fixed recipient in BOTH agents'
#: mail-sending code". FIXED status, so the loader rejects any other value
#: rather than trusting the config: a typo here mails a stranger.
MANDATORY_REPORTING_ADDRESS = "rmisegal+uoh26finalgame@gmail.com"

#: An environment variable NAME -- never its value, never a filesystem path
#: (rules 39-40). A real credential path or a pasted JSON blob cannot match.
_ENV_VAR_NAME = re_compile(r"^[A-Z][A-Z0-9_]*$")


class ReportingMode(str, Enum):
    """`dry_run` writes the report to disk and TRANSMITS NOTHING; `live` sends.

    Every config this repository ships is `dry_run`. Only the 07-10 human
    checkpoint flips one to `live`, for one supervised send, and flips it back.
    """

    DRY_RUN = "dry_run"
    LIVE = "live"


class ReportingKey(str, Enum):
    """Field names for config/{police,thief}/reporting.json.

    Structural only -- no numeric literal on this enum. The five floor-checked
    row names are absent on purpose: they come from GATEKEEPER_MINIMA, so this
    file cannot drift from the LLM loader's spelling of them.
    """

    VERSION = "version"
    GROUP_GATEKEEPER = "gatekeeper"
    REQUESTS_PER_HOUR = "requests_per_hour"
    GROUP_REPORTING = "reporting"
    MODE = "mode"
    RECIPIENT = "recipient"
    ARTIFACT_DIR = "artifact_dir"
    CREDENTIALS_ENV_VAR = "credentials_env_var"
    TOKEN_ENV_VAR = "token_env_var"


def require_group(data: dict, key: ReportingKey) -> dict:
    """The named top-level object, or a KeyError/TypeError naming it."""
    group = require_key(data, key.value, source=REPORTING_CONFIG_SOURCE)
    if not isinstance(group, dict):
        raise TypeError(
            f"{REPORTING_CONFIG_SOURCE} field '{key.value}' must be an object, "
            f"got {type(group).__name__}"
        )
    return group


def read_gatekeeper_group(group: dict) -> dict[str, int]:
    """Table 19's seven rows plus SEGAL's hourly ceiling, all validated.

    Rows 1-5 carry MINIMUM status: config may raise them, never lower them,
    and a violation names the key and its floor. Rows 6-7 are negotiable and
    take no floor. `requests_per_hour` is docs/SEGAL_GUIDELINES.md:173's own
    figure for the generic API gatekeeper (OQ-1); it has no Table-19 row, so
    the only check it can carry is that it is a positive count.
    """
    fields: dict[str, int] = {}
    for name, key, row, minimum in GATEKEEPER_MINIMA:
        value = require_int(group, key.value, source=REPORTING_CONFIG_SOURCE)
        if value < minimum:
            raise ValueError(
                f"{REPORTING_CONFIG_SOURCE} field '{key.value}' must be >= {minimum} "
                f"(docs/PARAMETERS.md Table 19 row {row} minimum), got {value}"
            )
        fields[name] = value
    for name, key in GATEKEEPER_NEGOTIABLE:
        fields[name] = require_int(group, key.value, source=REPORTING_CONFIG_SOURCE)
    hourly = require_int(
        group, ReportingKey.REQUESTS_PER_HOUR.value, source=REPORTING_CONFIG_SOURCE
    )
    if hourly <= 0:
        raise ValueError(
            f"{REPORTING_CONFIG_SOURCE} field '{ReportingKey.REQUESTS_PER_HOUR.value}' "
            f"must be a positive count of requests (docs/SEGAL_GUIDELINES.md:173), "
            f"got {hourly}"
        )
    fields["requests_per_hour"] = hourly
    return fields


def read_reporting_group(group: dict) -> dict[str, object]:
    """The structural leaves: mode, recipient, artifact dir, env-var NAMES."""
    raw_mode = require_str(group, ReportingKey.MODE.value, source=REPORTING_CONFIG_SOURCE)
    try:
        mode = ReportingMode(raw_mode)
    except ValueError as exc:
        permitted = ", ".join(member.value for member in ReportingMode)
        raise ValueError(
            f"{REPORTING_CONFIG_SOURCE} field '{ReportingKey.MODE.value}' must be one "
            f"of [{permitted}], got {raw_mode!r}"
        ) from exc
    recipient = require_str(group, ReportingKey.RECIPIENT.value, source=REPORTING_CONFIG_SOURCE)
    if recipient != MANDATORY_REPORTING_ADDRESS:
        raise ValueError(
            f"{REPORTING_CONFIG_SOURCE} field '{ReportingKey.RECIPIENT.value}' must be "
            f"exactly {MANDATORY_REPORTING_ADDRESS!r}, the single mandatory destination "
            f"(docs/PARAMETERS.md:176), got {recipient!r}"
        )
    artifact_dir = require_str(
        group, ReportingKey.ARTIFACT_DIR.value, source=REPORTING_CONFIG_SOURCE
    )
    if not artifact_dir.strip():
        raise ValueError(
            f"{REPORTING_CONFIG_SOURCE} field '{ReportingKey.ARTIFACT_DIR.value}' "
            f"must name a directory, got {artifact_dir!r}"
        )
    fields: dict[str, object] = {
        "mode": mode, "recipient": recipient, "artifact_dir": artifact_dir,
    }
    for key in (ReportingKey.CREDENTIALS_ENV_VAR, ReportingKey.TOKEN_ENV_VAR):
        fields[key.value] = _require_env_var_name(group, key)
    return fields


def _require_env_var_name(group: dict, key: ReportingKey) -> str:
    """Rules 39-40: config names the VARIABLE, the environment holds the value.

    A path, a token or a pasted credential all fail this shape, so a secret
    cannot reach git through a field that was only ever meant to hold a name.
    """
    name = require_str(group, key.value, source=REPORTING_CONFIG_SOURCE)
    if not _ENV_VAR_NAME.match(name):
        raise ValueError(
            f"{REPORTING_CONFIG_SOURCE} field '{key.value}' must be a bare environment "
            f"variable NAME matching {_ENV_VAR_NAME.pattern} -- never a credential, a "
            f"token or a path (rules 39-40). Got {name!r}"
        )
    return name
