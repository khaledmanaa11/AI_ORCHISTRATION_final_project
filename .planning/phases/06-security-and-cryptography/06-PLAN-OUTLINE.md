# Phase 6 Plan Outline — Security and Cryptography

**Phase:** `06-security-and-cryptography` · **Written:** 2026-08-09 · **Plans:** 06-01 … 06-04
**Context:** [`06-CONTEXT.md`](06-CONTEXT.md) · **Research:** [`06-RESEARCH.md`](06-RESEARCH.md)
**Requirements:** SEC-01 … SEC-08
**Gate:** §10.4 milestone 6 — *(1) a move is committed (SHA-256) then revealed with a valid
nonce, the four phases running Commit → Acknowledge → Reveal → Final Reveal/Audit; (2) the hash
covers canonical-JSON `{state, move, intent, nonce}`, the nonce (`secrets.token_hex(16)`) stays
secret until game end, any mismatch is a technical loss; (3) the Step-0 hardware declaration
(incl. exact commit hash) is verified before the first move.*

**All plans are subject to the standing gates, not restated per plan:** `ruff check` → 0 ·
`pytest --cov` ≥ 85% · every file ≤ 150 code lines · `uv` only · zero invented numbers ·
zero secrets in source · tests offline (no live network, no real opponent).

This phase is **integration, not new cryptography**: every primitive is stdlib
(`hashlib`/`secrets`/`hmac`/`json`) and every canonicalisation/comparison idiom already ships
(`config_hash.canonical_json`, `digests_match`). Phases 2/4/5 reserved the exact seams:
`MessageType` additive members (02-02), the handshake digest slot (04-02 — `handshake.py`'s
docstring names Step-0 as its next user), and the `TechnicalWin` pathway (02-07).
Book source verified directly this session: §5.2–§5.6, book pp. 32–40 (PDF 48–56).

## 1. Decisions — D-58 … D-65

New this phase, resolved from `06-RESEARCH.md` + the book under the autonomy directive. The
CONTEXT decisions (auto-collect Step-0, auto-declare audit verdicts + symmetric honesty,
`commit_reveal` toggle default ON, persisted local ledger) are locked and not re-derived.
Three CONTEXT corrections are binding (RESEARCH §Corrections): the `state` question is resolved
by the book, the Step-0 field list is extended to the full §5.5 set, and the sanity review is
non-blocking.

| ID | Decision | Source |
|----|----------|--------|
| **D-58** | **No new state-machine members; the both-locked reveal gate lives in the message exchange.** Commit/Ack/Reveal are a message-level sub-protocol inside the existing `MY_TURN`/`WAIT_OPPONENT` states. §5.3.2's guarantee — *reveal only when BOTH sides have locked their moves* — is enforced by the exchange order, not a new state: the turn initiator sends COMMIT and reveals only after it holds the opponent's ACK **and** the opponent's own COMMIT; the responder, upon receiving the initiator's COMMIT in its wait phase, decides its own move **then**, commits it, sends its COMMIT + ACK, and only later (in its own take phase) reveals. Per-turn pending commitment state lives in a small mutable holder on `AgentContext`, cleared at resolution. A missing ACK/COMMIT/REVEAL rides `call_with_retry`'s existing NetworkParams ladder into the existing `TechnicalWin(OPPONENT_UNRESPONSIVE)` path. Late/duplicate COMMIT/ACK messages are tolerated (drop/overwrite) exactly per 04-12's jitter lesson — only liveness caps raise. The pinned 6-member transition table does not change. A side effect, embraced: the responder now decides before seeing the initiator's current-turn reveal or hint — strictly closer to §6.4 blindness than today's flow. | Book §5.3.2 (verified in PDF), RESEARCH §Open-1, 04-12 |
| **D-59** | **One payload-builder for the commit hash.** A single `build_commit_payload()` produces the canonical `{"state","move","intent","nonce"}` dict used at Commit, at ledger-write, and at Audit re-hash — never rebuilt ad hoc. It serializes via `config_hash.canonical_json()` (QUAL-02, 3rd reuse), takes `move` as the **composite action dict** `{"move": move_payload.encode(...MOVE), "barrier": move_payload.encode(...BARRIER) | None}` (rule 27 / D-53 — direction tokens only, never a coordinate; barrier `None` always for the thief), and `intent` as `pursuit.shared.deception_types.Intent`'s value (the same flag Phase 4 commits in advance — no second truth/lie type). `H_commit = sha256(canonical_json(payload).encode("utf-8")).hexdigest()`. Verification uses `digests_match` (`secrets.compare_digest`). | Book §5.3.1 ("Move — the chosen physical action: movement, barrier placement, and the like"), RESEARCH §Don't-Hand-Roll, Pitfalls 2–3 |
| **D-66** | **Barrier placement goes over the wire inside the committed action — SEC-07's substance.** `turn_actions.py`/`turn_resolve.py`'s own docstrings defer "barrier placement over the wire" to Phase 6, and today the live pipeline provably discards the cop brain's `Decision.barrier` (`turn_language.py:81` takes `.move` only) — live P2P games are barrier-less, which cripples the cop (cop-win ⟺ forcing the thief's region into a forest). Phase 6 closes it: the decision surface returns the full `Decision` (move + optional barrier), the committed/revealed payload carries the composite action dict (D-59), `record_action` gains an optional barrier and builds `CopAction(move, barrier)`, and the receiver validates the barrier with the already-shipped `move_payload.decode`/`is_legal(BARRIER)` branch (quota via `barrier_cells`). Toggle-off stays move-only — byte-equivalent to the pre-Phase-6 wire, exactly as before. The legacy `BARRIER` MessageType/`receive_barrier` tool stay as unused Phase-2 surface. | turn_actions.py:14-15 + turn_resolve.py:20-22 docstrings, SEC-07, rules 15–16 |
| **D-67** | **The final audit cross-checks the revealed payload against what was actually played.** Hash-verifying the final-revealed `{state,move,intent,nonce}` against `H_commit` alone is bypassable: commit honestly to X, play Y in the in-game REVEAL, present X at final reveal — hash matches, forgery survives. The audit therefore verifies, per turn: (1) the re-hash matches the committed `H_commit` we observed, **and** (2) the revealed payload's composite action dict equals the action in that turn's in-game REVEAL envelope as recorded in our own wire log, **and** (3) turn keying is consistent (payload state's turn = record turn = observed turn). Move-match per turn transitively pins the whole trajectory (our engine derives their positions from their actions), so no deeper position cross-check is needed. Any failed check = `AUDIT_HASH_MISMATCH` = technical loss (rule 19). | Book §5.4, SEC-05, rule 19 |
| **D-60** | **State record = the committer's own local view, fixed fields:** `{game_id, turn, role, position: {row, col}, barriers_remaining}`. Per §5.3.1 the content is per-committer (anti-replay binding to a specific step) — peers share the RECIPE, not each other's contents. It stays inside the opaque hash during play and crosses the wire only inside FINAL_REVEAL after game end — consistent with rule 27 and D-48 (no coordinates in live protocol; disclosure only once the outcome is fixed). | Book §5.3.1/§5.4, RULES-RESOLUTION-LANG D-48 |
| **D-61** | **Shared `game_id` negotiated at handshake.** The handshake initiator proposes its `game_uid`; both peers adopt it as the game's `game_id`, naming `declaration_<game_id>.json`, the ledger file, and (Phase 7) the four report artifacts. Closes the researcher's gap: today each process invents its own `game_uid` with no cross-peer agreement. | RESEARCH §11, PARAMETERS artifact naming |
| **D-62** | **Step-0 signing = digest always, HMAC when the pre-supplied key exists.** The declaration is canonical-JSON hashed (SHA-256) always; additionally HMAC-SHA256-signed with the Phase-5 shared tunnel secret (`resolve_shared_secret`) — the book's "pre-supplied key" — when present. Absent secret (local/CI) ⇒ explicit `signed: false`, never silently treated as verified. Exchange + verification ride the handshake third-digest seam (SCENT_DIGEST precedent); a mismatch or missing declaration aborts before move 1 via a new `HandshakeOutcome` member. | Book §5.5, RESEARCH §8–9, Open-2 |
| **D-63** | **Step-0 auto-collect, full §5.5 field set, non-blocking.** `platform` + `psutil` (`uv add psutil`) for OS/CPU/RAM; GPU best-effort (`nvidia-smi` subprocess) with an honest `"not detected"` — never fabricated; LLM name read from the agent's existing `language.json`; code version from `version.py`; team code `khm-mn17` from `security.json`; games-played-so-far from a persisted counter file (rule 37 — incremented at game end, never hand-edited); exact commit hash via `git rev-parse HEAD` (rules 24/53). Sanity display is a log/print line — never `input()` (league runs unattended). | Book §5.5, RESEARCH §12, CONTEXT corr. b/c |
| **D-64** | **Nonce ledger = separate durable file, nonce never on the wire-mirroring log.** Per-turn append of `{turn, h_commit, payload}` to `<game_id>.ledger.jsonl` beside the event log, with `append_event`'s validate→serialize→write→flush→`os.fsync` durability. The wire-mirroring JSONL carries `h_commit` only until game end (rule 18). The ledger itself never crosses the wire — only its per-turn records travel inside FINAL_REVEAL at game end. | CONTEXT (locked), RESEARCH Pitfall 1 |
| **D-65** | **`security.json` byte-identical in both config dirs; prior locks are not re-audited.** Carries `commit_reveal` (default `true`) + `team_code` — same team, both agents, so byte-identity holds (rule 11). The Phase-4 scent digest is already locked at handshake (no audit re-check); the Phase-5 secret header is transport-layer only — Step-0 records its *presence* as metadata, never the value, and it is never a per-turn hash input. | RESEARCH §9–10, Open-4 |

**Not in scope:** emailing the declaration/reports (Phase 7 — Phase 6 writes the artifacts and
verdicts), the replay viewer (Phase 7, but consumes this phase's log shape), repo split/league
play (Phase 8), any change to the frozen 4-key `Envelope` shape, any change to Phase-3 strategy
or Phase-4 language behavior when `commit_reveal` is toggled off.

## 2. Numbers — all sourced, none invented

| Value | Number | Status | Source |
|---|---|---|---|
| Hash algorithm | SHA-256 | fixed | Book §5.3, rule 17, SEC-01 |
| Nonce size | `secrets.token_hex(16)` | fixed | Book §5.3.1, rule 18, SEC-04 |
| Canonical JSON | `sort_keys=True, separators=(",",":")` | fixed | Book §5.3.1, SEC-03 (shipped `canonical_json`) |
| Ack/commit wait, retries, backoff | `NetworkParams` (30 s / 3 / 5 s) | reused | Table 19 rows already in `network.json` (D-17 precedent) |
| Intent values | `truth` / `lie` | fixed | Book §5.3.1 (shipped `deception_types.Intent`) |
| Games-played counter start | 0 | structural | Rule 37 (a count, not a parameter) |

`security.json` introduces **no number** beyond the boolean toggle; every other key is a string.

## 3. Where the code goes

```
src/pursuit/security/            NEW package — imports sdk/shared only, never pursuit.network
  commit_pack.py                 build_commit_payload / commit / verify_reveal (D-59)   (06-01)
  state_record.py                build_state_record — D-60 field set                    (06-01)
  ledger.py                      CommitLedger append/read, fsync durability (D-64)      (06-01)
  step0_collect.py               declaration auto-collect (D-63)                        (06-03)
  step0_sign.py                  digest + HMAC sign/verify (D-62)                       (06-03)
  audit.py                       final-audit re-hash + verdict/evidence records         (06-03)

src/pursuit/shared/
  security_config.py             SecurityKey + SecurityParams + load_security_config
                                 (*Key-beside-loader convention)                        (06-01)

config/{police,thief}/
  security.json                  commit_reveal + team_code — byte-identical pair (D-65) (06-01)

src/pursuit/network/
  envelope.py                    + MessageType COMMIT / ACK / REVEAL / FINAL_REVEAL     (06-02)
  tools.py (or split sibling)    + 4 tool handlers via the existing _accept pattern     (06-02)
  turn_commit.py                 NEW sibling: the D-58 both-locked exchange (initiator
                                 and responder paths) — turn_actions.py is at 168 raw
                                 lines, do NOT grow it inline                          (06-02)
  turn_language.py               choose surface widened to return the full Decision
                                 (move + barrier) — today `.move` discards the barrier (06-02)
  turn_resolve.py                record_action gains optional barrier → CopAction(D-66) (06-02)
  handshake_* / agent_lifecycle  third digest (Step-0) + game_id adoption (D-61/D-62);
                                 lifecycle wiring via sibling module if line pressure   (06-03)
  verdict.py                     + TechnicalWinReason.AUDIT_HASH_MISMATCH               (06-03)
  event_log.py                   + EventType member(s) for commit/audit records         (06-02)

scripts/
  measure_gate6.py               localhost two-peer GATE-6 measurement (no env needed)  (06-04)

docs/
  PRD_commit_reveal.md           per-mechanism PRD (task 06-04)                         (06-04)
  phases/phase-6/GATE-6-MEASUREMENT.md  criteria verbatim + measured evidence           (06-04)
```

## 4. Plans and waves

| Plan | Delivers | Wave | Depends on |
|---|---|---|---|
| **06-01** | Crypto core — `security/` package (commit_pack, state_record, ledger), `security_config.py`, `security.json` pair. Unit tests incl. the one-test commit→reveal→audit round-trip (D-59), bool-corruption guard, ledger durability + nonce isolation | 1 | — |
| **06-02** | Four-phase wire protocol — MessageType members, tool handlers, `turn_commit.py`'s D-58 both-locked exchange (initiator + responder paths, jitter tolerance), barrier-over-the-wire inside the committed action (D-66, SEC-07), toggle-off bypass proven byte-equivalent, two-peer integration tests (incl. a forced cop barrier round-trip and the reveal-after-opponent-commit log-ordering assertion) | 2 | 06-01 |
| **06-03** | Step-0 + final audit — `uv add psutil`, step0 collect/sign, handshake third digest + `game_id` adoption + abort tests (SCENT_MISMATCH template), FINAL_REVEAL exchange at game end, audit verdicts through the `TechnicalWin` pathway (incl. symmetric honesty about our own mismatch), games-played counter, `declaration_<game_id>.json` | 3 | 06-02 |
| **06-04** | Gate + docs — `measure_gate6.py` (fully scriptable, localhost, zero env vars), tamper-harness proof (a forged reveal ⇒ `AUDIT_HASH_MISMATCH` technical loss), `GATE-6-MEASUREMENT.md`, `docs/PRD_commit_reveal.md`, graph refresh (06-96) | 4 | 06-03 |

Tracker rows 06-96/06-97/06-99 stay ROADMAP bookkeeping (graph refresh at plan+execute, phase
triplet, verify-work ticking) — not separate PLAN files, same as Phase 5.

## 5. Gate coverage

| §10.4 criterion | Proven by |
|---|---|
| 1 — four phases run, commit then reveal with valid nonce | 06-02 integration test; 06-04 measurement |
| 2 — canonical `{state,move,intent,nonce}`, nonce secret till end, mismatch = technical loss | 06-01 round-trip + wire-log nonce-absence test (06-02); 06-04 tamper proof |
| 3 — Step-0 (incl. exact commit hash) verified before move 1 | 06-03 handshake tests; 06-04 measurement |

GATE-6 needs **no credentials, no env vars, no second machine** — the whole gate runs as a
localhost two-process game.
