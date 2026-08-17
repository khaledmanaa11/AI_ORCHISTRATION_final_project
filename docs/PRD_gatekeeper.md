# PRD — the API gatekeeper (rate limiting, quota, DOS, and reporting)

Per-mechanism PRD required by [CLAUDE.md](../CLAUDE.md) §2.3 / Segal §2.3, and by
`.planning/ROADMAP.md` Phase 7 row **07-04**. It covers `services/llm/gatekeeper.py`,
`services/llm/bucket.py`, `services/llm/budget.py`, `shared/gatekeeper_params.py`,
`services/reporting/{quota,dos,chain}.py` and the two config files that supply every
number: `config/*/language.json` and `config/*/reporting.json`. Written by plan 07-09.

Companion PRDs: [PRD_end_of_game.md](PRD_end_of_game.md) (the caller),
[PRD_result_artifact.md](PRD_result_artifact.md) (the payload),
[PRD_mcp_transport.md](PRD_mcp_transport.md) (the peer transport, which is **not** an
external API and does not pass through here).

**A grader should be able to audit every outgoing-call limit in this project from this one
page.** §6 is the table of every number with the file and line that states it, and §7 names
the two that have no book source at all and says what was done instead.

---

## 1. One gatekeeper class, two instances (D-68)

`docs/SEGAL_GUIDELINES.md:179-182` is explicit: the rulebook's Gatekeeper (§9.3.1: quota
manager → token bucket → DOS detector) and the engineering standard's generic API
gatekeeper overlap, and the instruction is *"Build **one** gatekeeper satisfying both — the
rulebook's numeric thresholds live in PARAMETERS.md Table 19, and where the two documents
differ, take the stricter value."*

So there is exactly one `Gatekeeper` class (`services/llm/gatekeeper.py`), constructed
twice per process:

| Instance | Params object | Config file | Budget | Built by |
|---|---|---|---|---|
| LLM (Phase 4) | `LanguageParams` | `config/*/language.json` | a `TokenBudget` | `network/language_wiring.py` |
| Mail (Phase 7) | `ReportingParams` | `config/*/reporting.json` | `None` | `services/reporting/end_of_game_chain.build_reporting_chain` |

The two instances are told apart **structurally, not by a flag**. `shared/gatekeeper_params.py`
declares two `Protocol`s: `GatekeeperParams` (Table 19's seven rows) and `BudgetParams`
(Table 18 row 4 plus D-35's two degrade thresholds). `LanguageParams` satisfies both;
`ReportingParams` satisfies only the first, because a Gmail send spends no tokens.
`budget.budget_for_params` reads that difference and hands the mail instance `budget = None`
without any caller saying so.

`Gatekeeper` itself imports no vendor SDK. `services/llm/anthropic_provider.py` owns the
Anthropic dependency and `services/reporting/gmail_sink.py` owns `google-*` (D-70) — each is
the ONE module in `src/` that imports its vendor, so the door can be swapped at one address.

**Rule: no direct API call bypasses the gatekeeper** (`docs/SEGAL_GUIDELINES.md:171`,
QUAL-03). The peer-to-peer MCP transport is deliberately not routed through it: it is not a
third-party API, it has its own Table-18/NET deadline and retry machinery
(`network/deadline.py`), and putting a rate limiter between two agents playing turns would
make the gatekeeper a source of forfeits.

## 2. The Figure-13 chain, in the book's order (D-69)

`ReportingChain.send()` (`services/reporting/chain.py`) composes the book's §9.3.1 order
around the shipped gatekeeper rather than re-implementing any of it:

```
QuotaManager.try_consume()          # stage 1  — pre-call gate, durable, hourly
  → Gatekeeper.submit(...)          # stages 2-4 — queue, semaphore, TOKEN BUCKET, retry
      → DosDetector.observe(...)    # stage 3  — pre-call gate AND post-call observer
        → sink(report)              # stage 4  — DryRunSink (disk) or GmailSink (network)
```

**Why the bucket stays inside `submit()` and is not lifted out to sit between stages 1 and
3.** The bucket is not a separate object in this design's control flow: `submit()` awaits
`bucket.time_until_available()` *per attempt*, inside `_call_with_retry`, so a retry pays
for its own token — "every attempt, including a retry, is a real outgoing request"
(`gatekeeper.py:26-27`). Lifting it out would charge one token for a call that made four
HTTP requests, which is precisely the 429 that rule 28 exists to prevent. The book's chain
ORDER is preserved (quota before bucket, bucket before send, detector observing each
attempt); only the bucket's *ownership* stays where Phase 4 put it, which is what makes
this one gatekeeper instead of two.

The DOS detector sits **outside** `submit()` and therefore cannot read the private
`_bucket`. It observes through `Gatekeeper.bucket_ready`, a read-only property added by
07-01 for exactly this, which reads `time_until_available()` and never `try_acquire()` — so
observing the bucket can never consume the token the next real call needs.

## 3. The token bucket — the law, quoted

`docs/PARAMETERS.md:101-102`:

> Token-bucket rule: `tokens ← min(C, tokens + r·Δt)`, allow iff `tokens ≥ 1`, where `C` =
> capacity (burst size) and `r` = refill rate (sustained rate).

`services/llm/bucket.py` implements exactly that. `C` and `r` are both DERIVED from Table 19
row 1 and nothing else — `capacity = requests_per_minute`, `refill_rate =
requests_per_minute / 60.0` (`gatekeeper.py:76-80`). The 60.0 is a unit conversion
(`_SECONDS_PER_MINUTE`), not a parameter; the same is true of `_SECONDS_PER_HOUR = 3600.0`
in `quota.py`. Neither is a tunable and neither is written in any config file.

## 4. The refusal contract — queue, never crash, never a bare rejection

`docs/SEGAL_GUIDELINES.md:175-176`: *"On overflow: **FIFO queue, not rejection and not a
crash.** Queue depth from config, backpressure alert when full, drain mechanism when the
rate window reopens."*

Every refusal path in `ReportingChain` returns a `SendOutcome`; none raises into the turn
loop. There are four, one per `Refusal` member:

| Refusal | Raised by | Queued? |
|---|---|---|
| `DOS_LOCKED` | the detector has latched | yes |
| `QUOTA_EXHAUSTED` | the hourly window is spent | yes |
| `SEND_FAILED` | the full retry ladder failed | yes |
| `QUEUE_FULL` | the FIFO is already at `queue_depth` | **no** — logged at WARNING (the backpressure alert) |

The drain is **caller-driven** (`ReportingChain.drain()`): no thread, no timer, no
background task. `network/watchdog.py` (`os._exit(1)` after `watchdog_threshold` seconds of
silence) is this process's only liveness owner, and a second one racing it is how a game
dies mid-turn. `drain()` takes the queue in one slice before the first attempt, so a report
that fails again is re-queued for the NEXT drain rather than retried forever inside one.

On the LLM side the same contract has a different shape because a hint is needed *now*:
`GatekeeperOverflow` and a retry-exhausted call both surface to the caller, which converts
them into D-33's deterministic template fallback. Neither reaches the turn loop unhandled.

## 5. Where the mail instance's ladder meets the freeze watchdog

Worst case for one report, every figure a Table 19 row read from `reporting.json`:

```
response_timeout_seconds × (retries_before_failure + 1)   30 × 4 = 120 s
wait_after_error_seconds × retries_before_failure         30 × 3 =  90 s
                                                  total          = 210 s
watchdog_threshold_seconds                                       =  60 s   (3.5× smaller)
```

A shorter total bound would have to be a NEW number, which is the rule-1 violation
[CLAUDE.md](../CLAUDE.md) forbids. So the containment is a **touch per bounded attempt**
instead: `end_of_game_chain.watchdog_touching` wraps the sink and touches on entry and again
in a `finally`, making the largest gap between touches 30 s against a 60 s threshold while
the whole 210 s ladder stays available. `GmailSink` deliberately does **not** sleep on 429 —
it raises `GmailRetryableError` and the gatekeeper's ladder owns the wait. Full rationale in
[PRD_end_of_game.md](PRD_end_of_game.md) §3.

## 6. Every number, and the file and line that states it

Rule 1 ([CLAUDE.md](../CLAUDE.md)): never invent a numeric value. Every row below resolves
to a document line that actually says it. `config/police/reporting.json` and
`config/thief/reporting.json` carry the same citations in their own `_sources` object, so
the config file and this page cannot drift apart silently.

| Value | Where it is used | Shipped | Source | Status |
|---|---|---|---|---|
| `requests_per_minute` | bucket `C` and `r` (both instances) | 30 | [PARAMETERS.md:93](PARAMETERS.md) Table 19 row 1 · agrees with [SEGAL_GUIDELINES.md:173](SEGAL_GUIDELINES.md) | **minimum** |
| `parallel_requests` | `asyncio.Semaphore` | 2 | [PARAMETERS.md:94](PARAMETERS.md) row 2 | **minimum** |
| `wait_after_error_seconds` — LLM | backoff between attempts | 5 | [PARAMETERS.md:95](PARAMETERS.md) row 3 | **minimum** |
| `wait_after_error_seconds` — MAIL | backoff between attempts | 30 | OQ-3: [PARAMETERS.md:95](PARAMETERS.md) row 3 (5 s minimum, negotiable **upward**) + [SEGAL_GUIDELINES.md:174](SEGAL_GUIDELINES.md) `retry_after_seconds: 30` + [:182](SEGAL_GUIDELINES.md) "take the stricter value" | **minimum**, raised |
| `retries_before_failure` | attempt ladder, and the DOS latch | 3 | [PARAMETERS.md:96](PARAMETERS.md) row 4 · equals [SEGAL_GUIDELINES.md:174](SEGAL_GUIDELINES.md) `max_retries: 3` | **minimum** |
| `queue_depth` | `submit()`'s FIFO and the chain's send queue | 100 | [PARAMETERS.md:97](PARAMETERS.md) row 5 | **minimum** |
| `response_timeout_seconds` | `asyncio.wait_for` per attempt | 30 | [PARAMETERS.md:98](PARAMETERS.md) row 6 | negotiable |
| `watchdog_threshold_seconds` | the freeze watchdog (not the gatekeeper) | 60 | [PARAMETERS.md:99](PARAMETERS.md) row 7 | negotiable |
| `requests_per_hour` | `QuotaManager`'s ceiling | 500 | [SEGAL_GUIDELINES.md:173](SEGAL_GUIDELINES.md) | engineering standard |
| token-bucket law | `bucket.py` | — | [PARAMETERS.md:101-102](PARAMETERS.md) | fixed |
| `token_budget_per_series` | `TokenBudget` (LLM only) | see `language.json` | [PARAMETERS.md:83](PARAMETERS.md) Table 18 row 4 | negotiable |
| recipient | the one mail destination | `rmisegal+uoh26finalgame@gmail.com` | [PARAMETERS.md:176-179](PARAMETERS.md) Addresses | **fixed** |
| attachment filename | `result_<game_id>.json` | — | [PARAMETERS.md:168](PARAMETERS.md) | **fixed** |

Two conversions appear in source and are NOT parameters, because neither is tunable and
neither would ever be negotiated: `_SECONDS_PER_MINUTE = 60.0` (`gatekeeper.py:47`) and
`_SECONDS_PER_HOUR = 3600.0` (`quota.py:44`). `TOO_MANY_REQUESTS = 429` (`gmail_sink.py:69`)
is RFC 6585's status code, named rather than inlined, and rule 28 names 429 as the block the
bucket exists to prevent.

## 7. The two values with **no** book source, named as such

### OQ-1 — the daily send ceiling does not exist, so none is written

The book's §9.3.1 describes the quota manager as tracking a *daily* send ceiling.
`docs/PARAMETERS.md` Table 19 has **no daily row**, and no document in this project gives a
daily figure anywhere. An invented daily number would be a rule-1 violation dressed up as
diligence.

**What was done instead:** `QuotaManager` enforces the **hourly** bound `requests_per_hour:
500`, because that one IS sourced ([SEGAL_GUIDELINES.md:173](SEGAL_GUIDELINES.md)).
`reporting.json` has no daily leaf. Should a daily bound ever be structurally required, it
is **derived** as `24 × requests_per_hour` and labelled *derived* in both config and source
— never presented as a book value. There is no engineering default anywhere on this path.

The window is a WALL clock (`time.time`), not `time.monotonic`: the counter is required to
survive a process restart, and a monotonic reading is meaningless across one. It persists
through the project's single durable-write scheme (`shared/durable_write.py`: write → fsync
→ rotate to `.prev` → replace), the same one `step0_collect.record_game_played` and
`QTable.save()` use. Its file is `reporting_quota.json` beside the run output, deliberately
**not** in the shipped `config/` tree.

### OQ-2 — the DOS trip threshold has no number, so the detector carries none

Rule 29 ([RULES.md:65](RULES.md)) mandates a runaway-loop detector whose sanction is an
interface lock. **No document gives it a trip threshold or a lock duration.**

**What was done instead: a structural latch, not a labelled default.** `DosDetector` trips
when the token bucket has been continuously empty across `retries_before_failure + 1`
attempts — i.e. one full retry ladder produced nothing, the same boundary
`Gatekeeper._call_with_retry` already uses. That value is Table 19 row 4, already
floor-checked by the loader, and it is *injected*: the module holds no threshold of its own,
and the only integer literals in `dos.py` are a reset to zero and an increment by one.
`tests/unit/test_reporting_dos.py` asserts structurally that no numeric literal in that file
is ever used as a comparison operand.

**Prefer a structural definition over a labelled default whenever one exists — a number
nobody can source is a number nobody can defend.**

Latching means latching: there is no `unlock()` and no timeout, because rule 29's sanction
is an interface lock. A caller that wants to send again restarts the process.

### OQ-3, for completeness — resolved, and scoped to the mail instance only

`docs/PARAMETERS.md:95` gives `wait after error` as **5 sec, minimum** — negotiable upward,
never downward. `docs/SEGAL_GUIDELINES.md:174` gives `retry_after_seconds: 30`, and
[:182](SEGAL_GUIDELINES.md) instructs taking the stricter value. 30 s is upward of the
Table-19 minimum and the stricter posture toward a third-party API, so it satisfies both
documents. It applies to `config/*/reporting.json` **only**; `config/*/language.json` keeps
Phase 4's shipped 5 s and was not retuned. The same reading resolves `parallel_requests`: 2
(Table 19's minimum) is stricter than SEGAL's `concurrent_max: 5`, so 2 stands.

## 8. What the gatekeeper is measured by

- `tests/unit/services/test_gatekeeper.py`, `test_gatekeeper_retry.py` and
  `tests/unit/test_gatekeeper_order.py` — step order, including that `budget.reserve` stays
  above the queue check; `tests/unit/test_gatekeeper_params.py` for the two protocols and
  `test_gatekeeper_llm_unchanged.py` for Phase 4's byte-identical behaviour
- `tests/unit/services/test_bucket.py` — the Table-19 law; `services/test_budget.py` for D-35
- `tests/unit/test_reporting_quota.py`, `test_reporting_dos.py`, `test_reporting_chain.py`
- `tests/unit/test_gmail_sink.py`, `test_gmail_scope.py` — 429/backoff and rule 30, against
  an injected fake transport, never `DryRunSink`
- `scripts/measure_gate7.py` — the 429/429/200 ladder, the scope gate at both call sites,
  and the queue-and-drain round trip, recorded in
  [`phases/phase-7/gate7_measurement_evidence.json`](phases/phase-7/gate7_measurement_evidence.json)

## 9. Requirements covered

REPORT-02 (gatekeeper composition), REPORT-03 (token bucket), REPORT-04/REPORT-05 (send-only
mail transport), QUAL-03 (API gatekeeper), QUAL-05 (overflow queue), QUAL-11 (no defaulted
config values), DOC-02 (this document).
