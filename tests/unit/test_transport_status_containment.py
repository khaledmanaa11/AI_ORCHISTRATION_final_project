"""05-10: a gateway blip is transient; a 403 is still ours.

Sibling of `test_transport_failure_containment.py`, split at the 150-code-line gate (that file
is at 146) -- helpers are imported from it rather than re-derived, the same
`test_audit_send_failure.py` precedent it already follows.

`httpx.HTTPStatusError` matched no clause in `call_with_retry` before this plan: it is a
SIBLING of `TransportError` under `HTTPError`, not a subclass, so it escaped the ladder and
killed the process exactly as `ConnectError` did (deferred item #6). On league day this is the
likeliest real failure of all -- ngrok answers 502 whenever the peer's local server is briefly
unavailable.

Two paired boundaries, and the discrimination is what makes them worth writing:

- the 502/503/429 cases FAIL against the pre-05-10 ladder (they raise instead of recording a
  verdict) -- the revert probe is recorded in 05-10-SUMMARY.md;
- the 403/404 cases FAIL against a version that retries all of `HTTPStatusError`, which is the
  design alternative this plan had to refuse: `test_secret_channel.py` drives a REAL 403 over a
  real socket, so sweeping the class in would turn our own wrong secret into an accusation
  against a peer that answered us correctly (rules 16/22);
- the **501** case is the M2 control specifically: written against an "any 5xx" rule it FAILS.
  501 and 505 are deterministic refusals that fail identically on all four attempts, burn
  `3 x backoff_seconds`, and end in a durable `TechnicalWin(OPPONENT_UNRESPONSIVE)` -- the
  mirror of the `LocalProtocolError` shape 05-09 subtracted for exactly that reason.
"""

from __future__ import annotations

import httpx
import pytest

from pursuit.constants import Outcome
from pursuit.network.deadline_errors import unwraps_to_retryable
from pursuit.network.deadline_status import RETRYABLE_STATUS_CODES, retryable_status
from tests.unit.test_audit_send_failure import _events
from tests.unit.test_transport_failure_containment import (
    _accusations,
    _in_game_ctx,
    _take_one_turn,
)


def _status_error(code: int) -> httpx.HTTPStatusError:
    """Built by driving httpx's OWN `raise_for_status()`, never by hand -- so the message the
    evidence carries is the real library text a live tunnel would produce."""
    request = httpx.Request("POST", "http://127.0.0.1:9/mcp")
    response = httpx.Response(code, request=request)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return exc
    raise AssertionError(f"{code} is not an error status")


@pytest.mark.parametrize("code", [429, 500, 502, 503, 504])
async def test_a_transient_status_is_retried_and_ends_in_a_recorded_verdict(
    tmp_path, default_params, network_params, code,
):
    """The peer's tunnel answered about the SERVER's availability, not about our credentials.
    Every attempt fails here, so the accusation is correct -- what matters is that it is a
    RETURNED verdict in our own log, not an exception that ends the process before one exists."""
    ctx = _in_game_ctx(
        tmp_path, default_params, network_params, f"blip-{code}", lambda: _status_error(code),
    )

    outcome = await _take_one_turn(ctx, default_params)

    assert outcome is Outcome.TECHNICAL_LOSS
    assert len(ctx.runtime.client().calls) == ctx.net.retry_count + 1, "the ladder was not run"
    verdict = next(e for e in _events(ctx) if e["event"] == "technical_win")
    assert verdict["reason"] == "opponent_unresponsive"
    assert verdict["retries_attempted"] == ctx.net.retry_count + 1


@pytest.mark.parametrize("code", [400, 403, 404, 501, 505])
async def test_an_answer_about_our_own_request_still_raises_and_accuses_nobody(
    tmp_path, default_params, network_params, code,
):
    """403 is the live anchor (`test_secret_channel.py` pins a real one over a real socket): it
    means OUR OWN shared secret is wrong, and retrying it would burn the ladder and end in a
    false declaration. 501/505 are here for a different reason -- they are 5xx, and an "any 5xx"
    rule would sweep them in even though they are deterministic refusals."""
    ctx = _in_game_ctx(
        tmp_path, default_params, network_params, f"answer-{code}", lambda: _status_error(code),
    )

    with pytest.raises(httpx.HTTPStatusError, match=str(code)):
        await _take_one_turn(ctx, default_params)

    assert len(ctx.runtime.client().calls) == 1, f"{code}: our own bad request burned the backoff"
    assert _accusations(ctx) == [], f"{code}: an honest answer was turned into an accusation"


def test_the_retryable_set_is_enumerated_not_a_5xx_range():
    """A structural RFC 9110 constant set, not a PARAMETERS.md value. Pinned by NAME so a future
    reader cannot quietly widen it to `500 <= code < 600`."""
    assert sorted(RETRYABLE_STATUS_CODES) == [429, 500, 502, 503, 504]
    for deterministic in (501, 505):
        assert deterministic not in RETRYABLE_STATUS_CODES
        assert retryable_status(_status_error(deterministic)) is False
    assert retryable_status(httpx.ConnectError("not a status error at all")) is False


def test_a_wrapped_502_is_recognised_but_a_wrapped_403_is_not():
    """`unwraps_to_retryable` decides by class tuple; `retryable_status` is a PREDICATE, so the
    two must be wired together or a wrapped 502 would go unrecognised. fastmcp 3.4.5 preserves
    `HTTPStatusError` unwrapped on the connect path (re-verified: `client/client.py:620`), so
    this is defence in depth rather than the live shape -- wired now so they cannot diverge."""
    for code, expected in ((502, True), (403, False)):
        wrapper = RuntimeError(f"Client failed to connect: {code}")
        wrapper.__cause__ = _status_error(code)
        assert unwraps_to_retryable(wrapper) is expected
