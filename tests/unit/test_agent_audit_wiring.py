"""Coverage-closing tests (Rule 2) for agent_audit_wiring.py's own
technical-loss branches in run_final_audit: a failed FINAL_REVEAL push,
and a push that succeeds but nothing is ever received back -- plus, from
05-07, declare_step0's honest `llm_name` and the declaration's shape.

Both run_final_audit cases below deliberately omit `board_outcome`,
pinning the `board_outcome is None` branch -- the "turn loop never
resolved" case, where a technical loss is still the right verdict. They
are therefore NOT the production shape: `agent_entrypoint.run_agent`
always passes the turn loop's own outcome (05-04), and
`test_audit_send_failure.py` is the file that covers it."""

from __future__ import annotations

import dataclasses
import json

import pytest

from pursuit.constants import Outcome
from pursuit.network.agent_audit_wiring import declare_step0, run_final_audit
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.language_wiring import LLM_NAME_TEMPLATE_FALLBACK
from pursuit.network.state_machine import State
from pursuit.services.llm.client import API_KEY_ENV_VAR
from pursuit.shared.language_model_config import ModelKey
from pursuit.shared.security_config import SecurityParams
from tests.unit._fakes_agent import FakeClient, make_ctx

_ON = SecurityParams(version="1.00", commit_reveal=True, team_code="khm-mn17")

#: Fake, never a credential -- searched for below to prove the VALUE never
#: reaches the declaration, which is persisted AND sent to the opponent.
_SENTINEL_KEY = "not-a-real-key-05-07-sentinel"

#: The ten Sec5.5 field names, spelled out rather than read back from
#: `DeclarationField`, so a rename or an addition on either side fails
#: here. The declaration is HMAC-signed and verified before move 1
#: (Sec10.4 criterion 3): 05-07 moves ONE value, never the field set.
_DECLARATION_KEYS = frozenset({
    "role", "team_code", "os", "cpu", "ram_gb", "gpu",
    "llm_name", "code_version", "games_played_so_far", "commit_hash",
})


def _cfg(provider: str | None = None):
    cfg = load_agent_config("config/police")
    if provider is None:
        return cfg
    model = {**cfg.language.model, ModelKey.PROVIDER.value: provider}
    return dataclasses.replace(cfg, language=dataclasses.replace(cfg.language, model=model))


async def _declaration(cfg) -> dict:
    """declare_step0's own declaration, with the shape invariant checked on
    EVERY path through these tests, not just one."""
    _digest, envelope = await declare_step0(cfg)
    declaration = envelope["declaration"]
    assert len(declaration) == 10
    assert set(declaration) == _DECLARATION_KEYS
    return declaration


async def test_a_real_provider_with_no_key_declares_the_template_fallback(monkeypatch):
    """Rule 38: machine B declared `claude-haiku-4-5` while making zero
    calls (05-UAT G5). It now says what it can actually do."""
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    declaration = await _declaration(_cfg())
    assert declaration["llm_name"] == LLM_NAME_TEMPLATE_FALLBACK


async def test_a_real_provider_with_a_key_declares_the_configured_model_id(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, _SENTINEL_KEY)
    cfg = _cfg()
    declaration = await _declaration(cfg)
    assert declaration["llm_name"] == cfg.language.model[ModelKey.MODEL_ID.value]


@pytest.mark.parametrize("key_present", [True, False])
async def test_the_template_provider_declares_the_fallback_whatever_the_key_says(
    monkeypatch, key_present,
):
    """`template` never calls a model, so a key in the environment changes
    nothing it can honestly claim."""
    if key_present:
        monkeypatch.setenv(API_KEY_ENV_VAR, _SENTINEL_KEY)
    else:
        monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    declaration = await _declaration(_cfg("template"))
    assert declaration["llm_name"] == LLM_NAME_TEMPLATE_FALLBACK


async def test_the_declaration_never_carries_the_key_value(monkeypatch):
    """CLAUDE.md rule 4: this dict is written to disk and handed to the
    opponent, so the probe must stay presence-only end to end."""
    monkeypatch.setenv(API_KEY_ENV_VAR, _SENTINEL_KEY)
    declaration = await _declaration(_cfg())
    assert _SENTINEL_KEY not in json.dumps(declaration)


async def test_run_final_audit_is_technical_loss_when_the_push_fails(
    tmp_path, default_params, network_params,
):
    """No board_outcome: the turn loop never resolved, so nothing else
    stands and our own failed push is still a technical loss."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="final-audit-push-fail",
        security=_ON, client=FakeClient(fail=True), initial_state=State.GAME_OVER,
    )
    outcome = await run_final_audit(ctx)
    assert outcome is Outcome.TECHNICAL_LOSS


async def test_run_final_audit_is_technical_loss_when_the_opponent_never_answers(
    tmp_path, default_params, network_params,
):
    """Rule 36, unchanged by 05-04: a peer that never publishes its own
    nonces loses regardless of whether a board outcome stands."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="final-audit-recv-fail",
        security=_ON, initial_state=State.GAME_OVER,
    )
    outcome = await run_final_audit(ctx)
    assert outcome is Outcome.TECHNICAL_LOSS
