# Machine-B artifacts — RECEIVED 2026-08-16, criterion closed

This file was the shopping list for machine B's half of the attempt-4 evidence. All
items landed the same day and live in [`machineB-thief/`](machineB-thief/); the
cross-verification and closure narrative are in
[`GATE-5-MEASUREMENT.md`](../GATE-5-MEASUREMENT.md) → Attempt 4.

## Primary game — `d265603c116a9f99` (16:31 local, the Tee'd console's game)

- [x] `d265603c116a9f99.jsonl` — ends `game_over outcome=capture` + `audit_verdict matched=true` (agrees with A)
- [x] `d265603c116a9f99.ledger.jsonl` — all 6 `h_commit` values recompute and match A's received commits
- [x] `declaration_d265603c116a9f99.json` — digest recomputes; byte-identical to A's peer copy
- [x] `declaration_d265603c116a9f99_peer.json` — byte-identical to A's own declaration

## Bonus second game — `b22361aa93ccf310` (16:29 local)

- [x] Same four files, same results — second agreeing-verdict game

## Extras retained for honesty

- [x] `eb55daeefafb4208.jsonl` + its declaration — B's pre-game session that waited 60 s
      for A and honestly recorded its own `watchdog_incident` before the real games began

## Gaps, stated plainly

- [ ] `consoleB_attempt4.txt` — machine B's console was not Tee'd; unavailable. Machine A's
      console is retained. The measurement doc's stated closing condition (both JSONLs,
      agreeing verdicts, network note) is met without it.
- [x] Machine/network note — confirmed by the operator: A on phone hotspot, B on wired
      ethernet (same boundary as attempts 1–2).
