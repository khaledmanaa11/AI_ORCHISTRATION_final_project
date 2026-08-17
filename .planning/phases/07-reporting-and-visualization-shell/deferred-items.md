# Phase 7 — deferred items

Out-of-scope discoveries logged rather than fixed, per the executor scope boundary.
Each names the plan that found it and the plan that should own it.

---

## D7-1 · `.gitignore` ignores `logs/` wholesale while rule 50 requires four artifacts to be committed

**Found by:** 07-01 Task 3 (artifact-directory decision) · **Owner:** 07-02 (artifact spine)

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
