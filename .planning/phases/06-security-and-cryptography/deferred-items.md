# Deferred items — Phase 6 (found during 06-04 and 06-05, out of scope)

Per the execute-plan SCOPE BOUNDARY rule: logged, not fixed. Neither item blocks any GATE-6
criterion (both are documented, with the actual evidence used instead, in
`docs/phases/phase-6/GATE-6-MEASUREMENT.md`).

## 1. FINAL_REVEAL is never logged as a `message_sent`/`message_received` envelope record

**Found during:** 06-04 Task 1, while building `gate6_clean_game.py`'s envelope-type counter.

**What:** `src/pursuit/network/agent_audit_exchange.py`'s `push_final_reveal`/
`receive_final_reveal` (introduced in 06-03) call `client.call_tool`/`next_protocol_message`
directly but never call `append_event` the way `turn_commit_send.py`'s `send_and_log`/
`log_received` do for COMMIT/ACK/REVEAL. Only `record_audit_verdict`/`record_technical_loss`
(also 06-03) write to the JSONL. The result: a `message_sent`/`message_received` envelope-type
count over a game's own log can show `commit`/`ack`/`reveal` but never `final_reveal`, even
though the Final-Reveal/Audit phase genuinely ran.

**Why it is not fixed here:** it is pre-existing (06-03), unrelated to any file this plan
(06-04) modifies, and does not affect correctness or security — the `audit_verdict` record
(`matched`, `peer_audit`, `self_audit`) is *equivalent-or-better* evidence that the phase ran,
and is what `GATE-6-MEASUREMENT.md`/`gate6_measurement_evidence.json` actually cite
(`final_reveal_audit_confirmed`). It is a logging-granularity/consistency gap, not a missing
capability.

**Suggested fix, for whoever picks this up (Phase 7 or a Phase-6 polish pass):** have
`push_final_reveal`/`receive_final_reveal` call `append_event` the same way `send_and_log`/
`log_received` do, so a game's own JSONL carries a `final_reveal` envelope record symmetrically
with the other three phases. Low risk, additive only — no consumer currently depends on its
absence.

## 2. Measurement games advance the real `games_played.json` counter

**Found during:** 06-04 Task 1, first script run.

**What:** `scripts/measure_gate6.py` drives the real `declare_step0`/`write_declaration`
production path against `config/police`/`config/thief`, so every measurement game increments
the real, gitignored `config/{police,thief}/games_played.json` counter (rule 37) — exactly like
06-03's own `pytest` integration tests already do on every test run.

**Why it is not fixed here:** this is the shipped counter's correct, intended behavior (rule
37/38: increment at game end, never hand-edited) applied to a real game the script genuinely
played — not a defect. Flagged only so a future reader is not surprised the count moves after
running `pytest` or `measure_gate6.py` repeatedly. If a measurement-vs-league distinction is
ever wanted, it would need a new, explicit signal (e.g. a `measurement=True` flag threading down
to `record_game_played`) — a real design decision, not something to invent here.

---

## 3. An uncaught `ToolError` kills the agent mid-game, before it publishes its nonces

**Found during:** the 5-lens adversarial audit run at `/gsd:verify-work 6` (completeness
critic). **Verified directly** during 06-05: `deadline.py:128` holds `except ToolError: raise`
— deliberate, per its own docstring ("an application-level rejection must propagate
untouched") — and `grep -rn "ToolError" src/` shows **no other handler anywhere**.
`turn_actions.py` catches only `HintProtocolError`; `agent_entrypoint.py` and
`tunnel_wiring.py` use try/**finally**; `main.py` is a bare `asyncio.run`.

**Why it matters:** every send in the game (`push`, `send_and_log`, `send_move_only`,
`send_hint`, `push_final_reveal`) goes through that ladder. A peer whose tool body raises
answers our mid-game COMMIT with an exception that terminates our process **after**
`commit_own_action` has already written `{state, move, intent, nonce}` to our ledger but
**before** any FINAL_REVEAL is sent — so *we* end up the party that published no nonces
(rule 36), on one line of their code. Note also `tools.py:71` raises `ToolError` at the peer
for a malformed envelope, so two honest copies of this codebase would kill each other the
first time either sent something `Envelope.from_dict` rejects.

**Why it is not fixed here:** it is a Phase-2 error-handling concern in `deadline.py` /
`agent_entrypoint.py`, not part of 06-05's two diagnosed gaps, and not a §10.4 criterion. It
deserves its own decision about which exceptions become a technical loss rather than a crash.

**Suggested fix:** catch `ToolError` at the turn-loop boundary and convert it to the existing
`TechnicalWin`/technical-loss pathway, so the game ends through the normal terminal path — one
that already publishes the ledger.

## 4. `_accept` never checks that an inbound envelope's `sender` is the opponent's role

**Found during:** the same audit. **Verified directly:** `tools.py::_accept` builds the
`Envelope` with `EnvelopeKey.SENDER: sender` straight from the tool argument, with no check
against the expected opponent role. `turn_actions.py` then feeds that field into
`engine_agent(...)` and `record_action(ctx, move_envelope.sender, ...)`.

**Why it matters:** a peer stamping `sender` as *our own* role writes into our own buffer slot
(`turn_resolve.py`), so `maybe_resolve` never fires — a stall/desync rather than a board
hijack. On the tunnelled path the shared secret is the only thing binding an inbound envelope
to the real opponent, and it is `None` on every localhost/CI path.

**Why it is not fixed here:** same reason as item 3 — outside 06-05's diagnosed gaps, and it
needs a decision about whether a wrong `sender` is a technical loss or a dropped message.

**Note:** all five audit lenses chased `turn`; none read `sender`. Worth a dedicated pass over
every other peer-supplied envelope field before league play.
