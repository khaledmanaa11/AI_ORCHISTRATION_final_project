"""The reporting services package -- the book's Figure-13 gatekeeper chain
(§9.3.1, rules 28-29; REPORT-02/03/04).

`QuotaManager` -> `Gatekeeper.submit()` (the Phase-4 token bucket, unchanged
and still inside `submit`) -> `DosDetector` -> the injected sink. This is the
package's public surface -- import from here, not from the sibling modules
directly, matching `services/llm/__init__.py`'s convention so 07-04's mail
transport and 07-07's end-of-game hook code against one stable path.

NOTHING IN THIS PACKAGE TRANSMITS. The sink is injected and has no default;
07-04 adds `DryRunSink` (disk) and `GmailSink` (the only module that will
import `google-*`). Every shipped config carries `reporting.mode = dry_run`.
"""

from pursuit.services.reporting.artifacts import (
    ArtifactField,
    ArtifactPrefix,
    artifact_digest,
    artifact_digest_matches,
    artifact_header,
    config_filename,
    declaration_filename,
    log_filename,
    next_sub_game_index,
    result_filename,
    sub_game_suffix,
    write_artifact,
)
from pursuit.services.reporting.chain import Refusal, ReportingChain, SendOutcome
from pursuit.services.reporting.dos import DosDetector
from pursuit.services.reporting.quota import QuotaField, QuotaManager

__all__ = (
    "ArtifactField",
    "ArtifactPrefix",
    "DosDetector",
    "QuotaField",
    "QuotaManager",
    "Refusal",
    "ReportingChain",
    "SendOutcome",
    "artifact_digest",
    "artifact_digest_matches",
    "artifact_header",
    "config_filename",
    "declaration_filename",
    "log_filename",
    "next_sub_game_index",
    "result_filename",
    "sub_game_suffix",
    "write_artifact",
)
