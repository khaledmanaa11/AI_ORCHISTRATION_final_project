# Deferred items — phase 8

Out-of-scope discoveries, logged rather than fixed. Each names what was measured and who owns it.

## 1. `test_belief_enabled_completes_within_the_per_turn_time_budget` is load-sensitive

**Found by:** 08-10, in the full mono-repo suite run at `534ce7f`
**Status:** deferred — not caused by this plan's changes, and the file is out of its scope

The full suite reported one failure:

```
tests/integration/test_belief_policy.py:172
assert max(thief_ms) < thief_params.max_decision_ms
AssertionError: assert 57.33779999718536 < 50
  where 57.33... = max([2.329, 2.298, 2.850, 4.033, 3.149, 3.495, ...])
```

**One sample out of many spiked to 57 ms against a 50 ms budget; the typical sample is 2–4 ms.**
The run was made on a machine that had just executed two full `pytest --cov` runs inside the
split repositories, so the spike is scheduler noise rather than a decision-path regression.

Measured immediately afterwards on a quiet machine: `tests/integration/test_belief_policy.py`
**3 passed** twice in a row, 1.06 s and 1.04 s. The same test also passed inside **both** split
repositories in the same session (2533 passed, 0 failed, twice).

**Why it is not fixed here.** The file is outside 08-10's scope and the plan's brief names it
explicitly as not to be touched. The defect is real but structural: a wall-clock maximum over a
whole game asserted against a fixed budget will occasionally lose to the operating system.
A median or a percentile would measure the decision path rather than the machine — a change to
a phase-5 measurement contract, which belongs to whoever owns `max_decision_ms`, not to the
repository split.

**`max_decision_ms = 50` is a config value and was NOT touched.** Loosening a parameter to make
a test pass is the failure mode this repository is built to refuse.
