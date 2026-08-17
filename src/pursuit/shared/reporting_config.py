"""Fail-loud config loader for reporting.json -- the MAIL gatekeeper's limits
and the reporting shell's structural strings (D-68/D-69; REPORT-02/03/04).

Follows shared/language_config.py's four-part convention exactly: a `*Key`
str-Enum beside its own loader, a frozen params dataclass, the minima named in
a module-level table, and KeyError/TypeError/ValueError that name the
offending key. `ReportingKey`, `ReportingMode` and the per-group validation
live in shared/reporting_config_fields.py -- the same 150-line split 04-06
made between language_config.py and language_model_config.py -- and are
re-exported here so callers have ONE import path.

`ReportingParams` satisfies `GatekeeperParams` and NOT `BudgetParams`, and
that absence is the whole mechanism: it is what makes `budget_for_params`
hand the mail gatekeeper `budget = None` (D-68).

ZERO NEW BOOK NUMBERS. Every numeric leaf in reporting.json is a Table-19 row
or SEGAL's own figure, and each carries its citation in the file's `_sources`
object. Two leaves differ from config/*/language.json and both are OQ-3, which
is scoped to THIS instance -- Phase 4's LLM path is not retuned by this plan:
`wait_after_error_seconds` 30 (docs/PARAMETERS.md:95 gives 5 as a MINIMUM,
negotiable upward and never downward; docs/SEGAL_GUIDELINES.md:174 gives
`retry_after_seconds: 30`; :182 says take the stricter value) and
`parallel_requests` 2 (PARAMETERS' required minimum, and stricter than SEGAL's
`concurrent_max: 5`).

OQ-1: `requests_per_hour` is docs/SEGAL_GUIDELINES.md:173's sourced 500, and
is what QuotaManager enforces. NO document anywhere gives a DAILY figure, so
this file has no daily leaf. Should a daily bound ever be needed it is DERIVED
as 24 x requests_per_hour and labelled derived -- never a book value.

ARTIFACT DIRECTORY -- decided here, deliberately, not defaulted. The four
required JSON artifacts must be committed (docs/PARAMETERS.md "Required JSON
artifacts", rule 50), but `.gitignore` ignores `logs/` WHOLESALE while its own
comment claims the four artifacts are kept out of the ignore list -- and
`agent_step0_wiring.write_declaration` writes `declaration_<game_id>.json`
into `logs/<role>/`, so today's declaration artifact is unreachable to git.
`game_artifacts/` is used instead: verified NOT ignored (`git check-ignore`),
and distinct from the existing `artifacts/` tree, which holds regenerable
training curves and is excluded from ruff. The `logs/` contradiction is a
finding recorded for 07-02, which owns the artifact spine; this loader only
declines to inherit it.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from pursuit.shared.loader_helpers import require_str
from pursuit.shared.reporting_config_fields import (
    MANDATORY_REPORTING_ADDRESS,
    REPORTING_CONFIG_SOURCE,
    ReportingKey,
    ReportingMode,
    read_gatekeeper_group,
    read_reporting_group,
    require_group,
)

__all__ = (
    "MANDATORY_REPORTING_ADDRESS",
    "REPORTING_CONFIG_SOURCE",
    "ReportingKey",
    "ReportingMode",
    "ReportingParams",
    "load_reporting_config",
)


@dataclass(frozen=True)
class ReportingParams:
    """Typed, immutable container for every value load_reporting_config reads.

    The first seven fields ARE docs/PARAMETERS.md Table 19, in the order the
    table lists them, which is what makes this a `GatekeeperParams`. There is
    deliberately no token-budget field. Constructed only by
    load_reporting_config: a fresh instance per call, never a shared live
    object, so the police and thief processes can never leak state through it
    (CLAUDE.md rule 2).
    """

    version: str
    requests_per_minute: int
    parallel_requests: int
    wait_after_error_seconds: int
    retries_before_failure: int
    queue_depth: int
    response_timeout_seconds: int
    watchdog_threshold_seconds: int
    requests_per_hour: int
    mode: ReportingMode
    recipient: str
    artifact_dir: str
    credentials_env_var: str
    token_env_var: str


def load_reporting_config(path: "Path | str") -> ReportingParams:
    """Load and validate config/{police,thief}/reporting.json.

    Raises
    ------
    KeyError
        If any required key (top-level group or leaf) is absent.
    TypeError
        If a group is not an object, or a leaf carries the wrong type.
    ValueError
        If a Table-19 MINIMUM row (rows 1-5) is below its floor, if
        `requests_per_hour` is not positive, if `mode` is not a
        `ReportingMode`, if `recipient` is not the mandatory address, if
        `artifact_dir` is blank, or if either credential key holds anything
        but a bare environment-variable NAME. Every message names the key.
    """
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise TypeError(f"{REPORTING_CONFIG_SOURCE} must be a JSON object")

    version = require_str(data, ReportingKey.VERSION.value, source=REPORTING_CONFIG_SOURCE)
    fields: dict[str, object] = {"version": version}
    fields.update(read_gatekeeper_group(require_group(data, ReportingKey.GROUP_GATEKEEPER)))
    fields.update(read_reporting_group(require_group(data, ReportingKey.GROUP_REPORTING)))
    return ReportingParams(**fields)
