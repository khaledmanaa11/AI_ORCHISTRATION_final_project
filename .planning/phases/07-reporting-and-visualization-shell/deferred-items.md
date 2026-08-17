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
