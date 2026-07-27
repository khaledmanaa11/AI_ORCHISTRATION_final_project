# Strategy Module

> **Status: scaffold.** Structure required by §6.2; content is filled in during
> **Phase 3** (blind strategy module) and extended in **Phase 4** (scent + language).
> Sections marked _TBD_ are deliberately unfilled — do not invent values here, and do not
> let a planning agent fill them speculatively. Numbers come from
> [PARAMETERS.md](PARAMETERS.md).

## Why this module is separate

The book requires the decision logic to live in a module of its own, distinct from the
networking layer (§6.2). The orchestrator handles message passing, signature locking, and
turn management — deliberately *ignorant* of what makes a good move. Separating the two
means the generic communication plumbing can be tested without the strategy, and the
strategy can be swapped or retrained without touching the protocol.

## Where it plugs in

Reached from the `PeerRuntime` at one exact point: immediately after the incoming hint is
parsed, and before the outgoing Commit is packed.

```
incoming hint + scent → hint decode (parse text) → belief update (Bayes rule)
    → Q-policy move choice → LLM bluff text (deception) → Commit pack (out)
```

**Invariant:** the move is chosen by the algorithm at the `Q-policy` step. The language
model participates only at the two ends — decoding the opponent's words on the way in, and
writing our hint on the way out. It never selects the move (§6.2, rule 25).

## Wiring

Declared in the **private** per-peer config file under the `[strategy]` section:

```toml
[strategy]
police_class = "package.module:ClassName"   # TBD — set in Phase 3
thief_class  = "package.module:ClassName"   # TBD — set in Phase 3
```

Both classes inherit from `BrainBase` and override:

| Method | Responsibility | Applies to |
|---|---|---|
| `_pick_move` | Choose this turn's move | cop and thief |
| `_decide_move` | Barrier placement selection | cop only |

## Chosen approach

**Reinforcement learning (tabular Q-Learning), with a heuristic fallback.**

The book treats RL as one of three equal-citizen tracks (§6.3.1) — pure heuristics
(Bayes + Manhattan, the reference default), a bespoke heuristic algorithm, or RL. We chose
RL; the rationale is argued in [PROJECT_GUIDE.md §B](PROJECT_GUIDE.md#b-why-reinforcement-learning-expanded).

### Components

| Component | Purpose | Status |
|---|---|---|
| Belief map | Probability grid over opponent position, updated by Bayes rule from scent + hints | _TBD — Phase 4_ |
| State encoding | How `(own pos, belief, barriers, turn)` compresses into a Q-table key | _TBD — Phase 3_ |
| Action space | 4 orthogonal moves + stay; plus barrier placement for the cop | Fixed by spec |
| Reward function | Derived from the scoring table (§1.3 states R "translates directly" from it) | See [PARAMETERS.md](PARAMETERS.md) Table 17 |
| Exploration | ε-greedy | _TBD — ε schedule, Phase 3_ |
| Hyperparameters | `α` learning rate, `γ` discount factor | _TBD — Phase 3_ |
| Fallback policy | Bayes + Manhattan, used when the Q-table has not visited a state | _TBD — Phase 3_ |

### Training

No training happens during a league match — the policy must arrive trained.

- Offline self-play before matches; also against the reference implementation
  (`https://github.com/rmisegal/Game-P2P-Cop-Chase`).
- **Instrument from the first training run.** Learning curves are a mandatory README
  section when RL is used (§9.4.2 item 4, rule 42), and reconstructing them afterwards is
  painful.

### Known risk

The environment is non-stationary: the opponent is also learning, so standard convergence
guarantees do not hold. The heuristic fallback exists partly to bound the damage when the
learned policy meets a situation its training never covered.

## Deception policy

The hint channel is the only *voluntary* information channel — hints may be lies, and the
`intent` flag (`truth | lie`) is committed in advance so a side cannot retroactively claim
it was being honest (§5.3).

| Question | Decision |
|---|---|
| When to lie vs. tell the truth | _TBD — Phase 4_ |
| How the bluff text is generated | LLM, constrained to `[hint word limit]` words |
| How opponent hints are weighted against scent evidence | _TBD — Phase 4_ |

Truthfulness is mandatory in exactly one place: **at the moment of capturing a thief**,
the declaration must be true (rules 21–22). Lying there is immediate disqualification.

## Open questions for Phase 3

- Does the state space stay small enough for a tabular Q-table at 7×7 with barriers, or
  does the barrier layout need to be abstracted into features?
- Separate Q-tables for cop and thief, or one shared representation with a role flag?
- How many self-play episodes before the policy beats the Bayes + Manhattan baseline?
  (This is the success criterion for the Phase 3 gate.)
