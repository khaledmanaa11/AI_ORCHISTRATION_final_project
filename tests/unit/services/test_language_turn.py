"""Tests for `services/language_turn.py` -- the one guarded entry point
for the language half of a turn (Task 1). Every branch: empty/missing
text, budget too small to attempt, a provider abandoned mid-call, and the
happy path. No test performs network I/O -- every provider here is a
plain async fake."""

import asyncio
import random

from pursuit.services.language_turn import (
    MIN_CALL_BUDGET_SECONDS,
    compose_outgoing,
    decode_incoming,
    turn_budget_seconds,
)
from pursuit.services.llm.bluff import BluffContext
from pursuit.services.llm.budget import DegradeLevel
from pursuit.services.llm.decode import DecodeContext
from pursuit.services.llm.hintbank import HintBank
from pursuit.services.llm.provider import LlmResult
from pursuit.shared.deception_types import ClaimKind, DeceptionPlan, Intent
from pursuit.shared.inference import NO_EVIDENCE, Region


class _NetLike:
    def __init__(self, response_timeout: float, watchdog_threshold: float) -> None:
        self.response_timeout = response_timeout
        self.watchdog_threshold = watchdog_threshold


class _HangingProvider:
    """Never returns within any reasonable test deadline."""

    async def complete(self, *, system_prompt, user_prompt, schema=None):
        await asyncio.sleep(999)


class _InstantProvider:
    def __init__(self, *, decode_evidence: bool) -> None:
        self._decode_evidence = decode_evidence

    async def complete(self, *, system_prompt, user_prompt, schema=None):
        if schema is not None:
            parsed = (
                {"region": Region.NORTH.value, "cells": [], "direction": None, "confidence": 0.9}
                if self._decode_evidence
                else {"region": None, "cells": [], "direction": None, "confidence": 0.0}
            )
            return LlmResult(text="{}", parsed=parsed, input_tokens=1, output_tokens=1)
        return LlmResult(text="I'm near the park.", parsed=None, input_tokens=1, output_tokens=1)


def _decode_ctx(provider) -> DecodeContext:
    return DecodeContext(provider=provider, board_size=7, arena="New York", word_limit=15)


def _bluff_ctx(provider) -> BluffContext:
    return BluffContext(
        provider=provider, degrade_level=DegradeLevel.FULL, arena="New York", word_limit=15,
        hint_bank=HintBank(rng=random.Random(1)),
    )


def _plan() -> DeceptionPlan:
    return DeceptionPlan(
        intent=Intent.TRUTH, kind=ClaimKind.LOCATION,
        claimed_region=Region.NORTH, true_region=Region.NORTH,
    )


def test_turn_budget_seconds_returns_the_smaller_bound():
    assert turn_budget_seconds(_NetLike(30, 60)) == 30
    assert turn_budget_seconds(_NetLike(90, 45)) == 45


async def test_decode_incoming_returns_no_evidence_for_missing_text():
    result = await decode_incoming(None, _decode_ctx(_HangingProvider()), timeout=30)
    assert result is NO_EVIDENCE
    result = await decode_incoming("", _decode_ctx(_HangingProvider()), timeout=30)
    assert result is NO_EVIDENCE


async def test_decode_incoming_skips_when_budget_is_too_small():
    result = await decode_incoming(
        "heading south", _decode_ctx(_HangingProvider()), timeout=MIN_CALL_BUDGET_SECONDS / 2,
    )
    assert result is NO_EVIDENCE


async def test_decode_incoming_abandons_a_stalled_provider_at_the_deadline():
    result = await decode_incoming(
        "heading south", _decode_ctx(_HangingProvider()), timeout=MIN_CALL_BUDGET_SECONDS + 0.05,
    )
    assert result is NO_EVIDENCE


async def test_decode_incoming_returns_real_evidence_on_success():
    result = await decode_incoming(
        "heading south", _decode_ctx(_InstantProvider(decode_evidence=True)), timeout=30,
    )
    assert result.is_evidence
    assert result.region is Region.NORTH


async def test_compose_outgoing_skips_when_budget_is_too_small():
    text = await compose_outgoing(
        _plan(), _bluff_ctx(_HangingProvider()), timeout=MIN_CALL_BUDGET_SECONDS / 2,
    )
    assert text


async def test_compose_outgoing_abandons_a_stalled_provider_at_the_deadline():
    text = await compose_outgoing(
        _plan(), _bluff_ctx(_HangingProvider()), timeout=MIN_CALL_BUDGET_SECONDS + 0.05,
    )
    assert text


async def test_compose_outgoing_returns_real_text_on_success():
    text = await compose_outgoing(
        _plan(), _bluff_ctx(_InstantProvider(decode_evidence=False)), timeout=30,
    )
    assert text == "I'm near the park."
