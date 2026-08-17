# Phase 7 — deferred items

Out-of-scope discoveries logged rather than fixed, per the executor scope boundary.
Each names the plan that found it and the plan that should own it.

---

## D7-1 · `.gitignore` ignores `logs/` wholesale while rule 50 requires four artifacts to be committed

**Found by:** 07-01 Task 3 (artifact-directory decision) · **Owner:** 07-02 (artifact spine)
· **RESOLVED by 07-02** — see the resolution note at the end of this entry.

`.gitignore` carries this comment immediately above `logs/`:

> Local run output. NOTE: the four required JSON artifacts
> (`declaration_`/`config_`/`log_`/`result_`) MUST be committed per rule 50 and
> Appendix F rule 4 — keep them out of this ignore list.

…and then ignores `logs/` wholesale on the next line. Meanwhile
`agent_step0_wiring.write_declaration` writes `declaration_<game_id>.json` into
`logs/<role>/`, so **the one artifact this project already produces is unreachable to
git today**. Verified with `git check-ignore`.

07-01 declined to inherit the contradiction: `reporting.json` sets
`artifact_dir = "game_artifacts"`, verified NOT ignored, and
`tests/unit/test_reporting_config.py` pins that the artifact directory is never under
`logs/`. It did **not** move `write_declaration`'s output or edit `.gitignore` — both
belong to 07-02, which owns artifact naming and placement.

**07-02 must decide:** move the declaration writer's output under the configured
artifact directory, or narrow the `logs/` ignore rule. Not both, and not neither.

### RESOLUTION (07-02, Task 3): move the artifact. The ignore rule is NOT narrowed.

**Not narrowed, for two reasons that are not preferences.** Git cannot re-include a file
whose *parent directory* is excluded, so `!logs/**/declaration_*.json` beneath `logs/` is a
silent no-op; narrowing genuinely means restructuring into `logs/**` plus a chain of
negations that the next editor can break without any signal — returning the repository to
exactly this bug, unnoticed. And `logs/` deliberately holds the bulky per-run wire logs
(`<uid>.jsonl`) and nonce ledgers (`<uid>.ledger.jsonl`); un-ignoring anything inside it
puts those one careless `git add` away from the tree.

**The precursor is not the artifact, and could never have been.** `write_declaration` runs
at handshake time, before move 1. `docs/PARAMETERS.md:165` requires
`declaration_<game_id>.json` to carry the **end time**, both teams' repo URLs, MCP server
addresses and the agreed token ceiling. The `logs/<role>/declaration_<game_id>.json` file
is therefore the immediately-durable **precursor** of the signed payload — valuable exactly
because it lands before a crash can happen — and the deliverable is 07-02's D-71 wrapper,
which embeds it verbatim and is a strict superset of it.

**What actually changed in the tree:**

1. `services/reporting/artifacts.write_artifact` **refuses** any path with a `logs`
   component (`ValueError`, message names D7-1). Enforcement at the one write site, not a
   convention every caller must remember. `write_config_artifact` and
   `write_declaration_artifact` both route through it, so the refusal is inherited.
2. The `.gitignore` **comment** was corrected — it asserted the four artifacts were kept
   out of the ignore list while the next line ignored `logs/` wholesale. **Zero ignore
   patterns changed**; verified by diffing both versions with comments stripped.
3. `game_artifacts/README.md` records where the four artifacts live and why not `logs/`.

**Verified, not assumed:** all 42 retained phase-5 remote-round files stay tracked and all
19 `declaration_*.json` among them stay un-ignored (they live under `docs/`, never under
`logs/`); `git status --untracked-files=all logs/` is empty, so no per-run log became
newly visible.

**Left for 07-07** (which owns the game-end hook and has the end time): calling
`write_declaration_artifact` from live wiring. Recorded under D7-3 below.

---

## D7-2 · Three copies of the durable-write retry/backoff pair

**Found by:** 07-01 Task 4 · **Owner:** whichever plan next touches `step0_collect.py`
or `QTable.save()`

The `retries=3, backoff=0.1` pair for a small local crash-safe JSON write is an
engineering default first measured by 03-05 (`QTable.save()`), copied into
`security/step0_collect.py:33-34`, and needed a third time by 07-01's `QuotaManager`.

07-01 extracted it to `shared/durable_write.py` as `DURABLE_WRITE_RETRIES` /
`DURABLE_WRITE_BACKOFF_SECONDS` — the module that owns the write scheme — and
`QuotaManager` uses those names. The two earlier copies still hold their own locals.

**Not folded onto the shared names by 07-01, deliberately:** `step0_collect.py` is the
rule-38 write path that 07-00 has just certified, and a drive-by edit there in the same
phase buys nothing and risks the one number whose sanction is absolute
disqualification. Fold them in when that file is next opened for a real reason.

---

## D7-3 · `ReportingChain` / `load_reporting_config` have no production caller yet

**Found by:** 07-01 self-audit · **Owner:** 07-04 (mail transport), 07-07 (end-of-game)

By design, not by omission. 07-01's `<non_goals>` exclude any mail sending and any
change to `agent_wiring.py`; the wave-2 plans that consume this layer declare
`depends_on: 07-01`. Recorded because "test-only reachability is dead code" is a real
audit finding elsewhere in this phase, and this is the one place it is expected.

Everything 07-01 added that COULD be wired now is wired now: `budget_for_params` is
called by `Gatekeeper.__init__`, `bucket_ready` by `chain.py`, `GatekeeperParams` and
`BudgetParams` by `gatekeeper.py` and `budget.py`, `GATEKEEPER_MINIMA` by both loaders.

**Extended by 07-02, same cause.** The artifact spine — `artifacts.py`,
`artifact_names.py`, `artifact_config.py`, `artifact_declaration.py`,
`artifact_declaration_fields.py` — likewise has no production caller yet: grepped, every
importer outside the package is a test. Nothing in this plan *could* be wired, and the
reason is structural rather than an omission:

- `write_declaration_artifact` needs `DeclarationContext` — repo URLs, MCP addresses, the
  agreed token ceiling and the **end time**. The end time exists only at game end, which is
  07-07's `end_of_game.py`.
- `write_config_artifact` needs the artifact directory from `load_reporting_config`, which
  no production path loads yet — the same D7-3, owned by 07-04/07-07.

Reachability *inside* the spine is complete: `write_artifact` ← both artifact writers ·
`artifact_header`/`artifact_digest` ← `artifact_config.py` · `sub_game_suffix` ←
`config_filename`/`log_filename`/`artifact_header` · `declaration_filename` ←
`write_declaration_artifact` · `verify_embedded_declarations` ←
`write_declaration_artifact` · `artifact_digest_matches` ← `verify_config_artifact`.

That last one was **found dead by the self-audit and fixed rather than excused**:
`artifact_digest_matches` had test-only reachability, which is exactly the finding 07-01
filed D7-3 for. `write_config_artifact` now re-reads the file it just wrote and re-checks
the embedded seal — a real round-trip check through `durable_write_json` and `json.loads`,
not a tautology on the in-memory object — and refuses to return a path to an artifact it
could not verify. That is the config half of the promise `write_declaration_artifact`
already made for signatures.

`next_sub_game_index`, `log_filename` and `result_filename` remain the three public names
with no in-package caller: 07-05 and 07-07 own them.

---

## D7-4 · `"declaration"` is an inline literal on the signed path, with no `SignKey` member

**Found by:** 07-02 Task 3 · **Owner:** whichever plan next opens `security/step0_sign.py`

`agent_step0_wiring.declare_step0` (line 72) returns
`{"declaration": declaration, **signature}`, and `SignKey` names `digest`/`signed`/`hmac`
but not `declaration`. `artifact_declaration.py` therefore had to name it locally as
`ENVELOPE_DECLARATION_KEY`, which is a second spelling of one wire key.

**Deliberately not folded onto `SignKey` by 07-02:** this plan's whole D-71 control is that
`git diff` over `step0_sign.py` / `step0_collect.py` / `agent_step0_wiring.py` is EMPTY,
because one field moving inside that signed payload aborts every game at the handshake. A
pure-rename drive-by there would have destroyed the evidence for the control while buying
nothing. Fold it in when that file is opened for a real reason — the D7-2 precedent.

---

## D7-5 · A recoverable `illegal transition handshake -> handshake` on every dev_launch run

**Found by:** 07-02 verification (`dev_launch.py`) · **Owner:** unclaimed — a Phase-2/6
state-machine question, not a Phase-7 one

Every `dev_launch.py` run logs exactly one, on the police side, before `game_over`:

```json
{"event": "illegal_transition", "state_from": "handshake", "sender": "police",
 "details": {"reason": "illegal transition handshake -> handshake",
             "severity": "recoverable"}}
```

**Pre-existing and unrelated to 07-02**, verified by reading the four most recent runs'
logs: all four carry exactly one, including runs recorded before this plan's first commit.
Each of those games still reached `outcome: capture` at turn 5 with `audit_verdict
matched: true` on both sides, so nothing is currently broken by it — the machine itself
marks it `recoverable`.

Logged rather than fixed, per the executor scope boundary: it is in the handshake path
07-02's D-71 control requires to stay byte-unchanged, and chasing it here would have traded
the control for a benign log line.

---

## D7-6 · The `local-truth` CI job is RED until 07-06 creates `src/pursuit/gui/`

**Found by:** 07-03 Task 3 (by construction, not by accident) · **Owner:** 07-06 (live GUI)
· **RESOLVED by 07-06** — `src/pursuit/gui/` now holds five real modules and the gate prints
`OK: 5 module(s) scanned`, exit 0. Turned green by CODE, never by softening: the gate was
HARDENED in the same commit (see D7-9), and `test_gui_structural.py` asserts a non-zero module
count beside every clean verdict.

`scripts/check_local_truth.py` exits **2** when its scan root is missing or holds zero
modules, and `.github/workflows/quality-gate.yml` now runs it as its own job. Measured
today:

```
$ uv run python scripts/check_local_truth.py
ERROR: local-truth gate scanned nothing: ...\src\pursuit\gui does not exist.
       07-06 creates it; until then this gate cannot vouch for anything.
exit=2
```

**Deliberate, and not softened.** The alternative wirings were each considered and
rejected:

* *Skip the job when the directory is missing* — that is exactly the vacuity the gate
  exists to prevent, moved from the script into the workflow. A gate that reports OK for
  having looked at nothing is worse than no gate, and `check_no_llm_in_strategy.py`'s
  `rglob` shape would have shipped precisely that.
* *Wire it at 07-06 instead* — leaves the enforcement out of CI for three more plans,
  during which `gui/` gets written.

A red job that says "the package this rule governs does not exist yet" is a true
statement. **07-06 turns it green** by creating `src/pursuit/gui/` with modules that pass
the check; nothing else needs to change.

**Also noted, not fixed (scope boundary):** `scripts/check_no_llm_in_strategy.sh` is
still **not** in `quality-gate.yml`, though it has existed since 03-10 and is run by hand
in every plan's verification block. Pre-existing and unrelated to 07-03, so it is
recorded here rather than silently added inside a commit about a different gate.

---

## D7-7 · The whole 07-03 surface has no production caller until 07-06

**Found by:** 07-03 self-audit · **Owner:** 07-06 (live GUI) · **The same finding as D7-3,
third occurrence** · **RESOLVED by 07-06.** Grepped again, not assumed: `build_local_view` ←
`sdk/view_publish.publish_view` ← `network/turn_resolve.maybe_resolve`; `HintHistory` ←
`AgentContext.view_history` (per-instance via `default_factory`, so NET-02 holds); `HintHistory.observe`
← `build_local_view`; and **`HintHistory.record_outgoing`, which had no caller at all**, ←
`network/turn_language_io.compose_and_send_hint`, called after the hint actually goes out. The live
sidebar therefore shows one peer's whole conversation rather than half of it.

Grepped, not assumed. `build_local_view` / `HintHistory` / `LocalView` are imported by
tests only; `HintHistory.record_outgoing` has no caller at all. Structural, exactly like
D7-3: this plan's `<non_goals>` exclude every line of Tkinter, and 07-06 declares the
consumer side of D-74.

Everything that COULD be wired now is wired now, and that half was checked rather than
waved past:

* `shared/roles.py` — `engine_agent`/`opponent_role` reach production through
  `network/orchestrator.py`'s re-export, so every pre-existing caller
  (`turn_actions`, `turn_commit`, `capture_declaration`, `agent_audit_wiring`,
  `agent_lifecycle`) exercises them unchanged.
* `BeliefMap.entropy()` — called by `network/turn_language.belief_snapshot` on the live
  path. Verified in a real game: six `language_turn` records, turn-0 entropy
  **5.6108** against `log2(49) = 5.6147` (and `ln(49) = 3.8918`), so production is
  provably on the log2 formula the extraction moved.
* `local_view` — imported by `view_builder`, which is the module 07-06 consumes.

---

## D7-8 · `belief_snapshot` still writes the true argmax to the JSONL log

**Found by:** 07-11 · **Owner:** 07-08 (replay viewer) · **Deliberately NOT fixed**

`network/turn_language.belief_snapshot` returns `ctx.brain.belief.argmax()` — the strategy
map, which on the cop seat is a delta on `ctx.state.thief`. Every `language_turn` record in
`events.jsonl` therefore carries the thief's true cell.

**This is correct and must stay.** The JSONL is the audit record (rule 38, and the
Phase-6 final-reveal audit depends on it being complete); rules 8–9 govern the **live
interface**, not the post-game log, and 07-11's own fix deliberately leaves the strategy
belief untouched for the same reason — provenance is legitimate, display is what is
regulated.

**07-08 inherits the constraint, and it is not optional:** the replay viewer may not render
`belief_argmax` (or anything derived from it) while a game is live, and if it renders it
post-game it must be labelled as the audit record rather than as the peer's belief.
`sdk/local_view.py` is the only shape a live panel may consume; the log is not one.

## D7-9 · `scripts/check_local_truth.py` hardening, still open

**Found by:** 07-11 (re-confirming 07-03's own non-goal) · **Owner:** 07-06
· **RESOLVED by 07-06.** All three holes were MEASURED OPEN before being closed, and none of
them was closed by weakening anything:

| Hole | At HEAD | After |
|---|---|---|
| a root holding one bare `__init__.py` | `OK: 1 module(s) scanned`, **exit 0** | `EmptyScanError`, **exit 2** |
| `panel.pyw` reading `ctx.state.thief` | **never scanned** (`rglob('*.py')`) | scanned and **reported** |
| `s = ctx.state; s.thief` + `getattr(ctx.state, 'thief')` + `asdict(s)['cop']` | `violations=[]`, **exit 0** | **3 violations**, exit 1 |

The dynamic-key check is on the KEY rather than on what it is applied to, which makes it total
over indirections nobody has thought of yet. The gate reached 198 code lines and was SPLIT into
`scripts/local_truth_ast.py`, loaded by file path so 07-03's standalone property (never imports
`pursuit`) survives; both halves are checked explicitly against the 150-line gate, which skips
`scripts/` in its no-argument form.

**What is still NOT closed, and is stated rather than papered over:** a parameter named `state`
(`def render(state): ...`) is outside what a single-module AST walk can resolve, and the gate
still cannot see a coordinate that is DRAWN rather than NAMED. That second question is asked by
`tests/unit/test_gui_recovery.py` at RUNTIME, over the rendered panel data, and this gate is
never cited as evidence about a panel.

Unchanged by this plan and restated because 07-11 proved the gate's blind spot is wider
than filed: it is an import/attribute gate and **cannot** see a coordinate that is *drawn*
rather than *named*. It returned `violations: []`, `OK: 1 module(s) scanned`, exit 0
against a synthetic panel that markered `belief.argmax` and labelled the `scent.opponent`
peak. Do not cite it as evidence about these panels. The attribute-chain indirection
(alias/`getattr`/`asdict`), the `rglob('*.py')` `.pyw` blind spot and the empty-`__init__.py`
anti-vacuity hole all remain 07-06's to close.

---

## D7-10 · A `.gitignore` secret pattern can swallow a source or test file silently

**Found by:** 07-04 self-audit (in its own work) · **Owner:** resolved here; the GATE is now
permanent

This plan's third test file shipped first as `tests/unit/test_gmail_secrets.py`. `.gitignore:26`
carries `*_secret*` — a correct rules-39-40 guard that must NOT be weakened — and it matched the
filename. `git status` simply never listed the file: 18 passing tests that git would have refused
to track, that CI would never have run, and that the grader would never have seen. **That is the
most complete form of the vacuity this phase keeps finding**, because the tests pass locally right
up until the moment they stop existing.

**Resolved, and not by loosening the pattern:** the file is renamed
`tests/unit/test_gmail_credentials.py`, and `test_no_source_or_test_file_is_swallowed_by_gitignore`
now runs `git check-ignore -z --stdin` over every `.py` under `src/`, `tests/`, `training/` and
`scripts/`. It fails (rather than skips) when git is unavailable, on the D7-6 standard that a gate
reporting OK for having looked at nothing is worse than no gate, and it carries an anti-vacuity
floor (`> 100` files scanned) plus a control that asserts the scan DOES find `.env`. Probe: a file
named `test_probe_secret_name.py` → **1 failed**.

Measured while fixing it: **no other `.py` in the repository is currently ignored.**

**Also learned, and written into the helper's docstring:** `subprocess.run(..., text=True)` on
Windows writes CRLF into the child's stdin, so `git check-ignore --stdin` saw every path with a
trailing `
` and reported **five false positives**. The check passes bytes with `-z`.

---

## D7-11 · `durable_write_json`'s two older copies of the retry/backoff pair are still un-folded

**Found by:** 07-01 (as D7-2) · **Restated by 07-04** · **Owner:** unchanged

07-04 opened `shared/durable_write.py` to extract `durable_write_bytes` (the `.eml` needed the same
crash-safe write, and a second write-and-rotate sequence would have been a second crash-safety
scheme). It deliberately did **not** fold `security/step0_collect.py`'s and `QTable.save()`'s local
copies onto the shared names while it was there: `step0_collect.py` is the rule-38 write path 07-00
certified, and D7-2's reasoning is unchanged by this plan touching a different function in the same
file. The extraction was proven byte-neutral rather than assumed — the JSON bytes are identical
either way (98 bytes for a payload carrying a newline, a tab and Hebrew), because `json.dumps`
escapes newlines and defaults to ASCII.

---

## D7-12 · Nothing in `src/` sends a report yet — D7-3, fourth occurrence

**Found by:** 07-04 self-audit · **Owner:** 07-07 (end-of-game)

Grepped, not assumed: every importer of `message.py`, `sink.py` and `gmail_sink.py` outside the
package is a test. Structural, exactly like D7-3: this plan's `<non_goals>` exclude "deciding WHEN a
report is sent", which is 07-07's `end_of_game.py`, and 07-07 declares `depends_on: 07-01`.

Everything that COULD be wired now is wired now, and that half was checked rather than waved past:
`report_filename` ← `build_report_message` and `DryRunSink.send` · `build_report_message` /
`render_message` ← both sinks · `write_artifact_bytes` ← `DryRunSink.send` · `durable_write_bytes` ←
`durable_write_json` and `write_artifact_bytes` · `require_send_only_scope` ←
`build_gmail_transport` **and** `load_send_only_credentials` · `load_send_only_credentials` ←
`build_gmail_transport`'s default · `_require_env_value` ← `build_gmail_transport`.

`build_gmail_transport` itself is the one public name whose only caller is 07-10's runbook, which is
what it exists for.


---

## D7-13 · One wire log can legitimately carry TWO `game_uid`s (D-61)

**Found by:** 07-05, building the artifact from a real `dev_launch` game · **Owner:**
resolved here for the `log_` artifact; **07-07 and 07-08 must inherit the fact**

`agent_lifecycle` mints a process-local `secrets.token_hex(8)` and opens the log **before**
the handshake; `game_identity.adopt_negotiated_game_id` then renames the log to the
negotiated id (D-61, closing 05-UAT G2). Every record written before that rename keeps its
pre-negotiation stamp.

Measured on `logs/thief/521519a78f96c255.jsonl`: **42 records, two `game_uid`s.** The single
pre-negotiation `illegal_transition` (D7-5's known recoverable one) carries
`3c0c5fd8f6705a3b`; the other 41 carry the negotiated `521519a78f96c255`, which is also the
filename. The police-side log of the same game carries one, because the negotiated id is the
police's own.

**Why it matters beyond 07-05:** a builder that reads "the log's `game_uid`" off the first
record would have **refused the thief an artifact in every game**. 07-05's own check caught
it only because it was written to fail loudly rather than to pick a value.

**Resolved here as:** the caller supplies the negotiated id, which must appear *somewhere* in
the log; every other id found is carried in `prior_game_uids`, **inside the artifact's seal**.
Dropping the older id would hide exactly the fact 05-UAT G2 exists to make visible.

## D7-14 · The `log_` builder has no production caller yet — D7-3, fifth occurrence

**Found by:** 07-05 self-audit · **Owner:** 07-07 (game-end hook), 07-08 (replay viewer)

Structural, exactly like D7-3/D7-7/D7-12, and this time it is also a **rule**: D-64 keeps the
nonce ledger off the wire path and only SEC-04's end-of-game publication makes it readable, so
the builder *must not* be reachable during play. 07-07 owns the game-end call site.

Unlike the earlier four, this one is **enforced rather than recorded**:
`tests/unit/test_log_artifact_reachability.py` re-runs the scan on every suite run over 173
`src/` files, watching both the module-path and the re-exported-name import forms, floored at
100 files with a control that finds a real import.

**That second form is not decoration.** The first version of the gate watched module paths
only, and a probe that added `from pursuit.services.reporting import artifact_log` to
`network/turn_actions.py` — a turn-loop module importing the builder — **passed 6/6**. The
package re-exports, so the name form is the one 07-07 is most likely to write.

`verify_log_turns` is 07-08's entry point and has no caller outside the package today; inside
it, `write_log_artifact` calls it post-write, so it is not dead code.


---

## D7-15 · `snapshot_path_for` and `ledger_path_for` are two spellings of one sibling convention

**Found by:** 07-06 Task 1 · **Owner:** whichever plan next opens `turn_commit_ledger.py`
for a real reason

`turn_commit_ledger.ledger_path_for` is `log_path.parent / f"{log_path.stem}.ledger.jsonl"`
and `sdk/view_publish.snapshot_path_for` is the same join with `view.json`. One shared
`sibling_path(log_path, suffix)` helper in `shared/` would own the convention outright.

**Deliberately not done by 07-06**, on the D7-2 / D7-4 precedent this phase has now applied
three times: `turn_commit_ledger.py` is the D-64 nonce path 06-05 certified, and renaming
through it for a one-expression path join buys nothing while putting every game's ledger
location at risk. `snapshot_path_for` names `ledger_path_for` in its own docstring as the
convention it follows, and `test_view_publish` asserts the two agree on the parent directory
and the stem, so they cannot drift apart silently. Fold them when that file is next opened.

---

## D7-16 · A view's own legal cell can collide with the leak scan's reversed-pair branch

**Found by:** 07-06, on the LIVE `dev_launch` game `2db6cc8b039c82e7` · **Owner:** nobody —
recorded so a future reader does not mistake it for a leak

`local_view_scanner.coordinate_hits` reports both `[row, col]` and `[col, row]`, because a
leak could arrive in either encoding. On that game the thief's true cell was `(2, 3)` and the
police's OWN cell was `(3, 2)`, so scanning the police snapshot for the truth reported
`$.own_cell: pair [3, 2]` — a **false positive** on a field rule 8 explicitly permits.

This is exactly the coincidence `local_view_fixtures.py`'s docstring says its chosen
coordinates avoid (`OPPONENT_CELL` differs from `OWN_CELL`, from every barrier and from every
other integer in the view), and here it is on live data rather than in a fixture. Confirmed a
false positive rather than assumed: the FORWARD pair `[2, 3]` appears nowhere in the file, and
neither flat index (17 row-major, 23 column-major) appears either.

**What to do with it:** nothing in source. When scanning a real snapshot by hand, separate the
forward pair from the reversed one before drawing a conclusion, and prefer the geometric
inversion — which returned `[]` on that same game — because it cannot collide this way.

---

## D7-17 · `game_id` is minted per GAME, while PARAMETERS reads it as the SERIES id

**Found by:** 07-07 Task 2 · **Owner:** 07-10 / Phase 8 (the league runner)

`docs/PARAMETERS.md`'s artifact table reads the two name parts as *series* and *match within
it*: "each filename embeds the game identifier `game_id` plus the match number `<NN>`, so
files from different matches can never be confused", and `result_<game_id>.json` is defined
as the "final results summary **across all sub-games**".

But `agent_entrypoint.run_agent` mints `secrets.token_hex(8)` and then adopts the negotiated
id (D-61), so today's `game_id` identifies **one game**. Measured on a real `dev_launch` run:
each game produced its own `result_<uid>.json` with exactly one sub-game and
`games_measured: 1`, and `<NN>` was `01` on both seats.

**The accumulator is not the problem and is not affected.** `record_sub_game` reads the
previous generation and adds to it, proven over two sub-games sharing a `game_id`
(`test_the_series_total_is_the_sum_of_two_sub_games`) and proven WRONG when the accumulation
is removed. What is missing is a series-scoped identifier for the accumulator to key on.

**Not fixed here, deliberately:** inventing an id scheme would be a protocol decision taken
in an artifact writer, and `game_id` is negotiated with the peer at handshake (D-61) — it is
not ours alone to redefine. Until a series id exists, a production series contains one
sub-game, which is *correct for a one-game series* and understates nothing.

---

## D7-18 · A `QuotaManager` path is unguarded against the shipped `config/` tree

**Found by:** 07-07's revert probe 17 · **Owner:** whichever plan next opens
`tests/_shipped_config_guard.py`

`tests/conftest.py`'s session-autouse guard patches `step0_collect.durable_write_json`, so it
catches writes to `games_played.json` by any route. It does **not** cover
`QuotaManager`, which reaches `durable_write_json` through its own module binding. Probe 17
pointed the quota path at `config/police/` and the suite happily wrote
`config/police/reporting_quota.json` — no test failed for the *write*; the probe failed only
because 07-07's own test asserts the file lands beside the run output.

Production is not affected: `end_of_game` passes `ctx.log_path.parent`, and
`test_the_quota_counter_lands_beside_the_run_output_not_in_config` pins it. The gap is that
the STRUCTURAL guard covers one writer while the rule ("no test writes the shipped config
tree") is about the tree. Widening it means guarding `durable_write_json` at its own module,
which is a change to a shared primitive and out of 07-07's scope.
