# PRD — Commit-Reveal Protocol (Cryptographic Security Layer)

**Version:** 1.00 · **Status:** approved · **Updated:** 2026-08-09

> Per-mechanism PRD required by CLAUDE.md and [SEGAL_GUIDELINES.md](SEGAL_GUIDELINES.md) §2.3,
> written after the code it describes (Phase 6 was implemented in four waves — 06-01..06-04 —
> under the project's autonomy directive; this document is the retrospective per-mechanism PRD
> §2.3 requires, mirroring [PRD_mcp_transport.md](PRD_mcp_transport.md)'s own section order
> exactly). Inherits the project [PRD.md](PRD.md); covers only the security/cryptography layer
> delivered in Phase 6. Every number is either traced to
> [`.planning/phases/06-security-and-cryptography/06-PLAN-OUTLINE.md`](../.planning/phases/06-security-and-cryptography/06-PLAN-OUTLINE.md)
> §2 or labelled a structural/engineering default — nothing here is invented.

## 1. Mechanism and scope

The commit-reveal layer makes every move provable after the fact: each side commits to a
SHA-256 hash of its intended action before either side can see the other's choice, then reveals
the action once both commitments are locked, and finally both sides cross-check every revealed
action against a durable local ledger at game end (SEC-08's mutual audit, rule 36). A Step-0
hardware declaration is exchanged and content-verified at handshake, before move 1, so the
league can trust who (and what hardware/commit hash) actually played.

**Requirements covered:**

| REQ-ID | Description |
|--------|-------------|
| SEC-01 | Moves use a commit-reveal protocol based on SHA-256 (rule 17) |
| SEC-02 | Four phases — Commit (hash) → Acknowledge → Reveal (move + hint, nonce hidden) → Final Reveal / Audit |
| SEC-03 | The hash covers `{state, move, intent, nonce}` serialized as canonical JSON (`sort_keys=True, separators=(",",":")`) |
| SEC-04 | The nonce is generated with `secrets.token_hex(16)`, kept secret until game end, verified with `secrets.compare_digest` |
| SEC-05 | Any hash mismatch at audit is a technical loss — score 0 to the forging team (rule 19) |
| SEC-06 | A signed Step-0 hardware declaration (OS/CPU/RAM/GPU/model/commit hash) is published before the first move (rules 24, 53) |
| SEC-07 | Barrier and capture declarations are open and truthful; false barrier/capture declarations are forbidden (rules 15–16, 21–22) |
| SEC-08 | A comprehensive mutual log audit runs at the end of every game (rule 36) |

**In scope (Phase 6):** the four-phase Commit→Acknowledge→Reveal→Final-Reveal/Audit exchange
(D-58), the canonical commit-hash recipe and per-turn nonce ledger (D-59/D-64), barrier
placement travelling inside the committed action (D-66, closing a pre-Phase-6 gap where the
live wire was barrier-less), the Step-0 hardware declaration — auto-collected, signed, and
exchanged at handshake with genuine content verification (D-62/D-63), and the Final-Reveal
mutual audit that cross-checks revealed actions against what was actually observed played,
including the rule-36 coverage check that closes the empty-`{"records": []}` evasion.

**Out of scope, each phrased as a future-phase extension, not a Phase-6 deliverable:** emailing
the declaration/reports (Phase 7 — Phase 6 only writes the artifacts and verdicts to disk).
The replay viewer (Phase 7, but consumes this phase's JSONL/ledger shape unchanged). Repo
split/league play (Phase 8). Any change to the frozen four-key `Envelope` shape (D-06, Phase 2)
— every new wire kind here is an additive `MessageType` member, never a reshape. Any change to
Phase-3 strategy or Phase-4 language behavior when `commit_reveal` is toggled off (the
toggle-off path is proven byte-equivalent to the pre-Phase-6 wire, 06-02).

## 2. Topology and design (D-58, D-59, D-64, D-66, D-67)

### 2.1 The four phases, and the initiator/responder asymmetry

```
police (fixed first-mover, book §6.4 / design note 7)     thief (responds, decides blind)
        │                                                          │
        ├─ commit + ledger-append (local) ───────────────────────► │
        ├─ COMMIT (h_commit) ───────────────────────────────────►  │  receives police's COMMIT,
        │                                                          │  THEN decides its own move
        │                                                          │  (still hasn't seen police's
        │                                                          │  reveal — closer to §6.4
        │                                                          │  blindness than a pre-Phase-6
        │                                                          │  flow), commits + ledger-appends
        │  ◄────────────────────────────────── COMMIT (h_commit) ─┤
        ├─ ACK (h_commit) ───────────────────────────────────────► │
        │  ◄──────────────────────────────────────────────── ACK ─┤
        ├─ REVEAL ({move, barrier, — nonce stays local}) ────────► │
        │  ◄─────────────────────────── REVEAL ({move, barrier}) ─┤
        │                     ... every turn, until GAME_OVER ...
        ├─ FINAL_REVEAL ({records: [ledger entries]}) ───────────► │
        │  ◄─────────────────────── FINAL_REVEAL ({records: [...]}) ┤
        └─ mutual audit (both directions) → outcome, possibly TECHNICAL_LOSS
```

**No new state-machine member exists for this (D-58).** The both-locked guarantee — reveal only
once BOTH sides have locked their moves — is enforced by the *message exchange order* inside the
existing `MY_TURN`/`WAIT_OPPONENT` states, not a new `State` enum value; the pinned six-state
transition table (Phase 2) is unchanged. Police, the fixed first-mover, already committed and
revealed its own action inside its own `initiate()` call by the time its own
`await_opponent_turn` runs, so it only *waits* for the opponent's REVEAL that turn — it never
decides a second time. Thief runs the full decide-now flow triggered by receiving police's
COMMIT. A missing ACK/COMMIT/REVEAL rides the existing `call_with_retry`/`NetworkParams` ladder
(D-17, no new number) into the existing `TechnicalWin(OPPONENT_UNRESPONSIVE)` path — late or
duplicate COMMIT/ACK messages are tolerated (dropped/overwritten), only the liveness cap raises.

### 2.2 The composite action dict and the barrier (D-59, D-66, SEC-07)

Every committed/revealed `move` is a composite dict, never a bare coordinate:

```json
{"move": {"kind": "move", "direction": "<DirectionWord>"},
 "barrier": {"kind": "barrier", "direction": "<DirectionWord>"} | null}
```

`move` is always present (a real step, or a "stay" token when a barrier is placed instead —
mirroring `CopAction.destination()`'s own semantics); `barrier` is present only on a turn the
cop actually places one, and is always `null` for the thief. This closes a real pre-Phase-6 gap:
`turn_language.py` provably discarded the cop brain's `Decision.barrier` before this phase, so
the live P2P wire was barrier-less. The composite dict crosses the wire only inside REVEAL;
COMMIT carries `h_commit` alone.

### 2.3 The hash recipe (D-59, SEC-01/03/04)

One function builds the hashed payload everywhere it is needed — at Commit, at ledger-write, and
at Audit re-hash — never rebuilt ad hoc:

```
payload = {"state": <D-60 state record>, "move": <composite action dict>,
           "intent": "truth" | "lie", "nonce": <64 hex chars>}
H_commit = sha256(canonical_json(payload).encode("utf-8")).hexdigest()
canonical_json(obj) = json.dumps(obj, sort_keys=True, separators=(",", ":"))
```

`canonical_json`/`digests_match` (`secrets.compare_digest`) are reused from
`pursuit.network.config_hash` — the SAME canonicalisation this project already locked for the
Phase-2 config digest and the Phase-4 scent digest (QUAL-02, one convention, not two). `nonce`
is always `secrets.token_hex(16)`, generated fresh inside `commit()` — never `random`, never
accepted as a caller-supplied argument for a new commitment. The **D-60 state record** carried
inside the hash is the committer's own local view only — `{game_id, turn, role,
position:{row,col}, barriers_remaining}` — per book §5.3.1's anti-replay binding to a specific
step; it stays inside the opaque hash during play and crosses the wire only inside FINAL_REVEAL.

### 2.4 The nonce ledger (D-64)

`CommitLedger` durably appends `{turn, h_commit, payload}` (the nonce lives *inside* `payload`)
to `<log-file-stem>.ledger.jsonl`, a sibling of the wire-mirroring event log, using the identical
validate→serialize→write→flush→`os.fsync` durability order `event_log.append_event` already
uses. The wire-mirroring JSONL never carries the string `"nonce"` until FINAL_REVEAL publishes
the ledger's own records at game end (rule 18) — verified directly in `measure_gate6.py`'s own
evidence, not merely asserted.

### 2.5 Step-0: auto-collected, signed, content-verified before move 1 (D-62, D-63, SEC-06)

`collect_declaration()` gathers the full book §5.5 field set automatically: role, team code, OS
(`platform`), CPU cores + frequency and RAM (`psutil`), GPU best-effort (`nvidia-smi`
subprocess, an honest `{"present": false, "detail": "not detected"}` on any failure — never a
fabricated GPU), the agent's own LLM model name, code version, games-played-so-far (a persisted,
crash-safe counter, rule 37), and the **exact commit hash** (`git rev-parse HEAD`, rule 53,
raising loudly on failure rather than shipping a blank hash).

**Signing is digest-always, HMAC-when-a-shared-secret-exists (D-62):** the declaration is
canonical-JSON SHA-256 hashed unconditionally; additionally HMAC-SHA256-signed with the Phase-5
shared tunnel secret when one is configured. An absent secret (every local/CI run) produces an
explicit `signed: false` — never silently treated as verified.

**Verification is two-layered, not a naive equality check.** The handshake payload carries the
declaration's digest (`STEP0_DIGEST`, presence required — a Step-0 declaration is inherently
per-agent, so two different roles' digests can never be expected to match, unlike the
Phase-2/4 config/scent digests which ARE deliberately byte-identical across both config dirs)
and, whenever the sending side opts in, the full declaration **content**
(`STEP0_DECLARATION` — book §5.5's declaration is meant to be *published*, so sending content is
strictly more faithful than a bare digest). The receiving side verifies the content against its
own claimed digest via `step0_sign.verify_declaration`; a digest-only peer (an opponent's own
implementation we cannot force to publish content) still agrees, logged as digest-only; a
declaration mutated *after* its digest was computed aborts before move 1 via
`HandshakeOutcome.STEP0_MISMATCH` — the state machine escalates to `State.ERROR` through the
SAME seam the Phase-2/4 config/scent mismatches already use, no new transition row.

### 2.6 The Final-Reveal mutual audit (D-67, SEC-05/08)

Hash-verifying a revealed `{state,move,intent,nonce}` payload against `H_commit` **alone** is
bypassable: commit honestly to X, play Y in the in-game REVEAL, present X again at final
reveal — the hash matches and the forgery survives. The audit therefore reuses the existing
`TechnicalWin`/`TechnicalWinReason` pathway (Phase 2, `AUDIT_HASH_MISMATCH` is an additive
member, never a second parallel verdict type) and runs, per turn, per claimed entry: (1) an
observed commit exists for that turn; (2) the re-hash matches the `H_commit` this side actually
observed at Commit time; (3) the revealed composite action dict equals the action this side
actually observed in that turn's in-game REVEAL — the check that closes the hash-only bypass
above. A turn with an observed commit but no observed reveal is a legitimately *trailing* turn
(the ledger append precedes the REVEAL send, so an honest peer's own abnormal-ending final
reveal can contain one) and is `matched=True`, never misbranded a forgery. A fourth,
coverage-level check (closing rule 36's own cheapest evasion) requires every turn this side
watched *fully exchanged* (committed AND revealed in-game) to actually appear in the peer's
FINAL_REVEAL at all — an opponent sending `{"records": []}` no longer passes vacuously. The
SAME function also audits this side's own ledger against what it actually sent — symmetric
honesty: a self-mismatch is reported with the identical label as an opponent mismatch, never
suppressed.

#### 2.6.1 The audit's evidence is keyed on local turn truth, never the peer's claim

Every check above joins the peer's claimed entries to this side's observed history **by turn
number**, so where that number comes from is itself a security property. It is **this side's
own turn**, stamped by `turn_commit_send.log_received` (`local_turn`) and by
`turn_actions.await_opponent_turn` (its pre-resolve `observed_turn`, captured before
`maybe_resolve` advances the counter) — never the inbound envelope's own `turn` field, which
the peer chooses.

That distinction is load-bearing. While the audit keyed on the peer's declared turn, an
opponent could stamp its COMMIT and REVEAL envelopes with **disjoint** turn numbers and thereby
(1) empty the coverage check's "fully exchanged" intersection, so `{"records": []}` passed
vacuously once more, and (2) route every claimed entry into the trailing-turn exemption, so
check 3 never ran at all. One relabelled integer disabled both defences; the cheapest variant
stamped every envelope `turn=0`, so a single valid record satisfied an entire game's audit and
every other nonce stayed secret.

The peer's claimed turn is still stored verbatim inside the logged envelope — the fix removes
the adversary from the join key without discarding what the adversary said. This also fails
closed in the other direction: a peer publishing its FINAL_REVEAL records under skewed turn
numbers finds them absent from `observed_commits` (check 1 fails) while the real turns go
unreported (the coverage check names them).

An in-game *rejection* of a disagreeing turn stamp was considered and deliberately **not**
added: keying on local truth already closes both paths, and rejecting on a turn-stamp
disagreement risks a false accusation — the same trap as comparing two roles' Step-0 digests
for equality (§2.5), and a rules-16/22 hazard.

#### 2.6.2 A caught mismatch is durable

`run_turn_loop` writes the game's `game_over` record — the only event carrying an `outcome`
field — *before* the audit runs. On a mismatch, `record_audit_verdict` therefore appends a
**corrected** `game_over` carrying `technical_loss`, so the last outcome-bearing record is the
audited one; the earlier record is left in place, because the log is append-only evidence and
the pre-audit board result is a real fact about the game. The process exit code follows the
same outcome, so a caught cheat is visible without reading the JSONL at all.

## 3. Interfaces

Copied verbatim from the shipping SUMMARY files (06-01/06-02/06-03), not re-derived:

```python
# src/pursuit/security/commit_pack.py
def build_commit_payload(*, state: dict, move: dict, intent: str, nonce: str) -> dict: ...
def commit(state: dict, move: dict, intent: str) -> tuple[str, str]: ...          # (h_commit, nonce)
def verify_reveal(h_commit: str, *, state: dict, move: dict, intent: str, nonce: str) -> bool: ...

# src/pursuit/security/state_record.py
def build_state_record(
    *, game_id: str, turn: int, role: str,
    position: tuple[int, int], barriers_remaining: int,
) -> dict: ...

# src/pursuit/security/ledger.py
class CommitLedger:
    def __init__(self, path: Path | str) -> None: ...
    def append(self, *, turn: int, h_commit: str, payload: dict) -> None: ...
    def read_all(self) -> list[dict]: ...                                        # [] if no file yet

# src/pursuit/network/turn_commit.py
async def initiate(ctx, current, pre_cell, dest, barrier, plan) -> Outcome | None: ...
async def await_and_respond(ctx) -> tuple[Envelope | None, TechnicalWin | None]: ...
async def reveal_pending(ctx) -> Outcome | None: ...

# src/pursuit/security/step0_collect.py
def collect_declaration(
    *, role: str, team_code: str, llm_name: str, code_version: str, games_played: int,
) -> dict: ...
def read_games_played(path: Path | str) -> int: ...
def record_game_played(path: Path | str) -> None: ...

# src/pursuit/security/step0_sign.py
def digest_declaration(declaration: dict) -> str: ...
def sign_declaration(declaration: dict, *, secret: str | None) -> dict: ...       # {digest, signed, hmac}
def verify_declaration(
    declaration: dict, *, digest: str, hmac_value: str | None, secret: str | None,
) -> bool: ...

# src/pursuit/security/audit.py
@dataclass(frozen=True)
class AuditRecord:
    turn: int; matched: bool; detail: str

def audit_peer_records(
    observed_commits: dict[int, str], observed_reveals: dict[int, dict], peer_records: list[dict],
) -> list[AuditRecord]: ...
def all_matched(records: list[AuditRecord]) -> bool: ...

# src/pursuit/network/agent_audit_wiring.py
async def declare_step0(cfg: AgentConfig) -> tuple[str, dict]: ...                # (digest, envelope)
def write_declaration(ctx, cfg, result: HandshakeResult, declaration_envelope: dict) -> None: ...
async def run_final_audit(ctx: AgentContext) -> Outcome | None: ...               # None = clean
```

`run_agent` (`agent_entrypoint.py`) wires all of the above end to end and stays a thin caller:
Step-0 declare → sign → handshake (digest presence required, content verified when sent) →
persist ours + the peer's declaration → the commit-reveal turn loop → the Final-Reveal mutual
audit (when `security.commit_reveal` is on) → outcome, possibly overridden to
`Outcome.TECHNICAL_LOSS`.

## 4. Configuration (D-65)

`config/{police,thief}/security.json` is byte-identical (same team, both agents, rule 11):

```json
{"version": "1.00", "commit_reveal": true, "team_code": "khm-mn17"}
```

`commit_reveal` is the one protocol toggle; toggling it off reproduces the exact pre-Phase-6
wire (a single MOVE envelope per turn, byte-equivalent — proven in 06-02's own integration
test), so Phase-3 strategy and Phase-4 language behavior are provably unaffected either way.

## 5. Parameters and their sources

Every number this mechanism uses, traced to
[06-PLAN-OUTLINE.md §2](../.planning/phases/06-security-and-cryptography/06-PLAN-OUTLINE.md) —
none invented, none re-derived here:

| Parameter | Value | Status | Source |
|---|---|---|---|
| Hash algorithm | SHA-256 | fixed | Book §5.3, rule 17, SEC-01 |
| Nonce | `secrets.token_hex(16)` | fixed | Book §5.3.1, rule 18, SEC-04 |
| Canonical JSON | `sort_keys=True, separators=(",",":")` | fixed | Book §5.3.1, SEC-03 (reused `canonical_json`) |
| Ack/commit wait, retries, backoff | `NetworkParams` (30s / 3 / 5s) | reused | PARAMETERS.md Table 19 rows 3–4, 6 (D-17 precedent, no new number) |
| Intent values | `truth` / `lie` | fixed | Book §5.3.1 (shipped `deception_types.Intent`) |
| Games-played counter start | 0 | structural | Rule 37 (a count, not a game parameter) |

`security.json` introduces no number beyond the `commit_reveal` boolean; every other key is a
string. Ledger durability/backoff constants (`_COUNTER_RETRIES=3`/`_COUNTER_BACKOFF_SECONDS=0.1`
in `step0_collect.py`, mirroring `QTable.save()`'s own local durable-write precedent) are
structural engineering defaults, not PARAMETERS.md values, matching
[PRD_mcp_transport.md](PRD_mcp_transport.md) §10.2's own labelling discipline.

## 6. Acceptance criteria for this mechanism

Restated from the Phase-6 §10.4 milestone gate as observable checks, each measured (not merely
asserted) by `scripts/measure_gate6.py` — see
[`docs/phases/phase-6/GATE-6-MEASUREMENT.md`](phases/phase-6/GATE-6-MEASUREMENT.md) for the
measured evidence:

1. A move is committed (SHA-256) and then revealed with a valid nonce; the four phases run
   Commit → Acknowledge → Reveal → Final Reveal/Audit.
2. The hash covers canonical-JSON `{state, move, intent, nonce}`; the nonce stays secret until
   game end; any mismatch (including the hash-only-bypass case D-67 exists to close) is a
   technical loss.
3. The Step-0 hardware declaration (including the exact commit hash) is verified before the
   first move — a forged digest aborts the handshake before `State.MY_TURN` is ever reachable.

**OPEN:** None — every number this mechanism needs is either traced in §5 or labelled structural.
