"""Tests for the language.json loader (D-34/D-35, QUAL-02, QUAL-11).

Added beyond 04-03-PLAN.md's own `files_modified` list per CLAUDE.md's "every module
gets a test file" testing rule -- CLAUDE.md takes precedence over an incomplete plan
listing (project_context: CLAUDE.md directives are hard constraints).
"""

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from pursuit.shared.language_config import (
    LanguageKey,
    LanguageParams,
    load_language_config,
)

_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
POLICE_LANGUAGE = _CONFIG_DIR / "police" / "language.json"
THIEF_LANGUAGE = _CONFIG_DIR / "thief" / "language.json"


def _write_variant(tmp_path: Path, mutate) -> Path:
    """Write a mutated copy of the police language.json to tmp_path."""
    data = json.loads(POLICE_LANGUAGE.read_text(encoding="utf-8"))
    mutate(data)
    target = tmp_path / "language.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    return target


def test_loads_all_fields() -> None:
    """Every field loads from the real language.json -- no literal in this test."""
    raw = json.loads(POLICE_LANGUAGE.read_text(encoding="utf-8"))
    params = load_language_config(POLICE_LANGUAGE)
    gk, bud = raw[LanguageKey.GROUP_GATEKEEPER], raw[LanguageKey.GROUP_BUDGET]
    assert params.version == raw[LanguageKey.VERSION]
    assert params.requests_per_minute == gk[LanguageKey.REQUESTS_PER_MINUTE]
    assert params.parallel_requests == gk[LanguageKey.PARALLEL_REQUESTS]
    assert params.wait_after_error_seconds == gk[LanguageKey.WAIT_AFTER_ERROR_SECONDS]
    assert params.retries_before_failure == gk[LanguageKey.RETRIES_BEFORE_FAILURE]
    assert params.queue_depth == gk[LanguageKey.QUEUE_DEPTH]
    assert params.response_timeout_seconds == gk[LanguageKey.RESPONSE_TIMEOUT_SECONDS]
    assert params.watchdog_threshold_seconds == gk[LanguageKey.WATCHDOG_THRESHOLD_SECONDS]
    assert params.token_budget_per_series == bud[LanguageKey.TOKEN_BUDGET_PER_SERIES]
    assert params.model == {}


def test_params_are_frozen() -> None:
    """LanguageParams is immutable -- assignment raises FrozenInstanceError."""
    params = load_language_config(POLICE_LANGUAGE)
    with pytest.raises(FrozenInstanceError):
        params.queue_depth = 1  # type: ignore[misc]


def test_fresh_object_every_call() -> None:
    """NET-02 precedent: no module-level cache/singleton, ever."""
    a = load_language_config(POLICE_LANGUAGE)
    b = load_language_config(POLICE_LANGUAGE)
    assert a is not b
    assert a == b


def test_role_files_are_byte_identical() -> None:
    """Both role files carry identical gatekeeper/budget numbers (no per-role split)."""
    assert POLICE_LANGUAGE.read_bytes() == THIEF_LANGUAGE.read_bytes()
    assert load_language_config(POLICE_LANGUAGE) == load_language_config(THIEF_LANGUAGE)


def test_missing_group_raises(tmp_path: Path) -> None:
    """A missing top-level group fails loud at load time."""
    bad = _write_variant(tmp_path, lambda d: d.pop(LanguageKey.GROUP_GATEKEEPER))
    with pytest.raises(KeyError):
        load_language_config(bad)


def test_wrong_type_raises(tmp_path: Path) -> None:
    """A wrong-type leaf value fails loud at load time."""
    bad = _write_variant(
        tmp_path,
        lambda d: d[LanguageKey.GROUP_GATEKEEPER].__setitem__(
            LanguageKey.QUEUE_DEPTH, "many"
        ),
    )
    with pytest.raises(TypeError):
        load_language_config(bad)


def test_model_must_be_an_object(tmp_path: Path) -> None:
    """model must be a JSON object -- 04-06 extends it, this loader only gates the type."""
    bad = _write_variant(tmp_path, lambda d: d.__setitem__(LanguageKey.GROUP_MODEL, []))
    with pytest.raises(TypeError):
        load_language_config(bad)


@pytest.mark.parametrize(
    ("field", "minimum"),
    [
        (LanguageKey.REQUESTS_PER_MINUTE, 30),
        (LanguageKey.PARALLEL_REQUESTS, 2),
        (LanguageKey.WAIT_AFTER_ERROR_SECONDS, 5),
        (LanguageKey.RETRIES_BEFORE_FAILURE, 3),
        (LanguageKey.QUEUE_DEPTH, 100),
    ],
)
def test_below_table19_minimum_raises_naming_the_key(
    tmp_path: Path, field: LanguageKey, minimum: int
) -> None:
    """Table 19's five minima may never be lowered by config (CLAUDE.md rule 1)."""
    bad = _write_variant(
        tmp_path,
        lambda d, field=field, minimum=minimum: d[LanguageKey.GROUP_GATEKEEPER].__setitem__(
            field, minimum - 1
        ),
    )
    with pytest.raises(ValueError, match=field.value):
        load_language_config(bad)


@pytest.mark.parametrize(
    "field",
    [
        LanguageKey.REQUESTS_PER_MINUTE,
        LanguageKey.PARALLEL_REQUESTS,
        LanguageKey.WAIT_AFTER_ERROR_SECONDS,
        LanguageKey.RETRIES_BEFORE_FAILURE,
        LanguageKey.QUEUE_DEPTH,
    ],
)
def test_above_table19_minimum_loads(tmp_path: Path, field: LanguageKey) -> None:
    """Raising a minimum-status field is a valid negotiated agreement."""
    raised = _write_variant(
        tmp_path,
        lambda d, field=field: d[LanguageKey.GROUP_GATEKEEPER].__setitem__(
            field, d[LanguageKey.GROUP_GATEKEEPER][field] + 1000
        ),
    )
    assert load_language_config(raised) is not None


def test_negotiable_field_has_no_floor(tmp_path: Path) -> None:
    """response_timeout_seconds (Table 19 row 6) is negotiable -- any value loads."""
    low = _write_variant(
        tmp_path,
        lambda d: d[LanguageKey.GROUP_GATEKEEPER].__setitem__(
            LanguageKey.RESPONSE_TIMEOUT_SECONDS, 1
        ),
    )
    assert load_language_config(low).response_timeout_seconds == 1


def test_degrade_threshold_out_of_order_raises(tmp_path: Path) -> None:
    """D-35's ladder must be strictly ordered: short < template <= budget."""
    bad = _write_variant(
        tmp_path,
        lambda d: d[LanguageKey.GROUP_BUDGET].__setitem__(
            LanguageKey.SHORT_PROMPT_THRESHOLD_TOKENS,
            d[LanguageKey.GROUP_BUDGET][LanguageKey.TEMPLATE_ONLY_THRESHOLD_TOKENS] + 1,
        ),
    )
    with pytest.raises(ValueError, match="degrade thresholds"):
        load_language_config(bad)


def test_params_type_annotation_matches_dataclass() -> None:
    """Sanity: the loader's declared return type is the dataclass it constructs."""
    params = load_language_config(POLICE_LANGUAGE)
    assert isinstance(params, LanguageParams)
