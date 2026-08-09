"""Fail-loud config loader for scent.json -- the locked pheromone model (D-46,
D-49, D-50, LANG-04, LANG-07).

ScentKey lives HERE, not in pursuit.config_keys, deliberately breaking the
convention ConfigKey/NetworkConfigKey/StrategyKey set: config_keys.py is
already at its 150-code-line ceiling (Segal Table 5) and Phase 4's four new
negotiated-block enums (Scent/Language/Belief/Deception) would breach it. The
standing rule is split files, never compress code to fit -- so this enum
ships beside the one loader that validates it, extending the precedent
ResolutionKey already set for a negotiated block kept out of game_params.json.

load_scent_model() validates the WHOLE locked payload the book's Sec4.5 red
box requires both peers to exchange and verify before locking: the kernel
table, source/decay/window, and the worked numeric example. Kernel-shape and
worked-example validation live in scent_kernel.py, split out at this same
150-line ceiling once the two modules together (kernel checks + JSON
loading/digest) no longer fit in one file.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pursuit.network.config_hash import canonical_json
from pursuit.shared.loader_helpers import require_float, require_int, require_key, require_str
from pursuit.shared.scent_kernel import SCENT_SOURCE, check_worked_example, validated_kernel


class ScentKey(str, Enum):
    """Field names in scent.json (D-46, D-50). See module docstring for why
    this enum lives here instead of pursuit.config_keys."""

    VERSION = "version"
    SOURCE = "source"
    DECAY = "decay"
    WINDOW = "window"
    KERNEL = "kernel"
    WORKED_EXAMPLE = "worked_example"
    WORKED_INITIAL = "initial"
    WORKED_AFTER = "after_one_turn"

    def __str__(self) -> str:
        """Return the bare key string so json.dumps emits the field name."""
        return self.value


@dataclass(frozen=True)
class ScentModel:
    """The whole locked payload: Table 16's three fixed values, the Figure-4
    kernel, and the worked example both peers must agree on (Sec4.5).

    Constructed only by load_scent_model() -- callers never build this
    directly. `kernel` is a tuple of tuples (window rows of window floats
    each) so the whole object stays immutable, matching GameState's
    frozen-dataclass convention (D-12).
    """

    version: str
    source: float
    decay: float
    window: int
    kernel: tuple[tuple[float, ...], ...]
    worked_example_initial: float
    worked_example_after: float


def load_scent_model(path: Path | str) -> ScentModel:
    """Load and validate a scent.json file into a ScentModel.

    Raises
    ------
    KeyError
        If a required top-level or worked_example key is absent.
    TypeError
        If a field carries the wrong type.
    ValueError
        If window is even, the kernel is not window x window, an entry falls
        outside [0, source], the kernel is not symmetric under both
        reflections and the transpose, the centre entry is not source, or
        worked_example disagrees with source/decay.
    """
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)

    version = require_str(data, ScentKey.VERSION.value, source=SCENT_SOURCE)
    source = require_float(data, ScentKey.SOURCE.value, source=SCENT_SOURCE)
    decay = require_float(data, ScentKey.DECAY.value, source=SCENT_SOURCE)
    window = require_int(data, ScentKey.WINDOW.value, source=SCENT_SOURCE)
    if window % 2 == 0:
        raise ValueError(f"{SCENT_SOURCE}: 'window' must be odd, got {window}")

    kernel_raw = require_key(data, ScentKey.KERNEL.value, source=SCENT_SOURCE)
    kernel = validated_kernel(kernel_raw, window=window, source_value=source)

    worked = require_key(data, ScentKey.WORKED_EXAMPLE.value, source=SCENT_SOURCE)
    worked_initial = require_float(worked, ScentKey.WORKED_INITIAL.value, source=SCENT_SOURCE)
    worked_after = require_float(worked, ScentKey.WORKED_AFTER.value, source=SCENT_SOURCE)
    check_worked_example(worked_initial, worked_after, source=source, decay=decay)

    return ScentModel(
        version=version,
        source=source,
        decay=decay,
        window=window,
        kernel=kernel,
        worked_example_initial=worked_initial,
        worked_example_after=worked_after,
    )


def _as_payload(model: ScentModel) -> dict:
    """Reconstruct the exact nested JSON shape load_scent_model() parses, for
    scent_digest() to hash (D-46) -- the round-trip inverse of loading."""
    return {
        str(ScentKey.VERSION): model.version,
        str(ScentKey.SOURCE): model.source,
        str(ScentKey.DECAY): model.decay,
        str(ScentKey.WINDOW): model.window,
        str(ScentKey.KERNEL): [list(row) for row in model.kernel],
        str(ScentKey.WORKED_EXAMPLE): {
            str(ScentKey.WORKED_INITIAL): model.worked_example_initial,
            str(ScentKey.WORKED_AFTER): model.worked_example_after,
        },
    }


def scent_digest(model: ScentModel) -> str:
    """SHA-256 hex digest of the canonical JSON of the whole locked payload
    (D-46) -- kernel, source, decay, window AND the worked example together,
    reusing network/config_hash.py's canonical_json rather than a second
    serialiser. The example is inside the hash on purpose: Sec4.5 requires
    both sides to verify it, not just the raw model parameters.
    """
    return hashlib.sha256(canonical_json(_as_payload(model)).encode("utf-8")).hexdigest()
