---
phase: 08-submission-and-league-operations
plan: 08
subsystem: documentation
tags: [per-mechanism-prd, segal-2.3, sdk, tunnel, ngrok, gate-5, mechanism-register, contract-tests]

# Dependency graph
requires:
  - phase: 08-submission-and-league-operations
    provides: "08-01's scripts/submission_mechanisms.py -- the package walk and docs/mechanism-prd-map.json, the register this plan answers"
  - phase: 08-submission-and-league-operations
    provides: "08-07's tests/unit/doc_citation_helpers.py -- the backticked-path resolution the three PRDs are held to"
  - phase: 05-cloud-exposure-and-tunneling
    provides: "TunnelManager, tunnel_wiring, SharedSecretMiddleware and GATE-5-MEASUREMENT.md's four attempts, which PRD_tunnel.md specifies rather than re-derives"
provides:
  - "docs/PRD_sdk.md -- Sec2.3 for Table 5's first row, covering both halves of the package and stating the enforcement limit honestly"
  - "docs/PRD_tunnel.md -- the mechanism PRD_mcp_transport.md:28 explicitly excludes"
  - "docs/mechanism-prd-map.json answering for every package the walk finds: 10 of 10"
  - "tests/unit/test_mechanism_prd_contract.py -- the superseded-banner and transport-exclusion derivations pinned"
affects: [08-09, 08-10, 08-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "a PRD's own justification asserted as a test: PRD_tunnel.md exists because PRD_mcp_transport.md excludes the tunnel, so that exclusion is a test"
    - "known limits written into the PRD as OPEN rather than implied away (the SDK's protocol-facing half)"
key-files:
  created:
    - docs/PRD_sdk.md
    - docs/PRD_tunnel.md
    - tests/unit/test_mechanism_prd_contract.py
  modified:
    - docs/mechanism-prd-map.json
    - docs/SUBMISSION-CHECKLIST.md
    - docs/phases/phase-8/TODO.md

decisions:
  - "docs/PRD_display_belief.md stays UNCITED as gui/ coverage. It governs what a view may contain (rules 8-9), not how the seven gui/ files render; citing it would close the row with a document answering a different question."
  - "PRD_sdk.md records that nothing automated stops a future game rule being written into network/. Table 5 marks its own unmeasurable rows Code review and 08-01 prints them UNJUDGED; the same honesty applies to a PRD's own claim about itself."
  - "PRD_tunnel.md copies GATE-5's three 'what attempt 4 does not prove' items verbatim rather than summarising them, because the arc attempt 2 -> 05-11 -> attempt 4 invites the reading that the repair path was proven live. It was not."
  - "The mechanism register's gui entry was the actual open row, not the PRD. PRD_gui.md shipped at aa75852 with prds: [] still in the register, so the gate still reported GAP."

metrics:
  duration: "~1h"
  completed: 2026-08-17
---

# Phase 8 Plan 08: The Three Missing Per-Mechanism PRDs Summary

`docs/PRD_sdk.md` and `docs/PRD_tunnel.md` written from the source, and the mechanism register
updated so all three §2.3 rows — sdk, gui and the tunnel — close together.

**No `08-08-PLAN.md` exists.** Executed from `08-PLAN-OUTLINE.md` §9's 08-08 entry.
`docs/PRD_gui.md` was already written and committed at `aa75852` by the orchestrator and was
**not rewritten**; it is the tone and evidence standard the two new PRDs match.

## The finding: a PRD can ship and leave its row open

`docs/PRD_gui.md` was committed at `aa75852`. `check_submission.py` still reported
`G1-M[src/pursuit/gui]` as **GAP**, with the evidence line
`docs/mechanism-prd-map.json entry names neither a PRD nor a reason`.

The gate is right and the design is right: the inventory is walked from `git ls-files` and the
answer for each package is read from a committed register, so **writing the document is not the
same as answering for the package.** That is the same discipline that makes a newly added
package become a GAP row by itself. Recorded because the tempting reading — "the PRD exists,
so the row must be stale" — would have led to weakening the gate instead of updating the
register.

## What landed

**One commit, `f176923`** — the two PRDs, the register, and the contract.

### `docs/PRD_sdk.md`

Table 5's first row and §4's mandated single entry point. Eleven modules with their measured
code-line counts, split across two responsibilities that share one rule: **the SDK is the only
layer permitted to turn the engine's true joint state into anything anyone else may consume.**

What it documents that is not obvious from the code:

- **why the view logic is in `sdk/` and not `gui/`** — `pyproject.toml` omits `*/gui/*` from
  coverage, so logic there is invisible to the `fail_under = 85` gate, and
  `scripts/check_line_limit.sh` scans `src/`, `tests/`, `training/` only, so `scripts/` escapes
  **both** gates;
- the measured consequence: `view_render.shade` reserves the background colour for exactly
  zero, because a ramp that rounded small probabilities down would draw a **smaller** support
  than the published grid carries — the drawn/published ratios were 22.50 / 2.66 / **1.57**;
- the closed field set is **half** the mitigation, with the 07-11 incident named;
- a five-row table of what is enforced, by which gate, and whether that gate can fail —
  including that `scripts/check_local_truth.py` is an **import/attribute gate, not a disclosure
  gate**, and that 08-01's own G2-01 row is a presence check and is not evidence about the
  layer's contents.

**It states its own limit as OPEN:** nothing automated prevents a future game rule being
written into `src/pursuit/network/`. The enforced half is the GUI-facing one.

### `docs/PRD_tunnel.md`

The genuine hole. `docs/PRD_mcp_transport.md:28` puts *"ngrok/Localtonet tunneling"* out of
scope in as many words, so `network/`'s own PRD provably does not specify
`tunnel_manager.py`. Covers:

- the opt-in signal (the static-domain env var's **presence**; `tunnel.json` has no enable
  flag because D-55 makes it strings only);
- full dependency injection, so the whole suite drives the class with fakes — zero processes,
  zero sleeps, zero `ngrok.exe`;
- why the freeze watchdog is deliberately untouched: a tunnel drop is not a process freeze;
- **05-11's bounded repair and the drop that proved it had no caller** — attempt 2, game
  `5efbc5811fabfac4`, machine A's ingress dying at turn 4 while `ensure_connected()` sat
  designed, tested and uncalled;
- the D-56 shared-secret ASGI door, at the boundary rather than in five tool bodies;
- secrets as **names**: six string fields, three of them env-var names, not one value;
- `healthy()`'s **detection envelope**, stated rather than implied: agent-process and local-API
  death yes, a live-process upstream blip no, and the fresh-agent-without-our-domain blind spot
  named;
- §5's parameter table — every value reused from Table 19; **the mechanism introduces no number
  of its own**, and `tunnel.json` contains none beyond its version string;
- GATE-5's two criteria, including attempt 4's two games with agreeing verdicts and 26/26
  independent re-verification checks per game.

**§6.1 copies GATE-5's three limits verbatim** rather than summarising them: the 05-11 repair
path **never fired** (attempt 4 is evidence a *healthy* tunnel completes a round), the second
game is a deterministic replay, and machine B's console was not retained. And it adds the one
the gate document does not have to state: **that was our own second machine, not another
team's agent. No league game has been played.**

### The register

`docs/mechanism-prd-map.json`: `sdk` → `PRD_sdk.md`, `gui` → `PRD_gui.md`. The `network` note
now names `PRD_tunnel.md` as the tunnel's owner and records that the G1-M-TUNNEL row derives
the exclusion from the transport PRD's own text rather than trusting the note. The `shared`
entry's reason no longer describes the tunnel PRD as missing.

## Proof the new assertions fail on the old state

Run before the register moved and before the two PRDs were tracked:

```
uv run pytest tests/unit/test_mechanism_prd_contract.py
5 failed, 6 passed
```

The six that passed are pre-existing invariants this file now pins (the walk finds ≥ 10
packages; the register answers for the tree and nothing else; no cited PRD is superseded; the
banner is intact) — pinning, not regression, and labelled as such. The five that failed are the
five new claims.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 1 — Bug] A fabricated script name in `PRD_sdk.md`'s neighbour document**
- **Found during:** the citation contract, on `docs/QUALITY-25010.md`
- **Issue/Fix:** recorded in `08-07-SUMMARY.md` (`scripts/check_publication_safety.py` never
  existed). Noted here because the same check guards all three PRDs.

**2. [Rule 1 — Bug] Two wrong signatures and one wrong config path in `PRD_sdk.md`'s first draft**
- **Found during:** reading the source to verify the interface block, before commit
- **Issue:** `resolve_turn` was written with a `thief_action` parameter (the real one is
  `thief_move`); `terminal_outcome` was missing its `barrier` and `raced` parameters;
  `build_local_view` was missing `idle_seconds`; and the belief publication floor was
  attributed to a `config/police/display.json` that **does not exist** — the floors live in the
  `display` block of `config/police/belief.json`.
- **Fix:** all four corrected from the source, and the loader's refusal of a too-low floor added
  because it is the part that matters.
- **Commit:** `f176923`

**3. [Rule 1 — Bug] A stale count carried forward into `PRD_tunnel.md`**
- **Issue:** GATE-5's criterion-1 record says the smoke test returned "the five D-05 tool
  names" — true on 2026-08-09, but `tools.py` has carried **nine** handlers since Phase 6.
  Quoting it unqualified would have shipped a number that no longer describes the tree.
- **Fix:** "the tool list — five names at that date, nine since Phase 6 added the commit-reveal
  handlers".
- **Commit:** `f176923`

**4. [Rule 3 — Blocking] The citation floor was set too high for a document this plan may not edit**
- **Issue:** the anti-vacuity floor of 8 backticked paths failed on `docs/PRD_gui.md`, which
  writes many references as bare module names (`turn_language.py:57`) and legitimately has 5.
- **Fix:** two floors — 5 for all three PRDs, and **15** for the two written against the
  contract. The alternative, editing `PRD_gui.md` to satisfy a checker, was refused: the
  instruction not to rewrite it is the right one, and lowering a floor with the reason written
  in is honest where a silent rewrite is not.
- **Commit:** `f176923`

## Gates

| Gate | Result |
|---|---|
| `uv run pytest --cov` | **2413 passed / 0 failed** (this plan's 11 tests included) |
| coverage | **97.44%**, unchanged |
| `ruff check .` | 0 violations |
| `check_line_limit.sh` | exit 0 tree-wide, `tests/unit/test_mechanism_prd_contract.py` also checked by path |
| `check_submission.py` | exit 1 at **65 PASS / 8 GAP / 13 UNJUDGED** |
| `docs/mechanism-prd-map.json` | valid JSON; answers for **10 of 10** discovered packages, with zero stale entries |

## GAP movement — row by row

**62 PASS / 11 GAP → 65 PASS / 8 GAP. Three rows, and exactly the three 08-08 owned.**

| Row | Was | Now | Why |
|---|---|---|---|
| `G1-M[src/pursuit/sdk]` | GAP | PASS | `docs/PRD_sdk.md` written and cited from the register |
| `G1-M[src/pursuit/gui]` | GAP | PASS | the **register** now cites the PRD that shipped at `aa75852` |
| `G1-M-TUNNEL` | GAP | PASS | `docs/PRD_tunnel.md` exists; the row still derives its own premise (the module is tracked, the transport PRD still excludes tunneling) |

Group 1: 23 PASS / 5 GAP → **26 PASS / 2 GAP**. Every other group unmoved. The two remaining
group-1 rows are `G1-03b` (07-10's screenshots) and `G1-14` (08-09's prompt log).

**The eight that remain, and who owns each:** G1-03b + G5-04 (07-10's screenshots, jointly with
08-06), G1-14 + G5-02 + G5-03 + G5-05 (08-09), G6-08 the tag (08-11/08-12), T5-06 the version
reconciliation (08-11).

## Counters (rule 38)

Shared with 08-07, measured once across both plans: suite **1926 → 1926 / 1919 → 1919**
(delta 0/0); one real game **1926 → 1927 / 1919 → 1920** (delta +1/+1), `game_id`
`2582a94c8a5ec618`, both seats `matched=true`, `games_played_declared` deliberately unset.

## Nothing pushed

**No `git push`, no tag, no remote command was issued by this plan.** `git tag -l` is empty.
The out-of-band push of `acc5913` to `origin/main` is documented in `08-07-SUMMARY.md`; it
happened 6m39s after that commit, no git hook in this repository pushes, and `codex.exe` is
running on this machine despite CLAUDE.md retiring it. This plan's three commits are **not** on
`origin/main`, and no corrective remote action was taken.

## Self-Check: PASSED

Three created paths verified present, tracked and not gitignored; `f176923` verified reachable;
`docs/mechanism-prd-map.json` re-parsed as valid JSON and its answered-package count re-derived
from the walk (10/10) rather than counted by hand.
