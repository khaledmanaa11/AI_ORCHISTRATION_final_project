"""The Phase-4 regression guard for 07-01: the LLM gatekeeper instance's
EFFECTIVE parameters, read off the SHIPPED configs through the real
construction path.

Why it exists. OQ-3 negotiates the MAIL instance's backoff up to 30 s
(``docs/PARAMETERS.md:95`` gives 5 s as a MINIMUM -- negotiable upward;
``docs/SEGAL_GUIDELINES.md:174`` gives ``retry_after_seconds: 30``; ``:182``
says take the stricter value). That resolution is scoped to the new instance
ONLY. A silent retune of the LLM instance in the same commit would be a
Phase-4 behaviour change wearing a Phase-7 label, and no existing test asserts
these values against the real files -- ``tests/unit/services/test_gatekeeper``
builds its own ``_params()`` doubles, so it would stay green through any
config edit.

The expected values below are ``config/{police,thief}/language.json`` as
shipped, which 07-01 does not edit (verified separately by an empty
``git diff`` on both files). This file is the assertion that they did not
move.
"""

from pathlib import Path

import pytest

from pursuit.services.llm import DegradeLevel, Gatekeeper, TokenBudget
from pursuit.shared.language_config import load_language_config

_SHIPPED_CONFIG = Path(__file__).resolve().parents[2] / "config"

#: config/{police,thief}/language.json as shipped before AND after 07-01.
#: Rows 1-5 are docs/PARAMETERS.md Table 19 minima; rows 6-7 are its
#: negotiable rows. wait_after_error_seconds stays 5 -- OQ-3's 30 belongs to
#: the mail instance in reporting.json and must never leak here.
_EXPECTED_GATEKEEPER = {
    "requests_per_minute": 30,
    "parallel_requests": 2,
    "wait_after_error_seconds": 5,
    "retries_before_failure": 3,
    "queue_depth": 100,
    "response_timeout_seconds": 30,
    "watchdog_threshold_seconds": 60,
}

#: language.json's `budget` group: Table 18 row 4's negotiable series ceiling
#: plus D-35's two engineering-default degrade thresholds.
_EXPECTED_BUDGET = {
    "token_budget_per_series": 200_000,
    "short_prompt_threshold_tokens": 140_000,
    "template_only_threshold_tokens": 180_000,
}

_ROLES = ("police", "thief")


def _llm_gatekeeper(role: str) -> Gatekeeper:
    """The LLM instance exactly as ``network/language_wiring.py:160`` builds
    it: ``Gatekeeper(params=<loaded language.json>)``, no injected budget."""
    return Gatekeeper(params=load_language_config(_SHIPPED_CONFIG / role / "language.json"))


def test_the_expectation_tables_cover_every_row_they_claim_to() -> None:
    """The vacuity guard for the two parametrized tests below. An emptied or
    thinned table would SKIP silently and the whole Phase-4 regression guard
    would read as green. Seven Table-19 rows, three budget rows, two roles."""
    assert len(_EXPECTED_GATEKEEPER) == 7
    assert len(_EXPECTED_BUDGET) == 3
    assert len(_ROLES) == 2
    assert set(_EXPECTED_GATEKEEPER) | set(_EXPECTED_BUDGET) <= set(
        load_language_config(_SHIPPED_CONFIG / "police" / "language.json").__dict__
    )


@pytest.mark.parametrize("role", _ROLES)
@pytest.mark.parametrize(("field", "expected"), sorted(_EXPECTED_GATEKEEPER.items()))
def test_shipped_llm_gatekeeper_row_is_unchanged(role: str, field: str, expected: int) -> None:
    params = load_language_config(_SHIPPED_CONFIG / role / "language.json")
    assert getattr(params, field) == expected


@pytest.mark.parametrize("role", _ROLES)
@pytest.mark.parametrize(("field", "expected"), sorted(_EXPECTED_BUDGET.items()))
def test_shipped_llm_budget_row_is_unchanged(role: str, field: str, expected: int) -> None:
    params = load_language_config(_SHIPPED_CONFIG / role / "language.json")
    assert getattr(params, field) == expected


@pytest.mark.parametrize("role", _ROLES)
def test_llm_instance_still_holds_a_real_token_budget_under_the_same_name(role: str) -> None:
    """``bluff`` refreshes ``degrade_level`` off ``gatekeeper.budget.level``
    every turn (``language_wiring.py``'s LanguageRuntime docstring): the
    attribute NAME and its type are load-bearing, not just its numbers."""
    gk = _llm_gatekeeper(role)
    assert isinstance(gk.budget, TokenBudget)
    assert gk.budget.level is DegradeLevel.FULL
    assert gk.budget.report() == {
        "calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "level": "full",
        "budget": _EXPECTED_BUDGET["token_budget_per_series"],
    }


@pytest.mark.parametrize("role", _ROLES)
def test_llm_instance_bucket_is_still_derived_from_requests_per_minute(role: str) -> None:
    """C = requests_per_minute, r = requests_per_minute / 60 -- the derivation
    ``gatekeeper.py`` documents, asserted through the public seam and the
    bucket's own reading rather than re-deriving it here."""
    gk = _llm_gatekeeper(role)
    assert gk.bucket_ready is True
    assert gk._bucket.tokens == _EXPECTED_GATEKEEPER["requests_per_minute"]


def test_the_two_roles_ship_identical_llm_gatekeeper_settings() -> None:
    """A drift between cop and thief would be an unfair-configuration finding
    in its own right, and would also let a one-sided retune slip past the
    per-role assertions above."""
    police, thief = (
        load_language_config(_SHIPPED_CONFIG / role / "language.json") for role in _ROLES
    )
    for field in (*_EXPECTED_GATEKEEPER, *_EXPECTED_BUDGET):
        assert getattr(police, field) == getattr(thief, field), field
