"""`config_<game_id>_g<NN>.json` -- "the agreed configuration: every numeric
parameter above, cryptographically locked and identical on both sides"
(docs/PARAMETERS.md:166, Appendix F rules 1 and 3).

WHAT IS IN, AND WHY EXACTLY THESE FILES. Appendix F's parameter tables map
onto this repository's shipped config as follows, and every file below is
byte-identical in `config/police/` and `config/thief/` today -- which
`tests/unit/test_artifact_config.py` proves by building BOTH sides and
diffing the two artifacts, rather than by asserting this builder is careful:

  Tables 13, 15, 17 (board, movement/barriers, scoring)  -> game_params.json
  Table 16 (dynamic pheromones)                          -> scent.json
  Tables 14, 19 (arena/hints, gatekeeper)                -> language.json

WHAT IS OUT, AND WHY:

  network.json  -- Table 18. PER-AGENT by design (different port, different
                   opponent_url, D-04); `config_hash.py:13-16` states that
                   hashing it "would abort every game". Including it would
                   also break the byte-identity rule 11 requires.
  role.json     -- which side we are. Not a parameter; not agreed.
  reporting.json -- a SECOND Table-19 instance, governing OUR outgoing mail
                   to the lecturer rather than the game (07-01 OQ-3 tunes its
                   wait_after_error_seconds to 30 while language.json keeps
                   5). Two Table-19 rows in one artifact would read as a
                   contradiction; the game-facing instance is the one here.
  strategy/weights/belief/deception/resolution.json -- this side's policy.
                   Not Appendix F parameters, and publishing the policy the
                   opponent plays against is not what rule 11 asks for.

TWO KINDS OF DIGEST, KEPT DISTINGUISHABLE. `handshake_digests` holds ONLY the
digests actually exchanged with the peer and compared before move 1 --
`config_digest` over game_params.json (D-08/D-15) and `scent_digest` over the
locked scent model (D-46). `language.json` is shipped identically by both
sides but never goes on the wire, so it deliberately has NO handshake digest;
claiming one would assert an agreement that was never made. `config_digest`
(the artifact's own key) seals the whole embedded object through the one
`artifact_digest` seal.

ZERO NUMERIC VALUES ARE INTRODUCED HERE. Every parameter value is COPIED from
the already-shipped config file; nothing is re-typed and nothing is defaulted.
"""

from __future__ import annotations

import json
from pathlib import Path

from pursuit.network.config_hash import config_digest
from pursuit.services.reporting.artifacts import (
    artifact_digest,
    artifact_header,
    config_filename,
    write_artifact,
)
from pursuit.shared.scent_config import load_scent_model, scent_digest

__all__ = (
    "AGREED_CONFIG_STEMS",
    "GAME_PARAMS_STEM",
    "SCENT_STEM",
    "ConfigArtifactField",
    "build_config_artifact",
    "write_config_artifact",
)

GAME_PARAMS_STEM = "game_params"
SCENT_STEM = "scent"
LANGUAGE_STEM = "language"

# Ordered, and the order is load-bearing: it fixes the key order of the
# embedded object, so the two roles serialise byte-identically (rule 11)
# without depending on any dict-ordering accident.
AGREED_CONFIG_STEMS = (GAME_PARAMS_STEM, SCENT_STEM, LANGUAGE_STEM)


class ConfigArtifactField:
    """Key names for the config artifact -- structural, avoids magic strings."""

    CONFIG = "config"
    HANDSHAKE_DIGESTS = "handshake_digests"
    CONFIG_DIGEST = "config_digest"


def _read_config_file(config_dir: Path, stem: str) -> dict:
    """Read one shipped config file verbatim.

    `json.loads` on an explicitly utf-8 decoded read, exactly as
    `config_hash.config_digest` does it, so the object embedded here and the
    object hashed there are the same object.
    """
    return json.loads((config_dir / f"{stem}.json").read_text(encoding="utf-8"))


def build_config_artifact(
    config_dir: Path | str, *, game_uid: str, game_id: str, sub_game_index: int
) -> dict:
    """Assemble `config_<game_id>_g<NN>.json`'s content for one config dir.

    The embedded `config.game_params` is the exact object
    `config_hash.config_digest` hashes, so recomputing SHA-256 over
    `canonical_json` of it reproduces `handshake_digests.game_params` --
    the same string `agent_entrypoint.py:80` puts on the handshake wire. If
    those two ever disagree, the artifact and the game were locked to
    different configs (rule 11).
    """
    directory = Path(config_dir)
    config = {stem: _read_config_file(directory, stem) for stem in AGREED_CONFIG_STEMS}
    artifact = artifact_header(
        game_uid=game_uid, game_id=game_id, sub_game_index=sub_game_index
    )
    artifact[ConfigArtifactField.CONFIG] = config
    artifact[ConfigArtifactField.HANDSHAKE_DIGESTS] = {
        GAME_PARAMS_STEM: config_digest(directory / f"{GAME_PARAMS_STEM}.json"),
        SCENT_STEM: scent_digest(load_scent_model(directory / f"{SCENT_STEM}.json")),
    }
    artifact[ConfigArtifactField.CONFIG_DIGEST] = artifact_digest(config)
    return artifact


def write_config_artifact(
    artifact_dir: Path | str,
    config_dir: Path | str,
    *,
    game_uid: str,
    game_id: str,
    sub_game_index: int,
) -> Path:
    """Build and durably write the config artifact, through the one
    `write_artifact` gate -- so this writer inherits D7-1's refusal of any
    path under `logs/` rather than restating it."""
    artifact = build_config_artifact(
        config_dir, game_uid=game_uid, game_id=game_id, sub_game_index=sub_game_index
    )
    return write_artifact(artifact_dir, config_filename(game_id, sub_game_index), artifact)
