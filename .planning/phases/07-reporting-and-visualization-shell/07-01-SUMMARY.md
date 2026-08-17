---
phase: 07-reporting-and-visualization-shell
plan: "01"
subsystem: services/gatekeeper-chain
tags: [D-68, D-69, REPORT-02, REPORT-03, REPORT-04, OQ-1, OQ-2, OQ-3, rule-28, rule-29, rule-39, rule-40, phase-4-regression-guard]
one_liner: "One gatekeeper class now serves the LLM and the mail path through a structural GatekeeperParams protocol and an injected-optional budget, with the book's Figure-13 stages -- durable hourly quota, a DOS latch that owns no threshold of its own, and a FIFO chain where every refusal is a return value -- in front of it; Phase 4's LLM instance is proven byte-unchanged across all 22 of its effective parameters."
requires:
  - "Nothing. Wave 1, no depends_on."
provides:
  - "shared/gatekeeper_params.py: GatekeeperParams + BudgetParams protocols -- the type both LanguageParams and ReportingParams satisfy (D-68)"
  - "services/llm/gatekeeper.py: params retyped, budget injected/optional and derived, plus the public read-only bucket_ready seam DosDetector observes"
  - "services/llm/gatekeeper_types.py: CallResult + GatekeeperOverflow, split out at the 150-line gate; public import path unchanged"
  - "shared/reporting_config.py + reporting_config_fields.py: load_reporting_config, ReportingParams, ReportingMode, MANDATORY_REPORTING_ADDRESS"
  - "config/{police,thief}/reporting.json: the mail instance's configured limits, every numeric leaf cited to a file and line, mode dry_run"
  - "services/reporting/: QuotaManager, DosDetector, ReportingChain, SendOutcome, Refusal -- the Figure-13 composition"
  - "shared/durable_write.py: DURABLE_WRITE_RETRIES / DURABLE_WRITE_BACKOFF_SECONDS, extracted at the third consumer"
affects:
  - "07-04 (mail transport) and 07-07 (end-of-game) consume ReportingChain and load_reporting_config; both declare depends_on 07-01"
tech-stack:
  added: []
  patterns:
    - "typing.Protocol for a structural contract, chosen over a shared base dataclass specifically to avoid changing LanguageParams' MRO and field order in a commit that must prove Phase 4 unchanged"
    - "presence of a field group as the caller discriminator (budget_for_params), so no caller passes a flag and no caller can pass the wrong one"
key-files:
  created:
    - src/pursuit/shared/gatekeeper_params.py
    - src/pursuit/services/llm/gatekeeper_types.py
    - src/pursuit/shared/reporting_config.py
    - src/pursuit/shared/reporting_config_fields.py
    - src/pursuit/services/reporting/{__init__,quota,dos,chain}.py
    - config/{police,thief}/reporting.json
    - tests/unit/test_gatekeeper_{params,order,llm_unchanged}.py
    - tests/unit/test_reporting_{config,config_errors,quota,dos,chain}.py
    - .planning/phases/07-reporting-and-visualization-shell/deferred-items.md
  modified:
    - src/pursuit/services/llm/gatekeeper.py
    - src/pursuit/services/llm/budget.py
    - src/pursuit/shared/language_config.py
    - src/pursuit/shared/durable_write.py
    - src/pursuit/shared/language_model_config.py
decisions:
  - "GatekeeperParams is a Protocol, not a base dataclass -- zero runtime change to LanguageParams"
  - "reporting artifacts go to game_artifacts/, not logs/, which .gitignore ignores wholesale"
  - "OQ-1/OQ-2/OQ-3 carried verbatim from the outline; zero numbers invented"
metrics:
  tasks: 4
  commits: 5
  tests_added: 132
  suite: "1557 -> 1689 passed, 0 failed"
  coverage: "96.65% -> 96.80%"
  completed: 2026-08-17
status: complete
---

# Phase 7 Plan 01: Gatekeeper Chain Extension Summary

Rules 28-29 require a token bucket and a DOS detector on the outgoing mail path, and
SEGAL §4 forbids a second gatekeeper. So this plan extends shipped, tested Phase-4
code — which is exactly what makes it the riskiest kind of addition.

## The outline's line budget was wrong, and it decided the whole shape

`07-PLAN-OUTLINE.md` §5 asserts that "`gatekeeper.py` is at 89 counted lines with room
for the `GatekeeperParams` extraction". **Measured first, with the gate's own awk**
(`scripts/check_line_limit.sh`), before writing anything:

```
src/pursuit/services/llm/gatekeeper.py      135 / 150      15 lines of headroom
src/pursuit/shared/language_config.py       139 / 150      11 lines of headroom
src/pursuit/network/language_wiring.py      129 / 150      21 lines of headroom
```

Neither plausible host could take the extraction, so it landed in a new file. And the
edit did not fit even so: adding D-68's optional budget and D-69's `bucket_ready` seam
took `gatekeeper.py` to **153/150**. `CallResult` and `GatekeeperOverflow` — the two
types a *caller* imports, as opposed to the machinery only `Gatekeeper` runs — moved to
`gatekeeper_types.py`, which is a split on a meaning boundary rather than an arbitrary
one and mirrors 04-06's `language_config.py` → `language_model_config.py`. Nothing was
compressed and no docstring was trimmed (CLAUDE.md: *split files, never compress*).

Every file, final:

| File | Lines | | File | Lines |
|---|---|---|---|---|
| `shared/gatekeeper_params.py` | 55 | | `services/reporting/__init__.py` | 22 |
| `services/llm/gatekeeper.py` | 136 | | `services/reporting/quota.py` | 99 |
| `services/llm/gatekeeper_types.py` | 36 | | `services/reporting/dos.py` | 64 |
| `services/llm/budget.py` | 112 | | `services/reporting/chain.py` | 108 |
| `shared/reporting_config.py` | 106 | | `shared/durable_write.py` | 80 |
| `shared/reporting_config_fields.py` | 125 | | `shared/language_config.py` | 139 |

Test files: 122 / 104 / 93 / 89 / 134 / 110 / 108 / 137. All ≤ 150.

## The Phase-4 control — the thing this plan most needed to get right

OQ-3 negotiates the **mail** instance's backoff up to 30 s. A silent retune of the LLM
instance would be a Phase-4 regression wearing a Phase-7 commit, and the existing
gatekeeper tests could not have caught it: they build their own `_params()` doubles and
never read the shipped files.

The LLM gatekeeper's effective parameters were dumped from `config/{police,thief}/`
through the real construction path — `Gatekeeper(params=load_language_config(...))`,
exactly as `language_wiring.py:160` builds it — **before any change and again at the
end**:

```
police: 22 effective parameters, IDENTICAL = True
thief:  22 effective parameters, IDENTICAL = True
```

Covering `requests_per_minute` 30 · `parallel_requests` 2 · `wait_after_error_seconds`
**5** · `retries_before_failure` 3 · `queue_depth` 100 · `response_timeout_seconds` 30 ·
`watchdog_threshold_seconds` 60 · bucket capacity 30 and refill 0.5/s · semaphore value
2 · a real `TokenBudget` at 200000/140000/180000, level `full`. **The mail instance
ships 30 s; the LLM instance still ships 5 s.** `git diff config/*/language.json` is
empty. Every pre-existing Phase-4 gatekeeper/budget/bucket test passes **unmodified**.

The only difference in `submit()` is the two `None` guards, and the statement **order**
is untouched — `reserve()` still above the queue-depth check, `settle()` still on the
success path only:

```
-  self.budget.reserve(estimated_tokens)                 +  if self.budget is not None:
   if self._waiting >= self._params.queue_depth:         +      self.budget.reserve(estimated_tokens)
                                                            if self._waiting >= self._params.queue_depth:
```

`tests/unit/test_gatekeeper_llm_unchanged.py` makes that permanent: 26 tests reading the
real files, so the next person to "harmonise" the two configs fails the suite.

## D-35's order had no test, and now has four with recorded probes

`budget.reserve()` runs unconditionally and *above* the overflow check; `settle()` runs
only on success. That is deliberate — "the degrade level reflects every **queued** call
immediately, not just completed ones" — and nothing asserted it. An executor tidying the
new `None` guard could have moved one line and turned the degrade ladder into a
completed-call counter with the whole Phase-4 suite still green.

## Revert probes — thirteen, with real counts

Every behaviour was reverted and measured. No probe is a shape check.

| # | Mutation | Result |
|---|---|---|
| 1 | `reserve()` moved below the queue-depth check | **1 failed, 50 passed** |
| 2 | `reserve()` moved below `_call_with_retry` | **2 failed, 49 passed** |
| 3 | `settle()` made unconditional (`finally`) | **4 failed, 47 passed** |
| 4 | bucket refill `r = rpm` instead of `rpm/60` | **1 failed, 8 passed** (`At index 0 diff: 0.333… != 20.0`) |
| 5 | env-var NAME check disabled | **10 failed, 47 passed** |
| 6 | Table-19 floor check disabled | **5 failed, 52 passed** |
| 7 | mandatory-recipient check disabled | **1 failed, 56 passed** |
| 8 | DOS latches one attempt early (`>` → `>=`) | **4 failed, 28 passed** |
| 9 | DOS latch short-circuit removed | **2 failed, 30 passed** *(was 0 failed — see below)* |
| 10 | chain order swapped, quota spent before the DOS gate | **1 failed, 31 passed** |
| 11 | DOS lock genuinely auto-clears | **2 failed, 30 passed** |
| 12 | chain propagates a failed send instead of queueing | **4 failed, 28 passed** |
| 13 | quota counted in memory, not durably | **7 failed, 25 passed** |

Controls restored cleanly each time (51 / 32 / 57 passed).

Probe 1 is the one the plan named, and it fails on test (a) **alone** — which is the
point: (a) is the only test in the repository that can see that move.

## Two holes the self-audit found in my own work

**Probe 9 first returned 0 failed / 32 passed.** `test_a_latched_lock_never_clears` only
asserted `locked`, and the line I deleted is a short-circuit, not the latch — so the
latch survived while the *evidence* of the run that caused it was silently reset to zero
by the first ready observation. Exposing `consecutive_empty_observations` at all is for
post-mortem reachability, so the counter is now pinned too, and probe 9 fails 2.

**An AST scan over every `parametrize` in `tests/`** for a source whose size cannot be
resolved to a non-empty literal flagged two of this plan's own:
`test_gatekeeper_llm_unchanged.py` parametrized over `_EXPECTED_GATEKEEPER` and
`_EXPECTED_BUDGET` with nothing asserting either still had rows. Thinning one would have
**skipped silently and left the single most important control in this plan reading as
green while asserting nothing.** Now guarded: 7 Table-19 rows, 3 budget rows, 2 roles,
and every field name must exist on the loaded `LanguageParams`. Collected counts for all
eight new files, verified non-zero: 11 / 4 / 26 / 15 / 43 / 13 / 11 / 9 = **132**.

Two lines were also unreachable by the suite and are now covered — `quota.py`'s
bool-count branch (the `{"count": true}` fixture returned one branch earlier, having no
`window_start`) and `reporting_config.py`'s non-object-file `TypeError`. Both modules
100%.

**Production reachability, grepped:** `budget_for_params` ← `gatekeeper.py:81` ·
`bucket_ready` ← `chain.py:125` · `GatekeeperParams` ← `gatekeeper.py:69` ·
`BudgetParams` ← `budget.py:129` · `GATEKEEPER_MINIMA`/`_NEGOTIABLE` ← both loaders ·
`QuotaManager`/`DosDetector` ← `chain.py`. `ReportingChain` and `load_reporting_config`
have **no production caller yet**, by design — 07-01's non-goals exclude the wiring and
07-04/07-07 declare `depends_on: 07-01`. Recorded as **D7-3** rather than glossed.

## Zero numbers invented

`reporting.json` carries a `_sources` object citing every numeric leaf to a file and
line, and a test asserts every numeric leaf **has** a citation — so an uncited number
added later fails the suite rather than shipping.

- **OQ-1** — SEGAL:173's sourced `requests_per_hour: 500` is what `QuotaManager`
  enforces. No document gives a daily figure, so **no daily leaf exists**; a test asserts
  the gatekeeper group contains no `day`. A daily bound, if ever needed, is derived as
  `24 × requests_per_hour` and labelled derived.
- **OQ-2** — `DosDetector` latches on a strict `>` against the **injected**
  `retries_before_failure`, so it owns no threshold. Its only integer literals are a
  reset to 0 and an increment by 1; a test parses the file and asserts **no numeric
  literal is ever a comparison operand**. Latching means latching — no `unlock`, no
  timeout.
- **OQ-3** — 30 s for the mail instance only, both sides pinned in one test so neither
  can be harmonised into the other.
- The five Table-19 minima are imported from `language_config.GATEKEEPER_MINIMA` rather
  than re-declared (now public, having gained a second consumer), so a floor cannot drift
  between the two instances.
- `shared/gatekeeper_params.py` holds **no numeric literal at all** — asserted by AST
  walk, not grep, because its docstring legitimately cites the measured line counts and a
  grep would have flagged those and proved nothing.

## The artifact-directory decision, made deliberately

`.gitignore` ignores `logs/` **wholesale**, immediately beneath its own comment claiming
the four required JSON artifacts are kept out of the ignore list — and
`agent_step0_wiring.write_declaration` writes `declaration_<game_id>.json` into
`logs/<role>/`. The one artifact this project already produces is therefore unreachable
to git today.

`reporting.json` sets `artifact_dir = "game_artifacts"`, verified not ignored with
`git check-ignore`, and distinct from the existing `artifacts/` tree (regenerable
training curves, excluded from ruff). A test pins that the artifact directory is never
under `logs/`. The contradiction itself is **D7-1**, for 07-02, which owns the artifact
spine: move the declaration writer's output, or narrow the ignore rule — not both, not
neither.

## Interruption and what was re-verified

**The run was killed by an `ECONNRESET` connection error**, immediately after the
verification block for Task 4 and before the self-audit step. Three commits (`c43ca63`,
`c6c5a98`, `dfcb62a`) had landed; the Quota Manager, DOS detector, chain, their three
test files, the `durable_write.py` constants and `deferred-items.md` were written but
**uncommitted**.

Nothing was redone blind. The working tree was read back and verified before anything
was committed: all four reporting modules parse, the package imports, `ruff` is clean.
**Re-run from scratch rather than inherited:** the production-caller grep, the
`parametrize` vacuity scan, the collected-test counts, the LLM effective-parameter pin,
the full suite with counters, and `dev_launch.py`. **Carried forward from before the
interruption:** the thirteen revert-probe counts and the pre-change line measurements —
both recorded against commits that were already in git, and both re-derivable. Nothing
in the uncommitted state was half-written or inconsistent.

## Gates

```
ruff check .                       All checks passed          (0 violations)
check_line_limit.sh                exit 0                     (tracked)
check_line_limit.sh <16 new paths> exit 0                     (explicit -- the no-arg
                                                               form enumerates via
                                                               git ls-files and would
                                                               pass vacuously on an
                                                               untracked file)
check_no_llm_in_strategy.py        OK
pytest tests/ --cov                1689 passed, 0 failed      (baseline 1557)
                                   coverage 96.80%            (baseline 96.65%)
git diff config/*/language.json    EMPTY
dev_launch.py                      exit 0
                                   both sides audit_verdict matched=true, 5 turns
                                   outcome capture, zero technical_win
```

New-module coverage: `chain.py` 100% · `dos.py` 100% · `quota.py` 100% ·
`gatekeeper.py` 100% · `gatekeeper_types.py` 100% · `gatekeeper_params.py` 100% ·
`reporting_config.py` 100% · `reporting_config_fields.py` 100%.

## Games-played counters — rule 38

Read directly (the files are gitignored):

```
FULL SUITE     before 1911 / 1904    after 1911 / 1904    DELTA 0 / 0
ONE REAL GAME  before 1911 / 1904    after 1912 / 1905    DELTA 1 / 1
```

07-00's guarantee holds under this plan's changes: a whole test run costs nothing, and
one real game costs exactly one. The **value** remains deliberately unset and is the
human's at 07-10.

## Deviations from plan

1. **[Rule 3 — blocking] `gatekeeper_types.py` created.** Not in `files_modified`. The
   plan's own edits took `gatekeeper.py` to 153/150 and CLAUDE.md forbids compressing to
   fit. Public import path unchanged.
2. **[Rule 3 — blocking] `reporting_config_fields.py` created.** Same cause: the loader
   plus its validation is 231 code lines. Same 04-06 precedent the plan cites.
3. **[Rule 3 — blocking] test files split.** The plan named
   `tests/unit/test_gatekeeper_params.py` for Tasks 1 and 2 and one file per reporting
   module; the line gate forced `test_gatekeeper_order.py`,
   `test_gatekeeper_llm_unchanged.py` and `test_reporting_config_errors.py` out of them.
4. **[Rule 2 — missing critical functionality] `GATEKEEPER_MINIMA` / `GATEKEEPER_NEGOTIABLE`
   made public** in `language_config.py`. The alternative was a third copy of the
   Table-19 floors, which CLAUDE.md Table 5 forbids and which would let a floor drift
   between the two gatekeeper instances. Pure rename plus a comment; no behaviour change,
   no test edited.
5. **[Rule 2] `DURABLE_WRITE_RETRIES` / `DURABLE_WRITE_BACKOFF_SECONDS` extracted** into
   `durable_write.py` at the third consumer. The two earlier copies were deliberately
   **not** folded in — `step0_collect.py` is the rule-38 write path 07-00 has just
   certified, and a drive-by edit there buys nothing. Logged as **D7-2**.
6. **[Rule 1 — bug] A false comment corrected** in `language_model_config.py`. It said
   `services.llm.gatekeeper` imports `language_config.py` at its top level; this plan
   removed that arc. The deferred import stays (shared/ must not import the services.llm
   package at module scope), and the comment now says which part is which. 07-00's lesson
   is that a document certifying a wrong fact turns every future reader away at the door.

No architectural decisions were needed; no checkpoint was reached; no authentication gate
occurred.

## Commits

- `c43ca63` — feat(07-01): one gatekeeper class, two callers — budget injected and optional
- `c6c5a98` — test(07-01): pin submit()'s reserve/settle order — four probes, real counts
- `dfcb62a` — feat(07-01): reporting.json + fail-loud loader, every number traced to a line
- `d528517` — feat(07-01): QuotaManager, DosDetector and the Figure-13 chain
- `8f89125` — test(07-01): close two vacuity holes and two coverage gaps found by self-audit

## Open, for the plans that own it

**D7-1** the `logs/` ignore contradiction (07-02) · **D7-2** the durable-write constant
migration · **D7-3** `ReportingChain` and `load_reporting_config` await their 07-04/07-07
wiring. All three in `deferred-items.md`.

## Self-Check: PASSED

All 20 claimed files verified present on disk and tracked by git; all five claimed
commit hashes verified reachable in `git log`. Checked with `[ -f ]` and
`git log --oneline --all | grep`, not from memory -- this SUMMARY was written after an
`ECONNRESET` interruption, so nothing in it is inherited without a disk reading.
