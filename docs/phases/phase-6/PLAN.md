# Phase 6 PLAN — Security and Cryptography

**Version:** 1.00 · **Status:** ◐ approved · **Updated:** 2026-08-09

> How Phase 6 is built. The authoritative plan set lives in
> `.planning/phases/06-security-and-cryptography/` (outline + 06-01…06-04); this file is the
> grader-facing map of it.

## Components

| Component | Files | Plan |
|---|---|---|
| Crypto core | `security/{commit_pack,state_record,ledger}.py`, `shared/security_config.py`, `config/{police,thief}/security.json` | 06-01 |
| Four-phase wire protocol | `network/turn_commit.py` (+ wait sibling), `envelope.py`, `tools.py`, `agent_context.py`, `turn_actions.py`, `turn_language*.py`, `turn_resolve.py` | 06-02 |
| Step-0 + final audit | `security/{step0_collect,step0_sign,audit}.py`, `handshake_{wire,evaluate}.py`, `agent_entrypoint.py` (+ audit-wiring sibling), `verdict.py` | 06-03 |
| Gate evidence + PRD | `scripts/measure_gate6.py`, `GATE-6-MEASUREMENT.md`, `docs/PRD_commit_reveal.md` | 06-04 |

## Interfaces

- `commit_pack.build_commit_payload(*, state, move, intent, nonce) -> dict` — the **one**
  assembly point (D-59). `commit(state, move, intent) -> (h_commit, nonce)` generates the nonce
  internally (`secrets.token_hex(16)`) and hashes `canonical_json(payload)` with SHA-256.
  `verify_reveal(h_commit, *, state, move, intent, nonce) -> bool` rebuilds through the same
  builder and compares with `digests_match` (`secrets.compare_digest`).
- The hashed `move` is the **composite action dict**
  `{"move": {kind, direction}, "barrier": {kind, direction} | None}` — direction tokens only,
  never a coordinate (rule 27 / D-53); `barrier` is always `None` for the thief (D-59/D-66).
- `state_record.build_state_record(...)` — exactly `{game_id, turn, role, position:{row,col},
  barriers_remaining}` (D-60): the committer's own view, per §5.3.1 an anti-replay binding.
  Content is per-committer; only the canonical-JSON **recipe** is shared.
- `turn_commit.initiate / await_and_respond / reveal_pending` — the both-locked exchange
  (D-58). Neither side reveals before it holds the opponent's COMMIT.
- `step0_sign.sign_declaration(declaration, *, secret)` — always SHA-256-digested, additionally
  HMAC-SHA256-signed when the Phase-5 shared secret exists; no secret ⇒ explicit
  `signed: false`, never a silently-assumed verification (D-62).
- `audit.audit_peer_records(observed_commits, observed_reveals, peer_records)` — three checks
  per turn: commitment observed, re-hash matches, **and** the revealed action equals the action
  actually played in-game (D-67).

## Wave graph

```
w1: 06-01  (crypto core — standalone, no wiring)
      |
w2: 06-02  (four-phase wire protocol + barriers on the wire)
      |
w3: 06-03  (Step-0 declaration + Final-Reveal mutual audit)
      |
w4: 06-04  (gate measurement + per-mechanism PRD + graph refresh)
```

## Test plan

- Every suite stays offline: no live network, no opponent, no API key. The two-peer proofs
  reuse `tests/integration/two_peer_game.py` (the harness 04-12 built), never a second runner.
- The commit→reveal→audit round-trip is proven in **one** test, not two isolated unit halves —
  the canonical-JSON drift failure mode only appears when both ends run together.
- `security.commit_reveal=false` is proven byte-equivalent to the pre-Phase-6 wire, so the
  toggle isolates lower layers without changing them.
- Existing Phase 2–5 tests pass unmodified, with two deliberate exceptions: `test_gate4.py` and
  `test_language_pipeline.py` read the action off the wire log and must handle the new envelope
  **type and payload shape**. Their invariants (intent committed before hint text; no numeric
  coordinate in any outgoing action payload) are preserved and re-applied at the correct depth —
  never relaxed.

## Phase ADRs

D-58 (no new State members; the both-locked reveal gate lives in the message exchange) ·
D-59 (one payload-builder, one canonical serializer, composite action dict) · D-60 (the fixed
state-record field set) · D-61 (shared `game_id` negotiated at handshake) · D-62 (Step-0 digest
always, HMAC when a pre-supplied key exists) · D-63 (auto-collect the full §5.5 field set,
non-blocking) · D-64 (nonce ledger separate from the wire-mirroring log) · D-65
(`security.json` byte-identical; prior locks not re-audited) · D-66 (barriers travel inside the
committed action) · D-67 (the audit cross-checks revealed-vs-played). Authoritative text:
[06-PLAN-OUTLINE.md §1](../../../.planning/phases/06-security-and-cryptography/06-PLAN-OUTLINE.md).

## Risks

- **Canonical-JSON drift** between the commit site and the audit site is the single most likely
  cause of a false mismatch — and a mismatch is a loss (rule 19). Mitigated structurally by
  D-59's single builder plus a round-trip test that exercises both ends together.
- **Nonce leakage** into the wire-mirroring JSONL would be a rule-18 disqualification.
  Mitigated by a separate ledger file (D-64) and an explicit absence assertion in the two-peer
  test.
- **Line-limit pressure**: `turn_actions.py` (148/150), `orchestrator.py`, `agent_lifecycle.py`
  and `agent_wiring.py` were all at or near the ceiling before this phase. Splits are
  pre-authorized in the plans (`agent_context.py`, `turn_commit*`, the audit-wiring sibling)
  rather than improvised under the pre-commit gate.
- **Protocol deadlock** is the failure mode a both-locked gate invites. The exchange trace is
  written out in 06-02 and re-derived independently during plan verification; the responder's
  own buffer fill stays at reveal time so a game-ending resolution can never strand its
  outstanding REVEAL.
