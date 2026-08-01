"""Offline training harness for the Q-learning strategy module (STRAT-06).

This package is offline tooling only: nothing under src/pursuit/ imports it
(training/ imports FROM src/pursuit/, never the reverse). Episodes step
pursuit.sdk.engine directly and never pursuit.network -- training must never
touch the FastMCP transport layer (D-17).
"""
