"""GATE-4 criterion 1 (decode-fixture accuracy): replay tests/fixtures/hints_{en,he}.json
through the shipped decode_hint(), scored against each case's `expect` shape (04-14 Task 1).

Mocked mode feeds each case's own recorded `response` dict back through a provider --
the same technique tests/unit/services/test_decode.py already uses. This checks
decode.py's OWN schema re-validation logic (it must reject the prompt-injection case
even though the canned `response` claims confidence 1.0), not a live model.

Live mode sends `hint` to the real API and scores the answer against `expect`,
IGNORING `response` entirely -- the fixture file's own documented contract
(tests/fixtures/hints_en.json's `note` field: "Plan 04-14 sends `hint` to the real
API once and scores the answer against `expect`, ignoring `response`").
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pursuit.services.llm.decode import DecodeContext, decode_hint
from pursuit.services.llm.gatekeeper import Gatekeeper
from pursuit.services.llm.provider import LlmResult, Provider

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
#: Matches the fixtures' own hint lengths and the negotiated arena
#: (language.json's `model` group) -- kept local so this module has no
#: dependency on a live AgentConfig just to score a fixture.
_WORD_LIMIT = 15
_ARENA = "New York"
_BOARD_SIZE = 7


class _RecordedResponseProvider:
    """Feeds ONE fixture case's own `response` dict back as the decode
    result. Never touches a network."""

    def __init__(self, response: dict) -> None:
        self._response = response

    async def complete(self, *, system_prompt, user_prompt, schema=None):
        return LlmResult(
            text=json.dumps(self._response),
            parsed=dict(self._response),
            input_tokens=40,
            output_tokens=15,
            model="mocked-fixture-replay",
        )


@dataclass(frozen=True)
class FixtureResult:
    case_id: str
    hint: str
    matched: bool
    got: dict
    expect: dict


def build_live_provider(cfg) -> Provider:
    """A real `AnthropicProvider`, built the same way `language_wiring.py`
    builds the production one, for scoring fixtures against the actual API
    (D-32) -- a fresh `Gatekeeper` so this never shares budget state with a
    game's own runtime object (CLAUDE.md rule 2)."""
    from pursuit.services.llm.anthropic_provider import AnthropicProvider

    model = cfg.language.model
    gatekeeper = Gatekeeper(params=cfg.language)
    return AnthropicProvider(
        gatekeeper=gatekeeper,
        model_id=model["model_id"],
        max_tokens=model["max_tokens"],
        timeout_seconds=model["timeout_seconds"],
    )


def _load(language: str) -> dict:
    path = _FIXTURES_DIR / f"hints_{language}.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _describe(inference) -> dict:
    return {
        "region": inference.region.value if inference.region is not None else None,
        "direction": inference.direction.value if inference.direction is not None else None,
        "cells": list(inference.cells),
        "confidence": inference.confidence,
        "is_evidence": inference.is_evidence,
    }


def _matches(got: dict, expect: dict, *, exact_confidence: bool = True) -> bool:
    """Shape match per 04-14 ("accuracy against their expected shapes").

    `exact_confidence=True` is for MOCKED scoring, where the canned response
    IS the expected object and any drift is a codec bug. Live scoring passes
    False: a real model never reproduces a recorded float to 1e-9, and what
    the gate measures there is the SHAPE -- region/direction/cells and
    whether the hint counted as evidence at all.
    """
    shape_ok = (
        got["region"] == expect["region"]
        and got["direction"] == expect["direction"]
        and got["cells"] == expect["cells"]
        and got["is_evidence"] == expect["is_evidence"]
    )
    if not exact_confidence:
        return shape_ok
    return shape_ok and abs(got["confidence"] - expect["confidence"]) < 1e-9


async def _score_case(
    case: dict, provider: Provider, *, exact_confidence: bool = True
) -> FixtureResult:
    context = DecodeContext(
        provider=provider, board_size=_BOARD_SIZE, arena=_ARENA, word_limit=_WORD_LIMIT
    )
    inference = await decode_hint(case["hint"], context)
    got = _describe(inference)
    matched = _matches(got, case["expect"], exact_confidence=exact_confidence)
    return FixtureResult(case["id"], case["hint"], matched, got, case["expect"])


async def score_fixture_language_mocked(language: str) -> list[FixtureResult]:
    """Score every case in hints_<language>.json, one fresh
    `_RecordedResponseProvider` per case (each case owns its own canned
    answer). Exact-confidence match: the canned response IS the expectation."""
    data = _load(language)
    return [
        await _score_case(case, _RecordedResponseProvider(case["response"]))
        for case in data["cases"]
    ]


async def score_fixture_language_live(language: str, provider: Provider) -> list[FixtureResult]:
    """Score every case in hints_<language>.json against ONE real provider
    instance (shared across cases so the gatekeeper's own accounting is
    honest about how many real calls this check made). Shape match only --
    a live model never reproduces the recorded confidence float."""
    data = _load(language)
    return [
        await _score_case(case, provider, exact_confidence=False)
        for case in data["cases"]
    ]
