"""D-33: every way the language layer can fail still finishes a correctly
scored game. Four games, each a complete two-peer run through
`two_peer_game.play_two_peer_game` (04-12's own harness) -- no test here
performs network I/O.
"""

from __future__ import annotations

import dataclasses
import itertools
import json

from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.hint_payload import Intent
from pursuit.services.llm.budget import DegradeLevel
from pursuit.services.llm.provider import LlmFailure, LlmFailureReason, LlmResult
from tests.integration.two_peer_game import play_two_peer_game

_CFG_A = "config/police"
_CFG_B = "config/thief"


class _AlwaysFailingProvider:
    """Cycles through EVERY `LlmFailureReason` so no single mapping goes
    untested (Task 4). Never raises -- returns `LlmFailure`, exactly the
    D-33 contract a real provider must honour."""

    def __init__(self) -> None:
        self._reasons = itertools.cycle(LlmFailureReason)

    async def complete(self, *, system_prompt, user_prompt, schema=None):
        return LlmFailure(next(self._reasons), "simulated provider failure")


class _CountingProvider:
    """A provider that would succeed if called -- used to PROVE it is
    never actually called once `compose()` degrades to TEMPLATE_ONLY."""

    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, *, system_prompt, user_prompt, schema=None):
        self.calls += 1
        return LlmResult(text="unused", parsed=None, input_tokens=0, output_tokens=0)


def _events(log_path) -> list[dict]:
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


def _language_turns(log_path) -> list[dict]:
    return [e for e in _events(log_path) if e["event"] == "language_turn"]


async def test_no_key_finishes_on_the_template_path(tmp_path, monkeypatch):
    """Case 1: ANTHROPIC_API_KEY unset -- the real `claude_api` provider
    degrades to NO_KEY before ever touching the gatekeeper; the game still
    finishes with a legal hint every turn (the bank fallback)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config(_CFG_A), load_agent_config(_CFG_B)

    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid="no-key", log_dir=tmp_path,
    )

    assert outcome_a is not None and outcome_a == outcome_b
    for ctx, log_path in ((ctx_a, tmp_path / "a.jsonl"), (ctx_b, tmp_path / "b.jsonl")):
        turns = _language_turns(log_path)
        assert turns, f"{ctx.role}: no language_turn records"
        for record in turns:
            assert record["outgoing_hint"]["text"]
            assert record["outgoing_hint"]["intent"] in (Intent.TRUTH.value, Intent.LIE.value)


def _wire_failing_provider(ctx) -> None:
    fake = _AlwaysFailingProvider()
    ctx.language.decode_context = dataclasses.replace(ctx.language.decode_context, provider=fake)
    ctx.language.bluff_context = dataclasses.replace(ctx.language.bluff_context, provider=fake)


async def test_every_call_fails_finishes_on_the_template_path(tmp_path, monkeypatch):
    """Case 2: the provider itself is broken -- every decode AND every
    bluff call returns an `LlmFailure`, cycling reasons. Still a full,
    correctly-scored game with a legal hint every turn."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config(_CFG_A), load_agent_config(_CFG_B)

    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid="all-fail", log_dir=tmp_path, wire=_wire_failing_provider,
    )

    assert outcome_a is not None and outcome_a == outcome_b
    for log_path in (tmp_path / "a.jsonl", tmp_path / "b.jsonl"):
        for record in _language_turns(log_path):
            assert record["outgoing_hint"]["text"]


async def test_budget_exhausted_makes_zero_bluff_calls_after_crossing(tmp_path, monkeypatch):
    """Case 3: the budget starts past TEMPLATE_ONLY on both sides. A
    provider that WOULD succeed if called is wired into the bluff side
    specifically, proving `compose()` never calls it once degraded
    (D-35) -- the game still finishes with a hint every turn (the bank)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config(_CFG_A), load_agent_config(_CFG_B)
    counters: list[_CountingProvider] = []

    def wire(ctx) -> None:
        ctx.language.gatekeeper.budget.reserve(cfg_a.language.token_budget_per_series)
        assert ctx.language.gatekeeper.budget.level is DegradeLevel.TEMPLATE_ONLY
        counting = _CountingProvider()
        ctx.language.bluff_context = dataclasses.replace(ctx.language.bluff_context, provider=counting)
        counters.append(counting)

    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid="budget-exhausted", log_dir=tmp_path, wire=wire,
    )

    assert outcome_a is not None and outcome_a == outcome_b
    assert all(c.calls == 0 for c in counters), "compose() called the provider post-crossing"
    for log_path in (tmp_path / "a.jsonl", tmp_path / "b.jsonl"):
        for record in _language_turns(log_path):
            assert record["outgoing_hint"]["text"]  # the bank fallback still filled every turn


async def test_silent_opponent_completes_on_scent_alone(tmp_path, monkeypatch):
    """Case 4 (not degradation, same risk class): thief never sends a
    hint. Police's belief still runs (scent alone), NO_EVIDENCE every
    turn, and the game still finishes."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config(_CFG_A), load_agent_config(_CFG_B)

    def silence_thief(ctx) -> None:
        if ctx.role == "thief":
            ctx.language = None  # no LanguageRuntime -> take_my_turn sends no hint at all

    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid="silent-thief", log_dir=tmp_path, wire=silence_thief,
    )

    assert outcome_a is not None and outcome_a == outcome_b
    turns = _language_turns(tmp_path / "a.jsonl")
    assert turns, "police: no language_turn records"
    for record in turns:
        assert record["incoming_hint"]["outcome"] == "no_hint"
        assert record["incoming_hint"]["text"] is None
        assert record["belief_entropy"] is not None
        assert record["belief_entropy"] >= 0.0
