"""Evidence for 03-11's mixing requirement and PLAN.md ADR P3-14.

Claim under test: under simultaneous moves, capture is a ONE-STEP GUESSING GAME,
so a deterministic thief is exploitable and a mixing thief is not.

Measured 2026-08-05 (seed 4242), swap rule excluded, both sides perfect-info:

    resolution  cop             thief          capture%   barriers
    strict      chase           any                  0%        0.0
    strict      greedy_barrier  any                  0%        2.0
    strict      mcts            deterministic       96%        6.1
    strict      mcts            mixing              36%        7.1
    engine      mcts            deterministic       88%        5.5
    engine      mcts            mixing              40%        7.8

CAVEATS, recorded so the numbers are not over-read:
  - The search cop's rollouts use the thief's real policy, i.e. a PERFECT opponent
    model. 96% is therefore an upper bound; the 36-40% figures are the honest ones.
  - `greedy_barrier` here is a component-size stand-in, NOT the shipped
    `strategy/barriers.py` (which scores BFS distance to a far corner). Read the 0%
    as "a greedy one-step barrier rule fails", not "our file fails".
  - The cop uses plain UCT. Lisý/Lanctot (NIPS 2013) show UCT is the most
    exploitable node rule for simultaneous-move games, so a regret-matching cop
    (ADR P3-13) should do BETTER than these numbers, not worse.
  - `resolution` brackets the unresolved 03-17 question: `strict` = capture on the
    thief's POST-move cell (B==D), `engine` = its PRE-move cell (B==C, what
    capture.py currently implements). The conclusion holds under both.

Run: uv run python scratchpad/mixed_thief.py
"""

from __future__ import annotations

import math
import random

SIZE = 7
NCELL = SIZE * SIZE
HORIZON = 35          # PARAMETERS.md Table 15 row 3
QUOTA = 14            # PARAMETERS.md Table 15 row 2
THIEF_START = 3 * SIZE + 3
COP_START = 0

NEI: list[tuple[int, ...]] = []
for _i in range(NCELL):
    _r, _c = divmod(_i, SIZE)
    NEI.append(tuple(
        (_r + _dr) * SIZE + _c + _dc
        for _dr, _dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        if 0 <= _r + _dr < SIZE and 0 <= _c + _dc < SIZE
    ))

DIST = [[abs(a // SIZE - b // SIZE) + abs(a % SIZE - b % SIZE)
         for b in range(NCELL)] for a in range(NCELL)]


def moves(cell: int, bar: int) -> list[int]:
    """Orthogonal step or stay, barrier-aware (book Sec 3.4)."""
    return [cell] + [n for n in NEI[cell] if not bar >> n & 1]


def spots(cop: int, bar: int, placed: int) -> list[int]:
    """Barrier candidates: adjacent to the cop, quota permitting."""
    if placed >= QUOTA:
        return []
    return [n for n in NEI[cop] if not bar >> n & 1]


def comp_size(cell: int, bar: int, blocked: int) -> int:
    seen, stack, size = 1 << cell, [cell], 0
    while stack:
        for n in NEI[stack.pop()]:
            if not bar >> n & 1 and not seen >> n & 1 and n != blocked:
                seen |= 1 << n
                stack.append(n)
        size += 1
    return size


def thief_deterministic(cop: int, thief: int, bar: int, rng) -> int:
    opts = moves(thief, bar)
    best = max(DIST[o][cop] for o in opts)
    return rng.choice([o for o in opts if DIST[o][cop] == best])


def thief_mixing(cop: int, thief: int, bar: int, rng) -> int:
    """03-11's safety filter, then UNIFORM over what survives it."""
    opts = [o for o in moves(thief, bar) if o != cop]
    safe = [o for o in opts if DIST[o][cop] >= 2]
    return rng.choice(safe if safe else opts)


THIEVES = {"deterministic": thief_deterministic, "mixing": thief_mixing}


def cop_chase(cop: int, thief: int, bar: int, placed: int, rng):
    opts = moves(cop, bar)
    best = min(DIST[o][thief] for o in opts)
    return (0, rng.choice([o for o in opts if DIST[o][thief] == best]))


def cop_greedy_barrier(cop: int, thief: int, bar: int, placed: int, rng):
    if DIST[cop][thief] <= 1:
        return cop_chase(cop, thief, bar, placed, rng)
    base = comp_size(thief, bar, cop)
    best_gain, best_cell = 0, None
    for cand in spots(cop, bar, placed):
        gain = base - comp_size(thief, bar | 1 << cand, cop)
        if gain > best_gain:
            best_gain, best_cell = gain, cand
    return (1, best_cell) if best_cell is not None else cop_chase(cop, thief, bar, placed, rng)


def resolve(action, cop, thief, bar, placed, thief_fn, rng, model):
    """One joint turn. Move XOR barrier (D-12). No swap rule -- capture.py has none."""
    kind, cell = action
    if kind == 0:
        ncop, nbar, nplaced = cell, bar, placed
    else:
        ncop, nbar, nplaced = cop, bar | 1 << cell, placed + 1
    if model == "engine":                       # capture vs the thief's PRE-move cell
        if ncop == thief or nbar >> thief & 1:
            return True, ncop, thief, nbar, nplaced
        return False, ncop, thief_fn(ncop, thief, nbar, rng), nbar, nplaced
    nthief = thief_fn(cop, thief, bar, rng)     # thief cannot see the cop's choice
    return (ncop == nthief or nbar >> nthief & 1), ncop, nthief, nbar, nplaced


def rollout(action, cop, thief, bar, placed, turn, thief_fn, rng, model) -> float:
    hit, cop, thief, bar, placed = resolve(
        action, cop, thief, bar, placed, thief_fn, rng, model)
    while not hit:
        turn += 1
        if turn >= HORIZON:
            return 0.0
        hit, cop, thief, bar, placed = resolve(
            cop_chase(cop, thief, bar, placed, rng), cop, thief, bar, placed,
            thief_deterministic, rng, model)
    return 1.0


def cop_search(cop, thief, bar, placed, rng, turn, thief_fn, model, sims):
    """Plain UCT -- see caveat 3 in the module docstring."""
    acts = [(0, m) for m in moves(cop, bar)] + [(1, b) for b in spots(cop, bar, placed)]
    if len(acts) == 1:
        return acts[0]
    wins, visits = [0.0] * len(acts), [0] * len(acts)
    for n in range(sims):
        i = max(range(len(acts)), key=lambda k: (
            1e9 if visits[k] == 0
            else wins[k] / visits[k] + 1.4 * math.sqrt(math.log(n + 1) / visits[k])))
        wins[i] += rollout(acts[i], cop, thief, bar, placed, turn, thief_fn, rng, model)
        visits[i] += 1
    return acts[max(range(len(acts)), key=lambda k: wins[k] / max(visits[k], 1))]


def play(cop_name, thief_name, model, rng, sims):
    cop, thief, bar, placed, turn = COP_START, THIEF_START, 0, 0, 0
    thief_fn = THIEVES[thief_name]
    while turn < HORIZON:
        if cop_name == "chase":
            act = cop_chase(cop, thief, bar, placed, rng)
        elif cop_name == "greedy_barrier":
            act = cop_greedy_barrier(cop, thief, bar, placed, rng)
        else:
            act = cop_search(cop, thief, bar, placed, rng, turn, thief_fn, model, sims)
        hit, cop, thief, bar, placed = resolve(
            act, cop, thief, bar, placed, thief_fn, rng, model)
        if hit:
            return True, placed
        turn += 1
    return False, placed


def main() -> None:
    print(f"{SIZE}x{SIZE}, {HORIZON} turns, quota {QUOTA}, perfect info, no swap rule\n")
    head = f"{'resolution':<12}{'cop':<16}{'thief':<15}{'capture%':>10}{'barriers':>10}"
    print(head + "\n" + "-" * len(head))
    for model in ("strict", "engine"):
        for cop_name in ("chase", "greedy_barrier", "search"):
            for thief_name in ("deterministic", "mixing"):
                n, sims = (25, 120) if cop_name == "search" else (300, 0)
                rng = random.Random(4242)
                caps = bars = 0
                for _ in range(n):
                    won, placed = play(cop_name, thief_name, model, rng, sims)
                    caps += won
                    bars += placed
                print(f"{model:<12}{cop_name:<16}{thief_name:<15}"
                      f"{100 * caps / n:>9.0f}%{bars / n:>10.1f}")


if __name__ == "__main__":
    main()
