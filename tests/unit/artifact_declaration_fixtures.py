"""Shared builders for the declaration-artifact tests.

Extracted at the second consumer (CLAUDE.md Table 5: no duplication), when
`test_artifact_declaration.py` reached 154/150 code lines and split its
peer-boundary half into `test_artifact_declaration_peer.py`. The envelopes are
built by the REAL `step0_sign.sign_declaration`, never a hand-rolled digest.

Not named `test_*`, so pytest collects nothing here -- the same shape
`tests/integration/late_peer_harness.py` already uses.
"""

from pursuit.security.step0_collect import DeclarationField
from pursuit.security.step0_sign import sign_declaration
from pursuit.services.reporting import artifact_declaration as decl

GAME_UID = "5efbc5811fabfac4"
SECRET = "not-a-real-secret-only-a-fixture"
SECRETS = (None, SECRET)

# The ten §5.5 keys `step0_collect.collect_declaration` assembles, with fixture
# values. Named from DeclarationField so a renamed key breaks these tests
# rather than letting them drift onto a stale spelling.
SEC55 = {
    DeclarationField.ROLE: "police",
    DeclarationField.TEAM_CODE: "khm-mn17",
    DeclarationField.OS: "Windows-11",
    DeclarationField.CPU: {"cores": 8, "freq_mhz": 2400.0},
    DeclarationField.RAM_GB: 15.7,
    DeclarationField.GPU: {"present": False, "detail": "not detected"},
    DeclarationField.LLM_NAME: "claude-haiku-4-5",
    DeclarationField.CODE_VERSION: "1.00",
    DeclarationField.GAMES_PLAYED_SO_FAR: 3,
    DeclarationField.COMMIT_HASH: "0" * 40,
}


def make_context() -> decl.DeclarationContext:
    """Fixture values only -- no repo URL, address or ceiling here is claimed
    to be the project's real one; 07-07 supplies those from live wiring."""
    return decl.DeclarationContext(
        repo_urls={"police": "https://example.invalid/a", "thief": "https://example.invalid/b"},
        mcp_server_addresses={"police": "http://127.0.0.1:8001/mcp"},
        token_ceiling=200000,
        start_time="2026-08-17T10:00:00Z",
        end_time="2026-08-17T10:12:00Z",
    )


def make_envelope(secret, **overrides) -> dict:
    """`{"declaration": {...ten keys...}, **signature}` -- the exact dict
    `agent_step0_wiring.declare_step0` returns."""
    declaration = {**SEC55, **overrides}
    signature = sign_declaration(declaration, secret=secret)
    return {decl.ENVELOPE_DECLARATION_KEY: declaration, **signature}


def make_artifact(*, own_secret=None, peer_envelope=None) -> dict:
    return decl.build_declaration_artifact(
        game_uid=GAME_UID,
        game_id=GAME_UID,
        own_envelope=make_envelope(own_secret),
        peer_envelope=peer_envelope,
        context=make_context(),
    )
