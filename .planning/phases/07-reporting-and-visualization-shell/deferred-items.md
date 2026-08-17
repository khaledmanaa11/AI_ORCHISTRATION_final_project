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
third occurrence**

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
trailing `` and reported **five false positives**. The check passes bytes with `-z`.

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

