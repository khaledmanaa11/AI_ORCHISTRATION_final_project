# Phase 6: Security and Cryptography - Context

**Gathered:** 2026-07-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 delivers the trust layer: the **four-phase commit-reveal protocol**
(Commit → Acknowledge → Reveal → Final Reveal/Audit) over SHA-256 of canonical JSON
(`sort_keys=True, separators=(",",":")`) covering `{state, move, intent, nonce}`; nonce
from `secrets.token_hex(16)`, secret until game end, verified with
`secrets.compare_digest`; the **Step-0 hardware declaration** published before move 1;
and the **mutual log audit** at game end. Any hash mismatch at audit is a technical loss
for the forging team (SEC-01…SEC-08).

Most of this phase is **spec-locked** — hash recipe, nonce rules, protocol phases, and
sanctions are fixed by the book and are not design choices.

Out of scope: reporting the audit by email (Phase 7 wires the reports; Phase 6 produces
the verdicts and artifacts).

**Planning-day note:** refresh the graph (`/gsd:graphify`) before
`/gsd:plan-phase 6 --chunked` (task 06-96).

**Researcher question (resolve from the book §E before planning):** the exact definition
of `state` inside the hashed `{state, move, intent, nonce}` — full local view, or a
defined subset (turn number, own position, …)? Both sides must serialize it identically
or every audit fails.

</domain>

<decisions>
## Implementation Decisions

### Step-0 hardware declaration (SEC-06)
- **Auto-collect + one review**: code gathers OS/CPU/RAM/GPU facts (platform/psutil) and
  the **exact git commit hash** automatically, writes `declaration_<game_id>.json`,
  shows it once for sanity, then hash-signs and publishes it at handshake (and later by
  email via Phase 7). No hand-typed hardware specs.

### Audit verdicts (SEC-05, SEC-08)
- **Auto-declare + evidence**: an opponent hash mismatch automatically declares the
  technical win, writes the exact mismatching hashes/messages into the JSONL log as
  evidence, and flows into the game report. League games run unattended — no human in
  the loop.
- **Symmetric honesty**: if OUR OWN hash fails verification (a bug), report it
  truthfully — never suppress or misreport (rules 16/22/38 territory: lying in
  declarations is instant disqualification).

### Development ergonomics
- **Config toggle, default ON**: `security.commit_reveal=true` is the default and the
  league mode; tests and local debugging may flip it off to isolate lower layers.
  League/shipped configs always ship with it on.

### Crash safety
- **Persisted local ledger**: every commit/nonce appends to a local file per turn —
  consistent with Phase 2's persist-every-turn policy, so the Final Reveal/Audit
  survives a crash. The ledger never crosses the wire; nonce secrecy is about
  transmission, not our own disk.

### Claude's Discretion
- Ledger file format and rotation; commit-pack message layout inside the Phase-2 typed
  envelope (new types: commit / ack / reveal / final_reveal)
- How commit-reveal sub-states slot into the Phase-2 state machine (the enum + transition
  table was designed for this insertion)
- Folding the Phase-4 scent-model lock and Phase-5 shared-secret header into the audit
  trail

</decisions>

<specifics>
## Specific Ideas

- Canonical-JSON helper is ONE shared function used everywhere (hashing, scent lock,
  config hash) — a serialization mismatch between call sites is an auto-loss generator.
- `secrets` module only — `random` for nonces is a disqualification-grade bug.
- Per-mechanism PRD due this phase (task 06-04): `docs/PRD_commit_reveal.md`.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-security-and-cryptography*
*Context gathered: 2026-07-28*
