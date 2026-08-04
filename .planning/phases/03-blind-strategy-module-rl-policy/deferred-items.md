# Deferred Items — Phase 03 (blind-strategy-module-rl-policy)

Out-of-scope discoveries logged per the executor's deviation-rules scope boundary: found during
one plan's execution, caused by that plan's change, but owned by a different plan's declared
file-ownership scope. Not fixed here — flagged for the owning plan to correct in passing.

## From 03-13 (turns_remaining + config surface)

1. **`docs/PRD_rl_strategy.md` Sec2 still documents the deleted `turn_bucket` key format**
   (the key template, the field table, and the worked example all show the pre-03-13 bucket
   value). Caused by: Task 1's `turn_bucket` -> `turns_remaining` replacement. Owner: **03-22**
   (D-27 deviation-defence deliverable, which bumps `docs/PRD_rl_strategy.md` to v2.00 describing
   search-over-learned-evaluation — the natural place to also correct Sec2). Not fixed in 03-13
   because `docs/PRD_rl_strategy.md` is not in 03-13's `files_modified` list and file-ownership
   (D-18, outline §7) assigns doc plans to their own wave.

2. **`training/harness.py`'s `EpisodeConfig` docstring still says "turn_bucket_fractions
   encode_state needs"** — stale prose only; `encode_state`'s call signature is unchanged so
   nothing there is functionally broken. Caused by: Task 1's same change. Owner: **03-14**
   (`training/harness.py` is 03-14's file this same wave, per outline §7's file-ownership table:
   "training/harness.py is touched by 03-14 (w1), 03-15 (w2), 03-20 (w4) — sequential by wave,
   never parallel"). Not fixed in 03-13 to avoid a same-wave parallel edit to a file 03-13 does
   not own.
