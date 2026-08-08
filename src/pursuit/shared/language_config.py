"""Fail-loud config loader for language.json (D-34/D-35; QUAL-03, QUAL-05, LANG-06).

load_language_config() is the single entry point for the LLM gatekeeper's rate-limit
and budget numbers. Three JSON groups: `gatekeeper` (docs/PARAMETERS.md Table 19 --
five MINIMUM-status rows floor-checked against _GATEKEEPER_MINIMA below, plus two
NEGOTIABLE rows loaded with no floor), `budget` (Table 18 row 4's negotiable series
ceiling, plus two engineering-default degrade thresholds -- D-18 discipline: neither
threshold is a book value, both are labelled as such here, not in the loader body),
and `model` (an opaque dict; plan 04-06 defines and reads its contents -- this loader
only requires the key to be present and object-typed).

Deviation from the config_keys.py convention (04-PLAN-OUTLINE.md Sec4 point 2):
LanguageKey lives here, beside its own loader, instead of in pursuit.config_keys --
that module is already 90 of its 150 permitted lines, and four more phase-4 key
enums (Scent/Language/Belief/Deception) would breach the file-size gate. Every other
phase-4 config loader follows the same pattern.
"""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pursuit.shared.loader_helpers import require_int, require_key

LANGUAGE_CONFIG_SOURCE = "language.json"


class LanguageKey(str, Enum):
    """Field names for config/{police,thief}/language.json.

    Structural only -- no numeric literal lives on this enum (D-05 discipline
    extended to Phase 4); every number is in the JSON files or _GATEKEEPER_MINIMA.
    """

    VERSION = "version"
    GROUP_GATEKEEPER = "gatekeeper"
    REQUESTS_PER_MINUTE = "requests_per_minute"
    PARALLEL_REQUESTS = "parallel_requests"
    WAIT_AFTER_ERROR_SECONDS = "wait_after_error_seconds"
    RETRIES_BEFORE_FAILURE = "retries_before_failure"
    QUEUE_DEPTH = "queue_depth"
    RESPONSE_TIMEOUT_SECONDS = "response_timeout_seconds"
    WATCHDOG_THRESHOLD_SECONDS = "watchdog_threshold_seconds"
    GROUP_BUDGET = "budget"
    TOKEN_BUDGET_PER_SERIES = "token_budget_per_series"
    SHORT_PROMPT_THRESHOLD_TOKENS = "short_prompt_threshold_tokens"
    TEMPLATE_ONLY_THRESHOLD_TOKENS = "template_only_threshold_tokens"
    GROUP_MODEL = "model"


@dataclass(frozen=True)
class LanguageParams:
    """Typed, immutable container for every value load_language_config() reads.

    Constructed only by load_language_config() -- callers never build this directly
    (NET-02 precedent: a fresh instance every call, never a shared live object, so
    police and thief processes can never leak state through it -- CLAUDE.md rule 2).
    """

    version: str
    requests_per_minute: int
    parallel_requests: int
    wait_after_error_seconds: int
    retries_before_failure: int
    queue_depth: int
    response_timeout_seconds: int
    watchdog_threshold_seconds: int
    token_budget_per_series: int
    short_prompt_threshold_tokens: int
    template_only_threshold_tokens: int
    model: dict


# docs/PARAMETERS.md Table 19's five MINIMUM-status rows (book values, not
# engineering defaults -- D-18 discipline). Config may raise these, never lower
# them; load_language_config() enforces the floor and names the key on violation.
# (field name, LanguageKey, Table 19 row #, minimum)
_GATEKEEPER_MINIMA: tuple[tuple[str, LanguageKey, int, int], ...] = (
    ("requests_per_minute", LanguageKey.REQUESTS_PER_MINUTE, 1, 30),
    ("parallel_requests", LanguageKey.PARALLEL_REQUESTS, 2, 2),
    ("wait_after_error_seconds", LanguageKey.WAIT_AFTER_ERROR_SECONDS, 3, 5),
    ("retries_before_failure", LanguageKey.RETRIES_BEFORE_FAILURE, 4, 3),
    ("queue_depth", LanguageKey.QUEUE_DEPTH, 5, 100),
)

# Table 19's two NEGOTIABLE rows (6, 7) -- loaded with no floor check: any agreed
# value is valid, the shipped file value is only the default absent an agreement.
_GATEKEEPER_NEGOTIABLE: tuple[tuple[str, LanguageKey], ...] = (
    ("response_timeout_seconds", LanguageKey.RESPONSE_TIMEOUT_SECONDS),
    ("watchdog_threshold_seconds", LanguageKey.WATCHDOG_THRESHOLD_SECONDS),
)


def load_language_config(path: "Path | str") -> LanguageParams:
    """Load and validate config/{police,thief}/language.json.

    Raises
    ------
    KeyError
        If any required key (top-level group or leaf) is absent.
    TypeError
        If any leaf value carries the wrong type.
    ValueError
        If a `gatekeeper` field with MINIMUM status (Table 19 rows 1-5) is set
        below its floor, or the `budget` degrade thresholds are not strictly
        ordered -- both name the offending key and its value(s).
    """
    with Path(path).open() as fh:
        data = json.load(fh)

    version = str(require_key(data, LanguageKey.VERSION.value, source=LANGUAGE_CONFIG_SOURCE))
    gatekeeper = require_key(
        data, LanguageKey.GROUP_GATEKEEPER.value, source=LANGUAGE_CONFIG_SOURCE
    )
    budget_group = require_key(data, LanguageKey.GROUP_BUDGET.value, source=LANGUAGE_CONFIG_SOURCE)
    model = require_key(data, LanguageKey.GROUP_MODEL.value, source=LANGUAGE_CONFIG_SOURCE)
    if not isinstance(model, dict):
        raise TypeError(
            f"{LANGUAGE_CONFIG_SOURCE} field '{LanguageKey.GROUP_MODEL.value}' "
            f"must be an object, got {type(model).__name__}"
        )

    fields: dict[str, object] = {"version": version, "model": model}
    for name, key, _row, minimum in _GATEKEEPER_MINIMA:
        value = require_int(gatekeeper, key.value, source=LANGUAGE_CONFIG_SOURCE)
        if value < minimum:
            raise ValueError(
                f"{LANGUAGE_CONFIG_SOURCE} field '{key.value}' must be >= {minimum} "
                f"(docs/PARAMETERS.md Table 19 minimum), got {value}"
            )
        fields[name] = value
    for name, key in _GATEKEEPER_NEGOTIABLE:
        fields[name] = require_int(gatekeeper, key.value, source=LANGUAGE_CONFIG_SOURCE)

    fields["token_budget_per_series"] = require_int(
        budget_group, LanguageKey.TOKEN_BUDGET_PER_SERIES.value, source=LANGUAGE_CONFIG_SOURCE
    )
    fields["short_prompt_threshold_tokens"] = require_int(
        budget_group,
        LanguageKey.SHORT_PROMPT_THRESHOLD_TOKENS.value,
        source=LANGUAGE_CONFIG_SOURCE,
    )
    fields["template_only_threshold_tokens"] = require_int(
        budget_group,
        LanguageKey.TEMPLATE_ONLY_THRESHOLD_TOKENS.value,
        source=LANGUAGE_CONFIG_SOURCE,
    )
    _check_degrade_order(fields, source=LANGUAGE_CONFIG_SOURCE)

    return LanguageParams(**fields)


def _check_degrade_order(fields: dict, *, source: str) -> None:
    """D-35's ladder must be strictly ordered: 0 < short < template <= budget."""
    short = fields["short_prompt_threshold_tokens"]
    template = fields["template_only_threshold_tokens"]
    budget = fields["token_budget_per_series"]
    if not (0 < short < template <= budget):
        raise ValueError(
            f"{source}: degrade thresholds must satisfy 0 < short_prompt_threshold_tokens "
            f"({short}) < template_only_threshold_tokens ({template}) <= "
            f"token_budget_per_series ({budget})"
        )
