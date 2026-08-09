"""`decode_hint` -- total, in every sense (D-33, D-41, D-44, LANG-06).

One entry point, and it never raises. Book Sec6.2 Figure 7 puts decode at the
very front of the turn pipeline and calls it *"parse text"*: it classifies and
describes, it never decides. The hard requirement is not accuracy, it is
TOTALITY -- every input, including a hostile or nonsensical one, produces
either a schema-valid `Inference` or `NO_EVIDENCE`, and a decode failure of
any kind costs the game exactly one turn of hint evidence and nothing else.

**Capability difference between the two provider modes, not a bug.** The
`template` provider (D-52's zero-token book default) cannot decode anything
-- it has no model behind it -- so under it `decode_hint` returns
`NO_EVIDENCE` immediately, without a call and without a token. In that
configuration the belief map runs on scent alone, which is a real and
deliberate reduction in what the agent can know, worth stating plainly
rather than hiding behind a uniformly-neutral return value.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from pursuit.services.llm.decode_prompt import build_system_prompt, build_user_prompt
from pursuit.services.llm.decode_schema import DECODE_SCHEMA, validate
from pursuit.services.llm.provider import LlmFailure, LlmFailureReason, LlmResult, Provider
from pursuit.services.llm.template_provider import TemplateProvider
from pursuit.shared.inference import Inference, no_evidence_for

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DecodeContext:
    """Everything one decode call needs, and nothing about the game's state.

    `word_limit` is PARAMETERS.md Table 14 row 2, supplied by the caller
    rather than read here: this module owns no config file, and the same
    negotiated number governs the hints we EMIT (04-10, which adds it to
    `language.json`). A required field with no default, so no call site can
    silently fall back to an invented ceiling.
    """

    provider: Provider
    board_size: int
    arena: str
    word_limit: int


async def decode_hint(text: str, context: DecodeContext) -> Inference:
    """Turn one opponent sentence into a bounded `Inference`, or into nothing.

    Every path that is not a clean, schema-valid decode returns the neutral
    result: a non-string or empty hint, a hint over the negotiated word limit,
    a provider that cannot decode, any `LlmFailure` reason, malformed JSON, a
    schema violation, an out-of-range confidence, or an unexpected exception
    escaping a provider. No path propagates an exception to the caller, and
    none reaches the belief map as a partial reading.
    """
    if not isinstance(text, str) or not text.strip():
        return _neutral("", reason="empty hint")
    words = len(text.split())
    if words > context.word_limit:
        return _neutral(text, reason=f"hint is {words} words, limit {context.word_limit}")
    if isinstance(context.provider, TemplateProvider):
        return _neutral(text, reason="template provider cannot decode")

    outcome = await _complete(text, context)
    if isinstance(outcome, LlmFailure):
        return _neutral(text, reason=f"provider failure: {outcome.reason.value}")

    payload = _payload(outcome)
    if payload is None:
        return _neutral(text, reason="response was not JSON")
    inference = validate(payload, board_size=context.board_size, raw_text=text)
    if inference is None:
        return _neutral(text, reason="response failed schema re-validation")

    _log.debug("decoded %r -> region=%s conf=%.2f", text, inference.region, inference.confidence)
    return inference


async def _complete(text: str, context: DecodeContext) -> LlmResult | LlmFailure:
    """The provider call, with the last backstop against an escaping exception.

    `Provider.complete` is contractually non-exceptional (D-33), but this
    module is the boundary that MUST hold even when a provider -- ours today,
    a third-party one later -- breaks that contract. Converting the exception
    into the same `LlmFailure` type keeps exactly one failure branch above.
    """
    try:
        return await context.provider.complete(
            system_prompt=build_system_prompt(arena=context.arena, board_size=context.board_size),
            user_prompt=build_user_prompt(text),
            schema=DECODE_SCHEMA,
        )
    except Exception as exc:  # a provider breaking D-33 still must not end a game
        _log.debug("provider threw during decode: %s: %s", type(exc).__name__, exc)
        return LlmFailure(LlmFailureReason.UNKNOWN, f"{type(exc).__name__}: {exc}")


def _payload(result: LlmResult | LlmFailure) -> object | None:
    """The parsed JSON object from a successful result.

    Prefers the provider's own `parsed` field (populated whenever a schema was
    supplied) and falls back to parsing `text` -- a provider that satisfies
    the protocol without populating `parsed` is still understood, and a body
    that is not JSON at all comes back as None.
    """
    parsed = getattr(result, "parsed", None)
    if parsed is not None:
        return parsed
    try:
        return json.loads(getattr(result, "text", ""))
    except (json.JSONDecodeError, TypeError):
        return None


def _neutral(text: str, *, reason: str) -> Inference:
    """`NO_EVIDENCE` carrying the sentence, logged with WHY it decoded to
    nothing.

    The reason is what makes 04-14 able to report a real decode-success rate:
    a silent no-evidence path failing 100% of the time is otherwise
    indistinguishable from an opponent whose hints genuinely say nothing.
    """
    _log.debug("hint decoded to no evidence (%s): %r", reason, text)
    return no_evidence_for(text)
