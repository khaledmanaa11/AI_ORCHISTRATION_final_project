"""Reliability: a bounded, adaptive per-opponent, per-game trust coefficient
(D-51 -- a DISCLOSED REVISION of D-40's "fixed" framing, taken under the
autonomy directive).

Book Sec6.4, p.47 (PDF 63): "with every incoming hint the side applies
Bayes' rule ... with a prior reliability coefficient for the text -- since
the text may be a lie." D-40 first read that coefficient as fixed; Sec4.4's
own worked example (p.30 / PDF 46) shows it MOVING -- a caught lie makes the
cop "lower the trust coefficient it assigns to that opponent's verbal
declarations." A constant number would leave the book's most concrete
mechanism unimplemented, so this module keeps the coefficient adaptive.

D-40's OTHER number -- the fixed mixing weight `w` in
`strategy/belief_hint.py`'s Bayes formula -- is UNCHANGED by this revision;
it is a separate `belief.json` field (`hint_likelihood.weight`) from this
module's `prior` (`reliability.prior`), not the same number twice. See
`belief_hint.py`'s docstring.

The clamp to `[r_min, r_max]` is the point, not a defensive afterthought: at
0 an honest opponent's information is wasted, at 1 a fluent liar is trusted
completely. Both bounds are configured, both strictly inside (0, 1), and no
sequence of observations can escape them (`shared/reliability_config.py`
validates this at load).

One instance per opponent, per game, reset at handshake -- rule 52 credits
exactly one counted game per opponent, and Appendix vav Sec2 rule 5 permits
an opponent to change its code between games, so a coefficient carried over
from a warm-up would describe a peer the scored game need not resemble. This
module holds no persistence of any kind: construct a fresh `Reliability` per
game, never save or load one.
"""

from __future__ import annotations

from dataclasses import dataclass

from pursuit.shared.reliability_config import ReliabilityParams


@dataclass
class Reliability:
    """One opponent's trust coefficient for one game. Mutable, like
    `BeliefMap`/`ScentField` -- `observe()` advances it in place across a
    live game, unlike a frozen `GameState` snapshot (D-12)."""

    config: ReliabilityParams

    def __post_init__(self) -> None:
        """Seed at the configured prior -- no observations yet this game."""
        self._value = self.config.prior

    @property
    def value(self) -> float:
        """The current coefficient. Always in `[config.r_min, config.r_max]`."""
        return self._value

    def observe(self, contradiction_score: float) -> None:
        """One hint's worth of evidence.

        `contradiction_score` is `scent_check.contradicts()`'s own output,
        in [0, 1] -- the strength of disagreement between a decoded claim
        and the trail we actually sensed. A POSITIVE score pulls the
        coefficient DOWN by `contradiction_step * contradiction_score`: a
        stronger disagreement earns a bigger step. An EXACTLY-zero score
        (the hint was fully consistent with the trail, or there was nothing
        to check) instead pulls the coefficient UP, a `recovery_rate`
        fraction of the remaining distance to the configured prior -- never
        overshooting it, since the pull is proportional. Either way the
        result is clamped to `[r_min, r_max]` before returning.
        """
        if not 0.0 <= contradiction_score <= 1.0:
            raise ValueError(
                "Reliability.observe: contradiction_score must be in [0, 1], "
                f"got {contradiction_score}"
            )
        if contradiction_score > 0.0:
            self._value -= self.config.contradiction_step * contradiction_score
        else:
            self._value += self.config.recovery_rate * (self.config.prior - self._value)
        self._value = min(self.config.r_max, max(self.config.r_min, self._value))
