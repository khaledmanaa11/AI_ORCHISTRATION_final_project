"""The --mocked two-peer game provider: 'recorded responses', not a live
model (04-14-PLAN.md Task 1: "the provider is mocked from recorded
responses"). Decode calls cycle through tests/fixtures/hints_{en,he}.json's
OWN recorded `response` dicts (the same fixtures the fixture-accuracy check
uses); bluff calls cycle a small fixed, legal phrase bank. Neither ever
touches a network, so a grader can rerun --mocked with no API key.
"""

from __future__ import annotations

import dataclasses
import itertools
import json
from pathlib import Path

from pursuit.services.llm.provider import LlmResult

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

#: Recorded bluff-style completions -- short, legal (<=15 words, no
#: coordinate), standing in for a real model's phrasing of whatever
#: DeceptionPlan it is handed. compose() never reads these back for
#: content, only for length/shape, so any fixed, legal sentence pool works.
_RECORDED_BLUFF_PHRASES = (
    "Still working my way toward the north side of the city.",
    "Nothing to report from over here right now.",
    "Heading east, past the usual crossing.",
    "Keeping close to the river for now.",
)


def _decode_responses() -> tuple[dict, ...]:
    responses: list[dict] = []
    for language in ("en", "he"):
        path = _FIXTURES_DIR / f"hints_{language}.json"
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        responses.extend(case["response"] for case in data["cases"])
    return tuple(responses)


class RecordedResponseProvider:
    """A provider whose answers are drawn from a fixed, recorded pool.

    Deterministic per-instance cycling (`itertools.cycle`, never `random`),
    so a --mocked run with a fixed seed set is byte-reproducible.
    """

    def __init__(self) -> None:
        self._decode_cycle = itertools.cycle(_decode_responses())
        self._bluff_cycle = itertools.cycle(_RECORDED_BLUFF_PHRASES)
        #: This provider bypasses AnthropicProvider entirely (it stands IN
        #: for it), so it never passes through Gatekeeper.submit() -- the
        #: real budget-accounting call site. These counters are the mocked
        #: run's own record of "how many simulated calls, how many
        #: simulated tokens", read back by gate4_games.py instead of the
        #: (permanently zero, for this provider) gatekeeper budget.
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0

    async def complete(self, *, system_prompt, user_prompt, schema=None):
        if schema is not None:
            response = next(self._decode_cycle)
            input_tokens, output_tokens = 45, 18
            result = LlmResult(
                text=json.dumps(response), parsed=dict(response),
                input_tokens=input_tokens, output_tokens=output_tokens, model="mocked-recorded",
            )
        else:
            input_tokens, output_tokens = 35, 12
            result = LlmResult(
                text=next(self._bluff_cycle), parsed=None,
                input_tokens=input_tokens, output_tokens=output_tokens, model="mocked-recorded",
            )
        self.calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        return result

    def report(self) -> dict:
        """Mirrors `TokenBudget.report()`'s shape (`services/llm/budget.py`)
        so downstream reporting code stays uniform -- SIMULATED numbers,
        never real API usage (labelled as such in the JSON output)."""
        return {
            "calls": self.calls, "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens, "level": "full (simulated)", "budget": None,
        }


def wire_mocked_provider(ctx) -> None:
    """`play_two_peer_game`'s own `wire` seam
    (tests/integration/two_peer_game.py): swap BOTH the decode and the
    bluff provider for one shared recorded-response instance, mirroring
    tests/integration/test_llm_degradation.py's own `_wire_failing_provider`.
    """
    provider = RecordedResponseProvider()
    ctx.language.decode_context = dataclasses.replace(ctx.language.decode_context, provider=provider)
    ctx.language.bluff_context = dataclasses.replace(ctx.language.bluff_context, provider=provider)
