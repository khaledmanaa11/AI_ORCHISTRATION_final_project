"""`compose()`: a `DeceptionPlan` becomes a legal hint, always (D-33, D-45,
D-36, LANG-01, LANG-02).

Three ways a turn's hint can go wrong in a league game -- over-length, a
coordinate leak, or no hint at all -- are all protocol violations. This
module closes all three by construction:

1. `TEMPLATE_ONLY`, a `template` provider, or (transitively, via the same
   `LlmFailure` branch as step 2) no API key -- straight to the bank. No
   network call, no latency.
2. Otherwise call the provider. Any `LlmFailure`, of any reason, including
   one raised instead of returned (a provider breaking its own D-33
   contract) -- straight to the bank.
3. Count the result. Over the limit -- exactly ONE retry with an explicit
   shortening instruction. Still over (or the retry itself failed) --
   truncate the best text in hand.
4. Validate with `assert_no_coordinates`. On violation -- straight to the
   bank; never attempt to repair text the model produced (a rewrite risks
   a second violation and costs another call).
5. Return.

`compose()` never raises and never returns an empty, over-length or
coordinate-bearing string -- every branch above ends in a legal one.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from pursuit.services.llm.bluff_prompt import build_system_prompt, build_user_prompt
from pursuit.services.llm.budget import DegradeLevel
from pursuit.services.llm.hintbank import HintBank
from pursuit.services.llm.provider import LlmFailure, LlmFailureReason, LlmResult, Provider
from pursuit.services.llm.template_provider import TemplateProvider
from pursuit.services.llm.wordcount import count, truncate
from pursuit.shared.deception_types import DeceptionPlan
from pursuit.shared.hint_guard import assert_no_coordinates

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class BluffContext:
    """Everything one `compose()` call needs, and nothing about the game's
    physical state (mirrors `DecodeContext`, `decode.py`).

    One instance per game, held by whoever wires the turn pipeline
    (04-12): `provider`/`arena`/`word_limit` are the SAME LLM-channel
    values `DecodeContext` reads, both sourced from `language.json`'s
    `model` group (carry-over A) -- one negotiated number, read on both
    the decode and the emission side. `hint_bank` is the one `HintBank`
    for the game (04-09's `Reliability` ownership precedent: constructed
    once, held for the game's duration, never shared between the cop and
    thief processes, CLAUDE.md rule 2). `degrade_level` is the one field
    that changes DURING a game as the token budget is spent (D-35); a
    caller re-reads `gatekeeper.budget.level` and rebuilds this context
    (or just this field) before each turn's call.
    """

    provider: Provider
    degrade_level: DegradeLevel
    arena: str
    word_limit: int
    hint_bank: HintBank


async def compose(plan: DeceptionPlan, context: BluffContext) -> str:
    """Turn `plan` into a legal hint -- total by construction. See the
    module docstring for the five-step order every call follows."""
    if context.degrade_level is DegradeLevel.TEMPLATE_ONLY or isinstance(
        context.provider, TemplateProvider
    ):
        return context.hint_bank.select(plan, arena=context.arena)

    outcome = await _complete(plan, context)
    if isinstance(outcome, LlmFailure):
        return context.hint_bank.select(plan, arena=context.arena)

    candidate = _usable_text(outcome)
    if candidate is None:
        return context.hint_bank.select(plan, arena=context.arena)

    if count(candidate) > context.word_limit:
        retry_outcome = await _complete(plan, context, shorten=True)
        if isinstance(retry_outcome, LlmResult):
            retried = _usable_text(retry_outcome)
            if retried is not None:
                candidate = retried
        if count(candidate) > context.word_limit:
            candidate = truncate(candidate, context.word_limit)

    try:
        assert_no_coordinates(candidate)
    except ValueError:
        return context.hint_bank.select(plan, arena=context.arena)

    return candidate


async def _complete(
    plan: DeceptionPlan, context: BluffContext, *, shorten: bool = False
) -> LlmResult | LlmFailure:
    """The one provider call `compose()` makes per attempt (at most twice:
    the original call, and -- only when it comes back over-length -- one
    retry). Mirrors `decode.py`'s own `_complete`: `Provider.complete` is
    contractually non-exceptional (D-33), but this is the boundary that
    MUST hold even when a provider breaks that contract."""
    try:
        return await context.provider.complete(
            system_prompt=build_system_prompt(arena=context.arena, word_limit=context.word_limit),
            user_prompt=build_user_prompt(plan, shorten=shorten),
        )
    except Exception as exc:  # a provider breaking D-33 still must not end a game
        _log.debug("provider threw during bluff: %s: %s", type(exc).__name__, exc)
        return LlmFailure(LlmFailureReason.UNKNOWN, f"{type(exc).__name__}: {exc}")


def _usable_text(result: LlmResult) -> str | None:
    """`result.text`, stripped, or None when it is missing or blank -- an
    empty completion is D-33's other named failure mode, not a crash."""
    text = getattr(result, "text", None)
    if not isinstance(text, str) or not text.strip():
        return None
    return text.strip()
