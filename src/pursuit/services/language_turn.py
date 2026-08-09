"""One guarded entry point for the language half of a turn (D-33, LANG-06).

Two async functions, each independently timeout-guarded against the SAME
turn budget: `decode_incoming` (book Sec6.2 Figure 7 stage 1) and
`compose_outgoing` (stage 4). The timeout-and-fallback policy lives here,
in ONE place, rather than at each call site -- scattering it is how one
path ends up without it, and a hint is not worth forfeiting a league game
over (network/watchdog.py's freeze detector does not distinguish "the turn
is slow" from "the turn is dead"; neither decode_hint() nor compose() has
its own timeout).

Budget: the caller (network/turn_language.py) computes `turn_budget_seconds`
once per turn -- the smaller of `network.response_timeout` and
`network.watchdog_threshold` -- and passes each call its own remaining
slice. Below `MIN_CALL_BUDGET_SECONDS` a call is skipped outright rather
than attempted: an honest skip, logged, beats a forfeit.
"""

from __future__ import annotations

import asyncio
import logging

from pursuit.services.llm.bluff import BluffContext, compose
from pursuit.services.llm.decode import DecodeContext, decode_hint
from pursuit.shared.deception_types import DeceptionPlan
from pursuit.shared.inference import NO_EVIDENCE, Inference

_log = logging.getLogger(__name__)

#: Below this many seconds of remaining turn budget, a language call is
#: skipped outright. An engineering default (D-18), not a PARAMETERS.md
#: value -- any positive floor works, this one just names "not worth it".
MIN_CALL_BUDGET_SECONDS = 0.5


def turn_budget_seconds(net) -> float:
    """The whole turn's language ceiling: the smaller of the two configured
    bounds (Task 1), never hardcoded -- both fields already come from the
    negotiated `NetworkParams`. `network.response_timeout` is the
    per-message deadline the language calls ride alongside;
    `network.watchdog_threshold` is the freeze detector that would
    otherwise kill the whole process while decode/compose run (neither
    call touches `Watchdog.touch()`)."""
    return min(net.response_timeout, net.watchdog_threshold)


async def decode_incoming(
    text: str | None, context: DecodeContext, *, timeout: float
) -> Inference:
    """`decode_hint`, abandoned at `timeout` -- a stalled provider yields
    `NO_EVIDENCE`, never a hung turn (D-33). `text` is None/empty for "no
    hint arrived this turn" (a silent opponent, or turn 0): also
    `NO_EVIDENCE`, without ever attempting a call."""
    if not text:
        return NO_EVIDENCE
    if timeout < MIN_CALL_BUDGET_SECONDS:
        _log.info("decode_incoming: skipped, only %.2fs of turn budget remained", timeout)
        return NO_EVIDENCE
    try:
        return await asyncio.wait_for(decode_hint(text, context), timeout=timeout)
    except TimeoutError:
        _log.warning("decode_incoming: abandoned a provider at the %.2fs deadline", timeout)
        return NO_EVIDENCE


async def compose_outgoing(
    plan: DeceptionPlan, context: BluffContext, *, timeout: float
) -> str:
    """`compose()`, abandoned at `timeout` -- a stalled provider falls back
    to the SAME template bank `compose()` itself uses on every other
    failure path (D-33), never a hung turn."""
    if timeout < MIN_CALL_BUDGET_SECONDS:
        _log.info("compose_outgoing: skipped, only %.2fs of turn budget remained", timeout)
        return context.hint_bank.select(plan, arena=context.arena)
    try:
        return await asyncio.wait_for(compose(plan, context), timeout=timeout)
    except TimeoutError:
        _log.warning("compose_outgoing: abandoned a provider at the %.2fs deadline", timeout)
        return context.hint_bank.select(plan, arena=context.arena)
