# The 55 Mandatory Rules — Appendix E

> Source: `police_thief_p2p.pdf`, Appendix E (ה), book pages 126–134.
> Title in the book: *"Map of the mandatory rules — do, don't, and recommendations."*
>
> This appendix gathers every binding rule scattered through the book into one list.
> Failing these carries clear systemic meaning — disqualification, technical loss, or
> lost points. All numeric values referenced here live in [PARAMETERS.md](PARAMETERS.md).

**Action legend:** **MUST** (חובה) · **FORBIDDEN** (איסור) · **RECOMMENDED** (המלצה)

**The default rule:** anything not written here explicitly as mandatory *is not mandatory*.
Where the book does not state a rule, the sides are free to agree with the opponent on
different behaviour, or to act in their own interest within the rules.

---

## 1. Network architecture, decentralization and local epistemology

| # | Action | Rule | Sanction |
|---|---|---|---|
| 1 | **MUST** | Run the thief's code and the cop's code in **two separate processes** | Total failure and a breach of the Zero-Trust model |
| 2 | **FORBIDDEN** | Share memory or variables between the two sides — under any circumstance | **Immediate disqualification** for information leakage |
| 3 | **MUST** | Define the orchestrator component as the single entry point to the subsystem | Instability and failure |
| 4 | **MUST** | Manage game state with a proper state machine | Technical loss from an obscure system state |
| 5 | **MUST** | Report every attempt to transition to an illegal state | Logic error leading to a loss |
| 6 | **MUST** | Implement a deadline-tracker to prevent freezing while waiting on the opponent | System paralysis, loss on timeout |
| 7 | **MUST** | Run a watchdog monitoring process crashes and rescuing data | Game crash and loss of official documentation |
| 8 | **MUST** | Display **only local truth** in the live user interface | Disqualification for information leakage |
| 9 | **FORBIDDEN** | Display the full objective board state in the live interface | **Project disqualification** for illegal advantage |
| 10 | **MUST** | Use a tunneling tool to expose the local server to the public internet | Inability to compete in the league |

## 2. Spatial mechanics, physics and board constraints

| # | Action | Rule | Sanction |
|---|---|---|---|
| 11 | **MUST** | Verify the configuration file is identical **byte-for-byte** on both sides | Game disqualification for symmetry breach |
| 12 | **MUST** | Raise `minimum` parameter values by agreement only — **never** lower them | Deviation from threshold conditions → score disqualification |
| 13 | **MUST** | Move only in orthogonal directions | Illegal move and technical loss |
| 14 | **FORBIDDEN** | Make diagonal moves | Move rejected by the opponent, loss |
| 15 | **MUST** | Declare every barrier placement openly | Board forgery and automatic loss at audit |
| 16 | **FORBIDDEN** | Lie about where a barrier was placed | Severe disqualification cause |

## 3. Cryptography, log integrity and zero-knowledge

| # | Action | Rule | Sanction |
|---|---|---|---|
| 17 | **MUST** | Use a commit-reveal protocol based on SHA-256 | Absence of the mechanism renders the solution illegal |
| 18 | **MUST** | Keep the nonce absolutely secret until the end of the game | Disqualification for dictionary-attack exposure |
| 19 | **MUST** | Technically disqualify a game on **any** hash mismatch at audit | The iron law: **score 0** to the forging team |
| 20 | **MUST** | Build a viewer application replaying the game log and verifying it | Threshold condition for approving and submitting the project |
| 21 | **MUST** | Declare the truth **only** at the moment of capturing a thief | Immediate disqualification for denying reality |
| 22 | **FORBIDDEN** | Make a false capture declaration | **Immediate disqualification**, zero score, technical loss, no appeal |
| 23 | **MUST** | Cryptographically lock the scent-emission model before the game starts | Deviation in the decay formula voids the game |
| 24 | **MUST** | Perform the hardware declaration cryptographically before the game starts | Loss of eligibility for the computational-fairness bonus |

## 4. Strategy, language and the public network

| # | Action | Rule | Sanction |
|---|---|---|---|
| 25 | **RECOMMENDED** | Do **not** hand the movement decision to the language model — use it only for text processing and building a behavioural profile | No mandated sanction, but blind reliance invites hallucinations, illegal moves, and technical loss |
| 26 | **MUST** | Conduct communication in free natural language only | Preserves the psychological nature of the challenge |
| 27 | **FORBIDDEN** | Use direct numeric coordinates in the protocol | Disqualifies the game's nature as defined in the rulebook |
| 28 | **MUST** | Implement a token-bucket rate limiter for outgoing mail reports | Prevents a 429 block that would paralyse league reporting |
| 29 | **MUST** | Define a DOS detector guarding against runaway network resource consumption | Interface lock to prevent account blocking |
| 30 | **MUST** | Use **send-only** permission scope for the mail interface | Security breach that disqualifies the code |

## 5. League fairness, administration and competitive integrity

| # | Action | Rule | Sanction |
|---|---|---|---|
| 31 | **MUST** | Play the minimum number of games against **different** teams | Below the minimum → no passing grade |
| 32 | **MUST** | Report game results automatically via the mail interface | No report → the points from that game are disqualified |
| 33 | **MUST** | Design the game report as valid structured JSON | Code cannot parse free text → immediate disqualification |
| 34 | **FORBIDDEN** | Send a final report as free text — only as an attached JSON file | A non-JSON report is rejected in processing → zero score |
| 35 | **MUST** | Agree the result with the opponent; **each team sends its own separate report**. Non-reporting, or contradictory reports, by **one** team disqualifies the game and scores **0 for both teams** | The main enforcement mechanism preventing reporting fraud |
| 36 | **MUST** | Perform a comprehensive mutual log audit at the end of every game | Precondition before agreeing the shared JSON result |
| 37 | **MUST** | Declare accurately, at the start of each game, how many games have actually been played so far | Threshold condition for computing the true competition factor |
| 38 | **FORBIDDEN** | Falsely declare the number of games played | **Absolute disqualification** for an ethical and integrity breach |
| 39 | **FORBIDDEN** | Push secrets and credentials to the repository — even a private one shared only with the lecturer | Severe security failure and project failure |
| 40 | **MUST** | Add credential and secret files to `.gitignore` | Protection against leaking mail API credentials |
| 41 | **MUST** | Tag the submitted version with an appropriate Git tag | Necessary for the lecturer to check the final version |
| 42 | **MUST** | Write and attach a comprehensive academic report as a readable file in the repo — model description, tables, strategy, images, and learning curves *(curves required only if RL was used — §9.4.2 item 4)* | Without it the project is not academically complete |
| 43 | **MUST** | Download the submission form, fill it, save as PDF; do not alter or forge fields | Bureaucratic condition for a grade |
| 44 | **MUST** | Submit the assignment **separately for each team member** | Without personal submission the student earns no grade |
| 45 | **MUST** | Define a unique 8-character team identification code, no spaces | Any organizational failure blocks automatic attribution of reports |

## 6. Additions found when cross-checking the book

Rules present in the book's body but missing from the original map; added here for
completeness, with their source chapter.

| # | Action | Rule | Source |
|---|---|---|---|
| 46 | **MUST** | A barrier placed on the cell where the thief stands at the moment of contact counts as a **capture** (the cop wins) | Ch. 3 |
| 47 | **MUST** | A thief left with **no legal move** counts as captured | Ch. 3 |
| 48 | **MUST** | Score every end scenario per the scoring table — capture 20/5, survival 10/5, technical loss 0/0 | Ch. 3 + Appendix F |
| 49 | **MUST** | Submit **two separate GitHub repos** — cop and thief — with a cross-link in each README, two links in the submission form, and four links in both teams' JSON | Ch. 9 |
| 50 | **MUST** | Include in every repo at minimum: `README`, config file (`config/`), PRD files, a PLAN file, and TODO files | Ch. 9 |
| 51 | **MUST** | Send the automatic completion reports to the lecturer's `[agent reporting address]` | Ch. 9 |
| 52 | **MUST** | Hold **one scoring game only** against each opponent (no rematches for points); unscored warm-up games are permitted | Ch. 9 |
| 53 | **MUST** | Record in the Step-0 declaration the **commit hash** the game ran on. Changing code between games is allowed, but every game must update the hash | Ch. 5 |
| 54 | **MUST** | Report in the final JSON the total tokens consumed in the game (and across the series) | Ch. 5, Ch. 9 |
| 55 | **MUST** | Give a self-assessment score for **code quality only** — not for league game results | Ch. 11 |

---

## Quick reference: the cheapest ways to score zero

Ranked by how easily they happen by accident rather than intent:

1. **A missing game report** (35) — zeroes *both* teams, even the one that reported.
2. **Shared state between your own cop and thief** (2) — easy to do accidentally with a
   shared module holding live game state; disqualifies immediately.
3. **Showing the true board state in the live GUI** (9) — the tempting debugging shortcut.
4. **A hash mismatch at audit** (19) — usually a canonical-JSON serialization bug, not fraud.
5. **A wrong `fixed` parameter value** (12) — see [PARAMETERS.md](PARAMETERS.md).
6. **Credentials committed to the repo** (39–40) — set up `.gitignore` before writing any
   mail code, not after.
7. **Free-text instead of JSON in the report** (34).
8. **A false declaration** about a capture (22), a barrier (16), or the game count (38).
