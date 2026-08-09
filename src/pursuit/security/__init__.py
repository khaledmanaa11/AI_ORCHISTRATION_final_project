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
