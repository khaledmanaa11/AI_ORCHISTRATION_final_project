# Token-cost analysis and optimization strategy

**What the language layer costs, measured, and what to do about it.** Segal §17
("token-cost analysis and optimization strategy"). Closes `docs/SUBMISSION-CHECKLIST.md`
row **G5-05**. Rule 54 and PARAMETERS Table 18 row 4 require the actual spend to be reported
by email; this is the analysis behind that number.

Reproduce every figure on this page, offline, with no API key and no call:

```
uv run python scripts/token_cost_report.py            # -> artifacts/token_cost/token_cost.json
uv run python scripts/token_cost_report.py --render    # -> the tables below, verbatim
```

`tests/unit/test_research_docs.py` re-renders the block from the committed artifact and
compares it against this file. `tests/unit/test_token_cost.py` re-derives every ratio from
the same recorded JSON, so no expected value is typed into a test either.

---

## Read these limits first

* **n = 1.** Every real token figure below comes from **one** live game against
  `claude-haiku-4-5-20251001`, played on 2026-08-09 and recorded in
  `docs/phases/phase-4/gate4_measurement_live.json`. Twenty-three provider calls is a thin
  base for a budget plan and it is the only live base this project has.
* **That game ended at turn 14 of a 35-turn ceiling.** Every per-game and per-series figure
  is therefore an **extrapolation** that assumes a flat per-turn rate. One game cannot show
  that the rate is flat.
* **The mocked run is not a second sample.** `gate4_measurement_mocked.json` carries three
  games, and its own note says the per-call counts are **simulated**. They are used here for
  exactly one comparison — the call *rate* — and pooled on nothing.
* **No spend has ever been reported by email.** The Gmail path is dry-run only; nothing has
  been delivered (`docs/phases/phase-7/GATE-7-MEASUREMENT.md`, criterion 1 `PENDING`).
* **The games-played value is deliberately unset** (rule 38). Nothing here counts games
  played or infers one.
* **No league game has been played**, so none of this is a report of league spend.

---

<!-- BEGIN GENERATED: token-cost -->

| Measured, one live game | Value | Where from |
|---|---:|---|
| served model | `claude-haiku-4-5-20251001` | `docs/phases/phase-4/gate4_measurement_live.json` |
| turns played (ended in capture) | 14 | same |
| provider calls | 23 | same |
| input tokens | 11,633 | `response.usage` |
| output tokens | 439 | `response.usage` |
| **input share of spend** | **96.4%** | derived |
| tokens per call | 524.9 | derived |
| tokens per turn | 862.3 | derived |
| calls per turn | 1.643 | derived |
| cost | $0.013828 | `gate4_report.token_cost_usd` |
| effective $/M tokens | $1.1455 | derived |
| calls per turn, 3 MOCKED games | 1.662 (ratio 0.989) | `docs/phases/phase-4/gate4_measurement_mocked.json` |
| tokens per call, live / mocked | **9.83x** | the mock's counts are SIMULATED |

| Projected to a full-length game and a series | Value |
|---|---:|
| move ceiling scaled to | 35 turns |
| tokens per full-length game | 30,180 |
| cost per full-length game | $0.03457 |
| series budget (Table 18 row 4, negotiable) | 200,000 |
| full-length games the budget covers | 6.63 |
| games before `SHORT_PROMPT` (140,000) | 4.64 |
| games before `TEMPLATE_ONLY` (180,000) | 5.96 |
| tokens for 10 games (Table 18 row 5, FIXED) | 301,800 |
| **does the maximum series fit the budget?** | **NO** |

| Where the input goes | decode call | bluff call |
|---|---:|---:|
| system prompt, characters | 1,560 | 1,474 |
| user half, mean characters | 149.7 | 66.0 |
| **system share of input characters** | **91.2%** | **95.7%** |
| shipped estimate, tokens reserved | 727.2 | 685.0 |

Hint sample: **79** real sentences from tracked `docs/phases/phase-5` wire logs, mean 48.7 characters, max 69.

| Estimator calibration (`_estimate_tokens`) | Value |
|---|---:|
| estimated tokens per call | 706.1 |
| measured tokens per call | 524.9 |
| **estimate / measured** | **1.35x** |
| `max_tokens` ceiling as a share of the estimate | 42.5% |
| measured output tokens per call | 19.1 |
| sample | one live game (n=1), 23 provider calls |

<!-- END GENERATED: token-cost -->

---

## What the numbers say

**1. This is an input-cost problem, not an output-cost problem.** 96.4% of the measured spend
is input. Every optimization instinct that targets the reply — shorter hints, tighter
schemas, a smaller `max_tokens` for its own sake — is aiming at 3.6% of the bill.

**2. The system prompts are the input.** 91.2% of a decode call's input characters and 95.7%
of a bluff call's are the system prompt, and both are rebuilt and re-sent on **every single
call**. The variable half — one opponent sentence, mean 48.7 characters across all 79 real
hints this project has ever received — is noise beside them.

**3. The usual first lever is closed.** Both prompt modules state that Haiku 4.5's minimum
cacheable prefix is 4096 tokens, far above either prompt, so prompt caching cannot apply and
every prefix token bills at full price on every turn. That is a *cited vendor fact* from
`services/llm/decode_prompt.py` and `bluff_prompt.py`, not something measured here, and it
should be re-checked against the vendor's current documentation before it is relied on.

**4. The shipped estimator over-reserves by 1.35×, and the cause is identified.** `_estimate_tokens`
reserves `chars // 4 + max_tokens`. The `max_tokens=300` ceiling alone is **42.5%** of the
reservation, while the model actually returned **19.1** output tokens per call — 6.4% of the
ceiling. Because `TokenBudget.reserve()` counts the estimate *before* the call runs and the
level never regresses, the degrade ladder trips roughly a third earlier than the real spend
warrants. This is a safe direction to be wrong in, and it is still wrong by a measurable amount.

**5. A maximal series does not fit the budget.** At the measured rate a full-length game
costs ~30,180 tokens. The **fixed** maximum of 10 games per team (Table 18 row 5) projects to
**301,800** against the shipped 200,000-token budget. The ladder is what absorbs that: it
reaches `SHORT_PROMPT` at ~4.6 full-length games and `TEMPLATE_ONLY` at ~6.0, after which the
hint channel is served entirely from the zero-token template bank. **The design does not
break — but the language layer goes dark for roughly the last four games of a maximal
series**, and nobody had written that down before.

**6. The mock is honest about calls and useless about tokens.** Calls per turn: 1.643 live
against 1.662 mocked, a ratio of 0.989 — the pipeline shape transfers. Tokens per call:
**9.83×** apart. Any budget planned from a mocked run would be out by an order of magnitude.

---

## Optimization strategy

Ordered by measured leverage. Each names what it would change and what it costs.

**S1 — Shorten the system prompts. Highest leverage, and it is a correctness trade.**
The two prompts are 1,560 and 1,474 characters, re-sent per call, and they are 96% of the
input. But they are not padding: the decode prompt's bulk is the prompt-injection defence
(the opponent writes that input and is entitled to try to manipulate us) and the rule-25
clause; the bluff prompt's bulk is the D-39 style guide, whose first-person bullet was added
*because* a hint drifted into the third person in a real round
(`docs/PROMPT_LOG.md`, entry R1). Cutting either trades tokens for a defect this project has
already observed once. **Recommendation: do not cut blind.** If it is cut, cut the decode
prompt's region/heading enumeration first (it is the only part a JSON schema already
constrains) and re-run the EN/HE fixture accuracy against the change.

**S2 — Lower `model.max_tokens`. Highest leverage per unit of risk, and it is blocked on one
missing measurement.** It is 300 in `config/*/language.json` and contributes 42.5% of every
reservation, while real output averaged 19.1 tokens. Cutting it would not reduce the *bill*
at all — output is only 3.6% of spend — but it would stop the ladder degrading the agent
long before the budget is genuinely at risk. **The safe floor cannot be chosen from what is
recorded**: the live run stored a total and a mean, never a per-call maximum, and a
`max_tokens` set below the longest real reply truncates a hint. **Next measurement: record
`max(output_tokens)` per call.** That is a one-line addition to `scripts/gate4_runner.py`'s
accounting and it unblocks the change.

**S3 — Negotiate the token budget upward.** Table 18 row 4 is **negotiable** and the shipped
200,000 is our own default. A maximal series needs ~301,800 at the measured rate. This is the
only lever that fixes the shortfall without touching a prompt, and it costs nothing but a
line in the pre-game declaration.

**S4 — Do nothing and accept the ladder.** `DegradeLevel` already ends at `TEMPLATE_ONLY`,
which is served by the seeded template bank at **zero** tokens and never raises. A series that
exhausts its budget degrades to a legal, hint-every-turn agent rather than failing. This is
the current behaviour and it is defensible; it should be a decision, not a default nobody
examined.

**Rejected: calling the model less often.** `model.every_n_steps` is 1, and raising it would
halve the call count — but `shared/language_model_config.py:78-83` refuses any value above 1
by construction, because §10.4's GATE-4 criterion 3 requires **a hint every turn**. The lever
exists, the rules forbid it, and it is listed here so the next reader does not rediscover it
as an idea.

---

## What was not measured

* **Per-call maximum output tokens** — see S2. The single most valuable addition.
* **A second live game.** Every figure here rests on one. A second would turn "the rate is
  862 tokens per turn" from a point into an interval.
* **Whether the per-turn rate is flat.** The one game ran 14 turns; the projections assume
  turns 15–35 cost the same. A capture-at-14 game may be systematically cheaper than a game
  that runs to the ceiling.
* **The `SHORT_PROMPT` rung's actual saving.** The ladder's middle rung is implemented and
  tested, but no live game has ever reached it, so how much it saves is unmeasured.
* **Cost in USD at current pricing.** `scripts/gate4_report.py` carries Anthropic's published
  Haiku 4.5 rates as read in 2026-08 and says in its own comment that they must be
  reconfirmed before the league spend email. This document inherits that caveat.

---

## Related

* `docs/SENSITIVITY.md` — the game-parameter side of the same question
* `docs/PROMPT_LOG.md` — what the prompts say and why, with their revisions
* `notebooks/analysis.ipynb` — the burn-down chart, offline
* `src/pursuit/services/llm/budget.py` — the ladder these projections are read against
* `docs/PARAMETERS.md` Table 18 — the budget's status and the fixed game maximum
