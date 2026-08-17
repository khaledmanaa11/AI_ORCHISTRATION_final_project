"""Phase-6 cryptographic core: commit-reveal hashing, the state-record shape,
and the durable nonce ledger (SEC-01, SEC-03, SEC-04).

Every file this package gains, now and in 06-02/06-03, imports `pursuit.sdk`
or `pursuit.shared` only -- never `pursuit.network` -- with exactly ONE
narrow, deliberate exception: `commit_pack.py` imports `canonical_json` and
`digests_match` from `pursuit.network.config_hash`, the project's one
canonical JSON serializer and constant-time digest comparator (D-59,
QUAL-02). That module is a pure, dependency-free hashing leaf (only
`hashlib`/`json`/`secrets`/`pathlib`) with zero import of `AgentContext` or
the turn loop, so the exception does not reintroduce the coupling this
package's boundary exists to prevent. Do not add a second
`json.dumps(sort_keys=True, ...)` call anywhere in this package to avoid the
import -- see `commit_pack.py`'s own docstring for the full reasoning.
"""

#: Sec14 professional packaging. This package imports nothing, so `__all__`
#: declares its SUBMODULE INVENTORY -- the documented meaning of `__all__` on a
#: package. Derived from the tracked tree and re-derived on every run by
#: `tests/unit/test_package_exports.py`, so a module added here without being
#: exported, or exported after being deleted, fails that test rather than
#: leaving a decorative list behind.
__all__ = (
    "audit", "audit_record", "audit_shape", "audit_state", "commit_pack", "ledger",
    "state_record", "step0_collect", "step0_sign",
)
