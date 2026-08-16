"""Step-0 declaration collect/sign/declare (D-62/D-63) and its on-disk
persistence under the negotiated game_id (D-61).

Split out of `agent_audit_wiring.py` at the 150-code-line gate (Segal
Table 5) when 05-13's receive-leg policy took that file to exactly
150/150 -- the same relocate-and-re-export move `agent_audit_verdict.py`
already made out of `agent_audit_exchange.py`, and split along the seam
that module's own opening sentence already named: "Step-0 declaration
collect/sign/declare, AND the whole Final-Reveal/mutual-audit sequence"
were always two subjects sharing one file. `agent_audit_wiring.py` keeps
the Final-Reveal half and re-exports both public names below, so every
existing importer -- `agent_entrypoint`, `late_peer_harness`, the gate
scripts and the test suite -- resolves through it unchanged.

Split, never compressed: not one line of either function's body or
docstring was shortened to make room.
"""

from __future__ import annotations

from pursuit.network.agent_context import AgentContext
from pursuit.network.agent_wiring import AgentConfig
from pursuit.network.game_identity import negotiated_game_id
from pursuit.network.handshake_evaluate import HandshakeResult
from pursuit.network.language_wiring import declared_llm_name
from pursuit.network.secret_wiring import resolve_shared_secret
from pursuit.security import step0_collect, step0_sign
from pursuit.shared.durable_write import durable_write_json
from pursuit.shared.version import VERSION

_COUNTER_FILENAME = "games_played.json"
# Structural, matching QTable.save()'s own local durable-write precedent
# (03-05-SUMMARY.md) -- not a PARAMETERS.md value.
_DECLARE_RETRIES = 3
_DECLARE_BACKOFF_SECONDS = 0.1

__all__ = ["declare_step0", "write_declaration"]


async def declare_step0(cfg: AgentConfig) -> tuple[str, dict]:
    """Collect + sign THIS side's Step-0 declaration BEFORE the handshake
    (D-62/D-63) so its digest is ready to ride the handshake payload.
    Returns `(step0_digest, declaration_envelope)` -- the envelope is the
    exact dict `write_declaration` persists once the handshake agrees.

    `llm_name` is `declared_llm_name`'s answer, NOT a config echo (rule 38,
    05-UAT G5): only the VALUE of that one field moved, never the field
    set. The declaration's ten Sec5.5 keys are what `sign_declaration`
    HMACs and what `handshake_step0` verifies before move 1 (Sec10.4
    criterion 3), so a shape change here would break Step-0 against a
    peer."""
    games_played = step0_collect.read_games_played(cfg.config_dir / _COUNTER_FILENAME)
    llm_name = declared_llm_name(cfg.language.model)
    declaration = step0_collect.collect_declaration(
        role=cfg.role, team_code=cfg.security.team_code, llm_name=llm_name,
        code_version=VERSION, games_played=games_played,
    )
    secret = resolve_shared_secret(cfg.config_dir)
    secret_value = secret[1] if secret is not None else None
    signature = step0_sign.sign_declaration(declaration, secret=secret_value)
    return signature[step0_sign.SignKey.DIGEST], {"declaration": declaration, **signature}


def write_declaration(
    ctx: AgentContext, cfg: AgentConfig, result: HandshakeResult, declaration_envelope: dict,
) -> None:
    """Persist THIS side's own signed Step-0 declaration beside the log,
    named by the negotiated game_id (D-61) -- ONLY after a successful
    handshake -- then record this game against the per-role counter
    exactly once (rule 37/38). ALSO persists the PEER's own declaration
    (D-62 follow-up), when they sent one, so the content this side
    verified at handshake stays auditable after the fact (Phase 7);
    skipped entirely for a digest-only peer -- there is no content to save.

    05-05: the D-61 policy is no longer duplicated here -- the ONE definition
    lives in `game_identity.negotiated_game_id`, which `run_agent` has
    already applied to `ctx.game_uid` itself by the time this runs (so this
    call is idempotent on the live path: `negotiated_game_id(role, P, P)` is
    `P` for both roles). Calling it rather than reading `ctx.game_uid` keeps
    a caller that has NOT adopted -- the integration harnesses -- on exactly
    the pre-05-05 filename."""
    declared_game_id = negotiated_game_id(ctx.role, ctx.game_uid, result.peer_game_id)
    path = ctx.log_path.parent / f"declaration_{declared_game_id}.json"
    durable_write_json(
        path, declaration_envelope, retries=_DECLARE_RETRIES, backoff=_DECLARE_BACKOFF_SECONDS,
    )
    if result.peer_step0_declaration is not None:
        peer_path = ctx.log_path.parent / f"declaration_{declared_game_id}_peer.json"
        durable_write_json(
            peer_path, result.peer_step0_declaration,
            retries=_DECLARE_RETRIES, backoff=_DECLARE_BACKOFF_SECONDS,
        )
    step0_collect.record_game_played(cfg.config_dir / _COUNTER_FILENAME)
