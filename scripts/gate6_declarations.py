"""Step-0 declaration-file evidence -- split out of `gate6_clean_game.py`
at the 150-code-line house gate. Confirms both sides' `declaration_
<game_id>.json` (own) and `declaration_<game_id>_peer.json` (the peer's,
D-62 follow-up) exist, and that the OWN declaration file predates the
first commit/move content this side's own JSONL carries (Step-0 verified
before move 1)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from gate6_common import events

_MOVE_CONTENT_TYPES = {"commit", "move"}


def _predates_first_move(ctx, decl_path: Path) -> tuple[bool, str]:
    if not decl_path.exists():
        return False, f"{decl_path.name} does not exist"
    decl_epoch = decl_path.stat().st_mtime
    for r in events(ctx.log_path):
        env = r.get("envelope", {})
        if r.get("event") in ("message_sent", "message_received") and env.get("type") in _MOVE_CONTENT_TYPES:
            first_epoch = datetime.fromisoformat(r["timestamp"]).timestamp()
            return (
                decl_epoch <= first_epoch,
                f"declaration mtime={decl_epoch} <= first move-content ts={first_epoch}",
            )
    return True, "no move/commit content logged yet in this side's own JSONL"


def declaration_evidence(ctx, game_uid: str) -> dict:
    own = ctx.log_path.parent / f"declaration_{game_uid}.json"
    peer = ctx.log_path.parent / f"declaration_{game_uid}_peer.json"
    predates, detail = _predates_first_move(ctx, own)
    return {
        "own_declaration_exists": own.exists(),
        "peer_declaration_exists": peer.exists(),
        "predates_first_move_content": predates,
        "predates_detail": detail,
    }
