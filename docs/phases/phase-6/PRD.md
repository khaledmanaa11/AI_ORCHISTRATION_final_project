# Phase 6 PRD — Security and Cryptography

**Version:** 1.00 · **Status:** ◐ approved · **Updated:** 2026-08-09

> Phase-scoped PRD. Inherits the project [PRD.md](../../PRD.md); do not restate it — capture
> only what is specific to this phase. Numbers come from [PARAMETERS.md](../../PARAMETERS.md)
> and the book (§5.3–§5.5, book pp. 34–40), never invented.

## Goal
Commit-reveal protocol over SHA-256, nonce handling, Step-0 hardware declaration
(ROADMAP Phase 6). This is the trust layer: in a refereeless P2P game, cheating becomes
mathematically detectable rather than a matter of argument (book §5.2).

## Requirements covered
- **SEC-01** — moves use a commit-reveal protocol based on SHA-256 (rule 17).
- **SEC-02** — four phases: Commit → Acknowledge → Reveal → Final Reveal/Audit (§5.3).
- **SEC-03** — the hash covers `{state, move, intent, nonce}` as canonical JSON
  (`sort_keys=True, separators=(",",":")`).
- **SEC-04** — nonce from `secrets.token_hex(16)`, secret until game end, verified with
  `secrets.compare_digest` (rule 18).
- **SEC-05** — any hash mismatch at audit is a technical loss, score 0 to the forging team
  (rule 19, "the iron law").
- **SEC-06** — a signed Step-0 declaration (OS/CPU/RAM/GPU, LLM name, code version, team code,
  games played so far, exact commit hash) published before the first move (rules 24, 53).
- **SEC-07** — barrier and capture declarations are open and truthful (rules 15–16, 21–22).
- **SEC-08** — a comprehensive mutual log audit runs at the end of every game (rule 36).

## Acceptance criteria (= §10.4 milestone gate)
1. A move is committed (SHA-256 hash) and then revealed with a valid nonce; the four phases
   run Commit → Acknowledge → Reveal → Final Reveal/Audit.
2. The hash covers canonical-JSON `{state, move, intent, nonce}`; the nonce
   (`secrets.token_hex(16)`) stays secret until game end; any mismatch is a technical loss.
3. The Step-0 hardware declaration (incl. exact commit hash) is verified before the first move.

All three are measurable **on localhost with two processes** — this gate needs no credentials,
no environment variables, and no second machine. Evidence:
[GATE-6-MEASUREMENT.md](GATE-6-MEASUREMENT.md), written by plan 06-04.

## In scope / Out of scope (this phase)
- **In:** the `pursuit.security` package (canonical commit/reveal hashing, the state record,
  the durable nonce ledger); four new wire message kinds and the both-locked Commit→Ack→Reveal
  exchange; **barrier placement over the wire** inside the committed action (the Phase-2/3
  deferral that SEC-07 finally closes); the Step-0 declaration, its handshake verification, and
  the negotiated `game_id`; the end-of-game mutual audit and its technical-loss verdict; an
  eleventh config block `security.json`; `docs/PRD_commit_reveal.md`.
- **Out:** emailing the declaration or the reports (Phase 7 — this phase produces the artifacts
  and verdicts); the replay viewer application (Phase 7, though it replays this phase's log
  shape); repo split and league play (Phase 8); any change to the frozen 4-key `Envelope`
  shape, to Phase-3 strategy internals, or to Phase-4 language behavior.

## Dependencies
- Depends on: Phase 5 (cloud exposure) — its shipped **code**, not its pending GATE-5
  measurement. The Phase-5 shared tunnel secret doubles as the book's "pre-supplied key" for
  the Step-0 HMAC when present.
- External: `psutil` (new — Step-0 CPU/RAM facts); `git` on PATH (the exact commit hash, rule
  53). No API key, no account, no network service.

## Success metrics & test scenarios
- Unit: commit→reveal→audit round-trip in one test (not two isolated halves); a single-field
  tamper in any of `state`/`move`/`intent`/`nonce` always disagrees; `intent` as a bool is
  rejected; the ledger survives append→read with the nonce intact; Step-0 signs and verifies,
  and is honest (`signed: false`) when no key exists.
- Integration (offline, two peers): all four message kinds observed on the wire; every REVEAL
  sent strictly after the opponent's COMMIT is held; a forced cop barrier round-trips through
  commit, reveal, and both engines identically; the nonce appears in **no** wire-mirroring log
  while it is present in each side's own ledger; `commit_reveal=false` leaves the pre-Phase-6
  exchange byte-equivalent.
- Tamper proofs (both classes): a payload that no longer hashes to its commitment, **and** an
  honestly-hashed payload whose action differs from what was actually played in-game — each
  produces `AUDIT_HASH_MISMATCH` and `Outcome.TECHNICAL_LOSS`.
- Standing gates: ruff 0 · coverage ≥85% · files ≤150 code lines · no secrets · no invented
  numbers.

## Design decisions (phase ADRs)
D-58…D-67 — recorded authoritatively in
[06-PLAN-OUTLINE.md §1](../../../.planning/phases/06-security-and-cryptography/06-PLAN-OUTLINE.md).
Headline four: **D-58** (no new state-machine members; the both-locked reveal gate lives in the
message exchange), **D-59** (one payload-builder, one canonical serializer), **D-66** (barriers
travel inside the committed action — SEC-07's substance), **D-67** (the audit cross-checks the
revealed action against what was actually played, closing the hash-only bypass).
