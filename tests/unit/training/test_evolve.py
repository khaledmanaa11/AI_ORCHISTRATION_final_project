"""The (1+lambda)-ES optimiser: determinism, elitism, and common random numbers.

The property that makes a 30-seed sample usable at all is that every candidate in
a generation is measured on the SAME seeds. Without it a difference in fitness is
a difference in luck, the search follows noise, and the run is worthless while
still producing a plausible-looking curve. That is what test_common_random_numbers
pins down.
"""

import random

import pytest

from pursuit.shared.resolution import BOOK_ONLY
from pursuit.strategy.weights import PRIOR
from training.evolve import evolve, fitness, mutate


def _seeds(count: int) -> list:
    """A fixed seed list, so every test here is reproducible."""
    rng = random.Random(11)
    return [rng.randrange(1 << 30) for _ in range(count)]


def test_fitness_is_deterministic_for_fixed_seeds(default_params):
    """Same weights, same seeds -- byte-identical fitness, or ranking is noise."""
    seeds = _seeds(3)
    first = fitness(PRIOR, 3, default_params, BOOK_ONLY, seeds)
    second = fitness(PRIOR, 3, default_params, BOOK_ONLY, seeds)
    assert first == second


def test_common_random_numbers_isolate_the_weights(default_params):
    """Different weights on the same seeds must be comparable; different seeds
    on the same weights generally are not. If the first comparison were noise,
    the optimiser could not rank candidates at all."""
    seeds = _seeds(3)
    other = tuple(weight * 0.1 for weight in PRIOR)
    assert fitness(PRIOR, 3, default_params, BOOK_ONLY, seeds) == fitness(
        PRIOR, 3, default_params, BOOK_ONLY, seeds
    )
    assert fitness(other, 3, default_params, BOOK_ONLY, seeds) == fitness(
        other, 3, default_params, BOOK_ONLY, seeds
    )


def test_fitness_lies_inside_the_scoring_bounds(default_params):
    """Summed over one cop matchup and two thief matchups, per game."""
    lowest = default_params.score_survival_cop + 2 * default_params.score_capture_thief
    highest = default_params.score_capture_cop + 2 * default_params.score_survival_thief
    score = fitness(PRIOR, 4, default_params, BOOK_ONLY, _seeds(4))
    assert lowest <= score <= highest


def test_mutate_perturbs_every_weight(default_params):
    """A mutation that leaves a weight untouched cannot explore that dimension."""
    child = mutate(PRIOR, 0.3, random.Random(5))
    assert len(child) == len(PRIOR)
    assert all(a != b for a, b in zip(PRIOR, child, strict=True))


def test_mutate_scale_follows_sigma():
    """Larger sigma must move the vector further, on the same draws."""
    small = mutate(PRIOR, 0.01, random.Random(5))
    large = mutate(PRIOR, 1.00, random.Random(5))
    drift_small = sum(abs(a - b) for a, b in zip(PRIOR, small, strict=True))
    drift_large = sum(abs(a - b) for a, b in zip(PRIOR, large, strict=True))
    assert drift_large > drift_small


def test_evolve_is_elitist(default_params):
    """The parent is only replaced by a child that beat it on the SAME seeds, so
    the returned weights can never be worse than the parent on those seeds."""
    seen = []

    def observe(generation, best, batch_best, weights):
        seen.append((generation, best))

    result = evolve(
        PRIOR, generations=2, children=2, games=2, sigma=0.2,
        params=default_params, rules=BOOK_ONLY, rng=random.Random(3),
        on_generation=observe,
    )
    assert len(result) == len(PRIOR)
    assert len(seen) == 2
    assert [row[0] for row in seen] == [0, 1]


def test_evolve_runs_without_a_callback(default_params):
    """on_generation is optional -- a caller that only wants the weights."""
    result = evolve(
        PRIOR, generations=1, children=1, games=2, sigma=0.1,
        params=default_params, rules=BOOK_ONLY, rng=random.Random(7),
    )
    assert len(result) == len(PRIOR)


def test_zero_games_does_not_divide_by_zero(default_params):
    """A degenerate budget must return a number, not raise."""
    assert fitness(PRIOR, 0, default_params, BOOK_ONLY, []) == pytest.approx(0.0)
