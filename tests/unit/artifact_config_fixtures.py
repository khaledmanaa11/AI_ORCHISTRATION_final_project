"""Shared builders for the config-artifact tests.

Extracted at the second consumer (CLAUDE.md Table 5: no duplication), when
`test_artifact_config.py` reached 153/150 code lines and split its seal /
round-trip half into `test_artifact_config_seal.py`.

These read the REAL `config/police/` and `config/thief/` trees, not doubles: a
double would prove the builder is self-consistent and nothing about whether
the artifact and the handshake agree.

Not named `test_*`, so pytest collects nothing here.
"""

from pathlib import Path

from pursuit.services.reporting import artifact_config

REPO_ROOT = Path(__file__).resolve().parents[2]
ROLES = ("police", "thief")
GAME_UID = "5efbc5811fabfac4"


def config_dir(role: str) -> Path:
    """The shipped config tree for one role, asserted present -- a silently
    missing tree would make every digest comparison below vacuous."""
    directory = REPO_ROOT / "config" / role
    assert (directory / "game_params.json").is_file(), directory
    return directory


def build(role: str) -> dict:
    return artifact_config.build_config_artifact(
        config_dir(role), game_uid=GAME_UID, game_id=GAME_UID, sub_game_index=1
    )
