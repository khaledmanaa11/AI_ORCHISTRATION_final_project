"""Small wiring closures + config-dir readers -- split out of
agent_lifecycle.py at the 150-code-line gate (Segal Table 5): role.json
reading, `AgentConfig`/`load_agent_config` (the four per-agent config files),
and the NET-09 inbound handshake seam. `agent_lifecycle.py` imports every
name here and re-exports it, so `agent_lifecycle.load_role` /
`.load_agent_config` / `.make_transition_reporter` / `.make_freeze_handler` /
`.make_handshake_responder` keep working for every caller (including the
tests) exactly as if they were still defined there.

05-05: the two NET-05/NET-07 JSONL sink closures now LIVE in
`game_identity.py` (this file measured 148/150 and had no room for their
D-61 `GameIdentity` parameter) and are re-exported below unchanged -- the
same relocate-and-re-export move `secret_wiring.py` made in 05-02. Every
existing importer, including `agent_lifecycle` and the tests that reach them
through it, resolves them exactly as before.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pursuit.network.envelope import EnvelopeKey, MessageType
from pursuit.network.game_identity import (  # noqa: F401  -- re-export only
    GameIdentity,
    make_freeze_handler,
    make_transition_reporter,
)
from pursuit.network.handshake import respond_to_handshake
from pursuit.network.state_machine import TransitionReporter, TurnStateMachine
from pursuit.network.tools import HandshakeHandler
from pursuit.shared.belief_config import BeliefParams, load_belief_config
from pursuit.shared.config import GameParams, load_game_params
from pursuit.shared.deception_config import DeceptionParams, load_deception_config
from pursuit.shared.language_config import LanguageParams, load_language_config
from pursuit.shared.network_config import NetworkParams, load_network_config
from pursuit.shared.resolution import RESOLUTION_SOURCE, ResolutionRules, load_resolution_rules
from pursuit.shared.scent_config import ScentModel, load_scent_model
from pursuit.shared.security_config import SecurityParams, load_security_config
from pursuit.shared.strategy_config import StrategyParams, load_strategy_config


class RoleKey:
    """The one key role.json carries -- named, not a bare string literal."""

    ROLE = "role"


def load_role(config_dir: Path | str) -> str:
    """Read the per-agent role.json (NET-01: role comes from the config dir
    named on the command line, never a flag or a global)."""
    path = Path(config_dir) / "role.json"
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    role = data.get(RoleKey.ROLE)
    if not isinstance(role, str) or not role.strip():
        raise ValueError(f"{path}: missing or blank {RoleKey.ROLE!r}")
    return role


@dataclass(frozen=True)
class AgentConfig:
    """The ten per-agent config files, loaded once and handed to
    build_context. Phase 4 adds five negotiated blocks (strategy, language,
    belief, scent, deception) so the live turn loop can build a real mover
    and a real language pipeline instead of the Phase-2/3 placeholders.
    Phase 6 adds `security` (commit_reveal toggle + team_code, D-65)."""

    config_dir: Path
    role: str
    params: GameParams
    net: NetworkParams
    rules: ResolutionRules
    strategy: StrategyParams
    language: LanguageParams
    belief: BeliefParams
    scent: ScentModel
    deception: DeceptionParams
    security: SecurityParams


def load_agent_config(config_dir: Path | str) -> AgentConfig:
    """Load role.json + network.json + game_params.json + the optional
    negotiated resolution.json, plus strategy/language/belief/scent/
    deception/security.json, from ONE per-agent directory -- the only
    source for this process's identity (NET-01). A missing resolution.json
    is not an error: it degrades to BOOK_ONLY (RULES-RESOLUTION.md Sec5)."""
    directory = Path(config_dir)
    role = load_role(directory)
    net = load_network_config(directory / "network.json")
    params = load_game_params(directory / "game_params.json")
    rules = load_resolution_rules(directory / RESOLUTION_SOURCE)
    strategy = load_strategy_config(directory / "strategy.json")
    language = load_language_config(directory / "language.json")
    belief = load_belief_config(directory / "belief.json")
    scent = load_scent_model(directory / "scent.json")
    deception = load_deception_config(directory / "deception.json")
    security = load_security_config(directory / "security.json")
    return AgentConfig(
        config_dir=directory, role=role, params=params, net=net, rules=rules,
        strategy=strategy, language=language, belief=belief, scent=scent, deception=deception,
        security=security,
    )


def make_handshake_responder(
    *, machine: TurnStateMachine, reporter: TransitionReporter, local_digest: str, local_role: str,
    local_scent_digest: str | None = None,
    local_step0_digest: str | None = None, local_game_id: str | None = None,
    local_step0_declaration: dict | None = None, shared_secret: str | None = None,
) -> HandshakeHandler:
    """THE NET-09 inbound seam (D-05, D-08, design note 12): an `async def`
    adapter around 02-08's synchronous `respond_to_handshake` -- required to
    be async because 02-06's tool body awaits it directly on this process's
    event loop (RESEARCH Pitfall 2). `local_scent_digest` (04-12) locks
    D-46/rule 23 on the LIVE path; `local_step0_digest`/`local_game_id`/
    `local_step0_declaration`/`shared_secret` (06-03, D-61/D-62) do the
    same for Step-0 verification and the negotiated game_id -- every one
    defaults None so a caller opting out still degrades to config-only
    agreement rather than a hard requirement. Every value here MUST be a
    plain parameter, computed before this closure is built (design note
    12): it cannot close over an AgentContext that does not exist yet."""

    async def _respond(turn: int, sender: str, payload: dict) -> dict:
        reply, _result = respond_to_handshake(
            machine=machine, reporter=reporter, local_digest=local_digest,
            local_role=local_role, local_scent_digest=local_scent_digest,
            local_step0_digest=local_step0_digest, local_game_id=local_game_id,
            local_step0_declaration=local_step0_declaration, shared_secret=shared_secret,
            incoming={
                EnvelopeKey.TYPE: MessageType.HANDSHAKE.value,
                EnvelopeKey.TURN: turn,
                EnvelopeKey.SENDER: sender,
                EnvelopeKey.PAYLOAD: payload,
            },
        )
        return reply

    return _respond
