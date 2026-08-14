"""Shared helpers for the two 05-06 hint-buffer test modules
(`test_turn_hint_buffer.py` -- wire evidence; `test_hint_freshness.py` --
the lookback window and the freshness guard). One copy, imported by both
(QUAL-02), exactly as `_fakes_agent.py` does for the network fakes.

Not a `test_*.py` file on purpose: pytest's default collection pattern
never imports this module as a test module, so it holds plain helper code
without tripping a "no test functions found" collection warning.
"""

from __future__ import annotations

import dataclasses
import json

from pursuit.network.hint_payload import HintKey, Intent

PEER_CLAIM = 99
"""The turn a hostile peer stamps on its own envelope -- deliberately
nothing this side would ever produce, so a record keyed on it is
unmistakable."""


def hint_payload(turn: int) -> dict:
    """A well-formed hint payload, the exact shape `build_hint` emits."""
    return {
        HintKey.TEXT.value: "heading uptown",
        HintKey.INTENT.value: Intent.TRUTH.value,
        HintKey.TURN.value: turn,
    }


def events(ctx) -> list[dict]:
    if not ctx.log_path.exists():
        return []
    return [json.loads(line) for line in ctx.log_path.read_text(encoding="utf-8").splitlines()]


def hint_records(ctx) -> list[dict]:
    """This side's own inbound-HINT wire records."""
    return [
        e for e in events(ctx)
        if e["event"] == "message_received" and e["envelope"]["type"] == "hint"
    ]


def at_turn(ctx, turn: int):
    """Place the context on a given turn. `GameState` is frozen, so this
    derives a successor rather than mutating -- the same
    `dataclasses.replace` the engine itself uses."""
    ctx.state = dataclasses.replace(ctx.state, turn=turn)
    return ctx
