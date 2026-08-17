# PRD — `log_<game_id>_g<NN>.json`, the verifiable turn journal

Per-mechanism PRD (CLAUDE.md §2.3 / Segal §2.3). Owner: 07-05. Consumers: 07-07
(sends it), 07-08 (recomputes hashes over it and displays the verdict).

`docs/PARAMETERS.md:167` fixes the contract:

> `log_<game_id>_g<NN>.json` — Turn-by-turn journal: commitments, moves, hints,
> verdicts, nonce and hash. **Enables full cryptographic verification in the
> replay simulator.**

Rule 20 makes that verifying replay a **threshold condition** for approving the
project, so this file is not a convenience log. It is the evidence.

## 1. What it is, and what it deliberately is not

It is the **wire record**: this side's JSONL wire log joined to this side's own
nonce ledger. Every value in it is either an envelope payload that crossed the
wire, a value from this side's own `CommitLedger`, or the peer's own claim
carried verbatim as evidence.

It carries **no internal inference** — no belief map, no scent grid, nothing
derived from `ctx.state`. Two independent reasons, and the second is the one
with a sanction attached:

1. **Verifiability.** A third party must recompute every hash from this file
   alone. Internal state is unverifiable noise; it cannot be checked, so it
   cannot be evidence.
2. **Rules 8–9.** 07-11 reproduced and closed a disqualifying leak in which the
   cop's published belief was a 1.0 delta on `ctx.state.thief` and the published
   opponent scent was the kernel centre on the true cell at `scent.json`'s
   `source: 0.9`. **D7-8 records that the true argmax is still written into every
   `language_turn` JSONL record — correctly**, because that log is the rule-38
   audit record and rules 8–9 govern the live interface. This artifact, however,
   is emailed to the lecturer. Anything internal that reaches it leaves the
   machine.

`log_turn_fields.py` therefore copies the language record by **allow-list**
(`HINT_BROADCAST_KEYS = ("intent", "text")`), never `**record` minus a
deny-list. An allow-list stays correct when a future plan adds a field to
`language_turn_record`; a deny-list ships it silently. `LANGUAGE_INTERNAL_FIELDS`
names the six excluded fields so a test can scan the serialised artifact for
each one.

## 2. The join key — local turn truth, and only that

Both sides of the join key on **the record's own top-level `turn`**, never on
`envelope["turn"]`.

This is not re-derived. `network/agent_audit_observed.observed` already states
it: the top-level turn is "a number THIS side stamped … never on the nested
`envelope`'s turn, which on the received side is whatever the peer chose to
claim." 06-05 measured the consequence of getting it wrong — keying on the
peer's number let an adversary stamp COMMIT and REVEAL with disjoint turns,
which emptied `audit.audit_peer_records`'s `set(commits) & set(reveals)`
coverage intersection (re-opening the `{"records": []}` rule-36 evasion) and
sent every entry down the trailing-commit exemption, so the D-67
revealed-vs-played check never fired.

The peer's claimed turn is **kept**, in `peer_claimed_turns`, as evidence. It is
never a key.

**Measured, on this repository's own real games:** the two numbers already
disagree without any adversary. Across 20 recorded `dev_launch` games, every
single one carries **5–6 received records whose local turn differs from the
peer's stamped envelope turn** — every incoming HINT, because a hint arrives one
turn late. A builder keyed on the peer's number would misfile every hint of
every honest game by one turn.

## 3. Crash tolerance — and what is *not* relaxed

`event_log.append_event` writes one line, then `flush()` + `os.fsync()`. An
interrupted process can therefore leave a **partial last line**.

`agent_audit_observed._read_log` and `ledger.CommitLedger.read_all` both raise
on that, and `read_all`'s docstring states the raise is deliberate fail-loud for
the **audit** path. **Neither contract is weakened.** `log_read.py` is a second
reader, because the two paths want opposite things:

| Path | On a partial tail | Why |
|---|---|---|
| Audit (`read_all`) | **raise** | An audit that cannot read its own evidence must stop |
| Replay artifact (`log_read`) | **drop it and say so** | An artifact that cannot be produced from a crashed game is useless exactly when it is needed |

A malformed line anywhere *other* than last is **corruption, not an interrupted
write**, and raises `CorruptLogError` — a distinct class from
`json.JSONDecodeError` (which is itself a `ValueError`) so a test can assert the
exact type. The dropped tail is reported in the artifact's `truncated_tail`
field, **inside the seal**, because whether a game's tail was lost is part of
the record's provenance.

## 4. Two event names bypass `EventType`

`EventType` has no `language_turn` and no `game_over` member.
`turn_events.language_turn_record` and `game_over_record` assemble their four
common fields directly and set `EventField.EVENT` to those bare strings — both
docstrings say so.

A builder filtering on `EventType(record[EVENT])` **raises** on those two; one
filtering on `record[EVENT] in EventType._value2member_map_` **drops them
silently**. Every filter in `log_join.py` is therefore on the string, and
`test_artifact_log.py` pins that both strings are still absent from `EventType`
— so if a later plan adds the members, that test fails and points here.

## 5. Re-hashing — one serializer, never two

`security/commit_pack.py` forbids a second `json.dumps(sort_keys=True, …)` in
this repository in as many words (D-59). `verify_log_turns` therefore rebuilds
through `commit_pack.verify_reveal`, which rebuilds through
`build_commit_payload` and compares with `digests_match`. The artifact's own
seal goes through `artifacts.artifact_digest`, which is `config_hash`'s one
`canonical_json`.

A second serializer would produce **false `FAILED` verdicts on the one screen
the grader inspects** (07-08).

`verify_log_turns` returns `(verified, committed)` and counts only turns
carrying an `h_commit`. A trailing game-over turn has wire records but no ledger
entry; counting it would make the ratio a lie. **Callers must check
`committed > 0`** — `audit_record.all_matched([])` returning `True` is this
repository's own canonical instance of the empty-sequence trap.

## 6. Nonce separation — during play, and only during play (D-64, SEC-04)

`security/ledger.py` states its file "is never read or written by anything on
the wire path (D-64)". Rule 18 keeps every nonce secret for exactly as long as
the game is live; only SEC-04's end-of-game publication makes the ledger
readable.

So this builder must be reachable **only** from a game-end path.
`tests/unit/test_log_artifact_reachability.py` enforces it as a scan rather than
recording it as a grep, because a grep in a summary rots. It asserts:

* no module outside `services/reporting` imports the builder, **by module path
  or by the package's re-exported name** — both forms, because the package
  re-exports and `from pursuit.services.reporting import write_log_artifact` is
  the form 07-07 will most likely use;
* no turn-loop module (`network/turn_*`, `orchestrator`) reaches it;
* `CommitLedger.read_all()` has exactly one production call site,
  `agent_audit_wiring.run_final_audit`, and `agent_entrypoint` calls it only
  after `run_turn_loop` has returned;
* the four `log_` modules never bind `CommitLedger` and never call `read_all`.

It is floored at >100 files scanned and carries a control that finds an import
that really is there (D7-6's standard: a gate reporting OK for having looked at
nothing is worse than no gate).

## 7. Zero numeric values introduced

Turn indices come from the records themselves. The filename and `<NN>` come from
07-02's `log_filename` / `next_sub_game_index`, which read them off
`docs/PARAMETERS.md:159-168`. Nothing here is an Appendix F parameter and
nothing is defaulted.
