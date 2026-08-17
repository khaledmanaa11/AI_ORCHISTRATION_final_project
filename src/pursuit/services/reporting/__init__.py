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

from pursuit.services.reporting.artifact_config import (
    ConfigArtifactField,
    build_config_artifact,
    write_config_artifact,
)
from pursuit.services.reporting.artifact_declaration import (
    DeclarationArtifactField,
    DeclarationContext,
    build_declaration_artifact,
    verify_embedded_declarations,
    write_declaration_artifact,
)
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
    write_artifact_bytes,
)
from pursuit.services.reporting.chain import Refusal, ReportingChain, SendOutcome
from pursuit.services.reporting.dos import DosDetector
from pursuit.services.reporting.message import (
    build_report_message,
    render_message,
    report_filename,
)
from pursuit.services.reporting.quota import QuotaField, QuotaManager
from pursuit.services.reporting.sink import DryRunSink, MailSink, SendReceipt

__all__ = (
    "ArtifactField",
    "ArtifactPrefix",
    "ConfigArtifactField",
    "DeclarationArtifactField",
    "DeclarationContext",
    "DosDetector",
    "DryRunSink",
    "MailSink",
    "QuotaField",
    "QuotaManager",
    "Refusal",
    "ReportingChain",
    "SendOutcome",
    "SendReceipt",
    "artifact_digest",
    "artifact_digest_matches",
    "artifact_header",
    "build_config_artifact",
    "build_declaration_artifact",
    "build_report_message",
    "config_filename",
    "declaration_filename",
    "log_filename",
    "next_sub_game_index",
    "render_message",
    "report_filename",
    "result_filename",
    "sub_game_suffix",
    "verify_embedded_declarations",
    "write_artifact",
    "write_artifact_bytes",
    "write_config_artifact",
    "write_declaration_artifact",
)
