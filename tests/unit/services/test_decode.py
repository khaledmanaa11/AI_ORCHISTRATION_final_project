"""decode.py: nothing an opponent can send, and nothing an API can do, gets
past `decode_hint` (D-33, D-41, D-44).

Every test mocks the provider. No test performs network I/O.
"""

import json
import pathlib

import pytest

from pursuit.services.llm.decode import DecodeContext, decode_hint
from pursuit.services.llm.provider import LlmFailure, LlmFailureReason, LlmResult
from pursuit.services.llm.template_provider import TemplateProvider
from pursuit.shared.directions import DirectionWord
from pursuit.shared.inference import Region

_FIXTURES = pathlib.Path(__file__).parents[2] / "fixtures"
WORD_LIMIT = 15  # PARAMETERS.md Table 14 row 2, passed in as the caller would


class FakeProvider:
    """Satisfies the Provider protocol; records every call it receives."""

    def __init__(self, outcome=None, *, boom: Exception | None = None):
        self.outcome = outcome
        self.boom = boom
        self.calls: list[dict] = []

    async def complete(self, *, system_prompt, user_prompt, schema=None):
        self.calls.append({"system": system_prompt, "user": user_prompt, "schema": schema})
        if self.boom is not None:
            raise self.boom
        return self.outcome


def result_for(obj: dict | None, *, text: str = "") -> LlmResult:
    """A successful LlmResult carrying `obj` as the parsed body."""
    return LlmResult(
        text=text or json.dumps(obj), parsed=obj, input_tokens=1, output_tokens=1
    )


def context_for(provider, board_size: int, *, word_limit: int = WORD_LIMIT) -> DecodeContext:
    return DecodeContext(
        provider=provider, board_size=board_size, arena="New York", word_limit=word_limit
    )


def load_cases(name: str) -> list[tuple[str, dict]]:
    """(id, case) pairs from a fixture file, for parametrize."""
    data = json.loads((_FIXTURES / name).read_text(encoding="utf-8"))
    return [(case["id"], case) for case in data["cases"]]


EN_CASES = load_cases("hints_en.json")
HE_CASES = load_cases("hints_he.json")


@pytest.mark.parametrize(
    ("case_id", "case"), EN_CASES + HE_CASES, ids=[f"{c[0]}" for c in EN_CASES + HE_CASES]
)
async def test_every_fixture_decodes_to_its_expected_shape(case_id, case, default_params):
    """The recorded response goes back through a mocked provider and must
    produce exactly the fixture's `expect` block."""
    provider = FakeProvider(result_for(case["response"]))
    inference = await decode_hint(case["hint"], context_for(provider, default_params.board_size))

    expected = case["expect"]
    assert inference.region == (Region(expected["region"]) if expected["region"] else None)
    assert inference.direction == (
        DirectionWord(expected["direction"]) if expected["direction"] else None
    )
    assert inference.cells == tuple(tuple(cell) for cell in expected["cells"])
    assert inference.confidence == expected["confidence"]
    assert inference.is_evidence is expected["is_evidence"]
    assert inference.raw_text == case["hint"]


@pytest.mark.parametrize(("case_id", "case"), HE_CASES, ids=[c[0] for c in HE_CASES])
async def test_hebrew_reaches_the_provider_unmangled(case_id, case, default_params):
    """D-44: the sentence must arrive at the model in the script it was sent."""
    provider = FakeProvider(result_for(case["response"]))
    await decode_hint(case["hint"], context_for(provider, default_params.board_size))
    assert case["hint"] in provider.calls[0]["user"]


def test_both_languages_share_one_output_vocabulary():
    """Hebrew fixtures must decode into the same schema enum as English ones."""
    en_regions = {c["expect"]["region"] for _, c in EN_CASES}
    he_regions = {c["expect"]["region"] for _, c in HE_CASES}
    assert he_regions <= en_regions


@pytest.mark.parametrize("empty", ["", "   ", "\n\t", None, 42])
async def test_an_empty_or_non_string_hint_short_circuits_with_zero_calls(empty, default_params):
    provider = FakeProvider(result_for({"region": "north"}))
    inference = await decode_hint(empty, context_for(provider, default_params.board_size))
    assert inference.is_evidence is False
    assert provider.calls == []


async def test_an_over_limit_hint_costs_no_token(default_params):
    """An opponent breaking rule 26 must not be able to bill us for it."""
    provider = FakeProvider(result_for({"region": "north"}))
    flood = " ".join(["word"] * (WORD_LIMIT + 1))
    inference = await decode_hint(flood, context_for(provider, default_params.board_size))
    assert inference.is_evidence is False
    assert provider.calls == []


async def test_a_hint_exactly_at_the_limit_is_decoded(default_params):
    provider = FakeProvider(
        result_for({"region": "north", "cells": [], "direction": None, "confidence": 0.5})
    )
    exact = " ".join(["north"] * WORD_LIMIT)
    inference = await decode_hint(exact, context_for(provider, default_params.board_size))
    assert inference.is_evidence is True
    assert len(provider.calls) == 1


async def test_the_template_provider_decodes_to_nothing_with_zero_calls(default_params):
    """D-52's zero-token mode has no model behind it; the belief map runs on
    scent alone there, which is a capability difference, not a bug."""
    provider = TemplateProvider(phrases=["anything"])
    inference = await decode_hint("I am north.", context_for(provider, default_params.board_size))
    assert inference.is_evidence is False
    assert inference.raw_text == "I am north."


@pytest.mark.parametrize("reason", list(LlmFailureReason))
async def test_every_failure_reason_yields_no_evidence(reason, default_params):
    provider = FakeProvider(LlmFailure(reason, "mocked"))
    inference = await decode_hint("I am north.", context_for(provider, default_params.board_size))
    assert inference.is_evidence is False
    assert inference.confidence == 0.0


async def test_malformed_json_yields_no_evidence(default_params):
    provider = FakeProvider(LlmResult(text="not json {", parsed=None, input_tokens=1, output_tokens=1))
    inference = await decode_hint("I am north.", context_for(provider, default_params.board_size))
    assert inference.is_evidence is False


async def test_a_schema_valid_but_out_of_range_confidence_yields_no_evidence(default_params):
    provider = FakeProvider(
        result_for({"region": "north", "cells": [], "direction": None, "confidence": 1.5})
    )
    inference = await decode_hint("I am north.", context_for(provider, default_params.board_size))
    assert inference.is_evidence is False


async def test_an_unknown_key_in_the_response_yields_no_evidence(default_params):
    provider = FakeProvider(
        result_for(
            {"region": "north", "cells": [], "direction": None, "confidence": 0.9, "move": "north"}
        )
    )
    inference = await decode_hint("I am north.", context_for(provider, default_params.board_size))
    assert inference.is_evidence is False


async def test_a_provider_that_raises_never_lets_the_exception_escape(default_params):
    """`Provider.complete` is contractually non-exceptional, but this boundary
    must hold even when a provider breaks that contract."""
    provider = FakeProvider(boom=RuntimeError("socket exploded"))
    inference = await decode_hint("I am north.", context_for(provider, default_params.board_size))
    assert inference.is_evidence is False
    assert inference.raw_text == "I am north."


async def test_a_provider_returning_text_without_parsed_is_still_understood(default_params):
    body = {"region": "south", "cells": [], "direction": None, "confidence": 0.7}
    provider = FakeProvider(
        LlmResult(text=json.dumps(body), parsed=None, input_tokens=1, output_tokens=1)
    )
    inference = await decode_hint("I am south.", context_for(provider, default_params.board_size))
    assert inference.region is Region.SOUTH


async def test_the_schema_is_sent_on_the_request(default_params):
    provider = FakeProvider(
        result_for({"region": "north", "cells": [], "direction": None, "confidence": 0.5})
    )
    await decode_hint("I am north.", context_for(provider, default_params.board_size))
    assert provider.calls[0]["schema"]["additionalProperties"] is False


async def test_the_decoder_returns_no_move_field_of_any_kind(default_params):
    """Rule 25 is the type signature here: there is nowhere to put a move."""
    provider = FakeProvider(
        result_for({"region": "north", "cells": [], "direction": None, "confidence": 0.5})
    )
    inference = await decode_hint("I am north.", context_for(provider, default_params.board_size))
    fields = set(vars(inference))
    assert not fields & {"move", "action", "preference", "evaluation", "score"}
