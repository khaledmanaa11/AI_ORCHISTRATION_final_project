# Phase 6: Security and Cryptography - Research

**Researched:** 2026-08-09
**Domain:** Commit-reveal cryptography (stdlib), FastMCP message-type wiring, Step-0 declaration
**Confidence:** HIGH — all findings are direct file:line reads of this repo plus the book
extracts; no web research performed (hard constraint: crypto is stdlib, no library choice needed).

## Summary

Phase 6 has almost no new library surface — `hashlib`/`secrets`/`json` (stdlib, already used
identically in `config_hash.py`/`scent_config.py`) wired into infrastructure Phases 2-4
specifically built to receive it. The book fixes the crypto recipe completely; what's open is
**integration**: which new `MessageType`/`EventType`/`TechnicalWinReason` members, where
Commit/Ack wrap `take_my_turn`/`await_opponent_turn`, and how the end-game audit reuses the
existing `TechnicalWin`/`Outcome.TECHNICAL_LOSS` pathway instead of a parallel one.

**Primary recommendation:** Don't design a new subsystem — follow the seams Phases 2/4 already
reserved. `envelope.py`'s docstring: "Phase-6 commit-reveal data arrive later as NEW MessageType
members." `handshake.py`'s docstring: "Phase 6 later adds a Step-0 declaration to this same
handshake by extending the envelope payload — the shape does not change." The two real gaps with
no existing code: `psutil` (not in `pyproject.toml`) for Step-0 hardware facts, and a
`games-played-so-far` counter / cross-peer `game_id` agreement (neither exists anywhere yet).

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Step-0 (SEC-06)**: auto-collect + one non-blocking review. Code gathers OS/CPU/RAM/GPU
  (platform/psutil) + exact git commit hash automatically, writes `declaration_<game_id>.json`,
  shows it once for sanity, hash-signs, publishes at handshake. No hand-typed hardware specs.
- **Audit verdicts (SEC-05, SEC-08)**: auto-declare + evidence. A hash mismatch auto-declares the
  technical win, logs the exact mismatching hashes as evidence, feeds the game report. Unattended
  league play — no human in the loop. **Symmetric honesty**: our own hash failure is also
  reported truthfully, never suppressed.
- **Dev ergonomics**: `security.commit_reveal=true` default ON; tests/local debugging may flip
  off. League configs always ship ON.
- **Crash safety**: persisted local ledger, one append per commit/nonce per turn (Phase-2
  persist-every-turn precedent); never crosses the wire.

### Claude's Discretion
- Ledger file format/rotation; commit-pack layout inside the Phase-2 envelope (new types:
  commit/ack/reveal/final_reveal).
- How commit-reveal sub-states slot into the state machine.
- Folding the Phase-4 scent lock + Phase-5 shared-secret header into the audit trail.

### Deferred Ideas
None in scope. Emailing the audit is Phase 7's job; Phase 6 produces verdicts/artifacts only.

### Corrections to CONTEXT.md (orchestrator context_audit, binding)
a. The `state` open question is **resolved** — see Book Requirements §2. Don't re-open it.
b. Step-0 auto-collect list is **incomplete** vs §5.5 — also needs language-model name, code
   version (`version.py`), team name (`khm-mn17`), games-played-so-far count. "Signed" →
   recommend HMAC via the Phase-5 shared tunnel secret (`resolve_shared_secret`), stdlib `hmac`.
c. "Shows it once for sanity" must be non-blocking (print/log or config-gated) — never
   `input()`, or league games hang.

## Book Requirements (police_thief_p2p.pdf §5, book pp. 32-40 — locked, verbatim-in-substance)

1. **§5.3 — four phases, in order**: Commit → Acknowledge → Reveal → Final Reveal/Audit.
   - **Commit**: send ONLY `H_commit = SHA256(canonical_json({"state","move","intent","nonce"}))`
     — `json.dumps(payload, sort_keys=True, separators=(",",":"))`, UTF-8, hexdigest. Reference
     `commit(state, move, intent)` generates `nonce = secrets.token_hex(16)` internally, returns
     `(h_commit, nonce)`.
   - **Acknowledge**: opponent confirms receipt; both sides locked; reveal happens ONLY after
     both commits are locked (§5.3.2).
   - **Reveal**: send Move + verbal hint. Nonce STAYS HIDDEN.
   - **Final Reveal/Audit**: game end only — ALL nonces published, both sides exchange COMPLETE
     logs (§5.4), each re-hashes the opponent's revealed `{state,move,intent,nonce}` per turn vs
     the declared `H_commit`. ANY mismatch = technical loss for the forging side (rule 19, score
     0), regardless of board outcome.
2. **§5.3.1 — `state` (resolves CONTEXT.md's open question)**: the committer's OWN board-view the
   move was based on; purpose is anti-replay. Book's reference code "seals a richer record (hint,
   verdict, step, role, sub_game)". Audit recomputes from what the COMMITTER reveals — state
   CONTENT is per-committer; only the canonical-JSON RECIPE must be identical across peers.
3. **Intent**: mandatory `"truth"|"lie"` flag declared in advance inside the hash — prevents
   retroactively claiming "I was honestly lying".
4. **Nonce**: `secrets.token_hex(16)`, never `random`; verify with `secrets.compare_digest`;
   secret until game end (rule 18 — exposure = disqualification).
5. **§5.5 — Step-0** (before move 1): a signed declaration ("signed by means of a pre-supplied
   key") with: OS, CPU cores+frequency, RAM, GPU/VRAM presence+video memory, LLM name, code
   version, team name, games played so far (rule 37), exact git commit hash (rules 24, 53 —
   later `github_commit` in Phase 7's email). LLM token consumption also monitored/sealed.
   Sanction for skipping: loss of computational-fairness bonus (rule 24 — softer than 18/19).
6. **Rule text** (`docs/RULES.md`, verbatim): R17 commit-reveal mandatory ("illegal solution
   without it"); R18 nonce secret till end ("disqualification for dictionary-attack exposure");
   R19 any mismatch → score 0 ("the iron law"); R20 replay-verifying viewer app (Phase 7, but
   Phase 6's log shape is what it replays); R24 Step-0 crypto before game start ("loss of
   fairness bonus"); R36 mutual log audit every game end ("precondition before agreeing result");
   R37 declare games-played-so-far accurately each game start; R38 false games-played count →
   absolute disqualification; R53 Step-0 records the commit hash, updated every game.
7. **Requirements**: SEC-01..SEC-08 (`.planning/REQUIREMENTS.md:64-71`). Milestone gate
   (`.planning/ROADMAP.md:172-174`): (1) commit→reveal with valid nonce, all four phases run;
   (2) hash covers canonical `{state,move,intent,nonce}`, nonce secret till end, mismatch =
   technical loss; (3) Step-0 (incl. exact commit hash) verified before move 1.
8. Plan sketch already in ROADMAP (`:180-187`, hypothesis not lock): 06-01 hashing/nonce, 06-02
   four-phase protocol in orchestrator, 06-03 Step-0 + audit, 06-04 `docs/PRD_commit_reveal.md`.

## Integration Surface Map

**1. `envelope.py`** — `MessageType` (L20-32): `HANDSHAKE, MOVE, BARRIER, GAME_OVER, HINT`.
Docstring explicitly reserves this insertion: new members (`COMMIT, ACK, REVEAL, FINAL_REVEAL`),
zero change to the frozen 4-key `Envelope` shape. `from_dict` already rejects unknown types.

**2. `config_hash.py`** — `canonical_json()` (L25-33) is the ONE project-wide serializer
(`sort_keys=True, separators=(",",":")`); the commit hash MUST call it (3rd reuse after
`config_hash`/`scent_config`, QUAL-02). `digests_match()` (L48-59) wraps
`secrets.compare_digest` — reuse for nonce/hash verification. `compare_named_digest()`
(L62-82, returns `(matched, detail)`, `None`-remote = mismatch) is the pattern for any new
Step-0 digest comparison at handshake.

**3. `state_machine.py`** — `State` (L30-38): six members today
(`INIT,HANDSHAKE,MY_TURN,WAIT_OPPONENT,GAME_OVER,ERROR`); docstring reserves additive insertion
("new State members plus new rows/edges... never a signature change"). `ALLOWED_TRANSITIONS`
(L41-48) is a dict keyed by every `State` — a new member needs a row or `attempt()` raises
`KeyError`. `RECOVERABLE_ATTEMPTS` (L68-79) is a second explicit allow-list for benign
illegal pairs (retries/duplicates) — any new sub-state needs its own recoverable entries or
ordinary jitter escalates to game-ending `PROTOCOL_VIOLATION`.
Tests pinning the table (`tests/unit/test_state_machine.py`, 10 tests): only
`test_state_set_matches_d09` (L31-41, hard-codes the 6-name set) breaks on a new member — must
be updated, not a regression. `test_transition_table_covers_every_state` auto-passes once rows
exist. `test_every_legal_transition_is_applied` sweeps the table itself (self-updating). Net:
low breakage risk for pure additions.

**4. `turn_actions.py` + `orchestrator.py`** — `take_my_turn` (L46-116): decode hint → choose
dest → buffer/`maybe_resolve` → build MOVE envelope → `call_with_retry` push to `receive_move`
→ log `message_sent` → send hint → `attempt(WAIT_OPPONENT)`. `await_opponent_turn` (L119-168):
bounded wait via `turn_buffer.await_move` (drains a leading HINT) → decode/validate via
`move_payload` → buffer/`maybe_resolve` → log `message_received` → `attempt(MY_TURN)`.
Commit/Ack must wrap BEFORE the existing MOVE push: compute `state/move/intent/nonce` →
send COMMIT (hash only) → wait opponent ACK (and their COMMIT) → THEN the existing MOVE send
becomes/gates the REVEAL (nonce still hidden, kept in the local ledger until game end).
`run_turn_loop` (L130-168) already writes the terminal `game_over_record` — audit's
mismatch verdict should compute/override `Outcome` at or just before this point, not in a
parallel path. **150-line pressure**: `turn_actions.py` is 168 raw lines already — Commit/Ack
wiring needs a NEW sibling module (mirror the `turn_buffer.py`/`turn_resolve.py` split), not
inline growth.

**5. `tools.py`** — five `@mcp.tool` handlers today (`handshake, receive_move, receive_barrier,
game_over, receive_hint`, L89-123), each via shared `_accept()` (L48-72: decode→enqueue→ack).
Identical signatures by design. **New commit/ack/reveal/final_reveal messages need NO new
tools beyond this same pattern** — four new ~5-line tool functions each calling
`_accept(queue, MessageType.X, ...)`, exactly like `receive_hint`. `register_tools()`'s
signature is unchanged.

**6. `event_log.py`** — `EventType` (L33-41) has no commit/audit member yet; add one (e.g.
`AUDIT_MISMATCH`) or stuff specifics into the existing `details` forward-compat hook (the
`technical_win_record` precedent). `append_event()` (L108-129): validate→serialize (inline
`json.dumps(sort_keys=True,...)`, same params as `canonical_json` but NOT routed through it —
pre-existing, fine for storage formatting)→write→flush→`os.fsync`. The persisted nonce ledger
should follow this exact durability precedent. **The commit HASH input itself must go through
`canonical_json()` specifically**, not just "any sort_keys call" — that's the one function
QUAL-02 designates as canonical for hash inputs.

**7. `deadline.py`/`verdict.py`/TechnicalWin pathway** — `TechnicalWinReason` (verdict.py
L15-23) has one member, `OPPONENT_UNRESPONSIVE`. Add a distinct member (e.g.
`AUDIT_HASH_MISMATCH`) — conflating it with unresponsiveness misreports the cause (rules
16/22/38). The existing 3-step technical-loss pattern (used identically at `turn_actions.py:
91-102`, `:137-147`, `turn_buffer.py:84-98`): log evidence → `attempt(GAME_OVER)` → return
`Outcome.TECHNICAL_LOSS`. The audit verdict (which runs AFTER `GAME_OVER`, a terminal state
with no outgoing edges) must reuse this SAME pattern as a post-hoc evidence append + outcome
override, not a parallel "audit result" type the rest of the pipeline can't consume.
`call_with_retry` (L92-146) is the only retry ladder — reuse its NetworkParams-sourced
timeout/retries/backoff for the Ack wait; no new numeric parameter needed.

**8. `secret_wiring.py`** — `resolve_shared_secret(config_dir)` (L24-40): reads `tunnel.json`'s
`secret_env` name, resolves from `os.environ`, returns `(header, value)` or `None`. This is the
CONTEXT-recommended Step-0 HMAC key candidate. **Caveat**: `None` whenever `tunnel.json`/
`secret_env` is unset — i.e. every current local/CI test. Step-0 signing needs an explicit
fallback for that case (see Open Decisions).

**9. Phase-4 seams** — **Scent lock** (`scent_config.py:131-138 scent_digest`,
`handshake_wire.py:30-50 HandshakeKey.SCENT_DIGEST`, `handshake_evaluate.py:30-38
HandshakeOutcome.SCENT_MISMATCH`) is the exact precedent: add a second locked digest to the
same handshake payload, compare via `compare_named_digest`, abort to `State.ERROR` with a
distinct outcome member. `handshake.py`'s docstring names Step-0 as the explicit next user of
this seam. Test templates to mirror: `tests/unit/test_handshake_abort.py` (5 tests: mismatch
aborts before move 1, report names both digests without "accusing" language, responder replies
+ aborts symmetrically, malformed≠unreachable) and `test_handshake_scent.py`.
**Move codec** (`move_payload.py` L101-157): `encode()`/`decode()` turn a coordinate into
`{kind, direction}` (rule 27 compliant — `encode()` raises on non-orthogonal steps). The
commit's `move` field should be this SAME dict, not a re-derived coordinate.
**Discretion item** (folding scent lock + Phase-5 secret into audit): scent digest is already
in every handshake JSONL record (locked at handshake, no audit re-check needed); the
shared-secret header is transport-layer only (never inside the Envelope payload per
`secret_wiring.py`'s scope note) — record presence/absence as Step-0 metadata, never the
secret value, and never as a per-turn hash input.

**10. Config conventions** — Per-agent dirs `config/{police,thief}/`, 11 files each. **`*Key`
beside-loader convention** (`scent_config.py`/`tunnel_config.py` precedent, since
`pursuit.config_keys` is at its 150-line ceiling): a new `security.json` needs its own
`security_config.py` with `SecurityKey` enum + `load_security_config()` + frozen
`SecurityParams`, structured like `tunnel_config.py` (small, mostly-structural). Must be
byte-identical across both dirs (rule 11, like `game_params.json`) if it carries the
`commit_reveal` toggle/shared protocol params; team-identity fields legitimately differ (like
`network.json`, excluded from the config digest by design). Handshake digest exchange happens
at `agent_lifecycle.py:120-125 default_context` (`local_digest`/`local_scent_digest` built
there, handed to `make_handshake_responder`) — Step-0 verification wires in at this exact
construction site as a third digest.

**11. Game identity** — `game_uid` is generated per-PROCESS at `agent_lifecycle.py:113`
(`secrets.token_hex(8)`, no cross-peer agreement) — NOT the same as `docs/PARAMETERS.md`'s
`<game_id>` used in `declaration_<game_id>.json`/`config_<game_id>_g<NN>.json`/etc. (lines
120-131). **No existing code negotiates a shared game_id between peers.** Flag for planner:
Phase 6 (Step-0) is the natural place to reconcile this, since `declaration_<game_id>.json` is
explicitly Phase-6-era. Either agree `game_id` at/before handshake, or explicitly defer full
filename compliance to Phase 7/8 and use `game_uid` as interim — decide explicitly, don't leave
implicit. Role bridging (`police`/`thief` → SDK's `cop`/`thief`) is
`orchestrator.py:112-119 engine_agent()` — unrelated seam, just be aware of it for state-record
role fields.

**12. `version.py` / team code / `psutil`** — `version.py`: `VERSION = "1.00"`. Team code
`khm-mn17` (8 chars, rule 45) is decided (`.planning/STATE.md:664`,
`docs/KHALED_PERSONAL_PLAN.md:34`, `08-CONTEXT.md:28`) but wired into NO config file yet —
introduce it in Phase 6 (Step-0 needs it now), Phase 8 only confirms presence.
**`psutil` is NOT a dependency** (`pyproject.toml` deps: `anthropic, fastmcp, pyngrok`; dev
group: `matplotlib, pytest*, ruff` — zero psutil matches, checked directly). Recommend
`uv add psutil` for CPU/RAM; GPU has no stdlib/psutil path on Windows — best-effort
`nvidia-smi` subprocess with honest "not detected" fallback, never a fabricated value. `platform`
module covers OS name/version with no new dependency. No existing helper computes the git
commit hash — `subprocess.run(["git","rev-parse","HEAD"])` would be the first `subprocess`
caller in `src/pursuit/` (stdlib, but a new pattern, not a reused one).

**13. Test conventions** — `tests/integration/two_peer_game.py` (70 lines, not `test_*.py`,
uncollected): `play_two_peer_game(cfg_a, cfg_b, *, game_uid, log_dir, wire=None)` builds two
REAL `AgentContext`s, wires FastMCP servers in-memory (no socket), real handshake, runs both
`run_turn_loop`s via `asyncio.gather`. Reuse this directly for Phase-6 two-peer commit-reveal +
audit tests. 150-line limit applies to test files too (confirmed in `check_line_limit.sh`
scanning `tests/**/*.py`). `test_handshake_abort.py` is the template for a Step-0
declaration-mismatch test, including its house style of asserting the abort report doesn't use
"accusing" language.

**14. `docs/phases/phase-4/RULES-RESOLUTION-LANG.md`** (5-line summary) — Book contradiction:
§5.3.2 requires revealing Move every turn; §6.4 requires neither side ever learns the true
location. **D-48 resolution (binding, implemented)**: keep per-turn Reveal, but as a direction
TOKEN (never coordinate) — opponent's position is known one turn STALE, never current-turn at
commit time. Phase 6 is fully consistent with this: Commit/Ack happen BEFORE Reveal, at a point
where the current turn's move genuinely is unknown to the opponent — wrapping Commit→Ack→Reveal
around the existing Move send does not conflict with D-48.

**15. Gate measurement pattern** (`05-03-SUMMARY.md`) — Phase 5's pattern: quote §10.4 criteria
verbatim, mark PASS/PENDING honestly, no fabricated numbers. Confirmed nothing in shipped code
forces the tunnel on (`resolve_shared_secret`/`tunnel_wiring` both no-op when unset). **GATE-6
can run fully on localhost, two processes, no tunnel** — the SUMMARY itself states Phase 6
depends on Phase 5's CODE, not its pending gate measurement. Structure `GATE-6-MEASUREMENT.md`
the same way, with the localhost two-peer run as the fully-scriptable core.

## Open Decisions for the Planner

1. **State-machine insertion shape**: new top-level `State` sub-states for Commit/Ack/Reveal, or
   a sub-protocol INSIDE the existing `MY_TURN`/`WAIT_OPPONENT`? **Recommended**: keep the six
   `State` members unchanged; model a missed Ack as a `call_with_retry` deadline failure (existing
   `TechnicalWin` path), not a new terminal state. Minimizes blast radius on the pinned transition
   table; add new States only if a concrete illegal-transition case demands it.
2. **Step-0 signing key**: use Phase-5's `resolve_shared_secret` (`hmac.new`) when present (real
   league play always has it), but define an explicit fallback for the secret-absent local/CI
   case (e.g. `signed: false` field) — never silently treat "no secret" as "verified."
3. **`game_id` vs `game_uid`**: no cross-peer agreement exists today (each process generates its
   own `game_uid` independently). Recommended: negotiate a shared value at/before handshake and
   treat it as the project's `game_id` for artifact naming, rather than inventing a second ID.
4. **`security.json` shape**: `SecurityParams.commit_reveal: bool` (default `True`), new
   `security_config.py` module. Byte-identical across both config dirs (protocol toggle/hash
   recipe must be symmetric); team-identity fields may need a separate non-digest-checked file,
   following the `network.json`-excluded-from-digest precedent.
5. **`psutil` dependency**: `uv add psutil` for CPU/RAM; GPU best-effort with honest fallback.
6. **New `TechnicalWinReason` member**: `AUDIT_HASH_MISMATCH`, distinct from
   `OPPONENT_UNRESPONSIVE`, so evidence never misreports the failure mode.
7. **Ledger location/format**: mirror `logs/{role}/{game_uid}.jsonl` with a sibling file (e.g.
   `logs/{role}/{game_uid}.ledger.jsonl`), same validate→write→flush→fsync sequence as
   `append_event`. Nonce must never appear in the wire-mirroring turn log before game end.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| JSON canonicalisation for hashing | A second `json.dumps(sort_keys=True,...)` | `config_hash.canonical_json()` | QUAL-02; already reused by `scent_config.py` |
| Constant-time digest compare | `==` on hex strings | `config_hash.digests_match()` (`secrets.compare_digest`) | Project's one comparison idiom |
| Truth/lie flag type | A second truth/lie enum for commit's `intent` | `pursuit.shared.deception_types.Intent` (already used by `hint_payload.py`) | Commit's `intent` and the hint's `intent` are the same flag, declared once per §5.3.1/rule 25 |
| Move representation in the hash | Re-deriving a coordinate | `move_payload.encode()`'s `{kind, direction}` dict | Already rule-27-compliant, already the wire shape |
| Handshake extension | New envelope shape/tool for Step-0 | Extend HANDSHAKE payload with a 3rd digest key, mirroring `SCENT_DIGEST` | `handshake.py` reserves exactly this seam |
| Ack-wait retry/backoff | A new timeout constant | `NetworkParams` via `call_with_retry` | D-17: reuse Table 19 rows, never invent a number |
| Crash-safe ledger write | A bespoke write-then-rename scheme | `event_log.append_event()`'s pattern, or `shared/durable_write.py` for atomic-replace needs | Both exist and are tested |

## Common Pitfalls

**1. Nonce leaking into the wire-mirroring JSONL before game end.** The persisted ledger stores
the nonce per turn; if it's written into the SAME log that mirrors `message_sent`/
`message_received` (rather than a separate file), an early read/transmit of that log leaks the
nonce — rule 18 disqualification. Keep the nonce ledger in a separate file; never put an
unsent value into `turn_events.turn_record(..., envelope=...)`.

**2. Canonical-JSON drift between Commit-time hash and Audit-time re-hash.** Two call sites
(Commit, weeks-later Audit) reconstructing "the same" `{state,move,intent,nonce}` dict from
different intermediate representations (e.g. `move_payload.encode()`'s dict vs a
`ResolvedAction`) silently diverge even with `sort_keys=True` (which fixes key order, not type/
shape drift). Define ONE payload-building function, call it from both sites; test by hashing at
commit, reveal, and re-hashing at "audit" in the same test — not two isolated unit tests.

**3. `bool` is an `int` subtype — silent corruption of hashed fields.** This project already
guards this everywhere (`envelope.py:_require_non_bool_int`, `move_payload.py:120-122`,
`loader_helpers.py:88`). Validate `intent` as exactly `Intent.TRUTH.value`/`Intent.LIE.value`
(reuse `hint_payload.validate_hint_payload`) before hashing — a stray `bool` serializes
differently than the intended string and silently changes the hash.

**4. New `State` members breaking tests loudly vs silently.** `test_state_set_matches_d09`
fails loudly on a new member (safe). The dangerous case: a new `ALLOWED_TRANSITIONS` pair
without a matching `RECOVERABLE_ATTEMPTS` entry for legitimate retries (e.g. a re-delivered
ACK) silently turns network jitter into `PROTOCOL_VIOLATION` → game-ending `State.ERROR` —
exactly the bug class `RULES-RESOLUTION-LANG.md` §3 already hit once in Phase 4 hint-buffering
(only a real two-peer concurrent run caught it, not unit tests). If new States are added, write
the `two_peer_game.py`-based concurrent test first.

**5. 150-line splits to anticipate.** `turn_actions.py` (168 raw lines), `turn_buffer.py` (168),
`state_machine.py` (181), `agent_lifecycle.py` (174), `orchestrator.py` (182) are all near/at
the ceiling already — Phase-6 wiring into any of these should be planned as a new sibling
module + re-export from day one (mirror the `handshake.py`/`handshake_wire.py`/
`handshake_evaluate.py` split, or the `orchestrator.py`/`turn_actions.py` PEP-562 lazy
re-export). `event_log.py` needs only a new `EventType` member — no split expected.

**6. Step-0 blocking unattended league play.** "Shows it once for sanity" must not become an
`input()` prompt — league games run unattended (same reasoning as the audit's own
auto-declare decision). Implement as a non-blocking print/log line.

## Metadata

**Confidence breakdown:**
- Book requirements: HIGH — orchestrator-supplied locked findings, cross-checked verbatim
  against `docs/RULES.md` and `.planning/REQUIREMENTS.md`.
- Integration surface: HIGH — every file:line read directly this session.
- Open decisions: MEDIUM — genuine judgment calls with no single locked answer; recommendations
  reasoned from existing patterns, not independently verified.
- Pitfalls: HIGH for items 1-4 (directly observed in code/tests/docs, including one real prior
  incident); MEDIUM for item 5 (raw `wc -l`, not exact code-line count — directional only).

**Research date:** 2026-08-09. **Valid until:** stable (fixed-protocol, stdlib-only phase);
re-verify only if planning is deferred past further Phase 7/8 edits to these same files.

## RESEARCH COMPLETE

**Phase:** 6 - Security and Cryptography
**Confidence:** HIGH

### Key Findings
- Every crypto primitive is already used correctly elsewhere (`canonical_json`,
  `digests_match`/`secrets.compare_digest`, `secrets.token_hex`) — this phase is integration,
  not new cryptography.
- Three explicit extension seams were pre-built: `envelope.py`'s `MessageType`,
  `state_machine.py`'s `State`/`ALLOWED_TRANSITIONS`, and `handshake.py`'s payload (docstring
  literally names Step-0 as its next user).
- The audit-mismatch verdict must reuse the existing `TechnicalWin`/`Outcome.TECHNICAL_LOSS`
  pathway (new `TechnicalWinReason` member), not a parallel result type.
- Two genuine gaps: `psutil` is not a dependency (Step-0 hardware facts need `uv add psutil` +
  best-effort GPU fallback); no cross-peer `game_id` agreement mechanism exists anywhere.
- Commit's `intent` field should reuse the existing `pursuit.shared.deception_types.Intent`
  enum already used by `hint_payload.py`, not a second truth/lie type.

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | stdlib only, all proven in this repo already |
| Architecture | HIGH | every seam directly read from source, three pre-documented by prior phases |
| Pitfalls | HIGH | grounded in existing code/tests, including one real prior incident |

### Open Questions
- State-machine insertion shape for Commit/Ack/Reveal (recommendation given, not locked).
- `game_id`/`game_uid` reconciliation (no existing mechanism; must be designed).
- Step-0 signing-key fallback when the Phase-5 tunnel secret is absent (local/CI dev flow).
- Exact `security.json` shape and whether team-identity fields sit inside or outside the
  digest-checked block.

### Ready for Planning
Research complete. Planner can now create PLAN.md files.
