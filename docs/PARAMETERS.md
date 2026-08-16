# Binding Parameters — Appendix F

> **This file is the single source of numeric truth for the project.**
> Source: `police_thief_p2p.pdf`, Appendix F (ו), book pages 135–141.
>
> Throughout the book, numbers appear in the prose only as *illustrations*, written as
> bracketed placeholders like `[board size]`. The real value is fixed **here and only
> here**. Never read a number out of the book's body text.

## How to read the Status column

| Status | Meaning |
|---|---|
| **fixed** (קבוע) | Binding. **Any deviation disqualifies the team.** Not negotiable under any circumstance. |
| **minimum** (מינימום) | The sides may negotiate the value **upward** by mutual agreement, but **never below** the value shown. Absent an explicit agreement, the code must default to the value shown. |
| **negotiable** (משא ומתן) | The sides may agree on any value. Absent an explicit agreement, the code must default to the value shown. |

The "Example value" column is the **pilot default**. For `minimum` rows it is a floor,
not a suggestion.

---

## Table 13 — Board, axis system, starting positions

| # | Parameter | Meaning | Example value | Status |
|---|---|---|---|---|
| 1 | `[board size]` | Square game grid edge | **7×7** | minimum |
| 2 | `[number of agents]` | Players in the match | **2** | **fixed** |
| 3 | `[axis origin]` | Corner holding cell (0,0) | top-left | negotiable |
| 4 | `[axis start index]` | Index each axis counts from | 0 | negotiable |
| 5 | `[start position – thief]` | Thief's opening cell | centre (3,3) | negotiable |
| 6 | `[start position – cop]` | Cop's opening cell | corner (0,0) | negotiable |

## Table 14 — Game arena and verbal hints

| # | Parameter | Meaning | Example value | Status |
|---|---|---|---|---|
| 1 | `[game arena]` | Real-world region the game is set in — supplies genuine directional cues for verbal hints. Empty `""` = generic directional cues | New York | negotiable |
| 2 | `[hint word limit]` | Max words in any verbal hint sent over the network. Applies to the template **and** to the system prompt given to the language model | **15** | negotiable |

## Table 15 — Movement and barriers

| # | Parameter | Meaning | Example value | Status |
|---|---|---|---|---|
| 1 | `[movement range]` | A single orthogonal step **or** stay in place; **no diagonals** | 4 + stay | **fixed** |
| 2 | `[barrier quota]` | Max barriers the cop may place across the game | **14** | minimum |
| 3 | `[move ceiling]` | Max turns in the match | **35** | minimum |
| 4 | `[survival threshold]` | Turns the thief must survive to win | **35** | minimum |

## Table 16 — Dynamic pheromones (scent)

All three are **fixed** — the decay model is cryptographically locked before the game
starts (rule 23), and any deviation in the formula voids the game.

| # | Parameter | Meaning | Example value | Status |
|---|---|---|---|---|
| 1 | `[scent strength at source]` | Pheromone intensity in the emitting cell | **0.9** | **fixed** |
| 2 | `[scent decay rate]` | Decay applied every turn | **0.10** | **fixed** |
| 3 | `[scent field size]` | Emission window around the agent | **5×5** | **fixed** |

## Table 17 — Scoring (capture, survival, tie)

All **fixed**. These values are also the natural reward signal for a reinforcement-learning
policy — §1.3 states the reward function R "translates directly from the scoring table."

| # | Parameter | Meaning | Value | Status |
|---|---|---|---|---|
| 1 | `[capture score – cop]` | Cop makes a successful capture | **20** | **fixed** |
| 2 | `[capture score – thief]` | Thief's score when captured | **5** | **fixed** |
| 3 | `[survival score – cop]` | Cop's score when the thief survives | **5** | **fixed** |
| 4 | `[survival score – thief]` | Thief survives successfully | **10** | **fixed** |
| 5 | `[tie score]` | Each side, when aggregate score across all sub-games against one opponent ends level | **2** | **fixed** |

Technical loss (forgery, hash mismatch, false declaration) = **0/0**. See rules 19, 22, 38.

## Table 18 — Network and league

| # | Parameter | Meaning | Example value | Status |
|---|---|---|---|---|
| 1 | `[number of opponents]` | Opponents in a series | **6** | **fixed** |
| 2 | `[diversity reward]` | Bonus for a win against an opponent not yet faced | **10** | **fixed** |
| 3 | `[minimum games]` | Minimum games per team to earn a project grade | **2** | **fixed** |
| 4 | `[token budget per series]` | Language-model token budget a lead team may require; actual spend must be reported by email | ~200,000 | negotiable |
| 5 | `[max games per team]` | Max games any one team may play | **10** | **fixed** |

Against each opponent there is **one scoring game only** — no rematches for points.
Unscored warm-up games are permitted and encouraged (rule 52).

## Table 19 — Gatekeeper: rate limiting and protection

| # | Parameter | Meaning | Example value | Status |
|---|---|---|---|---|
| 1 | `[requests per minute]` | Max outgoing API request rate | **30** | minimum |
| 2 | `[parallel requests]` | Max concurrent requests | **2** | minimum |
| 3 | `[wait after error]` | Backoff before a retry | **5 sec** | minimum |
| 4 | `[retries before failure]` | Retry attempts before giving up | **3** | minimum |
| 5 | `[queue depth]` | Request queue size under load | **100** | minimum |
| 6 | `[response timeout]` | Deadline on any network request | 30 sec | negotiable |
| 7 | `[watchdog threshold]` | Freeze duration before the watchdog intervenes | 60 sec | negotiable |

Token-bucket rule: `tokens ← min(C, tokens + r·Δt)`, allow iff `tokens ≥ 1`,
where `C` = capacity (burst size) and `r` = refill rate (sustained rate).

---

## Derived protocol constants — **not** Appendix F values

> Everything above comes from the book. This one section does not, and is marked so it
> can never be mistaken for a negotiable parameter. It has **no Status column on purpose**:
> a derived constant is not `fixed`, `minimum` or `negotiable` — it is *entailed* by a
> protocol rule stated elsewhere, so there is nothing to negotiate. It is recorded here,
> and only here, because a reader reconciling this repo against the book will look for
> every number in this file. It stays a **source constant with no config leaf** (rule 1).

| Constant | Where | Value | Entailed by |
|---|---|---|---|
| `_HINT_LOOKBACK_TURNS` | `src/pursuit/network/turn_hint_buffer.py` | **1 turn** | Message order, §6.2 / D-47 |

**Derivation.** A side emits its hint for turn *N* at the **tail** of turn *N* — after
`REVEAL(N)` has gone out and after a language-model compose has run. By the time the
receiver pulls it off its queue, that receiver's own `maybe_resolve` has already advanced
it to *N+1*. A zero-lookback receive guard (`turn < ctx.state.turn`) is therefore
structurally **unsatisfiable for a responder**: every correctly stamped inbound hint is
discarded before it can be decoded. One turn is the *minimum* that makes the channel
deliverable at all; anything older than that is genuinely stale and is still dropped.

**Measured, twice, unconfounded.** (1) `decode_turn_hint` emits `no_hint` on exactly one
branch — the buffer pop returning nothing — which sits upstream of every provider and API-key
concern, so the responder's 5-of-5 `no_hint` in the 2026-08-13 round proves the *buffer* was
empty; a key-starved decode logs `no_evidence` **with** the text instead. (2) In the post-fix
2026-08-16 attempt-4 round the responder's six inbound hint records all sit at
`record_turn == envelope_turn + 1` — 6 of 6, exactly on this boundary — while the
initiator's five sit at delta 0.

**Not the same case as `_MAX_PEER_GAME_ID`** (`game_identity_validate.py`), which is
deliberately *not* recorded here: that one is a structural limit derived from a filesystem's
255-byte path component, nobody should ever want to tune it, and no legal game's outcome
depends on it. This one describes a message ordering two independent implementations must
agree on. The two are treated differently on purpose.

---

## Mandatory rules attached to this table (Appendix F §2)

1. Every team must define **all** values above in its configuration file. Both teams must
   verify the values are identical and lock them cryptographically.
2. Each new game, the lead team may change settings, provided they still comply with the
   agreement reached with the opposing team.
3. Give the configuration file a **different name per game**, so any game can be
   reconstructed easily.
4. The configuration file of every game **must** be attached to the GitHub repository.
5. Code may change between games. Therefore **every game** requires an email to the
   lecturer carrying the **GitHub commit hash** the code ran on for that game.

---

## Required JSON artifacts

All four carry a shared `game_uid`, and each filename embeds the game identifier
`game_id` plus the match number `<NN>`, so files from different matches can never be
confused.

| File | Role |
|---|---|
| `declaration_<game_id>.json` | Pre-game declaration: both teams' identities, repo URLs, MCP server addresses, hardware spec, language model, agreed token ceiling, start/end times. Seals everything that does not change during the game. |
| `config_<game_id>_g<NN>.json` | The agreed configuration — every numeric parameter above, cryptographically locked and identical on both sides. |
| `log_<game_id>_g<NN>.json` | Turn-by-turn journal: commitments, moves, hints, verdicts, nonce and hash. Enables full cryptographic verification in the replay simulator. |
| `result_<game_id>.json` | Final results summary across all sub-games. **This is the mandatory report emailed to the lecturer.** |

## Addresses

| Purpose | Value |
|---|---|
| Reference implementation | `https://github.com/rmisegal/Game-P2P-Cop-Chase` |
| Lecturer — general correspondence, repo sharing | `rmisegal@gmail.com` |
| **Agent auto-report target** (`[agent reporting address]`) | `rmisegal+uoh26finalgame@gmail.com` |

The reporting address is the **single mandatory destination** for game reports, and must
be configured as the fixed recipient in **both** agents' mail-sending code.
