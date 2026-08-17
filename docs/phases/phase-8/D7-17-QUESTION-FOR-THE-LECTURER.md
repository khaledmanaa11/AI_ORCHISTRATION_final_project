# D7-17 — a question for the lecturer, drafted by 08-04, **sent by a human**

**Status:** DRAFT, unsent · **Owner of the sending step:** the human, at 08-12/08-13 (any day from
now) · **To:** `rmisegal@gmail.com` (`docs/PARAMETERS.md` Addresses — *"Lecturer — general
correspondence"*; **not** the auto-report address) · **Subject line below.**

> **Claude does not send this.** Mailing the lecturer is an outward-facing, irreversible act and
> sits with the three human-gated plans. What is automated here is the *drafting*, so the human
> reviews and sends rather than composes.

---

## Why this is a question and not a decision

`game_id` is **negotiated with the peer at handshake** (D-61). Redefining what it identifies is
therefore a change to what two independently-written agents agree on — a protocol decision over a
value we do not solely control, not an artifact-writer's choice. 07-07 refused to invent an id
scheme for exactly this reason and 08-04 does not overturn that refusal: inventing one would be the
kind of invention [CLAUDE.md](../../../CLAUDE.md)'s first prohibition forbids, in a file the
document fixes the name and fields of.

And the book pulls two ways. Both sides are quoted below verbatim, because the whole question is
that they do not agree.

## The two citations, quoted

**`docs/PARAMETERS.md:157-159`** — the artifact table's preamble, reading `game_id` as a **series**
id with a match number inside it:

> All four carry a shared `game_uid`, and each filename embeds the game identifier `game_id` plus
> the match number `<NN>`, so files from different matches can never be confused.

**`docs/PARAMETERS.md:168`** — the same reading, for the file that is actually scored:

> `result_<game_id>.json` | Final results summary **across all sub-games**. **This is the mandatory
> report emailed to the lecturer.**

**`docs/PARAMETERS.md:72`** — Table 17 row 5, which makes that aggregate **score-bearing**:

> `[tie score]` | Each side, when **aggregate score across all sub-games against one opponent** ends
> level | **2** | **fixed**

**`docs/PARAMETERS.md:86`** — rule 52, pulling the other way:

> Against each opponent there is **one scoring game only** — no rematches for points. Unscored
> warm-up games are permitted and encouraged (rule 52).

## What our implementation does today, measured

`agent_entrypoint.run_agent` mints `secrets.token_hex(8)` per game and then adopts the peer's
negotiated value (D-61). So today's `game_id` identifies **one game**: a production series file
holds exactly one sub-game and `<NN>` is `01` on both seats. Measured again on the real
`dev_launch` game 08-04 ran (`game_id` `397b3503b1bfa996`): one sub-game, `<NN>` = `01`, both seats.

The accumulator itself is correct and is proven over two sub-games sharing a `game_id`
(`test_the_series_total_is_the_sum_of_two_sub_games`, and proven wrong when the accumulation is
removed). **What is missing is a series-scoped identifier to key on** — not the arithmetic.

## The question, as it would be sent

> **Subject:** Cops-and-robbers final project — `game_id`: per game, or per series against one
> opponent?
>
> Dear Dr Segal,
>
> A question about the required JSON artifacts, before we play our league games.
>
> `docs/PARAMETERS.md` describes `result_<game_id>.json` as the "final results summary across all
> sub-games", and the tie rule settles on the "aggregate score across all sub-games against one
> opponent" — both of which read `game_id` as identifying a **series**, with `<NN>` numbering the
> matches inside it. But the rules also say that against each opponent there is **one scoring game
> only**, with unscored warm-ups permitted. Our agents negotiate a fresh `game_id` at each
> handshake, so today a series file contains exactly one sub-game and `<NN>` is always `01`.
>
> Could you confirm which of the following you intend?
>
> 1. **`game_id` is per game.** One scoring game per opponent means one sub-game per series, and
>    the current artifact is already correct; the "across all sub-games" wording is then simply the
>    general case.
> 2. **`game_id` is per opponent** — agreed with that opponent at the first handshake and reused
>    for their warm-ups and their scoring game, so the aggregate forms across all of them.
> 3. **Something else** — e.g. a separate series identifier alongside `game_id`.
>
> We ask rather than choose because `game_id` is negotiated with the opponent, so redefining it
> changes the protocol between two independently written agents; and because a misreported
> aggregate would touch the games-played and reporting rules we would rather not test.
>
> Thank you,
> *(team code and names)*

## The three options and what each costs

| # | Option | Cost |
|---|---|---|
| **(a)** | **Leave it.** One scored game per opponent (rule 52) means one sub-game per series, and the artifact is already correct for that. | If a lead team asks for an aggregated multi-sub-game result, we have no id to aggregate on. |
| **(b)** | **Reuse one `game_id` across every game against the same opponent**, agreed at the first handshake. | It must be agreed with a team we do not control, and a peer that mints a fresh id per game — as we do today — would break it **silently**. |
| **(c)** | **Add a separate series id** beside `game_id`, purely local, and key the accumulator on it. | A field `docs/PARAMETERS.md` does not name, in a grader-facing artifact whose four names and fields the document fixes. |

**The cheapest correct move before choosing is to ask**, which is what this file is for. Rule 38
territory is one misreported aggregate away and the question costs a message.

## What 08-04 did and did not do

- **Did:** draft this, with both citations quoted and the three costed options carried over from
  [`GATE-7-MEASUREMENT.md`](../phase-7/GATE-7-MEASUREMENT.md) §"D7-17 in full".
- **Did not:** invent an id scheme, change `game_id`'s minting, or touch the handshake. The
  declaration artifact 08-04 wired uses `ctx.game_uid` for both `game_uid` and `game_id`, exactly as
  the other three artifacts already do — so whichever answer arrives, one call site changes.
- **Did not:** send anything. No mail, no credentials, no account.
