"""Shared drivers for the two 05-14 single-decode modules
(`test_hint_replay.py` -- a re-send is decoded once on both roles'
timings; `test_hint_replay_window.py` -- the rule's boundaries). One copy,
imported by both (QUAL-02), exactly as `_hint_fixtures.py` already does
for the buffer helpers.

Not a `test_*.py` file on purpose: pytest never imports it as a test
module. `install_spy` is a plain function rather than a `@pytest.fixture`
for the same reason -- a fixture defined here would have to be imported
into each test module's namespace to be discovered, and ruff reads that
import shadowed by the test's own parameter as `F811`. Called explicitly,
it is one line per test and no lint suppression anywhere.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

from pursuit.network import turn_language_io
from pursuit.services.language_turn import MIN_CALL_BUDGET_SECONDS
from pursuit.shared.inference import NO_EVIDENCE
from tests.unit._fakes_agent import make_ctx
from tests.unit._hint_fixtures import at_turn, hint_payload

SENDER = "thief"
"""`opponent_wire_role` for `make_ctx`'s default police role."""

TEXT = hint_payload(0)["text"]

# Comfortably clear of the skip floor and DERIVED from it, so no new
# number enters the repo (CLAUDE.md rule 1). Test scaffolding only -- the
# `_FAST_TIMEOUT` precedent in `_fakes_agent.py`.
BUDGET_SECONDS = MIN_CALL_BUDGET_SECONDS * 2


class BeliefSpy:
    """The two side effects a second decode of the same hint duplicates."""

    def __init__(self) -> None:
        self.decoded: list[str] = []
        self.observed: list[object] = []


def install_spy(monkeypatch) -> BeliefSpy:
    """Intercept the bare `decode_incoming`/`observe_reliability` names in
    `turn_language_io`'s OWN globals -- GATE-4's established spy
    technique, which works precisely because those calls resolve through
    the enclosing module at call time rather than at def time."""
    watcher = BeliefSpy()

    async def _decode_incoming(text, context, *, timeout):
        watcher.decoded.append(text)
        return NO_EVIDENCE

    monkeypatch.setattr(turn_language_io, "decode_incoming", _decode_incoming)
    monkeypatch.setattr(
        turn_language_io,
        "observe_reliability",
        lambda ctx, inference: watcher.observed.append(inference),
    )
    return watcher


def language_ctx(tmp_path, default_params, network_params, label, turn):
    """A context on `turn` with just enough language runtime for
    `decode_turn_hint` to reach its decode branch."""
    ctx = at_turn(make_ctx(tmp_path, default_params, network_params, label=label), turn)
    ctx.language = SimpleNamespace(decode_context=object())
    return ctx


async def decode_once(ctx) -> dict:
    """One `decode_turn_hint` call, returning its own incoming log dict.
    Its `outcome` is the assertion surface: `no_evidence` means a text
    ARRIVED and was decoded, `no_hint` means nothing was in the buffer."""
    _, log = await turn_language_io.decode_turn_hint(ctx, time.monotonic(), BUDGET_SECONDS)
    return log


def resolve_turn(ctx, turn):
    """Exactly what `maybe_resolve` does to the hint buffers, and only
    that: clear `pending_hints`, advance the turn (`turn_resolve.py:96`)."""
    ctx.pending_hints = {}
    return at_turn(ctx, turn)
